from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CartItem, WishlistItem, Product, Order, OrderItem, Coupon, InventoryLog, Review
from ..schemas import CartIn, CheckoutIn, ReviewIn, OrderOut
from ..auth import current_user
from ..services.integrations import payment, shipping, email

router = APIRouter(prefix="/api", tags=["Shop"])

@router.get("/cart")
def get_cart(user=Depends(current_user), db: Session=Depends(get_db)):
    rows = db.query(CartItem).filter(CartItem.user_id==user.id).all()
    result=[]
    for row in rows:
        p=db.get(Product,row.product_id)
        result.append({"id":row.id,"product_id":p.id,"name":p.name,"price":p.price,"quantity":row.quantity,"image_url":p.image_url,"subtotal":p.price*row.quantity})
    return result

@router.post("/cart")
def add_cart(data: CartIn, user=Depends(current_user), db: Session=Depends(get_db)):
    p=db.get(Product,data.product_id)
    if not p: raise HTTPException(404,"Product not found")
    if data.quantity > p.stock: raise HTTPException(400,"Not enough stock")
    row=db.query(CartItem).filter(CartItem.user_id==user.id,CartItem.product_id==p.id).first()
    if row: row.quantity=data.quantity
    else: db.add(CartItem(user_id=user.id,product_id=p.id,quantity=data.quantity))
    db.commit(); return {"message":"Cart updated"}

@router.delete("/cart/{product_id}")
def remove_cart(product_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    row=db.query(CartItem).filter(CartItem.user_id==user.id,CartItem.product_id==product_id).first()
    if row: db.delete(row); db.commit()
    return {"message":"Removed"}

@router.get("/wishlist")
def wishlist(user=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(WishlistItem).filter(WishlistItem.user_id==user.id).all()
    return [db.get(Product,r.product_id) for r in rows]

@router.post("/wishlist/{product_id}")
def add_wishlist(product_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    if not db.query(WishlistItem).filter_by(user_id=user.id,product_id=product_id).first():
        db.add(WishlistItem(user_id=user.id,product_id=product_id)); db.commit()
    return {"message":"Added to wishlist"}

@router.post("/checkout",response_model=OrderOut)
def checkout(data:CheckoutIn,user=Depends(current_user),db:Session=Depends(get_db)):
    cart=db.query(CartItem).filter(CartItem.user_id==user.id).all()
    if not cart: raise HTTPException(400,"Cart is empty")
    total=0
    items=[]
    for c in cart:
        p=db.get(Product,c.product_id)
        if c.quantity>p.stock: raise HTTPException(400,f"Insufficient stock for {p.name}")
        total += p.price*c.quantity
        items.append((p,c.quantity))
    if data.coupon_code:
        coupon=db.query(Coupon).filter(Coupon.code==data.coupon_code.upper(),Coupon.active==True).first()
        if coupon: total *= (1-coupon.discount_percent/100)
    pay=payment.create_payment(total,data.payment_method)
    order=Order(user_id=user.id,total=round(total,2),status="PLACED",payment_status=pay["status"],shipping_address=data.shipping_address)
    db.add(order); db.flush()
    for p,qty in items:
        p.stock -= qty
        db.add(OrderItem(order_id=order.id,product_id=p.id,quantity=qty,unit_price=p.price))
        db.add(InventoryLog(product_id=p.id,change=-qty,reason=f"Order #{order.id}"))
    track=shipping.create_shipment(order.id,data.shipping_address)
    order.tracking_number=track["tracking_number"]
    for c in cart: db.delete(c)
    db.commit(); db.refresh(order)
    email.send(user.email,f"Order #{order.id} confirmed",f"Your order total is ₹{order.total}.")
    return order

@router.get("/orders",response_model=list[OrderOut])
def orders(user=Depends(current_user),db:Session=Depends(get_db)):
    return db.query(Order).filter(Order.user_id==user.id).order_by(Order.created_at.desc()).all()

@router.get("/orders/{order_id}/tracking")
def tracking(order_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    order=db.get(Order,order_id)
    if not order or order.user_id!=user.id: raise HTTPException(404,"Order not found")
    return shipping.track(order.tracking_number)

@router.post("/reviews")
def review(data:ReviewIn,user=Depends(current_user),db:Session=Depends(get_db)):
    if not db.get(Product,data.product_id): raise HTTPException(404,"Product not found")
    r=Review(user_id=user.id,**data.model_dump()); db.add(r); db.commit(); db.refresh(r); return r
