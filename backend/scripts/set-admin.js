// Local operator action only; does not create a password or a default account.
import mongoose from "mongoose";
import { User } from "../src/repository.js";
import { mongoUrl } from "../src/local-config.js";
const email = process.argv[2]?.trim().toLowerCase();
if (!email || !email.includes("@"))
  throw new Error("Usage: node scripts/set-admin.js existing-account-email");
await mongoose.connect(mongoUrl);
try {
  const result = await User.updateOne({ email }, { $set: { role: "admin" } });
  if (result.matchedCount !== 1)
    throw new Error(
      "Register the intended account first; no account was created",
    );
  console.log(
    "Administrator role assigned to the specified existing account. Sign in with its own password.",
  );
} finally {
  await mongoose.disconnect();
}
