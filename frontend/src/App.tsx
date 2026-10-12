import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  ArrowRight,
  Check,
  Heart,
  Leaf,
  Search,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import {
  api,
  ApiError,
  type Product,
  type Recommendation,
  type User,
} from "./api";

function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog ref={ref} onCancel={close} aria-label={title}>
      <div className="modal-head">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={close}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

function Card({
  product,
  reason,
  description,
  user,
  busy,
  openProduct,
  listAction,
}: {
  product: Product;
  reason?: string;
  description?: string;
  user: User | null;
  busy: boolean;
  openProduct: (product: Product) => void;
  listAction: (list: "wishlist" | "cart", id: number) => Promise<void>;
}) {
  return (
    <article className="card">
      <div className={"item-art tone-" + (product._id % 4)}>
        <button
          className="art-link"
          onClick={() => openProduct(product)}
          aria-label={"View " + product.title}
        >
          <span className="item-symbol">
            <ShoppingBag size={54} strokeWidth={1} />
          </span>
          <span className="item-number">
            {String(product._id).padStart(6, "0")}
          </span>
        </button>
        <button
          className={
            "save-button " +
            (user?.wishlist.includes(product._id) ? "saved" : "")
          }
          aria-label={
            (user?.wishlist.includes(product._id) ? "Unsave " : "Save ") +
            product.title
          }
          disabled={busy}
          onClick={() => void listAction("wishlist", product._id)}
        >
          <Heart
            size={18}
            fill={
              user?.wishlist.includes(product._id) ? "currentColor" : "none"
            }
          />
        </button>
      </div>
      <div className="card-copy">
        <span className="eyebrow">
          {product.category ? "Category " + product.category : "Uncategorized"}
        </span>
        <button className="text-link" onClick={() => openProduct(product)}>
          {product.title}
        </button>
        {reason && (
          <p className="reason">
            <Sparkles size={13} />
            {reason}
          </p>
        )}
        {description && (
          <details className="generated-description">
            <summary>AI catalogue summary</summary>
            <p>{description}</p>
            <small>
              Generated from the historical snapshot and reviewed for grounding.
              This is not current stock information.
            </small>
          </details>
        )}
        <div className="card-foot">
          <span>Research catalogue</span>
          <button
            aria-label={"Add " + product.title + " to basket"}
            disabled={busy}
            onClick={() => void listAction("cart", product._id)}
          >
            <ShoppingBag size={16} />
            {user?.cart.includes(product._id) ? "Remove" : "Add"}
          </button>
        </div>
      </div>
    </article>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null),
    [products, setProducts] = useState<Product[]>([]),
    [categories, setCategories] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]),
    [recError, setRecError] = useState("");
  const [query, setQuery] = useState(""),
    [category, setCategory] = useState(""),
    [cursor, setCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const [modal, setModal] = useState<
      "login" | "register" | "privacy" | "wishlist" | "cart" | null
    >(null),
    [detail, setDetail] = useState<Product | null>(null);
  const [refresh, setRefresh] = useState(0);
  const catalog = useRef<HTMLElement>(null);
  const filterKey = JSON.stringify([query, category, refresh]);
  const currentFilter = useRef(filterKey);
  currentFilter.current = filterKey;
  useEffect(() => {
    api<{ user: User }>("/me")
      .then((r) => setUser(r.user))
      .catch((e) => {
        if (!(e instanceof ApiError && e.status === 401))
          setError("The account service is unavailable.");
      });
    api<{ categories: string[] }>("/categories")
      .then((r) => setCategories(r.categories))
      .catch(() => {});
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timer = setTimeout(() => {
      api<{ products: Product[]; nextCursor: number | null }>(
        "/products?" +
          new URLSearchParams({
            ...(query ? { query } : {}),
            ...(category ? { category } : {}),
          }),
        "GET",
        undefined,
        controller.signal,
      )
        .then((r) => {
          setProducts(r.products);
          setCursor(r.nextCursor);
        })
        .catch((e) => {
          if (e.name !== "AbortError") setError(e.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, category, refresh]);
  useEffect(() => {
    const controller = new AbortController();
    setRecError("");
    api<{ items: Recommendation[] }>(
      "/recommendations",
      "GET",
      undefined,
      controller.signal,
    )
      .then((r) => setRecommendations(r.items))
      .catch((e) => {
        if (e.name !== "AbortError")
          setRecError(
            "Recommendations are temporarily unavailable. You can still browse the catalogue.",
          );
      });
    return () => controller.abort();
  }, [user, refresh]);
  async function act(action: () => Promise<void>) {
    setBusy(true);
    setNotice("");
    try {
      await action();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Please try again.");
    } finally {
      setBusy(false);
    }
  }
  async function auth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await act(async () => {
      const result = await api<{ user: User }>(
        modal === "register" ? "/auth/register" : "/auth/login",
        "POST",
        {
          email: form.get("email"),
          password: form.get("password"),
          ...(modal === "register" ? { name: form.get("name") } : {}),
        },
      );
      setUser(result.user);
      setModal(null);
      setNotice("Welcome to Pasal. Personalization is yours to choose.");
    });
  }
  async function listAction(list: "wishlist" | "cart", id: number) {
    if (!user) {
      setDetail(null);
      setModal("login");
      return;
    }
    await act(async () => {
      const add = !user[list].includes(id);
      const result = await api<{ user: User }>(
        "/" + list,
        add ? "POST" : "DELETE",
        { itemid: id },
      );
      setUser(result.user);
      setNotice(
        add
          ? list === "cart"
            ? "Added to your research basket."
            : "Saved to your wishlist."
          : "Item removed.",
      );
      if (add && list === "cart" && user.personalization)
        await api("/events", "POST", { itemid: id, type: "addtocart" }).catch(
          () => {},
        );
    });
  }
  function openProduct(product: Product) {
    setDetail(product);
    if (user?.personalization)
      void api("/events", "POST", { itemid: product._id, type: "view" }).catch(
        () => {},
      );
  }
  async function savePrivacy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await act(async () => {
      const result = await api<{ user: User }>("/privacy", "PUT", {
        personalization: form.has("personalization"),
        selectedCategories: form.getAll("categories"),
      });
      setUser(result.user);
      setModal(null);
      setNotice("Your preferences have been saved.");
    });
  }

  return (
    <>
      <div className="announcement">
        A more thoughtful way to discover. <span>Pasal · Research preview</span>
      </div>
      <header className="header">
        <a className="brand" href="#" aria-label="Pasal home">
          <span className="brand-mark">
            <Leaf size={20} />
          </span>
          pasal<span className="brand-dot">.</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#catalogue">Explore</a>
          <a href="#for-you">For you</a>
          <button onClick={() => setModal(user ? "privacy" : "login")}>
            Your preferences
          </button>
        </nav>
        <div className="header-actions">
          <button
            className="icon-button"
            aria-label="Open wishlist"
            onClick={() => setModal(user ? "wishlist" : "login")}
          >
            <Heart size={20} />
          </button>
          <button
            className="icon-button"
            aria-label="Open basket"
            onClick={() => setModal(user ? "cart" : "login")}
          >
            <ShoppingBag size={20} />
            {!!user?.cart.length && (
              <span className="count">{user.cart.length}</span>
            )}
          </button>
          <button
            className="account-button"
            onClick={() => setModal(user ? "privacy" : "login")}
          >
            <UserRound size={17} />
            <span>{user ? user.name.split(" ")[0] : "Sign in"}</span>
          </button>
        </div>
      </header>
      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">
              <span className="little-line" />
              DISCOVERY, WITH YOU IN MIND
            </span>
            <h1>
              A little less searching.
              <br />
              <em>A little more you.</em>
            </h1>
            <p>
              Explore the catalogue, save what catches your eye, and shape the
              recommendations you receive. Your preferences stay in your hands.
            </p>
            <button
              className="primary"
              onClick={() =>
                catalog.current?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Explore the catalogue <ArrowRight size={18} />
            </button>
            <div className="hero-note">
              <ShieldCheck size={16} />
              Personalization is optional. Always.
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="art-card art-card-back">
              <Leaf size={72} strokeWidth={1} />
            </div>
            <div className="art-card art-card-front">
              <ShoppingBag size={90} strokeWidth={0.8} />
              <span>Made for discovery.</span>
            </div>
            <div className="floating-label">
              <Sparkles size={17} />
              <div>
                A considered selection<small>Guided by your choices</small>
              </div>
            </div>
            <span className="vertical-label">EXPLORE · SAVE · DISCOVER</span>
          </div>
        </section>
        <section className="values" aria-label="Our approach">
          <div>
            <SlidersHorizontal size={20} />
            <span>
              Your choices lead<small>Choose if and how to personalize</small>
            </span>
          </div>
          <div>
            <ShieldCheck size={20} />
            <span>
              Transparent by design<small>Understand why an item appears</small>
            </span>
          </div>
          <div>
            <Heart size={20} />
            <span>
              Keep what you like<small>Build a wishlist at your own pace</small>
            </span>
          </div>
        </section>
        {notice && (
          <div className="notice" role="status">
            {notice}
            <button
              className="icon-button"
              aria-label="Dismiss message"
              onClick={() => setNotice("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        <section className="section" id="for-you">
          <div className="section-heading">
            <div>
              <span className="eyebrow">A PLACE TO START</span>
              <h2>
                {user?.personalization
                  ? "Selected with your activity in mind"
                  : "Discover a starting point"}
              </h2>
            </div>
            <button
              className="subtle-button"
              onClick={() => setModal(user ? "privacy" : "login")}
            >
              <SlidersHorizontal size={16} />
              Make it yours
            </button>
          </div>
          <p className="section-description">
            {user?.personalization
              ? "Your activity and preferences help select a recommendation strategy."
              : "Explore historically popular items. Sign in to choose whether to personalize."}
          </p>
          {recError ? (
            <div className="empty-state compact">
              <p>{recError}</p>
              <button
                className="subtle-button"
                onClick={() => setRefresh((v) => v + 1)}
              >
                Try again
              </button>
            </div>
          ) : recommendations.length ? (
            <div className="product-grid recommendations">
              {recommendations.slice(0, 4).map((r) => (
                <Card
                  user={user}
                  busy={busy}
                  openProduct={openProduct}
                  listAction={listAction}
                  key={r.itemid}
                  product={r.product}
                  reason={r.reason}
                  description={
                    r.description_source === "reviewed_generative_api"
                      ? (r.catalogue_description ?? undefined)
                      : undefined
                  }
                />
              ))}
            </div>
          ) : (
            <div className="empty-state compact">
              <Sparkles />
              <p>Recommendations will appear here when the service is ready.</p>
            </div>
          )}
        </section>
        <section className="catalogue section" id="catalogue" ref={catalog}>
          <div className="section-heading">
            <div>
              <span className="eyebrow">FIND YOUR NEXT DISCOVERY</span>
              <h2>Explore the catalogue</h2>
            </div>
            <span className="research-badge">
              Anonymized research collection
            </span>
          </div>
          <div className="filters">
            <label className="search">
              <Search size={18} />
              <input
                aria-label="Search by item number"
                placeholder="Search by item number"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              {query && (
                <button aria-label="Clear search" onClick={() => setQuery("")}>
                  <X size={16} />
                </button>
              )}
            </label>
            <label className="category-filter">
              <SlidersHorizontal size={17} />
              <select
                aria-label="Filter by category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    Category {c}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {loading ? (
            <div
              className="product-grid"
              aria-label="Loading catalogue"
              aria-busy="true"
            >
              {[1, 2, 3, 4].map((i) => (
                <div className="skeleton" key={i} />
              ))}
            </div>
          ) : error ? (
            <div className="empty-state" role="alert">
              <ShoppingBag />
              <h3>The catalogue is taking a moment</h3>
              <p>{error}</p>
              <button
                className="primary"
                onClick={() => setRefresh((v) => v + 1)}
              >
                Try again
              </button>
            </div>
          ) : products.length ? (
            <>
              <div className="product-grid">
                {products.map((p) => (
                  <Card
                    user={user}
                    busy={busy}
                    openProduct={openProduct}
                    listAction={listAction}
                    key={p._id}
                    product={p}
                  />
                ))}
              </div>
              {cursor !== null && (
                <button
                  className="load-more subtle-button"
                  disabled={busy}
                  onClick={() =>
                    void act(async () => {
                      const requestedFilter = filterKey;
                      const result = await api<{
                        products: Product[];
                        nextCursor: number | null;
                      }>(
                        "/products?" +
                          new URLSearchParams({
                            after: String(cursor),
                            ...(query ? { query } : {}),
                            ...(category ? { category } : {}),
                          }),
                      );
                      if (currentFilter.current !== requestedFilter) return;
                      setProducts((current) => [
                        ...current,
                        ...result.products,
                      ]);
                      setCursor(result.nextCursor);
                    })
                  }
                >
                  Explore more <ArrowRight size={16} />
                </button>
              )}
            </>
          ) : (
            <div className="empty-state">
              <Search />
              <h3>No items found</h3>
              <p>Try a different item number or category.</p>
              <button
                className="subtle-button"
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
        <section className="privacy-banner">
          <ShieldCheck size={34} />
          <div>
            <h2>A personal experience. Your decision.</h2>
            <p>
              Turn personalization on when you’re ready, or browse without it.
              You can clear your recommendation history at any time.
            </p>
          </div>
          <button
            className="light-button"
            onClick={() => setModal(user ? "privacy" : "login")}
          >
            Manage preferences <ArrowRight size={16} />
          </button>
        </section>
      </main>
      <footer>
        <a className="brand" href="#">
          pasal.
        </a>
        <p>
          An academic research prototype by Rajiv Ganeju.
          <br />
          Catalogue identifiers are anonymized. No payments, real orders or
          current stock claims.
        </p>
        <span>
          Thoughtful discovery.
          <br />
          Transparent recommendations.
        </span>
      </footer>
      {modal && (modal === "login" || modal === "register") && (
        <Modal
          title={
            modal === "register" ? "Make room for discovery" : "Welcome back"
          }
          close={() => setModal(null)}
        >
          <p className="muted">
            Save your favourites and choose your recommendation preferences.
          </p>
          <form onSubmit={auth} className="form">
            {modal === "register" && (
              <label>
                Your name
                <input
                  name="name"
                  autoComplete="name"
                  required
                  maxLength={80}
                />
              </label>
            )}
            <label>
              Email
              <input name="email" type="email" autoComplete="email" required />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={
                  modal === "register" ? "new-password" : "current-password"
                }
                required
                minLength={12}
                maxLength={128}
              />
            </label>
            <small>Use at least 12 characters.</small>
            <button className="primary" disabled={busy}>
              {busy
                ? "Please wait…"
                : modal === "register"
                  ? "Create account"
                  : "Sign in"}
              <ArrowRight size={16} />
            </button>
          </form>
          {notice && <p role="alert">{notice}</p>}
          <button
            className="switch-auth"
            onClick={() => {
              setNotice("");
              setModal(modal === "login" ? "register" : "login");
            }}
          >
            {modal === "login"
              ? "New to Pasal? Create an account"
              : "Already have an account? Sign in"}
          </button>
        </Modal>
      )}
      {modal === "privacy" && user && (
        <Modal title="Your preferences" close={() => setModal(null)}>
          <form onSubmit={savePrivacy} className="form">
            <label className="check-label">
              <input
                name="personalization"
                type="checkbox"
                defaultChecked={user.personalization}
              />
              <span>
                Personalize my recommendations
                <small>
                  Use my consented browsing and basket activity. Turning this
                  off clears recommendation history and category preferences.
                </small>
              </span>
            </label>
            <label>
              Preferred categories
              <select
                name="categories"
                multiple
                defaultValue={user.selectedCategories}
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    Category {c}
                  </option>
                ))}
              </select>
            </label>
            <small>
              Choose up to 30 categories. Hold Ctrl or Command to choose more
              than one.
            </small>
            <button className="primary" disabled={busy}>
              Save preferences <Check size={16} />
            </button>
          </form>
          <div className="privacy-actions">
            <button
              disabled={busy}
              onClick={() =>
                void act(async () => {
                  const result = await api<{ user: User }>(
                    "/history",
                    "DELETE",
                  );
                  setUser(result.user);
                  setModal(null);
                  setNotice(
                    "Recommendation history cleared. Personalization is off.",
                  );
                })
              }
            >
              Clear history and turn off
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void act(async () => {
                  await api("/auth/logout", "POST");
                  setUser(null);
                  setModal(null);
                })
              }
            >
              Sign out
            </button>
          </div>
          {notice && <p role="alert">{notice}</p>}
        </Modal>
      )}
      {(modal === "cart" || modal === "wishlist") && user && (
        <Modal
          title={modal === "cart" ? "Your research basket" : "Your wishlist"}
          close={() => setModal(null)}
        >
          <p className="muted">
            {modal === "cart"
              ? "A place to collect discoveries. This prototype does not take payments or place orders."
              : "Keep the catalogue items you want to revisit."}
          </p>
          {user[modal].length ? (
            <ul className="saved-list">
              {user[modal].map((id) => (
                <li key={id}>
                  <ShoppingBag size={22} />
                  <button
                    className="text-link"
                    onClick={() =>
                      void act(async () => {
                        const result = await api<{ product: Product }>(
                          "/products/" + id,
                        );
                        setDetail(result.product);
                      })
                    }
                  >
                    Catalogue item {id}
                  </button>
                  <button
                    className="icon-button"
                    aria-label={"Remove item " + id}
                    disabled={busy}
                    onClick={() => void listAction(modal, id)}
                  >
                    <X size={18} />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state compact">
              <Heart />
              <p>
                Nothing here yet. Explore and save something that interests you.
              </p>
            </div>
          )}
          {notice && <p role="status">{notice}</p>}
        </Modal>
      )}
      {detail && (
        <Modal title={detail.title} close={() => setDetail(null)}>
          <div className={"detail-art tone-" + (detail._id % 4)}>
            <ShoppingBag size={90} strokeWidth={1} />
          </div>
          <span className="eyebrow">
            Category {detail.category || "unknown"}
          </span>
          <p>
            This item belongs to the anonymized Retailrocket research catalogue.
            Its original product name, image and price are not available.
          </p>
          <p className="muted">
            Availability reflects the historical research snapshot, not current
            retail stock.
          </p>
          <button
            className="primary"
            disabled={busy}
            onClick={() => void listAction("cart", detail._id)}
          >
            <ShoppingBag size={17} />
            {user?.cart.includes(detail._id)
              ? "Remove from basket"
              : "Add to research basket"}
          </button>
        </Modal>
      )}
    </>
  );
}
