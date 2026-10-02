from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Product, Order, User, Supplier, Coupon, InventoryLog
from ..schemas import SupplierIn, CouponIn, OrderStatusIn, ORDER_STATUSES
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


def _order_dict(o):
    return {"id":o.id,"customer":o.user.email if o.user else None,"total":o.total,"status":o.status,
            "payment_status":o.payment_status,"tracking_number":o.tracking_number,
            "shipping_address":o.shipping_address,"created_at":o.created_at.isoformat(),
            "items":[{"product_id":i.product_id,"quantity":i.quantity,"unit_price":i.unit_price} for i in o.items]}

@router.get("/orders")
def all_orders(status:str|None=None,limit:int=50,admin=Depends(admin_user),db:Session=Depends(get_db)):
    """All customers' orders (the normal /api/orders only returns the logged-in user's)."""
    q=db.query(Order)
    if status: q=q.filter(Order.status==status.upper())
    return [_order_dict(o) for o in q.order_by(Order.id.desc()).limit(min(max(limit,1),200)).all()]

@router.put("/orders/{order_id}/status")
def update_order_status(order_id:int,data:OrderStatusIn,admin=Depends(admin_user),db:Session=Depends(get_db)):
    status=data.status.upper()
    if status not in ORDER_STATUSES: raise HTTPException(400,f"Status must be one of {ORDER_STATUSES}")
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,"Order not found")
    o.status=status
    if data.tracking_number is not None: o.tracking_number=data.tracking_number
    db.commit(); db.refresh(o); return _order_dict(o)
