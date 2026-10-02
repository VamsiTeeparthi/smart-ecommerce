from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import Product, Category
from ..schemas import ProductIn, ProductOut, CategoryIn, ProductBulkIn
from ..auth import admin_user

router = APIRouter(prefix="/api", tags=["Products"])

@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/categories", dependencies=[Depends(admin_user)])
def add_category(data: CategoryIn, db: Session = Depends(get_db)):
    obj = Category(name=data.name); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/products", response_model=list[ProductOut])
def products(search: str = "", category_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Product)
    if search: q = q.filter(or_(Product.name.ilike(f"%{search}%"), Product.description.ilike(f"%{search}%")))
    if category_id: q = q.filter(Product.category_id == category_id)
    return q.order_by(Product.id.desc()).all()

@router.get("/products/{product_id}", response_model=ProductOut)
def product(product_id: int, db: Session = Depends(get_db)):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    return obj

@router.post("/products", response_model=ProductOut, dependencies=[Depends(admin_user)])
def add_product(data: ProductIn, db: Session = Depends(get_db)):
    obj = Product(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.put("/products/{product_id}", response_model=ProductOut, dependencies=[Depends(admin_user)])
def update_product(product_id: int, data: ProductIn, db: Session = Depends(get_db)):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    for k,v in data.model_dump().items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj

@router.post("/products/bulk", response_model=list[ProductOut], dependencies=[Depends(admin_user)])
def add_products_bulk(data: ProductBulkIn, db: Session = Depends(get_db)):
    """Add many products in one request."""
    objs = [Product(**p.model_dump()) for p in data.products]
    db.add_all(objs); db.commit()
    for o in objs: db.refresh(o)
    return objs
