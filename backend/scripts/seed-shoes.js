// Additive starter catalogue. Existing products, profiles and orders stay intact.
import mongoose from "mongoose";
import { readFileSync } from "node:fs";
import { DemoProduct } from "../src/demo-repository.js";
import { mongoUrl } from "../src/local-config.js";
const images = JSON.parse(readFileSync(new URL('../../catalogue/shoe-images.json', import.meta.url), 'utf8'));
const records = [
  { image: 'shoe-black-derby', category: 'Formal shoes', subcategory: 'Derby', priceNpr: 3500,
    description: 'Black Derby shoe with a rubber sole, as identified by the photograph source. The brand and exact model are not documented.', attributes: ['Black', 'Derby', 'Rubber sole'] },
  { image: 'shoe-adidas-absolado', category: 'Sports shoes', subcategory: 'Football', priceNpr: 5500,
    description: 'Adidas Predator Absolado TRX TF football shoe, identified in a 2007 photograph. This historical reference does not establish current retail availability.', attributes: ['Adidas', 'Football', 'Absolado TRX TF'] },
];
await mongoose.connect(mongoUrl);
try {
  for (const record of records) {
    const result = await DemoProduct.updateOne({ _id: 'demo-'+record.image }, { $setOnInsert: {
      ...record, title: images[record.image].title, available: true, stock: 12,
      provenance: 'sourced_photo_simulated_offer',
    } }, { upsert: true, runValidators: true });
    console.log(record.image, result.upsertedCount ? 'inserted' : 'preserved');
  }
} finally { await mongoose.disconnect(); }
