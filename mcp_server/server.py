"""
MCP server for the Smart E-Commerce store.

Lets Claude manage the shop by calling your existing FastAPI backend as an admin.
Run:  python server.py     (listens on $PORT, default 8001)
"""
import hmac
import os

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
MCP_SECRET = os.environ.get("MCP_SECRET", "")
ALLOW_WRITES = os.environ.get("ALLOW_WRITES", "false").lower() in ("1", "true", "yes")

if len(MCP_SECRET) < 16:
    raise SystemExit("MCP_SECRET must be set to a random string of at least 16 characters.")
if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    raise SystemExit("ADMIN_EMAIL and ADMIN_PASSWORD must be set.")

# ---------------------------------------------------------------- server setup
server_kwargs = dict(
    name="Smart E-Commerce Admin",
    instructions=(
        "You manage an online store through its admin API. Look things up before changing them. "
        "Before any bulk change (many products, price changes), tell the user what you are about "
        "to do and wait for their confirmation. Prices are in INR. Report back what actually changed."
    ),
    host="0.0.0.0",
    stateless_http=True,
)
try:  # allow requests addressed to your Render hostname
    from mcp.server.transport_security import TransportSecuritySettings
    server_kwargs["transport_security"] = TransportSecuritySettings(enable_dns_rebinding_protection=False)
except ImportError:
    pass
mcp = FastMCP(**server_kwargs)

# ------------------------------------------------------------- backend client
_token: str | None = None


async def _login(client: httpx.AsyncClient) -> None:
    global _token
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        raise RuntimeError(f"Admin login to the store backend failed ({r.status_code}). Check ADMIN_EMAIL / ADMIN_PASSWORD.")
    _token = r.json()["access_token"]


async def api(method: str, path: str, **kwargs):
    """Call the backend as admin. Logs in on demand and again if the token expired."""
    global _token
    # timeout is long because the free Render backend can take ~1 min to wake up
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=90) as client:
        for attempt in (1, 2):
            if not _token:
                await _login(client)
            r = await client.request(method, path, headers={"Authorization": f"Bearer {_token}"}, **kwargs)
            if r.status_code == 401 and attempt == 1:
                _token = None
                continue
            break
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"Store backend returned {r.status_code}: {detail}")
    return r.json()


# ------------------------------------------------------------------ read tools
@mcp.tool()
async def store_summary() -> dict:
    """Overview: number of users, products, orders, total revenue and low-stock count."""
    return await api("GET", "/api/admin/dashboard")


@mcp.tool()
async def list_categories() -> list:
    """List product categories with their ids."""
    return await api("GET", "/api/categories")


@mcp.tool()
async def list_suppliers() -> list:
    """List suppliers with their ids."""
    return await api("GET", "/api/admin/suppliers")


@mcp.tool()
async def list_products(search: str = "", category_id: int | None = None, limit: int = 50) -> list:
    """Search products by name/description and optionally filter by category id."""
    params = {"search": search}
    if category_id:
        params["category_id"] = category_id
    items = await api("GET", "/api/products", params=params)
    return items[: max(1, min(limit, 200))]


@mcp.tool()
async def get_product(product_id: int) -> dict:
    """Get one product by id."""
    return await api("GET", f"/api/products/{product_id}")


@mcp.tool()
async def low_stock_items() -> list:
    """Products whose stock is at or below their reorder level (lowest stock first)."""
    items = await api("GET", "/api/admin/inventory")
    return [p for p in items if p["stock"] <= p["reorder_level"]]


@mcp.tool()
async def list_orders(status: str | None = None, limit: int = 20) -> list:
    """Recent orders from all customers (newest first). Optional status filter, e.g. PLACED, SHIPPED."""
    params = {"limit": max(1, min(limit, 100))}
    if status:
        params["status"] = status
    return await api("GET", "/api/admin/orders", params=params)


@mcp.tool()
async def sales_by_day() -> list:
    """Sales total and order count per day."""
    return await api("GET", "/api/admin/sales")


@mcp.tool()
async def list_coupons() -> list:
    """List discount coupons."""
    return await api("GET", "/api/admin/coupons")


