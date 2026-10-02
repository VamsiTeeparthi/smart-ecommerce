from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Product, Order, User, Supplier, Coupon, InventoryLog
from ..schemas import SupplierIn, CouponIn
from ..auth import admin_user

router=APIRouter(prefix="/api/admin",tags=["Admin"])

@router.get("/dashboard")
def dashboard(admin=Depends(admin_user),db:Session=Depends(get_db)):
    revenue=db.query(func.coalesce(func.sum(Order.total),0)).scalar()
    return {"users":db.query(User).count(),"products":db.query(Product).count(),"orders":db.query(Order).count(),"revenue":round(revenue,2),"low_stock":db.query(Product).filter(Product.stock<=Product.reorder_level).count()}

@router.get("/inventory")
def inventory(admin=Depends(admin_user),db:Session=Depends(get_db)):
    return db.query(Product).order_by(Product.stock.asc()).all()

@router.get("/sales")
def sales(admin=Depends(admin_user),db:Session=Depends(get_db)):
    rows=db.query(func.date(Order.created_at).label("date"),func.sum(Order.total).label("sales"),func.count(Order.id).label("orders")).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()
    return [{"date":str(r.date),"sales":round(r.sales or 0,2),"orders":r.orders} for r in rows]

@router.post("/suppliers")
def supplier(data:SupplierIn,admin=Depends(admin_user),db:Session=Depends(get_db)):
    s=Supplier(**data.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@router.get("/suppliers")
def suppliers(admin=Depends(admin_user),db:Session=Depends(get_db)): return db.query(Supplier).all()

@router.post("/coupons")
def coupon(data:CouponIn,admin=Depends(admin_user),db:Session=Depends(get_db)):
    c=Coupon(code=data.code.upper(),discount_percent=data.discount_percent); db.add(c); db.commit(); db.refresh(c); return c

@router.get("/coupons")
def coupons(admin=Depends(admin_user),db:Session=Depends(get_db)): return db.query(Coupon).all()
