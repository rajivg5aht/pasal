import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import DemoShop from "./DemoShop";
import Admin from "./Admin";

it("creates a demo product through the administrator form without assigning a research ID", async () => {
  const writes: Record<string, unknown>[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, options?: RequestInit) => {
      let data: unknown = {};
      if (input === "/api/me")
        data = { user: { name: "Operator", role: "admin" } };
      else if (input === "/api/admin/overview")
        data = {
          products: 0,
          available: 0,
          categories: [],
          activity: { consentingProfiles: 0, events: 0 },
          service: { status: "ok" },
          research: {
            window: "Test fixture",
            requests: 0,
            failures: 0,
            strategies: {},
            fallbackRecorded: 0,
            p95Ms: null,
            latestModel: null,
          },
        };
      else if (input === "/api/admin/products") {
        if (options?.method === "POST")
          writes.push(JSON.parse(options.body as string));
        data = { products: [] };
      } else throw new Error("Unexpected endpoint: " + input);
      return { ok: true, status: 200, json: async () => data };
    }),
  );
  render(<Admin />);
  await screen.findByRole("button", { name: "Save demo product" });
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "Demo tea mug" },
  });
  fireEvent.change(screen.getByLabelText("Category"), {
    target: { value: "Home" },
  });
  fireEvent.change(screen.getByLabelText("Subcategory"), {
    target: { value: "Mugs" },
  });
  fireEvent.change(screen.getByLabelText("Description"), {
    target: { value: "An explicitly synthetic test product." },
  });
  fireEvent.change(screen.getByLabelText("Illustration"), {
    target: { value: "mug" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save demo product" }));
  await screen.findByText("Demo product created.");
  expect(writes).toHaveLength(1);
  expect(writes[0]).toMatchObject({
    title: "Demo tea mug",
    image: "mug",
    category: "Home",
  });
  expect(writes[0]).not.toHaveProperty("_id");
});
const product = {
  _id: "demo-mug",
  title: "Synthetic morning mug",
  category: "Home",
  subcategory: "Mugs",
  description: "A synthetic demonstration mug.",
  priceNpr: 600,
  image: "mug",
  attributes: ["Synthetic ceramic"],
  available: true,
  provenance: "synthetic_demo",
};
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("uses only demo catalogue IDs for cart and wishlist and never calls the research ranker", async () => {
  let profile = {
    personalization: false,
    selectedCategories: [],
    eventCount: 0,
    wishlist: [] as string[],
    cart: [] as { productId: string; quantity: number }[],
  };
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    let data: unknown = {};
    if (input === "/api/me")
      data = {
        user: {
          id: "fixture",
          name: "Fixture",
          role: "customer",
          email: "fixture@example.test",
        },
      };
    else if (input === "/api/demo/categories") data = { categories: ["Home"] };
    else if (input.startsWith("/api/demo/products"))
      data = { products: [product] };
    else if (input === "/api/demo/profile")
      data = { profile, products: [product] };
    else if (input === "/api/demo/cart") {
      profile = { ...profile, cart: [JSON.parse(options?.body as string)] };
      data = { profile };
    } else if (input === "/api/demo/wishlist") {
      const body = JSON.parse(options?.body as string);
      profile = { ...profile, wishlist: body.add ? [body.productId] : [] };
      data = { profile };
    } else throw new Error("Unexpected endpoint: " + input);
    return { ok: true, status: 200, json: async () => data };
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<DemoShop />);
  await screen.findByRole("button", { name: "View Synthetic morning mug" });
  fireEvent.click(screen.getByRole("button", { name: "Add to cart" }));
  await screen.findByText("Your demo cart was updated.");
  expect(profile.cart).toEqual([{ productId: "demo-mug", quantity: 1 }]);
  fireEvent.click(
    screen.getByRole("button", { name: "Save Synthetic morning mug" }),
  );
  await screen.findByText("Wishlist updated.");
  expect(profile.wishlist).toEqual(["demo-mug"]);
  fireEvent.click(screen.getByRole("button", { name: "Open cart" }));
  await screen.findByRole("dialog", { name: "Your shopping cart" });
  expect(screen.getByRole("button", { name: "Review checkout" })).toBeTruthy();
  expect(
    fetchMock.mock.calls.some(
      ([p]) => p === "/api/recommendations" || p === "/api/events",
    ),
  ).toBe(false);
});
it("searches natural product text and opens a labelled synthetic detail", async () => {
  const fetchMock = vi.fn(async (input: string) => ({
    ok: input !== "/api/me",
    status: input === "/api/me" ? 401 : 200,
    json: async () =>
      input === "/api/me"
        ? { error: "Sign in" }
        : input === "/api/demo/categories"
          ? { categories: ["Home"] }
          : { products: [product] },
  }));
  vi.stubGlobal("fetch", fetchMock);
  render(<DemoShop />);
  fireEvent.change(screen.getByRole("textbox", { name: "Search products" }), {
    target: { value: "morning mug" },
  });
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(([p]) => p.includes("query=morning+mug")),
    ).toBe(true),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "View Synthetic morning mug" }),
  );
  await screen.findByRole("dialog", { name: "Synthetic morning mug" });
  expect(screen.getByText(/No verified brand or origin/)).toBeTruthy();
});
it("does not render administrator data for a customer", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ user: { name: "Customer", role: "customer" } }),
  }));
  vi.stubGlobal("fetch", fetchMock);
  render(<Admin />);
  await screen.findByText("Administrator access required.");
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(
    screen.queryByRole("button", { name: "Save demo product" }),
  ).toBeNull();
});

