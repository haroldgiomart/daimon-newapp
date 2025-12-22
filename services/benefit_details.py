import requests


API_URL = "https://sp37216i6g.execute-api.us-east-1.amazonaws.com/v1/benefit_details"

def get_benefit_details(benefitCode: str, benefitId: str) -> dict:
    """
    Consulta el detalle de un beneficio por benefitCode y benefitId
    """

    params = {
        "benefitCode": benefitCode,
        "_id": benefitId
    }

    print(f"PARAMS: {params}")

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        response = response.json()
        data = response['benefit']
        print(f"Data: {data}")
        return data

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout al consultar el servicio de beneficios"
        }

    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"Error HTTP al consultar beneficio: {str(e)}",
            "status_code": response.status_code
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Error de red al consultar beneficio: {str(e)}"
        }

if __name__ == '__main__':
    beneficio = {'benefitCode': 'C6669','_id':'dce2839d1432029d24146'}
    get_benefit_details(beneficio['benefitCode'], beneficio['_id'])
