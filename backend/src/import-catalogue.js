import fs from 'node:fs';
import readline from 'node:readline';
import {fileURLToPath} from 'node:url';
import dotenv from 'dotenv';
import mongoose from 'mongoose';
import {Product} from './repository.js';

dotenv.config({path: fileURLToPath(new URL('../../.env', import.meta.url)), quiet: true});
const catalogue = fileURLToPath(new URL('../../data/processed/metadata-event-count-v1/catalogue.jsonl', import.meta.url));
await mongoose.connect(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/pasal', {serverSelectionTimeoutMS: 5000});
let operations = []; let imported = 0;
try {
  const input = readline.createInterface({input: fs.createReadStream(catalogue), crlfDelay: Infinity});
  for await (const line of input) {
    const record = JSON.parse(line);
    const available = record.properties.available === '1';
    operations.push({updateOne: {filter: {_id: record.itemid}, update: {$set: {
      title: `Catalogue item ${record.itemid}`, category: record.properties.categoryid || '',
      available, metadataCutoffMs: record.as_of_ms, source: 'Retailrocket anonymized research catalogue'
    }}, upsert: true}});
    if (operations.length === 1000) {await Product.bulkWrite(operations); imported += operations.length; operations = [];}
  }
  if (operations.length) {await Product.bulkWrite(operations); imported += operations.length;}
  await Product.createIndexes();
  console.log(`Imported ${imported} historical catalogue records; only available=1 is browsable.`);
} finally {await mongoose.disconnect();}
