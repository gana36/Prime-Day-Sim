from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True) # UUID or Olist ID
    name = Column(String, index=True)
    category = Column(String, index=True)
    price = Column(Float)
    description = Column(String, nullable=True)

    inventory = relationship("Inventory", back_populates="product", uselist=False)

class Inventory(Base):
    __tablename__ = "inventory"

    product_id = Column(String, ForeignKey("products.id"), primary_key=True)
    count = Column(Integer, default=0)
    version = Column(Integer, default=1) # Optimistic Locking

    product = relationship("Product", back_populates="inventory")

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    status = Column(String, default="pending") # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
