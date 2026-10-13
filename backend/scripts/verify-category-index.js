// Local, additive index verification. No catalogue records or existing indexes change.
import mongoose from "mongoose";
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";

const output = process.argv[2];
if (!output) throw new Error("Supply a new aggregate evidence file path");
await mongoose.connect("mongodb://127.0.0.1:27017/pasal", {
  serverSelectionTimeoutMS: 5000,
});
try {
  const db = mongoose.connection.db;
  const products = db.collection("products");
  const measure = async () => {
    const categories = (await products.distinct("category", { available: true })).sort();
    const plan = await db.command({
      explain: { distinct: "products", key: "category", query: { available: true } },
      verbosity: "executionStats",
    });
    const stats = plan.executionStats;
    return {
      categories: categories.length,
      categorySetSha256: createHash("sha256").update(JSON.stringify(categories)).digest("hex"),
      keysExamined: stats.totalKeysExamined,
      documentsExamined: stats.totalDocsExamined,
      executionTimeMillis: stats.executionTimeMillis,
      winningPlan: plan.queryPlanner.winningPlan,
    };
  };
  const before = await measure();
  await products.createIndex({ available: 1, category: 1 });
  const after = await measure();
  if (before.categorySetSha256 !== after.categorySetSha256)
    throw new Error("Category results changed; inspect before interpreting timings");
  const report = {
    status: "local_category_index_equivalence_verified",
    before,
    after,
    limitations: ["Single-host diagnostic; timings are not a controlled benchmark", "Index is additive; catalogue data unchanged"],
  };
  await writeFile(output, JSON.stringify(report, null, 2), { flag: "wx" });
  console.log(JSON.stringify({ before, after }));
} finally {
  await mongoose.disconnect();
}
