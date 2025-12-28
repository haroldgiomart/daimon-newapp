import requests

API_URL = "https://sp37216i6g.execute-api.us-east-1.amazonaws.com/v1/wellness_videos"

def get_videos():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error obteniendo beneficios:", e)
        return {}

if __name__ == '__main__':
    get_benefits_by_subcategory()