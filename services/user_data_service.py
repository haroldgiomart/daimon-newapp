import boto3
import time
import os
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
from datetime import datetime

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


def add_disliked(user_id, item_id, item_type):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")

    # 1️⃣ Eliminar favorito si existe (regla: no puede ser favorite y disliked al mismo tiempo)
    table.delete_item(
        Key={
            "PK": f"USER#{user_id}",
            "SK": f"FAVORITE#{item_type.upper()}#{item_id}"
        }
    )

    # 2️⃣ Agregar disliked
    table.put_item(
        Item={
            "PK": f"USER#{user_id}",
            "SK": f"DISLIKED#{item_type.upper()}#{item_id}",
            "item_id": item_id,
            "entity_type": item_type,
            "created_at": int(time.time())
        }
    )


def remove_disliked(user_id, item_id, item_type):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_user_data")

    table.delete_item(
        Key={
            "PK": f"USER#{user_id}",
            "SK": f"DISLIKED#{item_type.upper()}#{item_id}"
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

def create_user_if_not_exists(user_id, email, first_name, last_name, image_url):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_users")

    response = table.get_item(
        Key={"user_id": user_id}
    )

    if "Item" in response:
        return

    table.put_item(
        Item={
            "user_id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "created_at": datetime.utcnow().isoformat(),
            "plan": "FREE",
            "image_url": image_url
        }
    )
