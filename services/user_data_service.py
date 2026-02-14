import boto3
import time
import os
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

load_dotenv()


def get_dynamodb_table():
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


def save_profile(user_id, survey_data, user_tags):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")

    table.put_item(
        Item={
            "PK": f"USER#{user_id}",
            "SK": "PROFILE",
            "survey_completed": True,
            "survey_data": survey_data,
            "user_tags": user_tags,
            "created_at": int(time.time())
        }
    )

def add_favorite(user_id, item_id, item_type):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")

    table.put_item(
        Item={
            "PK": f"USER#{user_id}",
            "SK": f"FAVORITE#{item_type.upper()}#{item_id}",
            "item_id": item_id,
            "entity_type": item_type,
            "created_at": int(time.time())
        }
    )


def remove_favorite(user_id, item_id, item_type):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")

    table.delete_item(
        Key={
            "PK": f"USER#{user_id}",
            "SK": f"FAVORITE#{item_type.upper()}#{item_id}"
        }
    )

def get_user_items(user_id):
    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")
    response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={
            ":pk": f"USER#{user_id}"
        }
    )
    return response.get("Items", [])


def get_user_favorites(user_id, item_type=None):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")

    if item_type:
        sk_prefix = f"FAVORITE#{item_type.upper()}#"
    else:
        sk_prefix = "FAVORITE#"

    response = table.query(
        KeyConditionExpression=
            Key("PK").eq(f"USER#{user_id}") &
            Key("SK").begins_with(sk_prefix)
    )

    return response.get("Items", [])