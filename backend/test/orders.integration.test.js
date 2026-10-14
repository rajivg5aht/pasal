import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import mongoose from "mongoose";
import session from "express-session";
import request from "supertest";
import { createApp } from "../src/app.js";
import { MongoRepository, User, Product } from "../src/repository.js";
import {
  DemoRepository,
  DemoProduct,
  DemoProfile,
} from "../src/demo-repository.js";
import {
  OrderService,
  DemoOrder,
  InventoryAudit,
  checkoutInput,
} from "../src/orders.js";

test("checkout validation rejects duplicate lines and non-demo identifiers", () => {
  const base = {
    key: randomUUID(),
    lines: [{ productId: "demo-mug", quantity: 1 }],
    expectedTotalNpr: 600,
    delivery: { recipient: "Test shopper", area: "Kathmandu", note: "" },
    simulationAccepted: true,
  };
  assert.equal(checkoutInput.safeParse(base).success, true);
  assert.equal(
    checkoutInput.safeParse({ ...base, lines: [...base.lines, ...base.lines] })
      .success,
    false,
  );
  assert.equal(
    checkoutInput.safeParse({
      ...base,
      lines: [{ productId: "461686", quantity: 1 }],
    }).success,
    false,
  );
  assert.equal(
    checkoutInput.safeParse({ ...base, simulationAccepted: false }).success,
    false,
  );
});

