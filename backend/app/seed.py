from .database import SessionLocal
from .models import User, Category, Product, Supplier, Coupon
from .auth import hash_password

CATEGORIES = ["Electronics", "Fashion", "Home", "Books", "Sports", "Beauty", "Grocery", "Toys"]

SUPPLIERS = [
    ("Demo Supplier", "supplier@example.com", "9999999999"),
    ("TechSource India", "sales@techsource.example.com", "9888800001"),
    ("StyleHub Wholesale", "orders@stylehub.example.com", "9888800002"),
    ("HomeNest Traders", "hello@homenest.example.com", "9888800003"),
]


def img(label: str) -> str:
    return f"https://placehold.co/600x400?text={label.replace(' ', '+')}"


# (name, description, price, category, supplier index, stock, reorder_level)
PRODUCTS = [
    # Electronics
    ("Wireless Headphones", "Bluetooth over-ear headphones", 2499, "Electronics", 0, 25, 5),
    ("Mechanical Keyboard", "RGB mechanical keyboard", 3499, "Electronics", 0, 18, 5),
    ("Smart Watch", "Fitness tracker with heart-rate and sleep monitoring", 4999, "Electronics", 1, 22, 6),
    ("Bluetooth Speaker", "Portable waterproof speaker with 12-hour battery", 1999, "Electronics", 1, 35, 8),
    ("Wireless Mouse", "Ergonomic 2.4GHz silent-click mouse", 799, "Electronics", 1, 50, 10),
    ("Power Bank 20000mAh", "Fast-charging USB-C power bank", 1799, "Electronics", 1, 40, 10),
    ("Webcam 1080p", "Full HD webcam with built-in microphone", 2299, "Electronics", 1, 15, 4),
    # Fashion
    ("Backpack", "Everyday laptop backpack", 1499, "Fashion", 0, 30, 8),
    ("Running Shoes", "Lightweight breathable running shoes", 2999, "Fashion", 2, 28, 6),
    ("Denim Jacket", "Classic fit unisex denim jacket", 2199, "Fashion", 2, 20, 5),
    ("Cotton T-Shirt", "Soft 100% cotton crew-neck tee", 599, "Fashion", 2, 80, 15),
    ("Leather Wallet", "Slim genuine leather bifold wallet", 899, "Fashion", 2, 45, 10),
    ("Sunglasses", "UV400 polarized aviator sunglasses", 1299, "Fashion", 2, 33, 8),
    # Home
    ("Table Lamp", "Warm LED bedside lamp with touch dimmer", 1199, "Home", 3, 26, 6),
    ("Ceramic Coffee Mug Set", "Set of 4 hand-glazed ceramic mugs", 699, "Home", 3, 60, 12),
    ("Cotton Bedsheet Set", "King size bedsheet with 2 pillow covers", 1599, "Home", 3, 24, 6),
    ("Air Fryer 4L", "Digital air fryer with 8 preset modes", 5499, "Home", 3, 14, 4),
    ("Wall Clock", "Minimalist silent-sweep wall clock", 749, "Home", 3, 38, 8),
    # Books
    ("Database Systems", "DBMS learning book", 899, "Books", 0, 12, 4),
    ("Python Crash Course", "Hands-on introduction to programming with Python", 749, "Books", 0, 30, 6),
    ("Atomic Habits", "Build good habits and break bad ones", 499, "Books", 0, 55, 10),
    ("Data Structures Made Easy", "Algorithms and data structures for interviews", 649, "Books", 0, 27, 6),
    # Sports
    ("Yoga Mat", "Non-slip 6mm exercise mat", 899, "Sports", 2, 42, 10),
    ("Dumbbell Set 10kg", "Adjustable rubber-coated dumbbell pair", 1999, "Sports", 2, 19, 5),
    ("Badminton Racket Pair", "Graphite racket set with carry cover", 1299, "Sports", 2, 31, 7),
    # Beauty
    ("Vitamin C Face Serum", "Brightening serum for daily skincare", 549, "Beauty", 3, 65, 12),
    ("Beard Trimmer", "Rechargeable cordless trimmer with 10 length settings", 1399, "Beauty", 1, 29, 6),
    # Grocery
    ("Organic Green Tea", "100 pure green tea bags", 349, "Grocery", 3, 90, 20),
    ("Mixed Dry Fruits 500g", "Premium almonds, cashews, raisins and walnuts", 599, "Grocery", 3, 70, 15),
    # Toys
    ("Building Blocks 500pc", "Creative interlocking blocks for kids 6+", 1099, "Toys", 3, 34, 8),
    ("Remote Control Car", "Rechargeable 4WD off-road RC car", 1899, "Toys", 3, 16, 4),
]


def seed():
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add_all([
                User(name="Admin", email="admin@example.com", password_hash=hash_password("admin123"), is_admin=True),
                User(name="Demo User", email="user@example.com", password_hash=hash_password("user123"), is_admin=False),
            ])

        # Categories and suppliers: add any that are missing (safe on existing databases)
        cats = {c.name: c for c in db.query(Category).all()}
        for name in CATEGORIES:
            if name not in cats:
                cats[name] = Category(name=name)
                db.add(cats[name])
        db.flush()

        existing_sup = {s.name: s for s in db.query(Supplier).all()}
        sups = []
        for name, email, phone in SUPPLIERS:
            if name not in existing_sup:
                existing_sup[name] = Supplier(name=name, email=email, phone=phone)
                db.add(existing_sup[name])
            sups.append(existing_sup[name])
        db.flush()

        # Products: add any that don't exist yet by name
        existing_products = {p.name for p in db.query(Product).all()}
        for name, desc, price, cat, sup_i, stock, reorder in PRODUCTS:
            if name in existing_products:
                continue
            db.add(Product(
                name=name, description=desc, price=price, image_url=img(name),
                category_id=cats[cat].id, supplier_id=sups[sup_i].id,
                stock=stock, reorder_level=reorder,
            ))

        if not db.query(Coupon).first():
            db.add(Coupon(code="WELCOME10", discount_percent=10))
        db.commit()
    finally:
        db.close()
