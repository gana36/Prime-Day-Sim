import boto3
import os
import json

# LocalStack SQS Configuration
SQS_REGION = "us-east-1"
SQS_ENDPOINT = os.getenv("SQS_ENDPOINT", "http://localhost:4566")
QUEUE_NAME = "prime-day-orders"

sqs_client = boto3.client(
    "sqs",
    region_name=SQS_REGION,
    endpoint_url=SQS_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

def get_queue_url():
    try:
        response = sqs_client.get_queue_url(QueueName=QUEUE_NAME)
        return response["QueueUrl"]
    except sqs_client.exceptions.QueueDoesNotExist:
        # Create queue if it doesn't exist (for local dev convenience)
        response = sqs_client.create_queue(QueueName=QUEUE_NAME)
        return response["QueueUrl"]

def send_order_message(order_data: dict):
    queue_url = get_queue_url()
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(order_data)
    )

def receive_messages(max_messages=10):
    queue_url = get_queue_url()
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=5 # Long polling
    )
    return response.get("Messages", [])

def delete_message(receipt_handle):
    queue_url = get_queue_url()
    sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
