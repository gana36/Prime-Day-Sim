provider "aws" {
  region = "us-east-1"
}

# 1. VPC & Networking
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "prime-day-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

# 2. SQS Queue (Order Buffer)
resource "aws_sqs_queue" "orders_queue" {
  name                      = "prime-day-orders"
  message_retention_seconds = 86400
  visibility_timeout_seconds = 30
}

# 3. RDS PostgreSQL (Inventory DB)
resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = "db.t3.micro"
  db_name              = "prime_db"
  username             = "user"
  password             = "password123" # In prod, use AWS Secrets Manager!
  skip_final_snapshot  = true
  publicly_accessible  = true # For demo purposes only
}

# 4. ElastiCache Redis (Caching)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "prime-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# 5. Lambda Function (Order Processor - Optional)
# This assumes you zip your worker code into 'worker.zip'
# resource "aws_lambda_function" "order_processor" {
#   filename      = "worker.zip"
#   function_name = "prime_order_processor"
#   role          = aws_iam_role.lambda_exec.arn
#   handler       = "app.worker.handler"
#   runtime       = "python3.11"
# }

output "sqs_url" {
  value = aws_sqs_queue.orders_queue.id
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
