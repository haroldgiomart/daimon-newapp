import boto3
import os

AWS_REGION = 'us-east-1'
ENVIRONMENT = 'local'

def get_dynamodb():
    if os.environ.get("ENVIRONMENT") == "local":
        return boto3.resource(
            "dynamodb",
            endpoint_url="http://localhost:8000",
            region_name="us-east-1"
        )

    return boto3.resource(
        "dynamodb",
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    )

def get_benefits_by_keys(keys: list):

    if not keys:
        return []

    dynamodb = get_dynamodb()
    table = dynamodb.Table("daimon_pbenefit")

    response = dynamodb.batch_get_item(
        RequestItems={
            table.name: {
                "Keys": keys
            }
        }
    )

    return response["Responses"].get(table.name, [])