# ----------------------------------------------------------------- write tools
if ALLOW_WRITES:

    @mcp.tool()
    async def add_product(name: str, price: float, category_id: int, description: str = "",
                          image_url: str = "", supplier_id: int | None = None,
                          stock: int = 0, reorder_level: int = 5) -> dict:
        """Add one product. Use list_categories / list_suppliers to find ids."""
        if price < 0 or stock < 0:
            raise ValueError("price and stock must not be negative")
        body = dict(name=name, description=description, price=price, image_url=image_url,
                    category_id=category_id, supplier_id=supplier_id, stock=stock, reorder_level=reorder_level)
        return await api("POST", "/api/products", json=body)

    @mcp.tool()
    async def add_products_bulk(products: list[dict]) -> list:
        """Add many products at once (max 50). Each item needs: name, price, category_id;
        optional: description, image_url, supplier_id, stock, reorder_level."""
        if not 1 <= len(products) <= 50:
            raise ValueError("Provide between 1 and 50 products")
        for p in products:
            if not {"name", "price", "category_id"} <= p.keys():
                raise ValueError(f"Each product needs name, price and category_id: {p}")
            if p["price"] < 0 or p.get("stock", 0) < 0:
                raise ValueError(f"price and stock must not be negative: {p['name']}")
        return await api("POST", "/api/products/bulk", json={"products": products})

    @mcp.tool()
    async def update_product(product_id: int, name: str | None = None, description: str | None = None,
                             price: float | None = None, image_url: str | None = None,
                             category_id: int | None = None, supplier_id: int | None = None,
                             stock: int | None = None, reorder_level: int | None = None) -> dict:
        """Change selected fields of a product (price, stock, name...). Omitted fields stay as they are."""
        changes = {"name": name, "description": description, "price": price, "image_url": image_url,
                   "category_id": category_id, "supplier_id": supplier_id, "stock": stock,
                   "reorder_level": reorder_level}
        changes = {k: v for k, v in changes.items() if v is not None}
        if not changes:
            raise ValueError("Nothing to change")
        if changes.get("price", 0) < 0 or changes.get("stock", 0) < 0:
            raise ValueError("price and stock must not be negative")
        current = await api("GET", f"/api/products/{product_id}")
        current.pop("id", None)
        current.update(changes)
        return await api("PUT", f"/api/products/{product_id}", json=current)

    @mcp.tool()
    async def add_category(name: str) -> dict:
        """Create a product category."""
        return await api("POST", "/api/categories", json={"name": name})

    @mcp.tool()
    async def add_supplier(name: str, email: str = "", phone: str = "") -> dict:
        """Create a supplier."""
        return await api("POST", "/api/admin/suppliers", json={"name": name, "email": email, "phone": phone})

    @mcp.tool()
    async def create_coupon(code: str, discount_percent: float) -> dict:
        """Create a coupon, e.g. code SAVE15 with discount_percent 15."""
        return await api("POST", "/api/admin/coupons", json={"code": code, "discount_percent": discount_percent})

    @mcp.tool()
    async def update_order_status(order_id: int, status: str, tracking_number: str | None = None) -> dict:
        """Set an order's status: PLACED, PROCESSING, SHIPPED, OUT_FOR_DELIVERY, DELIVERED or CANCELLED.
        Optionally set the tracking number."""
        body = {"status": status, "tracking_number": tracking_number}
        return await api("PUT", f"/api/admin/orders/{order_id}/status", json=body)


# ----------------------------------------------------------- auth + ASGI app
async def _reply(send, status: int, body: bytes, content_type: bytes = b"text/plain"):
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", content_type), (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})


class SecretAuth:
    """Only lets requests through that carry MCP_SECRET, either as the first URL segment
    (https://host/<SECRET>/mcp) or as an 'Authorization: Bearer <SECRET>' header."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":  # lifespan etc.
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        if path == "/health":
            await _reply(send, 200, b"ok")
            return

        authorized = False
        parts = path.split("/", 2)  # ['', first-segment, rest]
        if len(parts) >= 2 and parts[1] and hmac.compare_digest(parts[1], MCP_SECRET):
            new_path = "/" + (parts[2] if len(parts) == 3 else "")
            scope = dict(scope)
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode()
            authorized = True
        else:
            auth = dict(scope["headers"]).get(b"authorization", b"").decode()
            if auth.startswith("Bearer ") and hmac.compare_digest(auth[7:], MCP_SECRET):
                authorized = True

        if not authorized:
            await _reply(send, 401, b"Unauthorized")
            return
        await self.app(scope, receive, send)


app = SecretAuth(mcp.streamable_http_app())

if __name__ == "__main__":
    # access_log off so the secret URL is not written to logs
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8001")), access_log=False)
