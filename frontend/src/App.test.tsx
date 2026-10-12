import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";

const product = {
  _id: 7,
  title: "Catalogue item 7",
  category: "9",
  available: true,
  source: "Research",
  metadataCutoffMs: 100,
};
beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      const path = String(input);
      if (path === "/api/me")
        return {
          ok: false,
          status: 401,
          json: async () => ({ error: "Sign in" }),
        };
      if (path === "/api/categories")
        return {
          ok: true,
          status: 200,
          json: async () => ({ categories: ["9"] }),
        };
      if (path === "/api/recommendations")
        return { ok: true, status: 200, json: async () => ({ items: [] }) };
      return {
        ok: true,
        status: 200,
        json: async () => ({ products: [product], nextCursor: null }),
      };
    }),
  );
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("research storefront", () => {
  it("refreshes recommendations after a consented view is stored", async () => {
    let eventStored = false;
    const fetchMock = vi.fn(async (input: string) => {
      if (input === "/api/me")
        return {
          ok: true,
          status: 200,
          json: async () => ({
            user: {
              id: "fixture",
              name: "Fixture",
              email: "fixture@example.test",
              personalization: true,
              selectedCategories: [],
              wishlist: [],
              cart: [],
            },
          }),
        };
      if (input === "/api/categories")
        return {
          ok: true,
          status: 200,
          json: async () => ({ categories: [] }),
        };
      if (input === "/api/events") {
        eventStored = true;
        return { ok: true, status: 204 };
      }
      if (input === "/api/recommendations")
        return {
          ok: true,
          status: 200,
          json: async () => ({
            items: eventStored
              ? []
              : [
                  {
                    itemid: 7,
                    product,
                    reason: "Fixture recommendation",
                    description_source: "unavailable",
                    catalogue_description: null,
                  },
                ],
          }),
        };
      return {
        ok: true,
        status: 200,
        json: async () => ({ products: [product], nextCursor: null }),
      };
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await screen.findByRole("button", { name: "Fixture" });
    expect(
      await screen.findByText("Fixture recommendation"),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getAllByRole("button", { name: "Catalogue item 7" })[0],
    );
    await waitFor(() =>
      expect(
        screen.queryByText("Fixture recommendation"),
      ).not.toBeInTheDocument(),
    );
    expect(eventStored).toBe(true);
    expect(
      fetchMock.mock.calls.filter(([path]) => path === "/api/events"),
    ).toHaveLength(1);
  });
  it("closes item details when a guest starts basket sign-in", async () => {
    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Catalogue item 7",
      }),
    );
    expect(
      screen.getByRole("dialog", { name: "Catalogue item 7" }),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Add to research basket" }),
    );
    expect(
      screen.queryByRole("dialog", { name: "Catalogue item 7" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("dialog", { name: "Welcome back" }),
    ).toBeInTheDocument();
  });

  it("loads actual API cards and gates saving behind sign-in", async () => {
    render(<App />);
    expect(
      await screen.findByRole("button", { name: "Catalogue item 7" }),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Save Catalogue item 7" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Welcome back" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "minlength",
      "12",
    );
  });
  it("renders catalogue errors with a retry rather than fake products", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 503,
        json: async () => ({ error: "Service unavailable" }),
      })),
    );
    render(<App />);
    await waitFor(() =>
      expect(
        screen.getByText("The catalogue is taking a moment"),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("Catalogue item 7")).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("button", { name: "Try again" }).length,
    ).toBeGreaterThan(0);
  });
});
