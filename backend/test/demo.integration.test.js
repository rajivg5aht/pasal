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

test(
  "isolated demo catalogue, admin authorization, consent and shopping workflows",
  { skip: process.env.RUN_MONGO_TESTS !== "1" },
  async () => {
    const database = "pasal_test_" + randomUUID().replaceAll("-", "");
    await mongoose.connect("mongodb://127.0.0.1:27017/" + database, {
      autoCreate: false,
      autoIndex: false,
    });
    let owns = false;
    try {
      assert.equal(
        (await mongoose.connection.db.listCollections().toArray()).length,
        0,
      );
      owns = true;
      const app = createApp({
        repository: new MongoRepository(),
        demoRepository: new DemoRepository(),
        store: new session.MemoryStore(),
        sessionSecret: "fixture-secret-".repeat(4),
        recommend: async (profile) => {
          assert.equal(profile.event_count, 0);
          assert.deepEqual(profile.recent_items, []);
          return {
            items: [],
            strategy: "global_popularity",
            configuration: "fixture",
          };
        },
        serviceHealth: async () => ({ status: "ready" }),
      });
      const origin = "http://127.0.0.1:5173";
      const customer = request.agent(app),
        admin = request.agent(app);
      const registration = (agent, email) =>
        agent
          .post("/api/auth/register")
          .set("Origin", origin)
          .send({ name: "Test", email, password: "fixture-password-123" });
      await request(app).get("/api/admin/overview").expect(401);
      await request(app)
        .post("/api/auth/register")
        .set("Origin", origin)
        .send({
          name: "Bad",
          email: "bad@example.test",
          password: "fixture-password-123",
          role: "admin",
        })
        .expect(400);
      await registration(customer, "customer@example.test").expect(201);
      await customer.get("/api/admin/overview").expect(403);
      await customer
        .post("/api/admin/products")
        .set("Origin", origin)
        .send({})
        .expect(403);
      await registration(admin, "operator@example.test").expect(201);
      await User.updateOne(
        { email: "operator@example.test" },
        { $set: { role: "admin" } },
      );
      assert.equal((await admin.get("/api/me")).body.user.role, "admin");
      const data = {
        title: "Synthetic test mug",
        category: "Home",
        subcategory: "Mugs",
        description: "An explicitly synthetic fixture mug.",
        priceNpr: 600,
        image: "mug",
        attributes: ["Synthetic ceramic"],
        available: true,
      };
      await admin.post("/api/admin/products").send(data).expect(403);
      await admin
        .post("/api/admin/products")
        .set("Origin", origin)
        .send({ ...data, _id: "461686" })
        .expect(400);
      await admin
        .post("/api/admin/products")
        .set("Origin", origin)
        .send({ ...data, image: "https://example.test/tracker" })
        .expect(400);
      const created = (
        await admin
          .post("/api/admin/products")
          .set("Origin", origin)
          .send(data)
          .expect(201)
      ).body.product;
      assert.match(created._id, /^demo-/);
      assert.equal(created.provenance, "synthetic_demo");
      assert.equal(
        (await customer.get("/api/demo/products?query=mug")).body.products
          .length,
        1,
      );
      assert.equal(
        (await customer.get("/api/demo/products?query=%5B")).body.products
          .length,
        0,
      );
      await customer.get("/api/demo/products/461686").expect(400);
      await customer.get("/api/demo/profile").expect(200);
      await customer
        .post("/api/demo/events")
        .set("Origin", origin)
        .send({ productId: created._id, type: "view" })
        .expect(409);
      await customer
        .put("/api/demo/privacy")
        .set("Origin", origin)
        .send({ personalization: true, selectedCategories: ["Home"] })
        .expect(200);
      await customer
        .post("/api/demo/events")
        .set("Origin", origin)
        .send({ productId: created._id, type: "view" })
        .expect(204);
      await customer
        .put("/api/demo/wishlist")
        .set("Origin", origin)
        .send({ productId: created._id, add: true })
        .expect(200);
      await customer
        .put("/api/demo/cart")
        .set("Origin", origin)
        .send({ productId: created._id, quantity: 2 })
        .expect(200);
      await customer
        .put("/api/demo/cart")
        .set("Origin", origin)
        .send({ productId: created._id, quantity: 11 })
        .expect(400);
      await customer
        .post("/api/events")
        .set("Origin", origin)
        .send({ itemid: created._id, type: "view" })
        .expect(400);
      await customer
        .put("/api/demo/cart")
        .set("Origin", origin)
        .send({ productId: 461686, quantity: 1 })
        .expect(400);
      const u = await User.findOne({ email: "customer@example.test" }).lean();
      assert.equal(u.eventCount, 0);
      assert.deepEqual(u.cart, []);
      assert.deepEqual(u.wishlist, []);
      let p = (await customer.get("/api/demo/profile")).body;
      assert.equal(p.profile.eventCount, 1);
      assert.equal(p.profile.cart[0].quantity, 2);
      assert.equal(p.products[0]._id, created._id);
      await customer.get("/api/recommendations").expect(200);
      const stats = (await admin.get("/api/admin/overview").expect(200)).body;
      assert.equal(stats.products, 1);
      assert.equal(stats.activity.events, 1);
      assert.equal(stats.service.status, "ready");
      await admin
        .put("/api/admin/products/" + created._id)
        .set("Origin", origin)
        .send({ ...data, available: false, title: "Edited synthetic mug" })
        .expect(200);
      await customer.get("/api/demo/products/" + created._id).expect(404);
      assert.equal(
        (await customer.get("/api/demo/products")).body.products.length,
        0,
      );
      p = (await customer.get("/api/demo/profile")).body;
      assert.equal(p.products[0].available, false);
      await customer
        .put("/api/demo/cart")
        .set("Origin", origin)
        .send({ productId: created._id, quantity: 0 })
        .expect(200);
      await customer
        .put("/api/demo/wishlist")
        .set("Origin", origin)
        .send({ productId: created._id, add: false })
        .expect(200);
      await customer
        .delete("/api/demo/history")
        .set("Origin", origin)
        .expect(200);
      p = (await customer.get("/api/demo/profile")).body.profile;
      assert.equal(p.eventCount, 0);
      assert.equal(p.personalization, false);
      assert.deepEqual(p.cart, []);
      assert.deepEqual(p.wishlist, []);
      assert.equal(await Product.countDocuments(), 0);
      assert.equal(await DemoProduct.countDocuments(), 1);
      await customer.post("/api/auth/logout").set("Origin", origin).expect(204);
      await customer.get("/api/demo/profile").expect(401);
    } finally {
      if (
        owns &&
        mongoose.connection.name === database &&
        /^pasal_test_[a-f0-9]+$/.test(database)
      )
        await mongoose.connection.dropDatabase();
      await mongoose.disconnect();
    }
  },
);
