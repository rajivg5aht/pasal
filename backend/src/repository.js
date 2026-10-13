import mongoose from "mongoose";

const userSchema = new mongoose.Schema(
  {
    email: { type: String, required: true, unique: true },
    name: { type: String, required: true },
    passwordHash: { type: String, required: true },
    personalization: { type: Boolean, default: false },
    selectedCategories: { type: [String], default: [] },
    eventCount: { type: Number, default: 0 },
    recentItems: { type: [Number], default: [] },
    seenItems: { type: [Number], default: [] },
    wishlist: { type: [Number], default: [] },
    cart: { type: [Number], default: [] },
  },
  { timestamps: true },
);
const productSchema = new mongoose.Schema({
  _id: Number,
  title: String,
  category: String,
  available: Boolean,
  source: {
    type: String,
    default: "Retailrocket anonymized research catalogue",
  },
  metadataCutoffMs: Number,
});
productSchema.index({ available: 1, _id: 1 });
productSchema.index({ available: 1, category: 1 });
productSchema.index({ category: 1, available: 1, _id: 1 });
export const User = mongoose.model("User", userSchema);
export const Product = mongoose.model("Product", productSchema);

export class MongoRepository {
  createUser(data) {
    return User.create(data);
  }
  findByEmail(email) {
    return User.findOne({ email }).lean();
  }
  getUser(id) {
    return mongoose.isValidObjectId(id) ? User.findById(id).lean() : null;
  }
  async products({ after = -1, category, query, limit = 24 }) {
    const filter = { available: true, _id: { $gt: after } };
    if (category) filter.category = category;
    if (query) {
      if (!/^\d+$/.test(query)) return [];
      filter._id = Number(query);
    }
    return Product.find(filter).sort({ _id: 1 }).limit(limit).lean();
  }
  product(id) {
    return Product.findOne({ _id: id, available: true }).lean();
  }
  productsByIds(ids) {
    return Product.find({ _id: { $in: ids }, available: true }).lean();
  }
  categories() {
    return Product.distinct("category", { available: true });
  }
  setPrivacy(id, personalization, selectedCategories) {
    // Single-document update serializes privacy changes against event writes.
    return User.findByIdAndUpdate(
      id,
      {
        $set: {
          personalization,
          selectedCategories: personalization ? selectedCategories : [],
          ...(!personalization
            ? { eventCount: 0, recentItems: [], seenItems: [] }
            : {}),
        },
      },
      { returnDocument: "after" },
    ).lean();
  }
  resetProfile(id) {
    return this.setPrivacy(id, false, []);
  }
  recordEvent(id, itemid) {
    return User.findOneAndUpdate(
      { _id: id, personalization: true, "seenItems.99999": { $exists: false } },
      [
        {
          $set: {
            eventCount: { $add: ["$eventCount", 1] },
            seenItems: { $setUnion: ["$seenItems", [itemid]] },
            recentItems: {
              $slice: [
                {
                  $concatArrays: [
                    {
                      $filter: {
                        input: "$recentItems",
                        as: "item",
                        cond: { $ne: ["$$item", itemid] },
                      },
                    },
                    [itemid],
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
  changeList(id, field, itemid, add) {
    const filter = {
      _id: id,
      ...(add ? { [`${field}.99`]: { $exists: false } } : {}),
    };
    return User.findOneAndUpdate(
      filter,
      { [add ? "$addToSet" : "$pull"]: { [field]: itemid } },
      { returnDocument: "after" },
    ).lean();
  }
}
