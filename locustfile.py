from locust import FastHttpUser, task, between, events
import random

class PrimeDayUser(FastHttpUser):
    wait_time = between(1, 5) # Simulate think time between 1-5 seconds
    product_ids = []

    def on_start(self):
        """Fetch real product IDs from the API before starting tests"""
        if not PrimeDayUser.product_ids:
            try:
                response = self.client.get("/products")
                if response.status_code == 200:
                    products = response.json()
                    PrimeDayUser.product_ids = [p["id"] for p in products]
                    print(f"Loaded {len(PrimeDayUser.product_ids)} products for testing.")
                else:
                    print("Failed to load products! Defaulting to empty list.")
            except Exception as e:
                print(f"Error loading products: {e}")

    @task(3)
    def view_products(self):
        """User browses the product list (High frequency)"""
        self.client.get("/products")

    @task(1)
    def buy_product(self):
        """User attempts to buy a random product (Lower frequency)"""
        if not PrimeDayUser.product_ids:
            return

        product_id = random.choice(PrimeDayUser.product_ids)
        user_id = f"user_{random.randint(1, 100000)}"
        
        payload = {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 1
        }
        
        with self.client.post("/purchase", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 409:
                # 409 Conflict is expected if we hit optimistic locking limits
                response.failure("Got 409 Conflict - Should be queued!")
            else:
                response.failure(f"Failed with status {response.status_code}: {response.text}")

