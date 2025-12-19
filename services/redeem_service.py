import requests

def redeem_benefit(benefit_code:str) -> dict:

    print(benefit_code)

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

    print("Status:", response.status_code)
    print("Response:", response.text)
    return response.json()