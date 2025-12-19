import asyncio
import json
import os
from app import sqs, crud, database, schemas
from app.database import AsyncSessionLocal

async def process_orders():
    print("Worker started. Waiting for orders...")
    while True:
        try:
            # Run blocking SQS call in a separate thread to not block the async loop
            messages = await asyncio.to_thread(sqs.receive_messages)
            
            if not messages:
                await asyncio.sleep(1)
                continue

            for msg in messages:
                order_data = json.loads(msg["Body"])
                print(f"Processing order for Product: {order_data['product_id']}")
                
                # Process the order in DB
                async with AsyncSessionLocal() as db:
                    try:
                        # We reuse the create_order logic but we might need to adjust it 
                        # because the "reservation" might have already happened in Redis.
                        # For now, let's assume we are doing the full DB transaction here.
                        purchase_req = schemas.PurchaseRequest(**order_data)
                        await crud.create_order(db, purchase_req)
                        print(f"Order created successfully: {order_data}")
                        
                        # Delete message only after successful processing
                        await asyncio.to_thread(sqs.delete_message, msg["ReceiptHandle"])
                        
                    except Exception as e:
                        print(f"Failed to process order: {e}")
                        # In a real app, we would send to a Dead Letter Queue (DLQ)
                        
        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(process_orders())
