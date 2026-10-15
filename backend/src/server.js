import dotenv from "dotenv";
import mongoose from "mongoose";
import MongoStore from "connect-mongo";
import { fileURLToPath } from "node:url";
import { createApp } from "./app.js";
import { MongoRepository } from "./repository.js";
import { DemoRepository } from "./demo-repository.js";

dotenv.config({
  path: fileURLToPath(new URL("../../.env", import.meta.url)),
  quiet: true,
});
const mongoUrl = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/pasal";
await mongoose.connect(mongoUrl, { serverSelectionTimeoutMS: 5000 });
const upstream =
  process.env.RECOMMENDATION_SERVICE_URL || "http://127.0.0.1:8000";
if (!process.env.RECOMMENDATION_SERVICE_TOKEN || !process.env.SESSION_SECRET)
  throw new Error("Configure local service and session secrets");
const app = createApp({
  repository: new MongoRepository(),
  store: MongoStore.create({ mongoUrl }),
  demoRepository: new DemoRepository(),
  recommendDemo: async (payload) => {
    const response = await fetch(`${upstream}/demo/recommendations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Service-Token": process.env.RECOMMENDATION_SERVICE_TOKEN,
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error("Demo recommender unavailable");
    return response.json();
  },
  serviceHealth: async () => {
    const response = await fetch(`${upstream}/health`, {
      signal: AbortSignal.timeout(2000),
    });
    if (!response.ok) throw new Error("Unavailable");
    return response.json();
  },
  sessionSecret: process.env.SESSION_SECRET,
  production: process.env.NODE_ENV === "production",
  origins: process.env.APP_ORIGIN ? [process.env.APP_ORIGIN] : undefined,
  recommend: async (profile) => {
    const response = await fetch(`${upstream}/recommendations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Service-Token": process.env.RECOMMENDATION_SERVICE_TOKEN,
      },
      body: JSON.stringify(profile),
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error("Recommendation service unavailable");
    return response.json();
  },
});
const server = app.listen(
  Number(process.env.BACKEND_PORT || 3000),
  "127.0.0.1",
  () => console.log("Pasal backend ready on localhost"),
);
for (const signal of ["SIGINT", "SIGTERM"])
  process.on(signal, () =>
    server.close(async () => {
      await mongoose.disconnect();
      process.exit(0);
    }),
  );
