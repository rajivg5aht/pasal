import { createHash } from "node:crypto";
import mongoose from "mongoose";
import { Router } from "express";
import { z } from "zod";
import { DemoProduct, DemoProfile } from "./demo-repository.js";

export class CommerceError extends Error {
  constructor(message, status = 409) {
    super(message);
    this.status = status;
  }
}
export const transitions = Object.freeze({
  placed: ["confirmed", "cancelled"],
  confirmed: ["dispatched", "cancelled"],
  dispatched: ["delivered"],
  delivered: [],
  cancelled: [],
});
const orderSchema = new mongoose.Schema(
  {
    _id: String,
    customerId: { type: String, required: true, index: true },
    requestHash: String,
    status: { type: String, enum: Object.keys(transitions), required: true },
    lines: [
      {
        _id: false,
        productId: String,
        title: String,
        image: String,
        quantity: Number,
        unitPriceNpr: Number,
      },
    ],
    totalNpr: Number,
    delivery: { recipient: String, area: String, note: String },
    payment: { type: String, default: "simulation_no_charge" },
    source: { type: String, default: "synthetic_demo" },
    history: [{ _id: false, status: String, at: Date, actor: String }],
  },
  { timestamps: true, collection: "demo_orders" },
);
orderSchema.index({ customerId: 1, createdAt: -1, _id: 1 });
export const DemoOrder = mongoose.model("DemoOrder", orderSchema);
export const InventoryAudit = mongoose.model(
  "DemoInventoryAudit",
  new mongoose.Schema(
    {
      productId: String,
      before: Number,
      after: Number,
      actor: String,
    },
    { timestamps: true, collection: "demo_inventory_audit" },
  ),
);
const productId = z.string().regex(/^demo-[a-z0-9-]{1,60}$/);
export const checkoutInput = z
  .object({
    key: z.uuid(),
    lines: z
      .array(
        z
          .object({ productId, quantity: z.number().int().min(1).max(10) })
          .strict(),
      )
      .min(1)
      .max(100),
    expectedTotalNpr: z.number().int().min(1).max(10000000000),
    delivery: z
      .object({
        recipient: z.string().trim().min(2).max(80),
        area: z.enum(["Kathmandu", "Lalitpur", "Bhaktapur"]),
        note: z.string().trim().max(120).default(""),
      })
      .strict(),
    simulationAccepted: z.literal(true),
  })
  .strict()
  .superRefine((v, ctx) => {
    if (new Set(v.lines.map((l) => l.productId)).size !== v.lines.length)
      ctx.addIssue({ code: "custom", message: "Duplicate products" });
  });
const canonicalLines = (lines) =>
  [...lines]
    .map(({ productId, quantity }) => ({ productId, quantity }))
    .sort((a, b) => a.productId.localeCompare(b.productId));
const digest = (value) =>
  createHash("sha256").update(JSON.stringify(value)).digest("hex");
const publicOrder = (order) => {
  const { customerId, requestHash, __v, history, ...safe } = order;
  return {
    ...safe,
    history: history.map(({ status, at }) => ({ status, at })),
  };
};