test(
  "transactional orders preserve stock, prices, ownership and idempotency",
  { skip: process.env.RUN_ORDER_TESTS !== "1" },
  async () => {
    const database = "pasal_order_test_" + randomUUID().replaceAll("-", "");
    await mongoose.connect(
      `mongodb://127.0.0.1:27118/${database}?replicaSet=pasalOrderTest`,
      { serverSelectionTimeoutMS: 5000, autoCreate: false, autoIndex: false },
    );
    let owns = false;
    try {
      assert.equal(
        (await mongoose.connection.db.listCollections().toArray()).length,
        0,
      );
      owns = true;
      for (const model of [
        User,
        DemoProduct,
        DemoProfile,
        DemoOrder,
        InventoryAudit,
      ])
        await model.createCollection();
      const app = createApp({
        repository: new MongoRepository(),
        demoRepository: new DemoRepository(),
        store: new session.MemoryStore(),
        sessionSecret: "fixture-secret-".repeat(4),
        recommend: async () => ({ items: [] }),
      });
      const origin = "http://127.0.0.1:5173",
        buyer = request.agent(app),
        other = request.agent(app),
        admin = request.agent(app);
      const register = async (agent, email) =>
        (
          await agent
            .post("/api/auth/register")
            .set("Origin", origin)
            .send({
              name: "Demo tester",
              email,
              password: "fixture-password-123",
            })
            .expect(201)
        ).body.user.id;
      const buyerId = await register(buyer, "buyer@example.test"),
        otherId = await register(other, "other@example.test"),
        adminId = await register(admin, "admin@example.test");
      await User.updateOne({ _id: adminId }, { $set: { role: "admin" } });
      const data = {
        _id: "demo-mug",
        title: "Synthetic mug",
        category: "Home",
        subcategory: "Mugs",
        description: "Synthetic fixture mug",
        priceNpr: 600,
        image: "mug",
        attributes: [],
        available: true,
        stock: 3,
      };
      await DemoProduct.create([
        data,
        {
          ...data,
          _id: "demo-tea",
          title: "Synthetic tea",
          priceNpr: 200,
          stock: 0,
        },
      ]);
      const repo = new DemoRepository();
      await repo.profile(buyerId);
      await repo.profile(otherId);
      const putCart = async (id, lines) =>
        DemoProfile.updateOne({ _id: id }, { $set: { cart: lines } });
      const input = (lines, total) => ({
        key: randomUUID(),
        lines,
        expectedTotalNpr: total,
        delivery: {
          recipient: "Fictional shopper",
          area: "Kathmandu",
          note: "Simulation",
        },
        simulationAccepted: true,
      });
      const place = (agent, body) =>
        agent.post("/api/demo/orders").set("Origin", origin).send(body);
      await request(app).get("/api/demo/orders").expect(401);
      await buyer.get("/api/admin/orders").expect(403);
      assert.equal(
        (await buyer.get("/api/demo/checkout-status")).body.available,
        true,
      );
      // A failure on the second product rolls back the first product's decrement.
      const both = [
        { productId: "demo-mug", quantity: 1 },
        { productId: "demo-tea", quantity: 1 },
      ];
      await putCart(buyerId, both);
      await place(buyer, input(both, 800)).expect(409);
      assert.equal((await DemoProduct.findById("demo-mug")).stock, 3);
      assert.equal(await DemoOrder.countDocuments(), 0);
      assert.equal((await DemoProfile.findById(buyerId)).cart.length, 2);
      const lines = [{ productId: "demo-mug", quantity: 2 }];
      await putCart(buyerId, lines);
      await place(buyer, input(lines, 1)).expect(409); // Server prices, never client prices.
      assert.equal((await DemoProduct.findById("demo-mug")).stock, 3);
      const body = input(lines, 1200);
      const first = (await place(buyer, body).expect(201)).body.order;
      const replay = (await place(buyer, body).expect(200)).body;
      assert.equal(replay.order._id, first._id);
      assert.equal(replay.replay, true);
      assert.equal((await DemoProduct.findById("demo-mug")).stock, 1);
      assert.equal((await DemoProfile.findById(buyerId)).cart.length, 0);
      assert.equal(first.payment, "simulation_no_charge");
      assert.equal(first.customerId, undefined);
      assert.equal(first.requestHash, undefined);
      assert.equal(first.history[0].actor, undefined);
      await place(buyer, { ...body, expectedTotalNpr: 999 }).expect(409);
      assert.equal((await other.get("/api/demo/orders")).body.orders.length, 0);
      await other
        .post(`/api/demo/orders/${first._id}/cancel`)
        .set("Origin", origin)
        .send({})
        .expect(409);
      await buyer
        .post(`/api/demo/orders/${first._id}/cancel`)
        .set("Origin", origin)
        .send({})
        .expect(200);
      await buyer
        .post(`/api/demo/orders/${first._id}/cancel`)
        .set("Origin", origin)
        .send({})
        .expect(409);
      assert.equal((await DemoProduct.findById("demo-mug")).stock, 3);
      // Competing customers cannot oversell the same three units.
      await putCart(buyerId, lines);
      await putCart(otherId, lines);
      const outcomes = await Promise.all([
        place(buyer, input(lines, 1200)),
        place(other, input(lines, 1200)),
      ]);
      assert.deepEqual(outcomes.map((r) => r.status).sort(), [201, 409]);
      assert.equal((await DemoProduct.findById("demo-mug")).stock, 1);
      const winning = outcomes.find((r) => r.status === 201).body.order;
      const patch = (expected, status) =>
        admin
          .patch(`/api/admin/orders/${winning._id}`)
          .set("Origin", origin)
          .send({ expected, status });
      await patch("placed", "delivered").expect(409);
      await patch("placed", "confirmed").expect(200);
      await patch("placed", "cancelled").expect(409);
      await patch("confirmed", "dispatched").expect(200);
      await patch("dispatched", "delivered").expect(200);
      await patch("delivered", "cancelled").expect(409);
      await buyer
        .put("/api/admin/inventory/demo-mug")
        .set("Origin", origin)
        .send({ expected: 1, stock: 5 })
        .expect(403);
      await admin
        .put("/api/admin/inventory/demo-mug")
        .set("Origin", origin)
        .send({ expected: 2, stock: 5 })
        .expect(409);
      await admin
        .put("/api/admin/inventory/demo-mug")
        .set("Origin", origin)
        .send({ expected: 1, stock: 5 })
        .expect(200);
      assert.equal(await InventoryAudit.countDocuments(), 1);
      assert.equal((await DemoProduct.findById("demo-mug")).stock, 5);
      assert.equal(await Product.countDocuments(), 0);
      assert.equal((await User.findById(buyerId)).eventCount, 0);
      // Existing sessions lose order-admin rights immediately on role revocation.
      await User.updateOne({ _id: adminId }, { $set: { role: "customer" } });
      await admin.get("/api/admin/orders").expect(403);
    } finally {
      if (
        owns &&
        mongoose.connection.name === database &&
        /^pasal_order_test_[a-f0-9]+$/.test(database)
      )
        await mongoose.connection.dropDatabase();
      await mongoose.disconnect();
    }
  },
);

test(
  "checkout fails closed on a standalone database",
  { skip: process.env.RUN_MONGO_TESTS !== "1" },
  async () => {
    await mongoose.connect("mongodb://127.0.0.1:27017/pasal", {
      serverSelectionTimeoutMS: 3000,
    });
    try {
      const service = new OrderService();
      if (!(await service.available()))
        await assert.rejects(
          () =>
            service.transaction(() => {
              throw new Error("Must not run");
            }),
          /transaction-ready/,
        );
    } finally {
      await mongoose.disconnect();
    }
  },
);
