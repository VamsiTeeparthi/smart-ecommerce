# Smart E-Commerce + Inventory

A full-stack e-commerce + inventory management application designed to demonstrate DBMS concepts and third-party API integration.

## Stack
- Frontend: React + Vite
- Backend: Python + FastAPI + SQLAlchemy
- Database: SQLite by default (easy development); PostgreSQL-ready via DATABASE_URL
- Auth: JWT
- Integrations: payment, shipping, email, SMS, image storage, geocoding adapters
- No UI template is used.

## Modules
- Authentication
- Products and categories
- Cart
- Wishlist
- Orders and order tracking
- Inventory
- Suppliers
- Coupons/discounts
- Reviews
- Admin dashboard
- Sales analytics
- Integration endpoints

## Run

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
uvicorn app.main:app --reload
```

API: http://localhost:8000
Swagger: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo admin
On first startup the backend creates:
- admin@example.com / admin123
- user@example.com / user123

Change these credentials before production use.

## Real integrations
The code uses provider adapters. Set credentials in `backend/.env` and replace the demo provider implementations when you are ready:
- Payment: Stripe/Razorpay
- Shipping: Shippo/Shiprocket
- Email: SendGrid/Resend
- SMS: Twilio
- Image storage: Cloudinary/S3
- Geocoding: OpenStreetMap Nominatim or Google Maps

The demo mode is intentionally usable without paid API credentials.


## UI refresh
The React storefront has been redesigned with a polished NovaCart brand system, responsive layouts, promotional hero, category filters, product badges, trust sections, order/cart summaries, newsletter section, and a styled admin dashboard. The existing FastAPI endpoints and demo checkout flow are preserved.
