// Local end-to-end diagnostic. Creates two labelled synthetic accounts, then clears
// their consented activity. No real customer account or research artifact changes.
import assert from "node:assert/strict";
import { randomBytes, randomUUID } from "node:crypto";
import { writeFile } from "node:fs/promises";
const output = process.argv[2];
if (!output) throw new Error("Supply a new evidence output path");
function client() {
  let cookie = "";
  return async (path, method = "GET", body) => {
    const response = await fetch("http://127.0.0.1:3000/api" + path, {
      method,
      headers: {
        Origin: "http://127.0.0.1:5173",
        "Content-Type": "application/json",
        Cookie: cookie,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (response.headers.get("set-cookie"))
      cookie = response.headers.get("set-cookie").split(";")[0];
    const data = response.status === 204 ? null : await response.json();
    if (!response.ok)
      throw new Error(`${path}: ${response.status} ${data?.error}`);
    return data;
  };
}
const a = client(),
  b = client(),
  anonymous = client();
const register = async (call) =>
  call("/auth/register", "POST", {
    name: "Demo recommender verification fixture",
    email: `recommendation-${randomUUID()}@example.test`,
    password: randomBytes(24).toString("hex"),
  });
const evidence = {
  kind: "local_engineering_diagnostic_not_research_results",
  date: "2026-10-15",
  checks: [],
};
const check = (name, value) => {
  assert.ok(value, name);
  evidence.checks.push(name);
};
let registeredA = false,
  registeredB = false;
try {
  const products = (await anonymous("/demo/products")).products.filter(
    (p) => p.available && p.stock > 0,
  );
  assert.ok(products.length >= 3);
  const [first, second, third] = products;
  const initial = await anonymous("/demo/recommendations");
  check(
    "anonymous_results_use_only_eligible_demo_ids",
    initial.source === "synthetic_demo" &&
      initial.items.every(
        (r) =>
          r.productId === r.product._id &&
          r.product.available &&
          r.product.stock > 0,
      ),
  );
  await register(a);
  registeredA = true;
  await register(b);
  registeredB = true;
  for (const call of [a, b]) {
    await call("/demo/profile");
    await call("/demo/privacy", "PUT", {
      personalization: true,
      selectedCategories: [],
    });
  }
  await a("/demo/events", "POST", { productId: first._id, type: "view" });
  const content = await a("/demo/recommendations");
  check("one_event_selects_content_route", content.strategy === "content");
  check(
    "seen_item_excluded",
    content.items.every((r) => r.productId !== first._id),
  );
  await a("/demo/events", "POST", { productId: second._id, type: "view" });
  await b("/demo/events", "POST", { productId: first._id, type: "view" });
  await b("/demo/events", "POST", { productId: third._id, type: "view" });
  const hybrid = await a("/demo/recommendations");
  check("two_events_select_hybrid", hybrid.strategy === "cf_popularity_hybrid");
  for (let i = 0; i < 8; i++)
    await a("/demo/events", "POST", { productId: first._id, type: "view" });
  const cf = await a("/demo/recommendations");
  check(
    "sufficient_evidence_selects_cf",
    cf.strategy === "item_cf" && cf.routing.cf_confidence >= 0.25,
  );
  check(
    "cf_returns_co_viewed_unseen_demo_product",
    cf.items.some((r) => r.productId === third._id),
  );
  await a("/demo/history", "DELETE");
  const reset = await a("/demo/recommendations");
  check(
    "reset_discards_personalization",
    reset.personalized === false && reset.routing.history_event_count === 0,
  );
  check("demo_does_not_claim_genai", !cf.genai_used);
  const research = await a("/recommendations");
  check(
    "research_profile_remains_separate",
    research.routing.history_event_count === 0 &&
      research.items.every((r) => typeof r.itemid === "number"),
  );
  evidence.status = "passed";
} finally {
  if (registeredA) await a("/demo/history", "DELETE");
  if (registeredB) await b("/demo/history", "DELETE");
}
await writeFile(output, JSON.stringify(evidence, null, 2), { flag: "wx" });
console.log(JSON.stringify(evidence));
