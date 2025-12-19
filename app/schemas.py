from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProductBase(BaseModel):
    id: str
    name: str
    category: str
    price: float
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    inventory_count: int

    class Config:
        from_attributes = True

class PurchaseRequest(BaseModel):
    user_id: str
    product_id: str
    quantity: int = 1

class Order(BaseModel):
    id: str
    user_id: str
    product_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
