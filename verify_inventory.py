import asyncio
from sqlalchemy import func, select
from app.database import AsyncSessionLocal
from app import models

async def verify_inventory():
    async with AsyncSessionLocal() as db:
        print("Verifying Inventory Consistency...")
        
        # 1. Get total orders count
        result = await db.execute(select(func.count(models.Order.id)))
        total_orders = result.scalar()
        print(f"Total Orders Processed: {total_orders}")

        # 2. Check for negative inventory (The "Overselling" check)
        result = await db.execute(
            select(models.Inventory).where(models.Inventory.count < 0)
        )
        negative_inventory = result.scalars().all()
        
        if negative_inventory:
            print(f"❌ CRITICAL FAIL: Found {len(negative_inventory)} products with negative inventory!")
            for inv in negative_inventory:
                print(f"  - Product {inv.product_id}: Count {inv.count}")
        else:
            print("✅ SUCCESS: No negative inventory found. Optimistic Locking worked!")

        # 3. Optional: Check specific product consistency if we knew initial state
        # Since we randomized initial state in ingest_olist.py, we can't do a perfect sum check 
        # unless we recorded the start state. But "No Negative Inventory" is the key proof for overselling.

if __name__ == "__main__":
    asyncio.run(verify_inventory())
