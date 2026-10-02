import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./style.css";

const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "") + "/api";
const getToken = () => localStorage.getItem("token");

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`;
  const r = await fetch(API + path, { ...opts, headers });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw Error(d.detail || "Request failed");
  return d;
}

function App() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cart, setCart] = useState([]);
  const [user, setUser] = useState(null);
  const [view, setView] = useState("shop");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([
        api(`/products?search=${encodeURIComponent(search)}`),
        api("/categories"),
      ]);
      setProducts(p);
      setCategories(c);
      if (getToken()) {
        try {
          setUser(await api("/auth/me"));
          setCart(await api("/cart"));
        } catch {
          localStorage.removeItem("token");
          setUser(null);
          setCart([]);
        }
      }
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search]);

  useEffect(() => {
    if (!msg) return;
    const timer = setTimeout(() => setMsg(""), 3200);
    return () => clearTimeout(timer);
  }, [msg]);

  const filteredProducts = useMemo(() => {
    if (category === "all") return products;
    return products.filter(p => String(p.category_id) === String(category));
  }, [products, category]);

  const cartCount = cart.reduce((a, x) => a + x.quantity, 0);

  const login = async () => {
    const email = prompt("Email", "user@example.com");
    const password = prompt("Password", "user123");
    if (!email || !password) return;
    try {
      const d = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", d.access_token);
      setUser(d.user);
      setCart(await api("/cart"));
      setMsg("Welcome back! You are signed in.");
    } catch (e) { alert(e.message); }
  };

  const register = async () => {
    const name = prompt("Name", "New User");
    const email = prompt("Email");
    const password = prompt("Password");
    if (!email || !password) return;
    try {
      const d = await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });
      localStorage.setItem("token", d.access_token);
      setUser(d.user);
      setCart(await api("/cart"));
      setMsg("Account created. Welcome to NovaCart!");
    } catch (e) { alert(e.message); }
  };

  const add = async (p) => {
    if (!user) {
      alert("Please login first to add items to your cart.");
      return;
    }
    try {
      await api("/cart", {
        method: "POST",
        body: JSON.stringify({ product_id: p.id, quantity: 1 }),
      });
      setCart(await api("/cart"));
      setMsg(`${p.name} was added to your cart.`);
    } catch (e) { alert(e.message); }
  };

  const checkout = async () => {
    const address = prompt("Shipping address", "Hyderabad, Telangana, India");
    if (!address) return;
    try {
      await api("/checkout", {
        method: "POST",
        body: JSON.stringify({
          shipping_address: address,
          coupon_code: "WELCOME10",
          payment_method: "demo",
        }),
      });
      setCart([]);
      setView("orders");
      setMsg("Order placed successfully. Thank you for shopping with NovaCart!");
    } catch (e) { alert(e.message); }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setCart([]);
    setView("shop");
    setMsg("You have been signed out.");
  };

  return (
    <div className="app-shell">
      <div className="topbar">
        <span>FREE SHIPPING ON ORDERS OVER ₹999</span>
        <span className="topbar-right">Secure checkout • Easy returns • 24/7 support</span>
      </div>

      <header className="header">
        <button className="brand" onClick={() => { setView("shop"); setCategory("all"); }}>
          <span className="brand-mark">N</span>
          <span>Nova<span>Cart</span></span>
        </button>

        <div className="search-box">
          <span>⌕</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search products, brands & more..." />
          {search && <button className="clear-search" onClick={() => setSearch("")}>×</button>}
        </div>

        <nav className="nav">
          <button className={view === "shop" ? "nav-btn active" : "nav-btn"} onClick={() => setView("shop")}>Shop</button>
          {user && <button className={view === "orders" ? "nav-btn active" : "nav-btn"} onClick={() => setView("orders")}>Orders</button>}
          {user?.is_admin && <button className={view === "admin" ? "nav-btn active" : "nav-btn"} onClick={() => setView("admin")}>Dashboard</button>}
          <button className="cart-btn" onClick={() => setView("cart")}>
            <span>Bag</span><b>{cartCount}</b>
          </button>
          {user ? (
            <button className="account-btn" onClick={logout}><span className="avatar">{(user.name || "U")[0].toUpperCase()}</span>Logout</button>
          ) : (
            <div className="auth-actions"><button onClick={login}>Login</button><button className="signup-btn" onClick={register}>Sign up</button></div>
          )}
        </nav>
      </header>

      {msg && <div className="toast">✓ <span>{msg}</span></div>}

      {view === "shop" && (
        <main>
          <section className="hero">
            <div className="hero-copy">
              <div className="pill"><span>✦</span> THE SMARTER WAY TO SHOP</div>
              <h1>Good products.<br /><em>Great choices.</em><br />One place.</h1>
              <p>Discover everyday essentials and standout finds, thoughtfully brought together for a shopping experience that feels effortless.</p>
              <div className="hero-actions">
                <button className="cta" onClick={() => document.getElementById("products")?.scrollIntoView({ behavior: "smooth" })}>Explore collection <span>→</span></button>
                <button className="text-btn" onClick={() => setView("cart")}>View your bag</button>
              </div>
              <div className="trust-row"><span>✓ Secure payments</span><span>✓ Quality products</span><span>✓ Fast delivery</span></div>
            </div>
            <div className="hero-art">
              <div className="glow"></div>
              <div className="floating-card card-one"><span>★★★★★</span><strong>4.9/5</strong><small>Happy shoppers</small></div>
              <div className="product-orb">N</div>
              <div className="floating-card card-two"><span>↗</span><strong>10% OFF</strong><small>Use WELCOME10</small></div>
              <div className="hero-sticker">SHOP<br />SMART</div>
            </div>
          </section>

          <section className="benefits">
            <div><span className="benefit-icon">🚚</span><div><b>Fast & reliable</b><small>Delivery that keeps up</small></div></div>
            <div><span className="benefit-icon">🔒</span><div><b>Secure shopping</b><small>Your data stays protected</small></div></div>
            <div><span className="benefit-icon">↩</span><div><b>Easy returns</b><small>Shop with confidence</small></div></div>
            <div><span className="benefit-icon">♡</span><div><b>Made for you</b><small>Curated everyday picks</small></div></div>
          </section>

          <section className="collection-head" id="products">
            <div><p className="section-kicker">CURATED FOR YOU</p><h2>Shop the collection</h2><p>Simple finds, smart prices, zero fuss.</p></div>
            <span className="product-count">{filteredProducts.length} products</span>
          </section>

          <div className="category-row">
            <button className={category === "all" ? "chip selected" : "chip"} onClick={() => setCategory("all")}>All products</button>
            {categories.map(c => <button key={c.id} className={String(category) === String(c.id) ? "chip selected" : "chip"} onClick={() => setCategory(c.id)}>{c.name}</button>)}
          </div>

          {loading ? (
            <div className="skeleton-grid">{[1,2,3,4].map(x => <div className="skeleton" key={x}></div>)}</div>
          ) : filteredProducts.length ? (
            <div className="grid">{filteredProducts.map((p, i) => (
              <article className="card" key={p.id}>
                <div className="image-wrap">
                  <img src={p.image_url} alt={p.name} />
                  {i < 2 && <span className="product-badge">{i === 0 ? "POPULAR" : "TRENDING"}</span>}
                  <button className="heart" title="Wishlist">♡</button>
                </div>
                <div className="pad">
                  <small>{categories.find(c => c.id === p.category_id)?.name || "Featured"}</small>
                  <h3>{p.name}</h3>
                  <p>{p.description || "A carefully selected product from the NovaCart collection."}</p>
                  <div className="rating">★★★★★ <span>Trusted pick</span></div>
                  <div className="row"><b>₹{p.price}</b><span className={p.stock < 5 ? "stock low" : "stock"}>{p.stock < 5 ? `Only ${p.stock} left` : `${p.stock} in stock`}</span></div>
                  <button className="primary" onClick={() => add(p)}>Add to bag <span>→</span></button>
                </div>
              </article>
            ))}</div>
          ) : (
            <div className="empty search-empty"><div>⌕</div><h3>No products found</h3><p>Try another search or browse all products.</p><button className="cta small" onClick={() => { setSearch(""); setCategory("all"); }}>Show all products</button></div>
          )}

          <section className="quote-banner">
            <div className="quote-mark">“</div>
            <div><p>Shopping should feel less like a chore and more like discovering something you didn't know you needed.</p><span>— The NovaCart philosophy</span></div>
            <div className="quote-dot">✦</div>
          </section>

          <section className="newsletter">
            <div><p className="section-kicker">STAY IN THE LOOP</p><h2>Fresh finds. Better deals.</h2><p>Be the first to know about new arrivals, seasonal offers and special drops.</p></div>
            <div className="newsletter-form"><input placeholder="Your email address" /><button className="cta">Join NovaCart →</button></div>
          </section>
        </main>
      )}

      {view === "cart" && <Cart cart={cart} checkout={checkout} />}
      {view === "orders" && <Orders />}
      {view === "admin" && <Admin />}

      <footer>
        <div className="footer-main">
          <div className="footer-brand"><button className="brand"><span className="brand-mark">N</span><span>Nova<span>Cart</span></span></button><p>Smart commerce, beautifully simple.</p></div>
          <div><h4>SHOP</h4><a>All products</a><a>New arrivals</a><a>Best sellers</a></div>
          <div><h4>COMPANY</h4><a>About NovaCart</a><a>Our promise</a><a>Contact</a></div>
          <div><h4>HELP</h4><a>Shipping & returns</a><a>Privacy</a><a>Terms</a></div>
        </div>
        <div className="footer-bottom"><span>© 2026 NovaCart. All rights reserved.</span><span>Built with React + FastAPI • Designed for modern commerce</span></div>
      </footer>
    </div>
  );
}

function Cart({ cart, checkout }) {
  const total = cart.reduce((sum, x) => sum + Number(x.subtotal || 0), 0);
  return <main className="page">
    <div className="page-heading"><p className="section-kicker">YOUR SHOPPING BAG</p><h2>Ready when you are.</h2><p>Review your picks before checkout.</p></div>
    {!cart.length ? <div className="empty"><div className="empty-icon">🛍</div><h3>Your bag is waiting</h3><p>Add something you love from our collection.</p><button className="cta" onClick={() => location.reload()}>Continue shopping →</button></div> :
      <div className="cart-layout"><div className="cart">{cart.map(x => <div className="cartrow" key={x.id}><img src={x.image_url} alt={x.name}/><div><h3>{x.name}</h3><p>₹{x.price} × {x.quantity}</p></div><b>₹{x.subtotal}</b></div>)}</div>
      <aside className="summary"><p>ORDER SUMMARY</p><div><span>Subtotal</span><b>₹{total.toFixed(2)}</b></div><div><span>Discount</span><b className="discount">− 10%</b></div><div className="summary-total"><span>Total</span><strong>₹{(total * .9).toFixed(2)}</strong></div><small>Coupon WELCOME10 applied at checkout.</small><button className="primary" onClick={checkout}>Secure checkout →</button></aside></div>}
  </main>;
}

function Orders() {
  const [orders, setOrders] = useState([]);
  useEffect(() => { api("/orders").then(setOrders).catch(() => {}); }, []);
  return <main className="page"><div className="page-heading"><p className="section-kicker">YOUR ACCOUNT</p><h2>Order history</h2><p>Everything you've ordered, all in one place.</p></div>
    {!orders.length ? <div className="empty"><div className="empty-icon">📦</div><h3>No orders yet</h3><p>Your next order will appear here.</p></div> :
    orders.map(o => <div className="order" key={o.id}><div><span className="order-label">ORDER #{o.id}</span><h3>NovaCart purchase</h3><p>{new Date(o.created_at).toLocaleString()}</p></div><div><b>₹{o.total}</b><span className="status">{o.status} • {o.payment_status}</span></div><div><small>TRACKING</small><p>{o.tracking_number || "Preparing shipment"}</p></div></div>)}
  </main>;
}

function Admin() {
  const [d, setD] = useState(null), [sales, setSales] = useState([]);
  useEffect(() => { Promise.all([api("/admin/dashboard"), api("/admin/sales")]).then(([a,b]) => { setD(a); setSales(b); }).catch(() => {}); }, []);
  if (!d) return <main className="page"><div className="empty"><h3>Loading dashboard...</h3></div></main>;
  return <main className="page"><div className="page-heading"><p className="section-kicker">NOVA ADMIN</p><h2>Business dashboard</h2><p>A quick view of your store performance.</p></div>
    <div className="stats"><div><small>Revenue</small><strong>₹{d.revenue}</strong><span>↗ Store total</span></div><div><small>Orders</small><strong>{d.orders}</strong><span>↗ All orders</span></div><div><small>Products</small><strong>{d.products}</strong><span>↗ Catalogue</span></div><div><small>Low stock</small><strong>{d.low_stock}</strong><span>Needs attention</span></div></div>
    <div className="analytics"><div><h3>Sales analytics</h3><p>Daily store activity</p>{sales.map(x => <div className="sale-row" key={x.date}><span>{x.date}</span><b>₹{x.sales}</b><small>{x.orders} orders</small></div>)}</div><div className="admin-note"><span>✦</span><h3>Keep the momentum.</h3><p>Great stores are built from great customer experiences. Keep an eye on inventory and make every order count.</p></div></div>
  </main>;
}

createRoot(document.getElementById("root")).render(<BrowserRouter><App /></BrowserRouter>);
