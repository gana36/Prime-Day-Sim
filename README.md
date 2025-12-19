# Amazon Prime Day Simulator

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Amazon SQS](https://img.shields.io/badge/Amazon_SQS-FF9900?style=for-the-badge&logo=amazonsqs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)

A high-concurrency e-commerce inventory system designed to handle flash sale traffic without crashing or overselling. This project simulates the backend architecture used by major retailers like Amazon to manage massive traffic spikes during events like Prime Day and Black Friday.

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Concurrent Users Tested | 1,000+ |
| Requests Per Second | 122 RPS |
| Failure Rate | 0.03% |
| Orders Processed | 2,268 |
| Inventory Overselling | **Zero** |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│                    (Locust Load Test - 10,000 Users)                         │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI (Python AsyncIO)                            │ │
│  │                                                                        │ │
│  │   GET /products ──────────────▶ Redis Cache (TTL: 10s)                │ │
│  │                                      │                                 │ │
│  │                                      ▼ (cache miss)                    │ │
│  │                                 PostgreSQL                             │ │
│  │                                                                        │ │
│  │   POST /purchase ─────────────▶ SQS Queue ──▶ Return "pending"        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MESSAGE QUEUE                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Amazon SQS (via LocalStack)                         │ │
│  │                                                                        │ │
│  │   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                            │ │
│  │   │Ord 1│ │Ord 2│ │Ord 3│ │ ... │ │Ord N│   Buffers traffic spikes   │ │
│  │   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WORKER LAYER                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Background Worker (Python)                          │ │
│  │                                                                        │ │
│  │   1. Poll SQS for orders                                              │ │
│  │   2. Execute Optimistic Lock UPDATE                                   │ │
│  │   3. Create Order record                                              │ │
│  │   4. Delete message from queue                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌───────────────────┐              ┌───────────────────┐                   │
│  │    PostgreSQL     │              │       Redis       │                   │
│  │                   │              │                   │                   │
│  │  - products       │              │  - Product cache  │                   │
│  │  - inventory      │              │  - TTL: 10 sec    │                   │
│  │  - orders         │              │                   │                   │
│  │  - version column │◀─────────────│  (Write-back)     │                   │
│  │    (Optimistic    │              │                   │                   │
│  │     Locking)      │              │                   │                   │
│  └───────────────────┘              └───────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Optimistic Locking
Prevents the race condition where two users buy the last item simultaneously.

```sql
UPDATE inventory 
SET count = count - 1, version = version + 1 
WHERE product_id = 'xxx' 
  AND version = 1    -- Only succeed if unchanged
  AND count >= 1;    -- Only if stock exists
```

### Async Order Processing
The API accepts orders in approximately 5ms and offloads processing to SQS. The database never sees traffic spikes directly.

### Real-World Data
The database is seeded with 1,000+ real products from the [Olist E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

### Load Tested
Verified with Locust to handle 1,000+ concurrent users with zero overselling.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| API | FastAPI (Python) | High-performance async web framework |
| Database | PostgreSQL | ACID compliance, optimistic locking |
| Cache | Redis | Low-latency product listings |
| Queue | Amazon SQS | Async order processing buffer |
| Local AWS | LocalStack | SQS emulation for development |
| Infrastructure | Docker Compose | Container orchestration |
| Load Testing | Locust | Concurrent user simulation |
| IaC | Terraform | AWS infrastructure provisioning |

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/amazon-prime-day-simulator.git
cd amazon-prime-day-simulator

# Start infrastructure (PostgreSQL, Redis, LocalStack)
docker-compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
alembic upgrade head
python ingest_olist.py

# Start the API (Terminal 1)
uvicorn app.main:app --workers 4

# Start the Worker (Terminal 2)
python -m app.worker

# Run load test (Terminal 3)
locust -f locustfile.py --host=http://127.0.0.1:8000
```

Open `http://localhost:8089` to access the Locust UI.

---

## Testing and Verification

### Load Testing
```bash
locust -f locustfile.py --host=http://127.0.0.1:8000
```

### Verify No Overselling
```bash
python verify_inventory.py
```

Expected output:
```
Total Orders Processed: 2268
SUCCESS: No negative inventory found. Optimistic Locking worked!
```

---

## Project Structure

```
amazon-prime-day-simulator/
├── app/
│   ├── main.py           # FastAPI endpoints (GET /products, POST /purchase)
│   ├── models.py         # SQLAlchemy models (Product, Inventory, Order)
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── crud.py           # Database operations + Optimistic Locking
│   ├── database.py       # Async database connection
│   ├── sqs.py            # Amazon SQS utilities
│   └── worker.py         # Background order processor
├── markdowns/
│   ├── scenario3.md      # Normal purchase flow explained
│   ├── scenario4.md      # Race condition and optimistic locking
│   ├── scenario6.md      # High traffic spike handling
│   └── crud_explained.md # Database operations breakdown
├── terraform/
│   └── main.tf           # AWS infrastructure (RDS, SQS, ElastiCache)
├── alembic/              # Database migrations
├── locustfile.py         # Load testing script
├── ingest_olist.py       # Olist dataset ingestion
├── verify_inventory.py   # Consistency verification
├── docker-compose.yml    # Local infrastructure
├── requirements.txt      # Python dependencies
└── README.md
```

---

## AWS Deployment (Terraform)

The `terraform/` folder contains Infrastructure as Code for AWS:

- RDS (PostgreSQL)
- ElastiCache (Redis)
- SQS (Order Queue)
- VPC (Networking)

```bash
cd terraform
terraform init
terraform apply
```

---

## License

MIT License - feel free to use this project for learning and portfolio purposes.

---

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.
