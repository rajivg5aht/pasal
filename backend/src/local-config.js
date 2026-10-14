import dotenv from "dotenv";
import { fileURLToPath } from "node:url";
dotenv.config({ path: fileURLToPath(new URL("../../.env", import.meta.url)), quiet: true });
export const mongoUrl = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/pasal";