export class OrderService {
  async available() {
    const hello = await mongoose.connection.db.admin().command({ hello: 1 });
    return Boolean(hello.setName || hello.msg === "isdbgrid");
  }
  async transaction(work) {
    if (!(await this.available()))
      throw new CommerceError(
        "Checkout requires transaction-ready MongoDB. Your cart is unchanged.",
        503,
      );
    return mongoose.connection.transaction(work, {
      readPreference: "primary",
      writeConcern: { w: "majority" },
    });
  }
  async checkout(customerId, input) {
    const customer = String(customerId),
      lines = canonicalLines(input.lines);
    const id = "order-" + digest([customer, input.key]);
    const requestHash = digest({
      lines,
      expectedTotalNpr: input.expectedTotalNpr,
      delivery: input.delivery,
    });
    const replay = async () => {
      const existing = await DemoOrder.findById(id).lean();
      if (existing && existing.requestHash !== requestHash)
        throw new CommerceError(
          "Checkout key was already used for a different order",
        );
      return existing;
    };
    const existing = await replay();
    if (existing) return { order: publicOrder(existing), replay: true };
    try {
      const order = await this.transaction(async (session) => {
        const profile = await DemoProfile.findById(customer)
          .session(session)
          .lean();
        if (
          !profile ||
          JSON.stringify(canonicalLines(profile.cart)) !== JSON.stringify(lines)
        )
          throw new CommerceError(
            "Your cart changed. Review it before ordering.",
          );
        const snapshots = [];
        for (const line of lines) {
          const p = await DemoProduct.findOneAndUpdate(
            {
              _id: line.productId,
              available: true,
              stock: { $gte: line.quantity },
            },
            { $inc: { stock: -line.quantity } },
            { session, returnDocument: "before" },
          ).lean();
          if (!p)
            throw new CommerceError(
              "A product is unavailable or has insufficient demo stock. Your cart is unchanged.",
            );
          snapshots.push({
            ...line,
            title: p.title,
            image: p.image,
            unitPriceNpr: p.priceNpr,
          });
        }
        const totalNpr = snapshots.reduce(
          (sum, l) => sum + l.quantity * l.unitPriceNpr,
          0,
        );
        if (
          !Number.isSafeInteger(totalNpr) ||
          totalNpr !== input.expectedTotalNpr
        )
          throw new CommerceError(
            "Prices changed. Refresh your cart and review the new total.",
          );
        const [created] = await DemoOrder.create(
          [
            {
              _id: id,
              customerId: customer,
              requestHash,
              status: "placed",
              lines: snapshots,
              totalNpr,
              delivery: input.delivery,
              history: [{ status: "placed", at: new Date(), actor: customer }],
            },
          ],
          { session },
        );
        await DemoProfile.updateOne(
          { _id: customer },
          { $set: { cart: [] } },
          { session },
        );
        return created.toObject();
      });
      return { order: publicOrder(order), replay: false };
    } catch (error) {
      // A lost response or concurrent identical request must not deduct stock twice.
      const committed = await replay();
      if (committed) return { order: publicOrder(committed), replay: true };
      throw error;
    }
  }
  async list(customerId, after) {
    const filter = customerId ? { customerId: String(customerId) } : {};
    // Object identifiers are random; creation timestamp plus ID provides a stable cursor.
    if (after)
      filter.$or = [
        { createdAt: { $lt: new Date(after.at) } },
        { createdAt: new Date(after.at), _id: { $gt: after.id } },
      ];
    const rows = await DemoOrder.find(filter)
      .sort({ createdAt: -1, _id: 1 })
      .limit(50)
      .lean();
    return {
      orders: rows.map(publicOrder),
      next:
        rows.length === 50
          ? { at: rows.at(-1).createdAt, id: rows.at(-1)._id }
          : null,
    };
  }
  async transition(id, actor, expected, next, admin = false) {
    if (
      !transitions[expected]?.includes(next) ||
      (!admin && !(expected === "placed" && next === "cancelled"))
    )
      throw new CommerceError("Invalid order status transition");
    const order = await this.transaction(async (session) => {
      const filter = {
        _id: id,
        status: expected,
        ...(!admin ? { customerId: String(actor) } : {}),
      };
      const updated = await DemoOrder.findOneAndUpdate(
        filter,
        {
          $set: { status: next },
          $push: {
            history: { status: next, at: new Date(), actor: String(actor) },
          },
        },
        { session, returnDocument: "after" },
      ).lean();
      if (!updated)
        throw new CommerceError("Order not found or its status has changed");
      if (next === "cancelled")
        for (const line of updated.lines) {
          const result = await DemoProduct.updateOne(
            { _id: line.productId },
            { $inc: { stock: line.quantity } },
            { session },
          );
          if (result.matchedCount !== 1)
            throw new CommerceError(
              "Cannot restore stock for a missing product",
            );
        }
      return updated;
    });
    return publicOrder(order);
  }
  async setStock(productId, actor, before, after) {
    return this.transaction(async (session) => {
      const filter = {
        _id: productId,
        ...(before === 0
          ? { $or: [{ stock: 0 }, { stock: { $exists: false } }] }
          : { stock: before }),
      };
      const product = await DemoProduct.findOneAndUpdate(
        filter,
        { $set: { stock: after } },
        { session, returnDocument: "after" },
      ).lean();
      if (!product)
        throw new CommerceError(
          "Stock changed or product no longer exists. Refresh and retry.",
        );
      await InventoryAudit.create(
        [{ productId, actor: String(actor), before, after }],
        { session },
      );
      return product;
    });
  }
}

export function orderRouter({ requireUser, service = new OrderService() }) {
  const router = Router();
  const admin = [
    requireUser,
    (req, res, next) =>
      req.user.role === "admin"
        ? next()
        : res.status(403).json({ error: "Administrator access required" }),
  ];
  const cursor = z
    .object({
      at: z.iso.datetime(),
      id: z.string().regex(/^order-[a-f0-9]{64}$/),
    })
    .strict();
  const listQuery = z
    .object({
      at: z.iso.datetime().optional(),
      id: z
        .string()
        .regex(/^order-[a-f0-9]{64}$/)
        .optional(),
    })
    .strict();
  const parseCursor = (query) => {
    const v = listQuery.parse(query);
    return Object.keys(v).length ? cursor.parse(v) : undefined;
  };
  const orderId = z.string().regex(/^order-[a-f0-9]{64}$/);
  router.get("/demo/checkout-status", async (req, res) =>
    res.json({
      available: await service.available(),
      mode: "simulation_no_charge",
    }),
  );
  router.post("/demo/orders", requireUser, async (req, res) => {
    const result = await service.checkout(
      req.user._id,
      checkoutInput.parse(req.body),
    );
    res.status(result.replay ? 200 : 201).json(result);
  });
  router.get("/demo/orders", requireUser, async (req, res) =>
    res.json(await service.list(req.user._id, parseCursor(req.query))),
  );
  router.post("/demo/orders/:id/cancel", requireUser, async (req, res) => {
    z.object({}).strict().parse(req.body);
    res.json({
      order: await service.transition(
        orderId.parse(req.params.id),
        req.user._id,
        "placed",
        "cancelled",
      ),
    });
  });
  router.get("/admin/orders", ...admin, async (req, res) =>
    res.json(await service.list(null, parseCursor(req.query))),
  );
  router.patch("/admin/orders/:id", ...admin, async (req, res) => {
    const v = z
      .object({
        expected: z.enum(Object.keys(transitions)),
        status: z.enum(Object.keys(transitions)),
      })
      .strict()
      .parse(req.body);
    res.json({
      order: await service.transition(
        orderId.parse(req.params.id),
        req.user._id,
        v.expected,
        v.status,
        true,
      ),
    });
  });
  router.put("/admin/inventory/:id", ...admin, async (req, res) => {
    const v = z
      .object({
        expected: z.number().int().min(0).max(1000000),
        stock: z.number().int().min(0).max(1000000),
      })
      .strict()
      .parse(req.body);
    res.json({
      product: await service.setStock(
        productId.parse(req.params.id),
        req.user._id,
        v.expected,
        v.stock,
      ),
    });
  });
  router.use((error, req, res, next) =>
    error instanceof CommerceError
      ? res.status(error.status).json({ error: error.message })
      : next(error),
  );
  return router;
}
