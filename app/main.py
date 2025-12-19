from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
import redis.asyncio as redis
import json
import os
from typing import List

from app import models, schemas, crud, database

app = FastAPI(title="Amazon Prime Day Simulator")

# Redis Connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("startup")
async def startup_event():
    # Verify Redis connection
    try:
        await redis_client.ping()
        print("Connected to Redis")
    except Exception as e:
        print(f"Redis connection failed: {e}")

@app.get("/")
async def root():
    return {"message": "Amazon Prime Day Simulator API is running"}

@app.get("/products", response_model=List[schemas.Product])
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    # 1. Check Cache
    cache_key = f"products:{skip}:{limit}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # 2. Fetch from DB
    products = await crud.get_products(db, skip=skip, limit=limit)
    
    # 3. Update Cache (TTL 10 seconds for "flash sale" freshness)
    # Convert Pydantic models to dict for JSON serialization
    products_json = json.dumps([p.model_dump() for p in products])
    await redis_client.setex(cache_key, 10, products_json)
    
    return products

@app.post("/purchase", response_model=schemas.Order)
async def purchase_product(order: schemas.PurchaseRequest, db: AsyncSession = Depends(database.get_db)):
    try:
        # 1. Check Cache/Inventory (Fast Fail) - Optional but good for performance
        # For now, we trust the queue or do a quick Redis check (omitted for brevity, relying on worker)
        
        # 2. Send to SQS
        from app import sqs
        import uuid
        from datetime import datetime
        
        # Create a "pending" order object to return immediately
        order_id = str(uuid.uuid4())
        order_dict = order.model_dump()
        order_dict["order_id"] = order_id # Pass generated ID if needed, or let worker generate
        
        # We need to match the schema expected by the worker or just pass the request
        # The worker expects purchase request data. 
        # Let's send the raw request data.
        sqs.send_order_message(order_dict)
        
        # Return a "Pending" status response
        return schemas.Order(
            id=order_id,
            user_id=order.user_id,
            product_id=order.product_id,
            status="pending",
            created_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


