import asyncio
import csv
import random
import os
from app.database import AsyncSessionLocal, engine, Base
from app import models

CSV_FILE = "olist_products_dataset.csv"

async def ingest_data():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found!")
        return

    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"Reading {CSV_FILE}...")
    products_to_add = []
    inventory_to_add = []
    
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            # Olist data: product_id, product_category_name, ...
            p_id = row["product_id"]
            category = row["product_category_name"] or "uncategorized"
            
            # Generate synthetic data for missing fields
            price = round(random.uniform(10.0, 500.0), 2)
            name = f"{category.replace('_', ' ').title()} - {p_id[:8]}"
            inventory_count = random.randint(0, 100) # Scarcity for simulation!

            products_to_add.append(models.Product(
                id=p_id,
                name=name,
                category=category,
                price=price,
                description=f"Imported from Olist. Category: {category}"
            ))
            
            inventory_to_add.append(models.Inventory(
                product_id=p_id,
                count=inventory_count
            ))
            
            count += 1
            if count >= 1000: # Limit to 1000 products for this demo to keep it fast
                break

    print(f"Ingesting {len(products_to_add)} products...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Batch insert would be faster, but simple add_all is fine for 1000 rows
            db.add_all(products_to_add)
            db.add_all(inventory_to_add)
            await db.commit()
            print("Ingestion complete!")
        except Exception as e:
            print(f"Error during ingestion: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(ingest_data())
