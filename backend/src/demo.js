import { Router } from "express";
import { randomUUID } from "node:crypto";
import { z } from "zod";
const id = z.string().regex(/^demo-[a-z0-9-]{1,60}$/);
const images = [
  "bag",
  "mug",
  "bottle",
  "notebook",
  "scarf",
  "lamp",
  "basket",
  "tea",
];
const product = z
  .object({
    title: z.string().trim().min(3).max(100),
    category: z.string().trim().min(2).max(50),
    subcategory: z.string().trim().min(2).max(50),
    description: z.string().trim().min(10).max(1000),
    priceNpr: z.number().int().min(1).max(10000000),
    image: z.enum(images),
    attributes: z.array(z.string().trim().min(1).max(120)).max(8),
    available: z.boolean(),
  })
  .strict();

export function demoRouter({ repository, requireUser, serviceHealth }) {
  const router = Router();
  const admin = [
    requireUser,
    (req, res, next) =>
      req.user.role === "admin"
        ? next()
        : res.status(403).json({ error: "Administrator access required" }),
  ];
  const member = [
    requireUser,
    async (req, res, next) => {
      req.demoProfile = await repository.profile(req.user._id);
      next();
    },
  ];
  router.get("/demo/products", async (req, res) => {
    const input = z
      .object({
        query: z.string().trim().max(80).optional(),
        category: z.string().max(50).optional(),
        sort: z.enum(["name", "price-low", "price-high"]).optional(),
      })
      .strict()
      .parse(req.query);
    res.json({
      products: await repository.products(input),
      source: "synthetic_demo",
    });
  });
  router.get("/demo/categories", async (req, res) =>
    res.json({
      categories: [
        ...new Set((await repository.products()).map((p) => p.category)),
      ].sort(),
    }),
  );
  router.get("/demo/products/:id", async (req, res) => {
    const p = await repository.product(id.parse(req.params.id));
    if (!p?.available)
      return res.status(404).json({ error: "Demo product unavailable" });
    res.json({ product: p });
  });
  router.get("/demo/profile", ...member, async (req, res) => {
    const profile = req.demoProfile;
    res.json({
      profile,
      products: await repository.productsByIds([
        ...new Set([
          ...profile.wishlist,
          ...profile.cart.map((r) => r.productId),
        ]),
      ]),
    });
  });
  router.put("/demo/privacy", ...member, async (req, res) => {
    const input = z
      .object({
        personalization: z.boolean(),
        selectedCategories: z.array(z.string().trim().min(2).max(50)).max(12),
      })
      .strict()
      .parse(req.body);
    const known = new Set((await repository.products()).map((p) => p.category));
    if (input.selectedCategories.some((c) => !known.has(c)))
      return res.status(400).json({ error: "Unknown demonstration category" });
    res.json({
      profile: await repository.privacy(
        req.user._id,
        input.personalization,
        input.selectedCategories,
      ),
    });
  });
  router.delete("/demo/history", ...member, async (req, res) =>
    res.json({ profile: await repository.privacy(req.user._id, false, []) }),
  );
  router.post("/demo/events", ...member, async (req, res) => {
    const input = z
      .object({ productId: id, type: z.enum(["view", "addtocart"]) })
      .strict()
      .parse(req.body);
    if (!(await repository.product(input.productId))?.available)
      return res.status(404).json({ error: "Demo product unavailable" });
    if (!(await repository.event(req.user._id, input.productId)))
      return res
        .status(409)
        .json({ error: "Demo activity consent is disabled" });
    res.status(204).end();
  });
  router.put("/demo/wishlist", ...member, async (req, res) => {
    const input = z
      .object({ productId: id, add: z.boolean() })
      .strict()
      .parse(req.body);
    if (input.add && !(await repository.product(input.productId))?.available)
      return res.status(404).json({ error: "Demo product unavailable" });
    const profile = await repository.wishlist(
      req.user._id,
      input.productId,
      input.add,
    );
    if (!profile)
      return res.status(409).json({ error: "Wishlist capacity reached" });
    res.json({ profile });
  });
  router.put("/demo/cart", ...member, async (req, res) => {
    const input = z
      .object({ productId: id, quantity: z.number().int().min(0).max(10) })
      .strict()
      .parse(req.body);
    if (
      input.quantity &&
      !(await repository.product(input.productId))?.available
    )
      return res.status(404).json({ error: "Demo product unavailable" });
    const profile = await repository.cart(
      req.user._id,
      input.productId,
      input.quantity,
    );
    if (!profile)
      return res.status(409).json({ error: "Cart capacity reached" });
    res.json({ profile });
  });
  router.get("/admin/overview", ...admin, async (req, res) => {
    let health;
    try {
      health = await serviceHealth();
    } catch {
      health = { status: "unavailable" };
    }
    res.json({ ...(await repository.dashboard()), service: health });
  });
  router.get("/admin/products", ...admin, async (req, res) =>
    res.json({
      products: await repository.products({ includeInactive: true }),
      images,
    }),
  );
  router.post("/admin/products", ...admin, async (req, res) =>
    res
      .status(201)
      .json({
        product: await repository.create({
          ...product.parse(req.body),
          _id: "demo-" + randomUUID(),
          provenance: "synthetic_demo",
        }),
      }),
  );
  router.put("/admin/products/:id", ...admin, async (req, res) => {
    const updated = await repository.update(
      id.parse(req.params.id),
      product.parse(req.body),
    );
    if (!updated)
      return res.status(404).json({ error: "Demo product not found" });
    res.json({ product: updated });
  });
  return router;
}
