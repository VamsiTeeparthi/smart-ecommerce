from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_admin: bool
    model_config = {"from_attributes": True}

class CategoryIn(BaseModel):
    name: str

class ProductIn(BaseModel):
    name: str
    description: str = ""
    price: float
    image_url: str = ""
    category_id: int
    supplier_id: int | None = None
    stock: int = 0
    reorder_level: int = 5

class ProductOut(ProductIn):
    id: int
    model_config = {"from_attributes": True}

class ProductBulkIn(BaseModel):
    products: list[ProductIn] = Field(min_length=1, max_length=200)

class CartIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class CheckoutIn(BaseModel):
    shipping_address: str
    coupon_code: str | None = None
    payment_method: str = "demo"

class ReviewIn(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = ""

class CouponIn(BaseModel):
    code: str
    discount_percent: float = Field(gt=0, le=100)

class SupplierIn(BaseModel):
    name: str
    email: str = ""
    phone: str = ""

class OrderOut(BaseModel):
    id: int
    total: float
    status: str
    payment_status: str
    tracking_number: str
    shipping_address: str
    created_at: datetime
    model_config = {"from_attributes": True}

ORDER_STATUSES = ["PLACED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]

class OrderStatusIn(BaseModel):
    status: str
    tracking_number: str | None = None
