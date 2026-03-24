from datetime import datetime
import boto3
import requests
from services.dynamodb_service import get_dynamodb_table
from boto3.dynamodb.conditions import Key

benefit_table = "daimon_pbenefit"
redemptions_table = "daimon_benefit_redemptions"
limit = 15

def redeem_benefit(user_id: str, benefit_code:str) -> dict:

    print(f"Beneficio: {benefit_code}, UserId: {user_id}")

    url = f"https://apiv1.cuponstar.com/api/cupones/{benefit_code}/codigo"
    key = "IyxDYjdWxIm9nVqm6rqTUseHUVj6suALZlmwWuRqZRTt17c29YrttqzQJz6WlrUx"
    micrositio_id = 911206
    codigo_afiliado = 123456

    files = {
        "key": (None, key),
        "micrositio_id": (None, micrositio_id),
        "codigo_afiliado": (None, codigo_afiliado),
        "split": (None, "1"),
    }

    response = requests.post(url, files=files)

    if response.status_code == 200:
        timestamp = datetime.utcnow().isoformat()
        dynamodb = get_dynamodb_table()
        table = dynamodb.Table("daimon_benefit_redemptions")
        table.put_item(
            Item={
                "benefit_id": benefit_code,
                "timestamp": timestamp,
                "user_id": user_id
            }
        )

    return response.json()

def get_popular_benefits():
    dynamodb = get_dynamodb_table()
    table = dynamodb.Table(redemptions_table)

    counter = {}

    try:
        response = table.scan()
        items = response.get("Items", [])

        for item in items:
            benefit_id = item.get("benefit_id")
            if not benefit_id:
                continue

            counter[benefit_id] = counter.get(benefit_id, 0) + 1

        # ordenar por cantidad
        sorted_benefits = sorted(
            counter.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_ids = [b[0] for b in sorted_benefits[:limit]]

        return top_ids

    except Exception as e:
        print(f"Error GetPopularBenefits: {e}")
        return []


def get_benefit_ids(benefit_ids):
    dynamodb = get_dynamodb_table()
    table = dynamodb.Table(benefit_table)

    benefits = []

    for benefit_id in benefit_ids:

        benefit_id = "C" + benefit_id

        try:
            response = table.query(
                IndexName="benefitCode-index",
                KeyConditionExpression=Key("benefitCode").eq(benefit_id)
            )

            if response["Count"] > 0:
                benefits.append(response["Items"][0])

        except Exception as e:
            print(f"Error trayendo benefit {benefit_id}: {e}")

    return benefits


if __name__ == '__main__':
    ids_populares = get_popular_benefits()
    print(f"Ids populares: {ids_populares}")

    beneficios_populares = get_benefit_ids(ids_populares)
    print(f"Beneficios populares: {beneficios_populares}")

    #redeem_benefit("4946")