it("keeps a saved cart visible when optional activity is rejected and does not log quantity decreases", async () => {
  let profile = {
    personalization: true,
    selectedCategories: [],
    eventCount: 0,
    wishlist: [],
    cart: [] as { productId: string; quantity: number }[],
  };
  let events = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, options?: RequestInit) => {
      let data: unknown = {};
      if (input === "/api/me")
        data = { user: { id: "fixture", name: "Fixture", role: "customer" } };
      else if (input === "/api/demo/categories")
        data = { categories: ["Home"] };
      else if (input.startsWith("/api/demo/products"))
        data = { products: [product] };
      else if (input === "/api/demo/profile")
        data = { profile, products: [product] };
      else if (input === "/api/demo/cart") {
        profile = { ...profile, cart: [JSON.parse(options?.body as string)] };
        data = { profile };
      } else if (input === "/api/demo/events") {
        events++;
        return {
          ok: false,
          status: 409,
          json: async () => ({ error: "Consent changed in another tab" }),
        };
      } else throw new Error("Unexpected endpoint: " + input);
      return { ok: true, status: 200, json: async () => data };
    }),
  );
  render(<DemoShop />);
  await screen.findByRole("button", { name: "View Synthetic morning mug" });
  fireEvent.click(screen.getByRole("button", { name: "Add to cart" }));
  await screen.findByText(
    "Your cart was saved, but optional browsing activity was not recorded.",
  );
  expect(profile.cart).toEqual([{ productId: "demo-mug", quantity: 1 }]);
  fireEvent.click(screen.getByRole("button", { name: "Open cart" }));
  const quantity = await screen.findByRole("spinbutton", {
    name: "Quantity for Synthetic morning mug",
  });
  expect((quantity as HTMLInputElement).value).toBe("1");
  fireEvent.change(quantity, { target: { value: "2" } });
  await waitFor(() => expect(events).toBe(2));
  await waitFor(() => expect(quantity).not.toBeDisabled());
  fireEvent.change(quantity, { target: { value: "1" } });
  await waitFor(() => expect(profile.cart[0].quantity).toBe(1));
  await waitFor(() => expect(quantity).not.toBeDisabled());
  expect(events).toBe(2);
});
