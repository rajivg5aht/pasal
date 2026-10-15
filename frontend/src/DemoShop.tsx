import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Heart,
  ShoppingBag,
  Search,
  Leaf,
  X,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { api, type User } from "./api";
import ProductArt from "./ProductArt";
import { Checkout, OrderHistory, OrderSummary, type Order } from "./Orders";
type Product = {
  _id: string;
  title: string;
  category: string;
  subcategory: string;
  description: string;
  priceNpr: number;
  image: string;
  attributes: string[];
  available: boolean;
  stock?: number;
  provenance: string;
};
type Profile = {
  recommendationConsentVersion?: number;
  personalization: boolean;
  selectedCategories: string[];
  eventCount: number;
  wishlist: string[];
  cart: { productId: string; quantity: number }[];
};
const empty: Profile = {
  personalization: false,
  selectedCategories: [],
  eventCount: 0,
  wishlist: [],
  cart: [],
};
const money = (n: number) =>
  new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 0,
  }).format(n);
function Dialog({
  title,
  close,
  children,
  error,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
  error?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={close}
      className="shop-dialog"
      aria-label={title}
    >
      <div className="modal-head">
        <h2>{title}</h2>
        <button aria-label="Close dialog" onClick={close}>
          <X />
        </button>
      </div>
      {children}
      {error && (
        <p className="shop-error" role="alert">
          {error}
        </p>
      )}
    </dialog>
  );
}
export default function DemoShop() {
  const [placedOrder, setPlacedOrder] = useState<Order | null>(null);
  const [recommendations, setRecommendations] = useState<{
    items: { productId: string; reason: string; product: Product }[];
    strategy: string;
    fallback: string | null;
  } | null>(null);
  const [recommendationError, setRecommendationError] = useState("");
  const [user, setUser] = useState<User | null>(null),
    [profile, setProfile] = useState<Profile>(empty),
    [products, setProducts] = useState<Product[]>([]),
    [saved, setSaved] = useState<Product[]>([]),
    [related, setRelated] = useState<Product[]>([]),
    [categories, setCategories] = useState<string[]>([]);
  const [query, setQuery] = useState(""),
    [category, setCategory] = useState(""),
    [sort, setSort] = useState("name"),
    [modal, setModal] = useState(""),
    [detail, setDetail] = useState<Product | null>(null),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const [consent, setConsent] = useState(false),
    [preferred, setPreferred] = useState<string[]>([]);
  async function refreshProfile() {
    const r = await api<{ profile: Profile; products: Product[] }>(
      "/demo/profile",
    );
    setProfile(r.profile);
    setSaved(r.products);
    return r.profile;
  }
  useEffect(() => {
    const controller = new AbortController();
    setRecommendations(null);
    setRecommendationError("");
    api<{
      items: { productId: string; reason: string; product: Product }[];
      strategy: string;
      fallback: string | null;
    }>("/demo/recommendations", "GET", undefined, controller.signal)
      .then((result) => {
        if (!Array.isArray(result.items))
          throw new Error("Invalid recommendation response");
        if (!controller.signal.aborted) setRecommendations(result);
      })
      .catch((e) => {
        if (e.name !== "AbortError")
          setRecommendationError(
            "Suggestions are temporarily unavailable. You can still browse the shop.",
          );
      });
    return () => controller.abort();
  }, [profile, user]);
  useEffect(() => {
    api<{ user: User }>("/me")
      .then((r) => {
        setUser(r.user);
        void refreshProfile().catch((e) => setError(e.message));
      })
      .catch(() => {});
    api<{ categories: string[] }>("/demo/categories")
      .then((r) => setCategories(r.categories))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const timer = setTimeout(() => {
      api<{ products: Product[] }>(
        "/demo/products?" + new URLSearchParams({ query, category, sort }),
        "GET",
        undefined,
        controller.signal,
      )
        .then((r) => setProducts(r.products))
        .catch((e) => {
          if (e.name !== "AbortError") setError(e.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, category, sort]);
  useEffect(() => {
    setRelated([]);
    if (!detail) return;
    const controller = new AbortController();
    api<{ products: Product[] }>(
      "/demo/products?" + new URLSearchParams({ category: detail.category }),
      "GET",
      undefined,
      controller.signal,
    )
      .then((r) => setRelated(r.products))
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [detail]);
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  function needAccount() {
    if (!user) {
      setDetail(null);
      setModal("login");
      return true;
    }
    return false;
  }
  async function event(id: string, type: "view" | "addtocart") {
    if (profile.personalization && profile.recommendationConsentVersion === 1)
      await api("/demo/events", "POST", { productId: id, type });
  }
  function openProduct(p: Product) {
    setDetail(p);
    if (user && profile.personalization)
      void action(async () => {
        await event(p._id, "view");
        await refreshProfile();
      });
  }
  async function wishlist(p: Product) {
    if (needAccount()) return;
    await action(async () => {
      await api("/demo/wishlist", "PUT", {
        productId: p._id,
        add: !profile.wishlist.includes(p._id),
      });
      await refreshProfile();
      setNotice("Wishlist updated.");
    });
  }
  async function cart(p: Product, quantity: number) {
    if (quantity > 10) {
      setError("You can keep up to 10 of each demo product in your cart.");
      return;
    }
    if (needAccount()) return;
    await action(async () => {
      const previous =
        profile.cart.find((r) => r.productId === p._id)?.quantity || 0;
      const result = await api<{ profile: Profile }>("/demo/cart", "PUT", {
        productId: p._id,
        quantity,
      });
      setProfile(result.profile);
      setNotice(
        quantity ? "Your demo cart was updated." : "Removed from your cart.",
      );
      // Saving the cart and optional activity recording are separate operations.
      // A consent change in another tab must not hide a successful cart save.
      if (quantity > previous) {
        try {
          await event(p._id, "addtocart");
        } catch {
          setError(
            "Your cart was saved, but optional browsing activity was not recorded.",
          );
        }
      }
      await refreshProfile();
    });
  }
  function preferences() {
    if (needAccount()) return;
    setConsent(profile.personalization);
    setPreferred(profile.selectedCategories);
    setModal("preferences");
  }
  async function authenticate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await action(async () => {
      const r = await api<{ user: User }>("/auth/" + modal, "POST", {
        email: form.get("email"),
        password: form.get("password"),
        ...(modal === "register" ? { name: form.get("name") } : {}),
      });
      setUser(r.user);
      await refreshProfile();
      setModal("");
      setNotice("Welcome to Pasal.");
    });
  }
  const selected =
    profile.personalization && profile.selectedCategories.length
      ? products.filter((p) => profile.selectedCategories.includes(p.category))
      : [];
  const card = (p: Product) => (
    <article className="card" key={p._id}>
      <div className="item-art tone-1">
        <button
          className="art-link"
          onClick={() => openProduct(p)}
          aria-label={"View " + p.title}
        >
          <ProductArt kind={p.image} title={p.title} />
        </button>
        <button
          className={
            "save-button " + (profile.wishlist.includes(p._id) ? "saved" : "")
          }
          aria-label={"Save " + p.title}
          disabled={busy}
          onClick={() => void wishlist(p)}
        >
          <Heart
            size={18}
            fill={profile.wishlist.includes(p._id) ? "currentColor" : "none"}
          />
        </button>
      </div>
      <div className="card-copy">
        <span className="eyebrow">
          {p.category} · {p.subcategory}
        </span>
        <button className="text-link" onClick={() => openProduct(p)}>
          {p.title}
        </button>
        <p className="demo-price">{money(p.priceNpr)}</p>
        <div className="card-foot">
          <small>Synthetic demo</small>
          <button
            disabled={busy}
            onClick={() =>
              void cart(
                p,
                (profile.cart.find((r) => r.productId === p._id)?.quantity ||
                  0) + 1,
              )
            }
          >
            <ShoppingBag size={16} /> Add to cart
          </button>
        </div>
      </div>
    </article>
  );
  return (
    <>
      <a className="skip-link" href="#shop-catalogue">
        Skip to products
      </a>
      <div className="announcement">
        Kathmandu-inspired demo shop · Synthetic products and prices · No
        payments or delivery
      </div>
      <header className="header">
        <a className="brand" href="#">
          <Leaf /> pasal.
        </a>
        <nav className="shop-nav">
          <a href="#shop-catalogue">Shop</a>
          <a href="#research">Research Lab</a>
          <button onClick={preferences}>Preferences</button>
          {user?.role === "admin" && <a href="#admin">Administrator</a>}
        </nav>
        <div className="shop-actions">
          <button
            aria-label="Open wishlist"
            onClick={() => {
              if (!needAccount()) setModal("wishlist");
            }}
          >
            <Heart />
            <small>{profile.wishlist.length}</small>
          </button>
          <button
            aria-label="Open cart"
            onClick={() => {
              if (!needAccount()) setModal("cart");
            }}
          >
            <ShoppingBag />
            <small>{profile.cart.reduce((a, r) => a + r.quantity, 0)}</small>
          </button>
          <button onClick={() => setModal(user ? "account" : "login")}>
            {user?.name || "Sign in"}
          </button>
        </div>
      </header>
      <main>
        <section className="shop-hero">
          <div>
            <span className="eyebrow">EVERYDAY FINDS · KATHMANDU IN MIND</span>
            <h1>
              A little less searching.
              <br />
              <em>A little more you.</em>
            </h1>
            <p>
              Thoughtful everyday essentials, from a morning tea break to your
              next study session. Explore a clearly labelled demonstration of
              shopping with Pasal.
            </p>
            <a className="primary" href="#shop-catalogue">
              Explore the shop <ArrowRight size={18} />
            </a>
            <small>
              Illustrative products. No real orders or product-origin claims.
            </small>
          </div>
          <div className="shop-hero-art">
            <ProductArt kind="bag" title="Everyday tote concept" />
            <span>Made for everyday discovery.</span>
          </div>
        </section>
        <section className="shop-boundary">
          <ShieldCheck />
          <p>
            <strong>Two experiences, one honest prototype.</strong> This
            synthetic shop is separate from the experimentally evaluated
            Retailrocket recommender.{" "}
            <a href="#research">
              Open the Research Lab to see the real switching system →
            </a>
          </p>
        </section>
        {notice && (
          <p className="shop-notice" role="status">
            {notice}
            <button aria-label="Dismiss notice" onClick={() => setNotice("")}>
              <X size={16} />
            </button>
          </p>
        )}
        {error && (
          <p className="shop-error" role="alert">
            {error}
          </p>
        )}
        {selected.length > 0 && (
          <section className="shop-section">
            <h2>Your chosen categories</h2>
            <p>
              Filtered by your saved demo preferences. This is catalogue
              browsing, not a Retailrocket model prediction.
            </p>
            <div className="grid">{selected.slice(0, 4).map(card)}</div>
          </section>
        )}
        <section className="shop-section" aria-label="Shop recommendations">
          {profile.personalization &&
            profile.recommendationConsentVersion !== 1 && (
              <p>
                Your earlier consent covered category browsing.{" "}
                <button onClick={preferences}>
                  Review preferences to enable demo recommendations
                </button>
                . Enabling starts a fresh recommendation history.
              </p>
            )}
          <h2>
            {recommendations?.strategy === "catalogue_fallback"
              ? "Explore something new"
              : "Suggestions for your next visit"}
          </h2>
          <p>
            Suggestions use this demonstration catalogue and consented demo
            activity. They are separate from the Retailrocket research
            evaluation.
          </p>
          {recommendationError && <p role="status">{recommendationError}</p>}
          {!recommendations && !recommendationError && (
            <p role="status">Loading suggestions…</p>
          )}
          {recommendations && (
            <>
              {!recommendations.items.length && (
                <p>
                  No unseen, in-stock suggestions right now. Explore the full
                  catalogue below.
                </p>
              )}
              <div className="grid">
                {recommendations.items.map((r) => (
                  <div key={r.productId}>
                    {card(r.product)}
                    <p className="recommendation-reason">{r.reason}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
        <section className="shop-section" id="shop-catalogue">
          <span className="eyebrow">FIND YOUR NEXT EVERYDAY FAVOURITE</span>
          <h2>Explore the shop</h2>
          <div className="shop-filters">
            <label>
              <Search size={18} />
              <input
                aria-label="Search products"
                placeholder="Try a notebook, tea or a tote…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
            <select
              aria-label="Product category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <select
              aria-label="Sort products"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="name">Name: A–Z</option>
              <option value="price-low">Price: low to high</option>
              <option value="price-high">Price: high to low</option>
            </select>
          </div>
          {loading ? (
            <p role="status">Loading products…</p>
          ) : products.length ? (
            <div className="grid">{products.map(card)}</div>
          ) : (
            <div className="empty">
              <h3>No matching products</h3>
              <button
                onClick={() => {
                  setQuery("");
                  setCategory("");
                }}
              >
                Clear filters
              </button>
            </div>
          )}
        </section>
        <section className="shop-boundary">
          <Leaf />
          <p>
            <strong>Your choices stay yours.</strong> Demo activity is recorded
            only with your consent. It never enters the frozen thesis
            experiments.{" "}
            <button onClick={preferences}>Manage preferences →</button>
          </p>
        </section>
      </main>
      <footer className="shop-footer">
        <strong>pasal.</strong>
        <p>
          Kathmandu-oriented research prototype · All shop records, attributes,
          prices and illustrations are synthetic. No brands, fulfilment or real
          stock are claimed.
        </p>
        <a href="#research">Research methodology & live model</a>
        <a href="#admin">Administrator sign in</a>
      </footer>
      {(modal === "login" || modal === "register") && (
        <Dialog
          error={error}
          title={modal === "login" ? "Welcome back" : "Create an account"}
          close={() => setModal("")}
        >
          <form className="shop-form" onSubmit={authenticate}>
            {modal === "register" && (
              <label>
                Name
                <input
                  name="name"
                  required
                  maxLength={80}
                  autoComplete="name"
                />
              </label>
            )}
            <label>
              Email
              <input name="email" type="email" required autoComplete="email" />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                minLength={12}
                maxLength={128}
                required
                autoComplete={
                  modal === "login" ? "current-password" : "new-password"
                }
              />
            </label>
            <small>
              At least 12 characters. Demo and Research Lab use the same
              account, with separate profiles.
            </small>
            <button className="primary" disabled={busy}>
              {modal === "login" ? "Sign in" : "Register"}
            </button>
            <button
              type="button"
              onClick={() => setModal(modal === "login" ? "register" : "login")}
            >
              {modal === "login"
                ? "Create an account"
                : "Already registered? Sign in"}
            </button>
          </form>
        </Dialog>
      )}
      {modal === "account" && (
        <Dialog error={error} title="Your account" close={() => setModal("")}>
          <p>
            {user?.name} · {user?.email}
          </p>
          <button className="primary" onClick={preferences}>
            Manage demo preferences
          </button>
          <button onClick={() => setModal("orders")}>Order history</button>
          <button
            onClick={() =>
              void action(async () => {
                await api("/auth/logout", "POST");
                setUser(null);
                setProfile(empty);
                setSaved([]);
                setModal("");
                setNotice("Signed out.");
              })
            }
          >
            Sign out
          </button>
        </Dialog>
      )}
      {modal === "preferences" && (
        <Dialog
          error={error}
          title="Your demo preferences"
          close={() => setModal("")}
        >
          <form
            className="shop-form"
            onSubmit={(e) => {
              e.preventDefault();
              void action(async () => {
                await api("/demo/privacy", "PUT", {
                  personalization: consent,
                  selectedCategories: preferred,
                });
                await refreshProfile();
                setModal("");
                setNotice("Demo preferences saved.");
              });
            }}
          >
            <label className="check-label">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
              />{" "}
              Save my demo browsing activity and category choices
            </label>
            <p>
              Allow demo browsing to personalise your suggestions and contribute
              to co-viewing and popularity signals for other demo shoppers.
              Consenting profiles are used locally; customer activity is never
              sent to a Generative AI provider. Turning this off clears demo
              history and preferences and removes your contribution. Research
              Lab consent is separate.
            </p>
            <fieldset disabled={!consent}>
              <legend>Preferred categories</legend>
              {categories.map((c) => (
                <label className="check-label" key={c}>
                  <input
                    type="checkbox"
                    checked={preferred.includes(c)}
                    onChange={(e) =>
                      setPreferred(
                        e.target.checked
                          ? [...preferred, c]
                          : preferred.filter((x) => x !== c),
                      )
                    }
                  />
                  {c}
                </label>
              ))}
            </fieldset>
            <button className="primary" disabled={busy}>
              Save preferences
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void action(async () => {
                  await api("/demo/history", "DELETE");
                  await refreshProfile();
                  setModal("");
                  setNotice("Demo history cleared and consent turned off.");
                })
              }
            >
              Clear history and turn off
            </button>
          </form>
        </Dialog>
      )}
      {(modal === "wishlist" || modal === "cart") && (
        <Dialog
          error={error}
          title={modal === "cart" ? "Your shopping cart" : "Your wishlist"}
          close={() => setModal("")}
        >
          <p>
            Synthetic products only. Checkout creates a demonstration order,
            with no real charge or delivery.
          </p>
          {(modal === "cart"
            ? profile.cart.map((r) => r.productId)
            : profile.wishlist
          ).map((id) => {
            const p = saved.find((r) => r._id === id);
            const line = profile.cart.find((r) => r.productId === id);
            return (
              <div className="shop-list-row" key={id}>
                {p ? (
                  <>
                    <ProductArt kind={p.image} title={p.title} />
                    <div>
                      <button
                        onClick={() => {
                          setModal("");
                          openProduct(p);
                        }}
                      >
                        {p.title}
                      </button>
                      <p>
                        {money(p.priceNpr)}
                        {!p.available ? " · Unavailable" : ""}
                      </p>
                      {modal === "cart" && (
                        <label>
                          Quantity{" "}
                          <input
                            aria-label={"Quantity for " + p.title}
                            type="number"
                            min={1}
                            max={10}
                            value={line?.quantity || 1}
                            disabled={busy || !p.available}
                            onChange={(e) => {
                              const quantity = Number(e.target.value);
                              if (
                                Number.isInteger(quantity) &&
                                quantity >= 1 &&
                                quantity <= 10
                              )
                                void cart(p, quantity);
                            }}
                          />
                        </label>
                      )}
                    </div>
                    <button
                      aria-label={"Remove " + p.title}
                      disabled={busy}
                      onClick={() =>
                        void (modal === "cart" ? cart(p, 0) : wishlist(p))
                      }
                    >
                      <X />
                    </button>
                  </>
                ) : (
                  <p>Unavailable saved product. Contact the administrator.</p>
                )}
              </div>
            );
          })}
          {(modal === "cart" ? profile.cart : profile.wishlist).length ===
            0 && (
            <p className="empty">
              Nothing here yet. Explore the shop to find something you like.
            </p>
          )}
          {modal === "cart" && (
            <div className="shop-total">
              <strong>
                Demo total:{" "}
                {money(
                  profile.cart.reduce(
                    (a, r) =>
                      a +
                      (saved.find((p) => p._id === r.productId)?.priceNpr ||
                        0) *
                        r.quantity,
                    0,
                  ),
                )}
              </strong>
              <p>
                Demonstration prices. Availability and stock are checked when
                ordering.
              </p>
              <button
                className="primary"
                disabled={
                  busy ||
                  !profile.cart.length ||
                  profile.cart.some(
                    (l) => !saved.find((p) => p._id === l.productId)?.available,
                  )
                }
                onClick={() => {
                  setError("");
                  setModal("checkout");
                }}
              >
                Review checkout
              </button>
            </div>
          )}
        </Dialog>
      )}
      {modal === "checkout" && (
        <Dialog title="Demonstration checkout" close={() => setModal("")}>
          <Checkout
            lines={profile.cart}
            total={profile.cart.reduce(
              (sum, l) =>
                sum +
                (saved.find((p) => p._id === l.productId)?.priceNpr || 0) *
                  l.quantity,
              0,
            )}
            onPlaced={(order) => {
              setPlacedOrder(order);
              setModal("confirmation");
              void refreshProfile().catch((e) => setError(e.message));
            }}
            onReviewCart={() => {
              void action(async () => {
                await refreshProfile();
                setModal("cart");
              });
            }}
          />
        </Dialog>
      )}
      {modal === "confirmation" && placedOrder && (
        <Dialog
          title="Demonstration order placed"
          error={error}
          close={() => setModal("")}
        >
          <OrderSummary order={placedOrder} />
          <button onClick={() => setModal("orders")}>View order history</button>
        </Dialog>
      )}
      {modal === "orders" && (
        <Dialog title="Order history" close={() => setModal("")}>
          <OrderHistory />
        </Dialog>
      )}
      {detail && (
        <Dialog
          error={error}
          title={detail.title}
          close={() => setDetail(null)}
        >
          <div className="shop-detail">
            <ProductArt kind={detail.image} title={detail.title} />
            <div>
              <span className="eyebrow">
                {detail.category} · {detail.subcategory}
              </span>
              <p className="demo-price">{money(detail.priceNpr)}</p>
              <p>{detail.description}</p>
              <ul>
                {detail.attributes.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
              <small>
                Synthetic demo product and illustration. No verified brand or
                origin. ID: {detail._id}
              </small>
              <button
                className="primary"
                disabled={busy || !detail.available}
                onClick={() =>
                  void cart(
                    detail,
                    (profile.cart.find((r) => r.productId === detail._id)
                      ?.quantity || 0) + 1,
                  )
                }
              >
                Add to cart
              </button>
            </div>
          </div>
          <h3>More in {detail.category}</h3>
          <p>Same-category browsing, not model recommendations.</p>
          <div className="shop-related">
            {related
              .filter(
                (p) => p.category === detail.category && p._id !== detail._id,
              )
              .slice(0, 3)
              .map((p) => (
                <button key={p._id} onClick={() => openProduct(p)}>
                  {p.title} · {money(p.priceNpr)}
                </button>
              ))}
          </div>
        </Dialog>
      )}
    </>
  );
}
export type { Product };
