// Remove legacy non-shoe offers from the active shop without breaking old orders.
import mongoose from "mongoose";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { DemoProduct } from "../src/demo-repository.js";
import { mongoUrl } from "../src/local-config.js";
const shoeImages = JSON.parse(await readFile(new URL('../../catalogue/shoe-images.json', import.meta.url), 'utf8'));
await mongoose.connect(mongoUrl, { serverSelectionTimeoutMS: 5000 });
try {
  const rows = await DemoProduct.find({ provenance: 'synthetic_demo', image: { $nin: Object.keys(shoeImages) }, retired: { $ne: true } }).lean();
  if (rows.length) {
    const directory = new URL('../../tmp/catalogue-backups/', import.meta.url);
    await mkdir(directory, { recursive: true });
    await writeFile(new URL(`legacy-${Date.now()}.json`, directory), JSON.stringify(rows, null, 2), { flag: 'wx' });
    await DemoProduct.updateMany({ _id: { $in: rows.map(r => r._id) } }, { $set: { available: false, retired: true } });
  }
  console.log(JSON.stringify({ retired: rows.length, retainedForReferences: true, researchChanged: false }));
} finally { await mongoose.disconnect(); }
