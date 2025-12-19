import requests

API_URL = "https://sp37216i6g.execute-api.us-east-1.amazonaws.com/v1/benefits_by_subcategory"

def get_benefits_by_subcategory():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error obteniendo beneficios:", e)
        return {}