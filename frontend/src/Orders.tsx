import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "./api";
export type Order = {
  _id: string;
  status: string;
  createdAt: string;
  totalNpr: number;
  delivery: { recipient: string; area: string; note: string };
  lines: {
    productId: string;
    title: string;
    quantity: number;
    unitPriceNpr: number;
  }[];
  history: { status: string; at: string }[];
};
const money = (value: number) => `NPR ${value.toLocaleString("en-NP")}`;
export function OrderSummary({ order }: { order: Order }) {
  return (
    <article className="order-card">
      <h3>Demonstration order · {order.status}</h3>
      <p>
        <small>Reference: {order._id}</small>
      </p>
      <p>
        {new Date(order.createdAt).toLocaleString()} · {order.delivery.area}
      </p>
      <ul>
        {order.lines.map((l) => (
          <li key={l.productId}>
            {l.title} × {l.quantity} — {money(l.quantity * l.unitPriceNpr)}
          </li>
        ))}
      </ul>
      <strong>{money(order.totalNpr)}</strong>
      <p>
        Simulation only. No payment collected and no delivery will take place.
      </p>
      <details>
        <summary>Order timeline and demo delivery details</summary>
        <p>
          {order.delivery.recipient} · {order.delivery.area} ·{" "}
          {order.delivery.note}
        </p>
        <ol>
          {order.history.map((h, i) => (
            <li key={i}>
              {h.status} · {new Date(h.at).toLocaleString()}
            </li>
          ))}
        </ol>
      </details>
    </article>
  );
}
export function Checkout({
  lines,
  total,
  onPlaced,
  onReviewCart,
}: {
  lines: { productId: string; quantity: number }[];
  total: number;
  onPlaced: (order: Order) => void;
  onReviewCart?: () => void;
}) {
  const [available, setAvailable] = useState<boolean | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState(false);
  // Keep the exact request after an ambiguous network failure so retry cannot create another order.
  const pending = useRef<Record<string, unknown> | null>(null);
  useEffect(() => {
    api<{ available: boolean }>("/demo/checkout-status")
      .then((r) => setAvailable(r.available))
      .catch((e) => setError(e.message));
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    pending.current ??= {
      key: crypto.randomUUID(),
      lines,
      expectedTotalNpr: total,
      simulationAccepted: true,
      delivery: {
        recipient: data.get("recipient"),
        area: data.get("area"),
        note: data.get("note"),
      },
    };
    try {
      const r = await api<{ order: Order }>(
        "/demo/orders",
        "POST",
        pending.current,
      );
      onPlaced(r.order);
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && [400, 409].includes(e.status))
        setConflict(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <p>
        Signed-in demonstration checkout. Use fictional contact details only. No
        phone number, street address or payment information is required.
      </p>
      <p>
        <strong>Reviewed cart total: {money(total)}</strong> · No delivery fee
        or real charge.
      </p>
      {available === false && (
        <p role="status">
          Ordering is awaiting transaction-ready database setup. Your cart
          remains saved.
        </p>
      )}
      {available === null && <p>Checking checkout availability…</p>}
      <form className="shop-form" onSubmit={submit}>
        <fieldset disabled={busy || Boolean(pending.current)}>
          <label>
            Demo recipient name
            <input
              name="recipient"
              required
              minLength={2}
              maxLength={80}
              placeholder="Example shopper"
              autoComplete="off"
            />
          </label>
          <label>
            Demo delivery area
            <select name="area">
              <option>Kathmandu</option>
              <option>Lalitpur</option>
              <option>Bhaktapur</option>
            </select>
          </label>
          <label>
            Demo delivery note (optional)
            <input
              name="note"
              maxLength={120}
              placeholder="Fictional instructions only"
              autoComplete="off"
            />
          </label>
          <label className="check-label">
            <input type="checkbox" required /> I understand this is a simulated
            order with no charge or delivery.
          </label>
        </fieldset>
        <button
          className="primary"
          disabled={busy || available !== true || conflict}
        >
          {pending.current
            ? "Retry the same order"
            : "Place demonstration order"}
        </button>
        {pending.current && (
          <p>
            The submitted details are locked for safe retry. Check order history
            before starting a different checkout.
          </p>
        )}
      </form>
      {conflict && onReviewCart && (
        <button onClick={onReviewCart}>Refresh and review cart</button>
      )}
      {error && (
        <p role="alert" className="shop-error">
          {error}
        </p>
      )}
    </section>
  );
}
export function OrderHistory({ admin = false }: { admin?: boolean }) {
  const [orders, setOrders] = useState<Order[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [loaded, setLoaded] = useState(false);
  const [next, setNext] = useState<{ at: string; id: string } | null>(null);
  const path = admin ? "/admin/orders" : "/demo/orders";
  async function load(more = false) {
    setBusy(true);
    setError("");
    try {
      const r = await api<{
        orders: Order[];
        next: { at: string; id: string } | null;
      }>(path + (more && next ? "?" + new URLSearchParams(next) : ""));
      setOrders((old) => (more ? [...old, ...r.orders] : r.orders));
      setNext(r.next);
      setLoaded(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    void load();
  }, [admin]);
  async function change(order: Order, status: string) {
    setBusy(true);
    setError("");
    try {
      await api(
        admin ? `${path}/${order._id}` : `${path}/${order._id}/cancel`,
        admin ? "PATCH" : "POST",
        admin ? { expected: order.status, status } : {},
      );
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const transitions: Record<string, string[]> = {
    placed: ["confirmed", "cancelled"],
    confirmed: ["dispatched", "cancelled"],
    dispatched: ["delivered"],
  };
  return (
    <section className="orders-section">
      <h2>
        {admin ? "Manage demonstration orders" : "Your demonstration orders"}
      </h2>
      <button disabled={busy} onClick={() => void load()}>
        Refresh orders
      </button>
      {error && (
        <p role="alert" className="shop-error">
          {error}
        </p>
      )}
      {loaded && !orders.length && <p>No demonstration orders yet.</p>}
      {orders.map((order) => (
        <div key={order._id}>
          <OrderSummary order={order} />
          {(admin
            ? transitions[order.status] || []
            : order.status === "placed"
              ? ["cancelled"]
              : []
          ).map((status) => (
            <button
              disabled={busy}
              key={status}
              onClick={() => void change(order, status)}
            >
              {status === "cancelled"
                ? "Cancel order"
                : `Mark ${status} (simulation)`}
            </button>
          ))}
        </div>
      ))}
      {next && (
        <button disabled={busy} onClick={() => void load(true)}>
          Older orders
        </button>
      )}
    </section>
  );
}
