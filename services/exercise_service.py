import boto3
from collections import defaultdict
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = "daimon_physical_activity"
GSI_NAME = "GSI_Target"
ENVIRONMENT = os.environ['ENVIRONMENT']

print(f"Environment: {ENVIRONMENT}")


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


def decimal_to_float(obj):
    """
    Convierte Decimal (DynamoDB) a float para renderizar sin problemas
    """
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def get_exercises_grouped_by_target(target_filter: str | None = None,limit_per_target: int | None = None) -> dict:

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_physical_activity")
    grouped = defaultdict(list)

    # 👉 Caso 1: target específico
    if target_filter:
        response = table.query(
            IndexName=GSI_NAME,
            KeyConditionExpression=Key("target").eq(target_filter)
        )
        items = response.get("Items", [])

    # 👉 Caso 2: todos los targets
    else:
        # DynamoDB no permite query sin PK → usamos scan controlado
        response = table.scan(
            ProjectionExpression="#id, #name, target, bodyPart, difficultyLevel, gifUrl, kcalBurned",
            ExpressionAttributeNames={
                "#id": "id",
                "#name": "name"
            }
        )
        items = response.get("Items", [])

    # Agrupar
    for item in items:
        item = decimal_to_float(item)
        grouped[item["target"]].append(item)

    # Limitar por target si aplica
    if limit_per_target:
        grouped = {
            target: exercises[:limit_per_target]
            for target, exercises in grouped.items()
        }

    return dict(grouped)


def get_exercise_by_id(exercise_id: str):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_physical_activity")

    response = table.get_item(
        Key={
            "id": exercise_id
        }
    )

    return response.get("Item")


def all_items():
    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_physical_activity")

    grouped = defaultdict(list)
    scan_kwargs = {}

    while True:
        response = table.scan(**scan_kwargs)

        for item in response.get("Items", []):
            target = item.get("target")
            if target:
                grouped[target].append(item)

        if "LastEvaluatedKey" not in response:
            break

        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    # 🔤 Ordenar alfabéticamente por target
    ordered_result = {
        target: grouped[target]
        for target in sorted(grouped.keys())
    }

    return ordered_result



if __name__ == '__main__':
    #data = get_exercises_grouped_by_target("pantorrillas", 10)
    data = all_items()
    print(f"Exercises: {data}")