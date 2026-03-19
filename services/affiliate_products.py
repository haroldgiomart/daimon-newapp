import boto3
from collections import defaultdict
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

affiliate_products_table = "daimon_affiliate_products"
clicks_products_table = "daimon_affiliate_clicks"

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


def _decimal_to_native(value):
    """
    Convierte Decimal a int o float para que Jinja/JSON lo manejen bien.
    """
    if isinstance(value, list):
        return [_decimal_to_native(v) for v in value]

    if isinstance(value, dict):
        return {k: _decimal_to_native(v) for k, v in value.items()}

    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)

    return value


def _normalize_product(item: dict) -> dict:
    """
    Normaliza un producto para evitar errores en la plantilla.
    """
    item = _decimal_to_native(item)

    return {
        "_id": item.get("_id", ""),
        "productCode": item.get("productCode", ""),
        "name": item.get("name", "Producto sin nombre"),
        "shortDescription": item.get("shortDescription", ""),
        "description": item.get("description", ""),
        "affiliateType": item.get("affiliateType", "Amazon"),
        "subcategory": item.get("subcategory", "Otros"),
        "brand": item.get("brand", ""),
        "price": item.get("price"),
        "currency": item.get("currency", "COP"),
        "imageUrl": item.get("imageUrl", ""),
        "gallery": item.get("gallery", []),
        "affiliateUrl": item.get("affiliateUrl", ""),
        "rating": item.get("rating"),
        "reviewCount": item.get("reviewCount"),
        "isActive": item.get("isActive", True),
    }

def get_affiliate_products_grouped() -> dict:

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table(affiliate_products_table)

    response = table.scan(
        FilterExpression=Attr("isActive").eq(True)
    )

    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Attr("isActive").eq(True),
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    grouped = defaultdict(list)

    for raw_item in items:
        product = _normalize_product(raw_item)
        subcategory = product.get("subcategory") or "Otros"
        grouped[subcategory].append(product)

    grouped = dict(sorted(grouped.items(), key=lambda x: x[0].lower()))

    for subcategory, products in grouped.items():
        grouped[subcategory] = sorted(
            products,
            key=lambda p: p.get("name", "").lower()
        )

    return grouped

def get_affiliate_product_by_id(product_id: str) -> dict | None:

    if not product_id:
        return None

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table(affiliate_products_table)

    response = table.get_item(
        Key={"_id": product_id}
    )

    item = response.get("Item")

    if not item:
        return None

    product = _normalize_product(item)

    if not product.get("isActive", True):
        return None

    return product


def save_affiliate_click(affilliate_product: dict, user_id: str):

    if not affilliate_product:
        return

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table(clicks_products_table)

    click_id = str(uuid.uuid4())

    item = {
        "click_id": click_id,
        "product_id": affilliate_product['_id'],
        "productCode": affilliate_product['productCode'],
        "affiliateType": affilliate_product['affiliateType'],
        "user_id": user_id,
        "clicked_at": datetime.utcnow().isoformat()
    }

    table.put_item(Item=item)

if __name__ == '__main__':
    response = get_affiliate_products_grouped()
    print(f"Response: {response}")