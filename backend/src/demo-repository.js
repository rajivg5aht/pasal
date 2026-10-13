import mongoose from "mongoose";
const { Schema } = mongoose;
export const DemoProduct = mongoose.model(
  "DemoProduct",
  new Schema(
    {
      _id: String,
      title: String,
      category: String,
      subcategory: String,
      description: String,
      priceNpr: Number,
      image: String,
      attributes: [String],
      available: Boolean,
      provenance: { type: String, default: "synthetic_demo" },
    },
    { timestamps: true, collection: "demo_products" },
  ),
);
const profileSchema = new Schema(
  {
    _id: String,
    personalization: { type: Boolean, default: false },
    selectedCategories: { type: [String], default: [] },
    eventCount: { type: Number, default: 0 },
    recentItems: { type: [String], default: [] },
    wishlist: { type: [String], default: [] },
    cart: {
      type: [{ _id: false, productId: String, quantity: Number }],
      default: [],
    },
  },
  { timestamps: true, collection: "demo_profiles" },
);
export const DemoProfile = mongoose.model("DemoProfile", profileSchema);
export const ResearchRequest = mongoose.model(
  "ResearchRequest",
  new Schema(
    {
      status: Number,
      latencyMs: Number,
      strategy: String,
      configuration: String,
      cutoff: Number,
      fallback: String,
      createdAt: { type: Date, default: Date.now, expires: 604800 },
    },
    { collection: "research_request_metrics" },
  ),
);

export class DemoRepository {
  async products({
    query = "",
    category = "",
    sort = "name",
    includeInactive = false,
  } = {}) {
    const filter = includeInactive ? {} : { available: true };
    if (category) filter.category = category;
    if (query) {
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      filter.$or = ["title", "category", "subcategory", "description"].map(
        (key) => ({ [key]: { $regex: escaped, $options: "i" } }),
      );
    }
    const order =
      sort === "price-low"
        ? { priceNpr: 1, _id: 1 }
        : sort === "price-high"
          ? { priceNpr: -1, _id: 1 }
          : { title: 1, _id: 1 };
    return DemoProduct.find(filter).sort(order).limit(100).lean();
  }
  product(id) {
    return DemoProduct.findById(id).lean();
  }
  create(data) {
    return DemoProduct.create(data);
  }
  update(id, data) {
    return DemoProduct.findByIdAndUpdate(
      id,
      { $set: data },
      { returnDocument: "after", runValidators: true },
    ).lean();
  }
  async profile(id) {
    return DemoProfile.findOneAndUpdate(
      { _id: String(id) },
      { $setOnInsert: { _id: String(id) } },
      { upsert: true, returnDocument: "after", setDefaultsOnInsert: true },
    ).lean();
  }
  privacy(id, personalization, selectedCategories) {
    return DemoProfile.findByIdAndUpdate(
      String(id),
      {
        $set: {
          personalization,
          selectedCategories: personalization ? selectedCategories : [],
          ...(!personalization ? { eventCount: 0, recentItems: [] } : {}),
        },
      },
      { returnDocument: "after" },
    ).lean();
  }
  event(id, item) {
    return DemoProfile.findOneAndUpdate(
      { _id: String(id), personalization: true },
      [
        {
          $set: {
            eventCount: { $add: ["$eventCount", 1] },
            recentItems: {
              $slice: [
                {
                  $concatArrays: [
                    {
                      $filter: {
                        input: "$recentItems",
                        as: "item",
                        cond: { $ne: ["$$item", item] },
                      },
                    },
                    [item],
                  ],
                },
                -20,
              ],
            },
            updatedAt: "$$NOW",
          },
        },
      ],
      { returnDocument: "after", updatePipeline: true },
    ).lean();
  }
  wishlist(id, item, add) {
    return DemoProfile.findOneAndUpdate(
      {
        _id: String(id),
        ...(add ? { "wishlist.99": { $exists: false } } : {}),
      },
      { [add ? "$addToSet" : "$pull"]: { wishlist: item } },
      { returnDocument: "after" },
    ).lean();
  }
  cart(id, productId, quantity) {
    return DemoProfile.findOneAndUpdate(
      {
        _id: String(id),
        ...(quantity
          ? {
              $or: [
                { "cart.productId": productId },
                { "cart.99": { $exists: false } },
              ],
            }
          : {}),
      },
      [
        {
          $set: {
            cart: {
              $concatArrays: [
                {
                  $filter: {
                    input: "$cart",
                    as: "line",
                    cond: { $ne: ["$$line.productId", productId] },
                  },
                },
                quantity ? [{ productId, quantity }] : [],
              ],
            },
            updatedAt: "$$NOW",
          },
        },
      ],
      { returnDocument: "after", updatePipeline: true },
    ).lean();
  }
  productsByIds(ids) {
    return DemoProduct.find({ _id: { $in: ids } }).lean();
  }
  recordMetric(data) {
    return ResearchRequest.create(data);
  }
  async dashboard() {
    const [products, activity, metrics] = await Promise.all([
      DemoProduct.find().lean(),
      DemoProfile.aggregate([
        { $match: { personalization: true } },
        {
          $group: {
            _id: null,
            consentingProfiles: { $sum: 1 },
            events: { $sum: "$eventCount" },
          },
        },
      ]),
      ResearchRequest.find().sort({ createdAt: -1 }).limit(1000).lean(),
    ]);
    const times = metrics.map((r) => r.latencyMs).sort((a, b) => a - b);
    const strategies = {};
    for (const r of metrics)
      if (r.strategy)
        strategies[r.strategy] = (strategies[r.strategy] || 0) + 1;
    return {
      products: products.length,
      available: products.filter((p) => p.available).length,
      categories: [...new Set(products.map((p) => p.category))].sort(),
      activity: activity[0] || { consentingProfiles: 0, events: 0 },
      research: {
        window:
          "Latest 1,000 recorded requests retained up to seven days; collection began with this dashboard",
        requests: metrics.length,
        failures: metrics.filter((r) => r.status >= 400).length,
        strategies,
        fallbackRecorded: metrics.filter((r) => r.fallback).length,
        p95Ms: times.length ? times[Math.ceil(times.length * 0.95) - 1] : null,
        latestModel: metrics.find((r) => r.configuration)
          ? {
              configuration: metrics.find((r) => r.configuration).configuration,
              cutoff: metrics.find((r) => r.configuration).cutoff,
            }
          : null,
      },
    };
  }
}
