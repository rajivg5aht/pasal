// Explicit operator action only. Never run automatically during server startup.
// Copies application records to an EMPTY local replica set and preserves the source.
import mongoose from "mongoose";
const { MongoClient, BSON } = mongoose.mongo;
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";

if (!process.argv.includes("--confirm-stopped-backend"))
  throw new Error(
    "Stop the backend first, then pass --confirm-stopped-backend after approving the local database copy.",
  );
const source = new MongoClient("mongodb://127.0.0.1:27017/pasal");
const target = new MongoClient(
  "mongodb://127.0.0.1:27018/pasal?replicaSet=pasalLocal",
);
const evidence = {
  source: "localhost:27017/pasal",
  target: "localhost:27018/pasal",
  at: new Date().toISOString(),
  collections: [],
  sessions: "Excluded intentionally; users must sign in again",
};
async function fingerprint(collection) {
  const hash = createHash("sha256");
  let count = 0;
  for await (const doc of collection.find().sort({ _id: 1 })) {
    hash.update(BSON.EJSON.stringify(doc, { relaxed: false }) + "\n");
    count++;
  }
  return { count, sha256: hash.digest("hex") };
}
try {
  await source.connect();
  await target.connect();
  const src = source.db(),
    dst = target.db();
  const hello = await dst.admin().command({ hello: 1 });
  if (hello.setName !== "pasalLocal" || !hello.isWritablePrimary)
    throw new Error("Wrong or unavailable target replica set");
  if ((await dst.listCollections().toArray()).length)
    throw new Error(
      "Target is not empty; refusing to overwrite. Preserve and inspect any partial copy.",
    );
  for (const info of await src.listCollections().toArray()) {
    if (info.name === "sessions" || info.name.startsWith("system.")) continue;
    if (info.type !== "collection")
      throw new Error("Unsupported source object: " + info.name);
    const from = src.collection(info.name);
    const before = await fingerprint(from);
    await dst.createCollection(info.name, info.options);
    const to = dst.collection(info.name);
    let batch = [];
    for await (const doc of from.find().sort({ _id: 1 })) {
      batch.push(doc);
      if (batch.length === 500) {
        await to.insertMany(batch);
        batch = [];
      }
    }
    if (batch.length) await to.insertMany(batch);
    for (const index of await from.indexes()) {
      if (index.name === "_id_") continue;
      const { key, v, ns, ...options } = index;
      await to.createIndex(key, options);
    }
    const copied = await fingerprint(to),
      after = await fingerprint(from);
    if (
      JSON.stringify(before) !== JSON.stringify(copied) ||
      JSON.stringify(before) !== JSON.stringify(after)
    )
      throw new Error(
        "Source changed or copy mismatch: " +
          info.name +
          ". Do not switch the application.",
      );
    evidence.collections.push({ name: info.name, ...copied });
    console.log(info.name, copied.count, "verified");
  }
  evidence.status = "verified_copy";
  await writeFile(
    "../tmp/database-copy-evidence.json",
    JSON.stringify(evidence, null, 2),
    { flag: "wx" },
  );
  console.log(
    "Verified copy; source preserved. Inspect evidence before changing MONGODB_URI.",
  );
} finally {
  await source.close();
  await target.close();
}
