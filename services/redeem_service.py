from datetime import datetime
import boto3
import requests
from services.dynamodb_service import get_dynamodb_table

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

if __name__ == '__main__':
    redeem_benefit("4946")