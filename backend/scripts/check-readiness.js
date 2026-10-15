// Read-only local deployment checks. Never print connection strings or secrets.
import mongoose from "mongoose";
import { writeFile } from "node:fs/promises";
import { mongoUrl } from "../src/local-config.js";

const report = { checkedAtUtc: new Date().toISOString(), checks: [] };
async function check(name, run) {
  try {
    await run();
    report.checks.push({ name, passed: true });
  } catch {
    report.checks.push({ name, passed: false });
  }
}
await check("configured_database_is_writable_replica_primary", async () => {
  try {
    await mongoose.connect(mongoUrl, {
      serverSelectionTimeoutMS: 5000, autoCreate: false, autoIndex: false,
    });
    const hello = await mongoose.connection.db.admin().command({ hello: 1 });
    if (!hello.setName || !hello.isWritablePrimary || hello.logicalSessionTimeoutMinutes == null)
      throw new Error("Transaction prerequisites unavailable");
  } finally {
    await mongoose.disconnect();
  }
});
for (const [name, url, json] of [
  ["backend_ready", "http://127.0.0.1:3000/api/health", true],
  ["recommender_ready", "http://127.0.0.1:8000/health", true],
  ["frontend_reachable", "http://127.0.0.1:5173/", false],
]) {
  await check(name, async () => {
    const response = await fetch(url, { signal: AbortSignal.timeout(5000), redirect: "error" });
    if (!response.ok) throw new Error("Service unavailable");
    if (json && (await response.json()).status !== "ready") throw new Error("Not ready");
    if (!json && !(response.headers.get("content-type") || "").includes("text/html"))
      throw new Error("Expected frontend HTML");
  });
}
report.passed = report.checks.every((check) => check.passed);
report.scope = "Read-only process and database prerequisites; not a browser walkthrough, transaction execution or research validation.";
if (process.argv[2]) await writeFile(process.argv[2], JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify(report, null, 2));
if (!report.passed) process.exitCode = 1;
