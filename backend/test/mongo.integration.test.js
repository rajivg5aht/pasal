import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import mongoose from "mongoose";
import session from "express-session";
import request from "supertest";
import { MongoRepository, User, Product } from "../src/repository.js";
import { createApp } from "../src/app.js";

test(
  "real MongoDB: concurrent profile writes, opt-out and reset",
  { skip: process.env.RUN_MONGO_TESTS !== "1" },
  async () => {
    const database = `pasal_test_${randomUUID().replaceAll("-", "")}`;
    await mongoose.connect(`mongodb://127.0.0.1:27017/${database}`, {
      serverSelectionTimeoutMS: 3000,
      autoCreate: false,
      autoIndex: false,
    });
    let ownsDatabase = false;
    try {
      assert.equal(
        (await mongoose.connection.db.listCollections().toArray()).length,
        0,
      );
      ownsDatabase = true;
      await User.createCollection();
      await Product.createCollection();
      await User.createIndexes();
      await Product.createIndexes();
      await Product.create({
        _id: 7,
        title: "Fixture only",
        category: "9",
        available: true,
      });
      const repository = new MongoRepository();
      const user = await repository.createUser({
        email: "fixture@example.test",
        name: "Fixture",
        passwordHash: "not-a-login-credential",
      });
      assert.equal(await repository.recordEvent(user._id, 7), null);
      await repository.setPrivacy(user._id, true, ["9"]);
      await Promise.all(
        Array.from({ length: 20 }, () => repository.recordEvent(user._id, 7)),
      );
      let stored = await repository.getUser(user._id);
      assert.equal(stored.eventCount, 20);
      assert.deepEqual(stored.recentItems, [7]);
      assert.deepEqual(stored.seenItems, [7]);
      await repository.setPrivacy(user._id, false, []);
      assert.equal(await repository.recordEvent(user._id, 7), null);
      stored = await repository.getUser(user._id);
      assert.equal(stored.eventCount, 0);
      assert.deepEqual(stored.seenItems, []);
      await repository.changeList(user._id, "wishlist", 7, true);
      await repository.resetProfile(user._id);
      assert.deepEqual((await repository.getUser(user._id)).wishlist, [7]);
      const app = createApp({
        repository,
        store: new session.MemoryStore(),
        sessionSecret: "isolated-database-test-secret-at-least-32",
        recommend: async () => ({ items: [] }),
      });
      const products = await request(app).get("/api/products");
      assert.equal(products.status, 200);
      assert.equal(products.body.products[0]._id, 7);
    } finally {
      // Only the fresh, empty-before-test database created above is disposable.
      if (
        ownsDatabase &&
        mongoose.connection.name === database &&
        /^pasal_test_[a-f0-9]{32}$/.test(database)
      )
        await mongoose.connection.dropDatabase();
      await mongoose.disconnect();
    }
  },
);
