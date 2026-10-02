# Store MCP server (let Claude manage your shop)

Claude  <-->  this MCP server  <-->  your FastAPI backend (as admin)  <-->  Neon

## Tools
Read (always on): store_summary, list_categories, list_suppliers, list_products, get_product,
low_stock_items, list_orders, sales_by_day, list_coupons
Write (only when ALLOW_WRITES=true): add_product, add_products_bulk, update_product,
add_category, add_supplier, create_coupon, update_order_status
There is deliberately NO delete tool.

## 0. Redeploy the backend first
This update adds two admin endpoints the MCP server needs (all-orders list, order status update).
Push the new code to GitHub; Render redeploys automatically.

## 1. (Recommended) Create a dedicated admin account for Claude
Register a user on your site (e.g. claude-bot@example.com), then in Neon > SQL Editor:
    UPDATE users SET is_admin = true WHERE email = 'claude-bot@example.com';
Using a separate account lets you revoke Claude's access without touching your own login.

## 2. Deploy on Render (second Web Service, same repo)
- Root Directory: mcp_server
- Build Command: pip install -r requirements.txt
- Start Command: python server.py
- Instance Type: Free, same region as your backend
- Environment variables:
    BACKEND_URL    = https://YOUR-BACKEND.onrender.com   (no /api, no trailing slash)
    ADMIN_EMAIL    = the admin account from step 1
    ADMIN_PASSWORD = its password
    MCP_SECRET     = output of: python -c "import secrets; print(secrets.token_urlsafe(32))"
    ALLOW_WRITES   = false   (start read-only; change to true when you're ready)
Check https://YOUR-MCP.onrender.com/health  ->  ok

## 3. Add it to Claude
Claude > Customize > Connectors > + > Add custom connector, URL:
    https://YOUR-MCP.onrender.com/<MCP_SECRET>/mcp
Enable the connector in a chat from the "+" menu.

## Try it
- "Give me a summary of the store."
- "Which products are low on stock?"
- "Show orders with status PLACED."
(with ALLOW_WRITES=true)
- "Add 5 new products to the Home category."
- "Mark order 3 as SHIPPED with tracking number TRK123."
- "Increase all Books prices by 10%." (Claude should confirm first)

## Test locally
    cd mcp_server && pip install -r requirements.txt
    set the variables from .env.example in your shell, then: python server.py
    npx @modelcontextprotocol/inspector   ->  http://localhost:8001/<MCP_SECRET>/mcp

## Security notes
- The secret in the URL is the only thing protecting admin access. Treat the full URL like a password;
  don't share it or commit it. If it leaks, change MCP_SECRET on Render and update the connector URL.
- Access logs are disabled so the secret is not written to Render logs.
- Keep ALLOW_WRITES=false unless you want Claude to change data. Review what Claude proposes before approving writes.
- Free Render services sleep: the first call after idle time can take up to a minute (backend + MCP server both wake).

## Troubleshooting
- 401 Unauthorized: URL secret doesn't match MCP_SECRET.
- "Admin login ... failed": wrong ADMIN_EMAIL/ADMIN_PASSWORD, or the account isn't admin.
- "Invalid Host header" / 421: tell me; the transport-security setting needs adjusting for your mcp version.
- Tool missing in Claude: ALLOW_WRITES is false (write tools are hidden), or reconnect the connector.
