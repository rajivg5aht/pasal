// One-time synthetic inventory initialization; never overwrites an existing count.
import mongoose from "mongoose";
import { mongoUrl } from "../src/local-config.js";
import { DemoProduct } from "../src/demo-repository.js";
import { InventoryAudit, OrderService } from "../src/orders.js";
await mongoose.connect(mongoUrl, {serverSelectionTimeoutMS:5000});
try {
  const count = await new OrderService().transaction(async session => {
    const products = await DemoProduct.find({provenance:"synthetic_demo", stock:{$exists:false}}).session(session).lean();
    for (const product of products) {
      await DemoProduct.updateOne({_id:product._id,stock:{$exists:false}},{$set:{stock:12}},{session});
      await InventoryAudit.create([{productId:product._id,before:0,after:12,actor:"system:synthetic-stock-initialization"}],{session});
    }
    return products.length;
  });
  console.log(`Initialized ${count} existing synthetic products with 12 demonstration units each. No real inventory is claimed.`);
} finally {await mongoose.disconnect();}
