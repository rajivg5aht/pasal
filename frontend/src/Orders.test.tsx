import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { Checkout, OrderHistory } from "./Orders";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const order = {
  _id: "order-" + "a".repeat(64),
  status: "placed",
  createdAt: "2026-10-14T00:00:00Z",
  totalNpr: 600,
  delivery: { recipient: "Example", area: "Kathmandu", note: "" },
  lines: [
    {
      productId: "demo-mug",
      title: "Synthetic mug",
      quantity: 1,
      unitPriceNpr: 600,
    },
  ],
  history: [{ status: "placed", at: "2026-10-14T00:00:00Z" }],
};
const response = (value: unknown) => ({
  ok: true,
  status: 200,
  json: async () => value,
});
it("retries an ambiguous checkout using exactly the same idempotency key and payload", async () => {
  const writes: unknown[] = [];
  const placed = vi.fn();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, options?: RequestInit) => {
      if (url === "/api/demo/checkout-status")
        return response({ available: true });
      if (url === "/api/demo/orders") {
        writes.push(JSON.parse(options?.body as string));
        if (writes.length === 1) throw new Error("Network interrupted");
        return response({ order });
      }
      throw new Error("Unexpected request");
    }),
  );
  render(
    <Checkout
      lines={[{ productId: "demo-mug", quantity: 1 }]}
      total={600}
      onPlaced={placed}
    />,
  );
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Place demonstration order" }),
    ).not.toBeDisabled(),
  );
  fireEvent.change(screen.getByLabelText("Demo recipient name"), {
    target: { value: "Example shopper" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(
    screen.getByRole("button", { name: "Place demonstration order" }),
  );
  await screen.findByText("Network interrupted");
  fireEvent.click(screen.getByRole("button", { name: "Retry the same order" }));
  await waitFor(() => expect(placed).toHaveBeenCalledWith(order));
  expect(writes).toHaveLength(2);
  expect(writes[0]).toEqual(writes[1]);
  expect(writes[0]).toMatchObject({
    simulationAccepted: true,
    expectedTotalNpr: 600,
    lines: [{ productId: "demo-mug", quantity: 1 }],
  });
});
it("disables placing orders when transactional checkout is unavailable", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => response({ available: false })),
  );
  render(
    <Checkout
      lines={[{ productId: "demo-mug", quantity: 1 }]}
      total={600}
      onPlaced={vi.fn()}
    />,
  );
  await screen.findByText(/awaiting transaction-ready/);
  expect(
    screen.getByRole("button", { name: "Place demonstration order" }),
  ).toBeDisabled();
});
it("loads customer history and cancels only a placed order", async () => {
  let cancelled = false;
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      calls.push(url);
      if (url.endsWith("/cancel")) {
        cancelled = true;
        return response({ order: { ...order, status: "cancelled" } });
      }
      return response({
        orders: [{ ...order, status: cancelled ? "cancelled" : "placed" }],
        next: null,
      });
    }),
  );
  render(<OrderHistory />);
  fireEvent.click(await screen.findByRole("button", { name: "Cancel order" }));
  await screen.findByText("Demonstration order · cancelled");
  expect(screen.queryByRole("button", { name: "Cancel order" })).toBeNull();
  expect(calls).toContain(`/api/demo/orders/${order._id}/cancel`);
  expect(calls.some((p) => p.includes("/admin/"))).toBe(false);
});
