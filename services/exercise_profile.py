# services/exercise_profile.py

import boto3
from datetime import datetime
import os
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

def get_exercise_profile(user_id: str):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_profile")

    response = table.get_item(
        Key={"user_id": user_id}
    )
    return response.get("Item")


def save_exercise_profile(user_id: str, data: dict):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_profile")

    item = {
        "user_id": user_id,
        "goal": data.get("goal"),
        "level": data.get("level"),
        "duration": data.get("duration"),
        "location": data.get("location"),
        "focus": data.get("focus"),
        "injury": data.get("injury"),
        "created_at": datetime.utcnow().isoformat()
    }

    table.put_item(Item=item)

    return item