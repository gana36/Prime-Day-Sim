from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError
from app import models, schemas
import uuid

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Product)
        .options(selectinload(models.Product.inventory))
        .offset(skip)
        .limit(limit)
    )
    products = result.scalars().all()
    # Map to schema with inventory count
    return [
        schemas.Product(
            id=p.id,
            name=p.name,
            category=p.category,
            price=p.price,
            description=p.description,
            inventory_count=p.inventory.count if p.inventory else 0
        )
        for p in products
    ]

async def create_product(db: AsyncSession, product: schemas.ProductCreate, initial_inventory: int):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    
    db_inventory = models.Inventory(product_id=product.id, count=initial_inventory)
    db.add(db_inventory)
    
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def create_order(db: AsyncSession, order: schemas.PurchaseRequest):
    # Optimistic Locking Logic
    # 1. Get current inventory version
    result = await db.execute(
        select(models.Inventory).where(models.Inventory.product_id == order.product_id)
    )
    inventory = result.scalar_one_or_none()
    
    if not inventory:
        raise ValueError("Product not found")
    
    if inventory.count < order.quantity:
        raise ValueError("Out of stock")

    # 2. Decrement count with version check
    # UPDATE inventory SET count = count - 1, version = version + 1 WHERE product_id = X AND version = Y
    # SQLAlchemy handles this via optimistic locking if configured, but here we do it explicitly or via update statement
    
    # Explicit update with version check
    update_result = await db.execute(
        models.Inventory.__table__.update()
        .where(models.Inventory.product_id == order.product_id)
        .where(models.Inventory.version == inventory.version)
        .where(models.Inventory.count >= order.quantity)
        .values(count=models.Inventory.count - order.quantity, version=models.Inventory.version + 1)
    )
    
    if update_result.rowcount == 0:
        # If no rows updated, it means version changed (race condition) or stock ran out
        raise StaleDataError("Concurrent update detected")

    # 3. Create Order
    db_order = models.Order(
        id=str(uuid.uuid4()),
        user_id=order.user_id,
        product_id=order.product_id,
        status="processing"
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order




# curl -X POST "http://127.0.0.1:8000/purchase" -H "Content-Type: application/json" -d '{"user_id": "user_123", "product_id": "ffcaa5d3-4b21-4a10-b370-1e7daf04f562", "quantity": 1}'