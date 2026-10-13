import { useEffect, useState, type FormEvent } from "react";
import { api, type User } from "./api";
import type { Product } from "./DemoShop";
import ProductArt from "./ProductArt";
type Overview = {
  products: number;
  available: number;
  categories: string[];
  activity: { consentingProfiles: number; events: number };
  service: { status: string };
  research: {
    window: string;
    requests: number;
    failures: number;
    strategies: Record<string, number>;
    fallbackRecorded: number;
    p95Ms: number | null;
    latestModel: { configuration: string; cutoff: number } | null;
  };
};
const initial = {
  title: "",
  category: "",
  subcategory: "",
  description: "",
  priceNpr: 100,
  image: "bag",
  attributes: [] as string[],
  available: true,
};
export default function Admin() {
  const [user, setUser] = useState<User | null>(null),
    [checked, setChecked] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [overview, setOverview] = useState<Overview | null>(null),
    [products, setProducts] = useState<Product[]>([]),
    [edit, setEdit] = useState<string | null>(null),
    [form, setForm] = useState(initial);
  async function load() {
    const [o, p] = await Promise.all([
      api<Overview>("/admin/overview"),
      api<{ products: Product[] }>("/admin/products"),
    ]);
    setOverview(o);
    setProducts(p.products);
  }
  useEffect(() => {
    api<{ user: User }>("/me")
      .then(async (r) => {
        setUser(r.user);
        if (r.user.role === "admin") await load();
      })
      .catch((e) => {
        if (e.status !== 401) setError(e.message);
      })
      .finally(() => setChecked(true));
  }, []);
  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(e.currentTarget);
    try {
      const r = await api<{ user: User }>("/auth/login", "POST", {
        email: data.get("email"),
        password: data.get("password"),
      });
      setUser(r.user);
      if (r.user.role === "admin") await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function select(p: Product) {
    setEdit(p._id);
    setForm({
      title: p.title,
      category: p.category,
      subcategory: p.subcategory,
      description: p.description,
      priceNpr: p.priceNpr,
      image: p.image,
      attributes: p.attributes,
      available: p.available,
    });
    document
      .getElementById("product-editor")
      ?.scrollIntoView({ behavior: "smooth" });
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(
        edit ? "/admin/products/" + edit : "/admin/products",
        edit ? "PUT" : "POST",
        form,
      );
      await load();
      setNotice(edit ? "Demo product updated." : "Demo product created.");
      setEdit(null);
      setForm(initial);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="announcement">
        Pasal administrator · Demo catalogue only · Research artifacts are
        read-only
      </div>
      <header className="header">
        <a className="brand" href="#">
          pasal.
        </a>
        <nav className="shop-nav">
          <a href="#">Back to shop</a>
          <a href="#research">Research Lab</a>
        </nav>
      </header>
      <main className="admin-main">
        <h1>Administrator dashboard</h1>
        {error && (
          <p role="alert" className="shop-error">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="shop-notice">
            {notice}
          </p>
        )}
        {!checked ? (
          <p>Checking access…</p>
        ) : !user ? (
          <>
            <p>
              Sign in with an account assigned the administrator role by the
              local operator.
            </p>
            <form className="shop-form admin-login" onSubmit={login}>
              <label>
                Email
                <input
                  name="email"
                  type="email"
                  autoComplete="username"
                  required
                />
              </label>
              <label>
                Password
                <input
                  name="password"
                  type="password"
                  minLength={12}
                  autoComplete="current-password"
                  required
                />
              </label>
              <button className="primary" disabled={busy}>
                Administrator sign in
              </button>
            </form>
          </>
        ) : user.role !== "admin" ? (
          <section className="shop-boundary">
            <p>
              <strong>Administrator access required.</strong> This account is a
              customer. Public registration never grants administrator access.{" "}
              <a href="#">Return to the shop</a>.
            </p>
          </section>
        ) : (
          <>
            <div className="admin-heading">
              <p>
                Signed in as {user.name}. No customer identities or histories
                are exposed here.
              </p>
              <button
                onClick={() => void load().catch((e) => setError(e.message))}
              >
                Refresh actual records
              </button>
              <button
                onClick={() =>
                  void api("/auth/logout", "POST")
                    .then(() => {
                      setUser(null);
                      setOverview(null);
                      setProducts([]);
                    })
                    .catch((e) => setError(e.message))
                }
              >
                Sign out
              </button>
            </div>
            {overview && (
              <>
                <div className="admin-stats">
                  <article>
                    <strong>{overview.products}</strong>
                    <span>Demo products</span>
                  </article>
                  <article>
                    <strong>{overview.available}</strong>
                    <span>Active demo products</span>
                  </article>
                  <article>
                    <strong>{overview.categories.length}</strong>
                    <span>Demo categories</span>
                  </article>
                  <article>
                    <strong>{overview.activity.events}</strong>
                    <span>Consented demo events retained</span>
                  </article>
                </div>
                <section className="admin-panel">
                  <h2>Research service monitoring</h2>
                  <p>
                    Health: <strong>{overview.service.status}</strong> ·
                    Consenting demo profiles:{" "}
                    {overview.activity.consentingProfiles}
                  </p>
                  <p>
                    {overview.research.window}. Counters are recorded
                    observations, not experimental results.
                  </p>
                  <dl>
                    <dt>Requests / errors</dt>
                    <dd>
                      {overview.research.requests} /{" "}
                      {overview.research.failures}
                    </dd>
                    <dt>Recorded public-API P95</dt>
                    <dd>
                      {overview.research.p95Ms === null
                        ? "No observations"
                        : overview.research.p95Ms.toFixed(1) + " ms"}
                    </dd>
                    <dt>Last observed configuration</dt>
                    <dd>
                      {overview.research.latestModel?.configuration ||
                        "No successful request observed"}
                    </dd>
                    <dt>Model cutoff (UTC)</dt>
                    <dd>
                      {overview.research.latestModel
                        ? new Date(
                            overview.research.latestModel.cutoff,
                          ).toISOString()
                        : "Not observed"}
                    </dd>
                    <dt>Switching decisions</dt>
                    <dd>
                      {Object.entries(overview.research.strategies)
                        .map(([k, n]) => `${k}: ${n}`)
                        .join(" · ") || "No observations"}
                    </dd>
                    <dt>Explicit fallback reports</dt>
                    <dd>
                      {overview.research.fallbackRecorded} (unreported fallback
                      is unknown, not proof of absence)
                    </dd>
                  </dl>
                  <p>
                    Live metrics contain no user IDs. Generation quality and
                    final experiments remain separately versioned research
                    records.
                  </p>
                </section>
              </>
            )}
            <section className="admin-panel" id="product-editor">
              <h2>
                {edit
                  ? "Edit demonstration product"
                  : "Add demonstration product"}
              </h2>
              <p>
                Every record is explicitly synthetic. Never enter Retailrocket
                IDs or claim a verified brand. Choose a bundled illustration;
                remote images and uploads are disabled.
              </p>
              <form className="shop-form admin-form" onSubmit={save}>
                <label>
                  Name
                  <input
                    required
                    minLength={3}
                    maxLength={100}
                    value={form.title}
                    onChange={(e) =>
                      setForm({ ...form, title: e.target.value })
                    }
                  />
                </label>
                <label>
                  Category
                  <input
                    required
                    minLength={2}
                    maxLength={50}
                    list="demo-categories"
                    value={form.category}
                    onChange={(e) =>
                      setForm({ ...form, category: e.target.value })
                    }
                  />
                  <datalist id="demo-categories">
                    {overview?.categories.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </datalist>
                </label>
                <label>
                  Subcategory
                  <input
                    required
                    minLength={2}
                    maxLength={50}
                    value={form.subcategory}
                    onChange={(e) =>
                      setForm({ ...form, subcategory: e.target.value })
                    }
                  />
                </label>
                <label>
                  Demo price (NPR)
                  <input
                    type="number"
                    min={1}
                    max={10000000}
                    step={1}
                    required
                    value={form.priceNpr}
                    onChange={(e) =>
                      setForm({ ...form, priceNpr: Number(e.target.value) })
                    }
                  />
                </label>
                <label>
                  Description
                  <textarea
                    required
                    minLength={10}
                    maxLength={1000}
                    value={form.description}
                    onChange={(e) =>
                      setForm({ ...form, description: e.target.value })
                    }
                  />
                </label>
                <label>
                  Synthetic attributes (one per line, up to eight)
                  <textarea
                    value={form.attributes.join("\n")}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        attributes: e.target.value.split("\n"),
                      })
                    }
                  />
                </label>
                <label>
                  Illustration
                  <select
                    value={form.image}
                    onChange={(e) =>
                      setForm({ ...form, image: e.target.value })
                    }
                  >
                    {[
                      "bag",
                      "mug",
                      "bottle",
                      "notebook",
                      "scarf",
                      "lamp",
                      "basket",
                      "tea",
                    ].map((i) => (
                      <option key={i}>{i}</option>
                    ))}
                  </select>
                </label>
                <label className="check-label">
                  <input
                    type="checkbox"
                    checked={form.available}
                    onChange={(e) =>
                      setForm({ ...form, available: e.target.checked })
                    }
                  />{" "}
                  Available in demo shop
                </label>
                <ProductArt
                  kind={form.image}
                  title={form.title || "Product preview"}
                />
                <div>
                  <button className="primary" disabled={busy}>
                    Save demo product
                  </button>
                  {edit && (
                    <button
                      type="button"
                      onClick={() => {
                        setEdit(null);
                        setForm(initial);
                      }}
                    >
                      Cancel editing
                    </button>
                  )}
                </div>
              </form>
            </section>
            <section className="admin-panel">
              <h2>Demonstration catalogue</h2>
              <p>
                Edit category/subcategory fields to manage the taxonomy.
                Deactivate rather than deleting products; saved cart/history
                references remain intact.
              </p>
              <div className="admin-table">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Category</th>
                      <th>NPR</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((p) => (
                      <tr key={p._id}>
                        <td>
                          {p.title}
                          <small>{p._id}</small>
                        </td>
                        <td>
                          {p.category} / {p.subcategory}
                        </td>
                        <td>{p.priceNpr}</td>
                        <td>{p.available ? "Active" : "Inactive"}</td>
                        <td>
                          <button onClick={() => select(p)}>
                            Edit {p.title}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </>
  );
}
