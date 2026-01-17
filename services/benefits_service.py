import requests

API_URL = "https://sp37216i6g.execute-api.us-east-1.amazonaws.com/v1/benefits_by_subcategory"
MAX_BENEFITS_PER_SUBCATEGORY = 11


def _normalize_benefit(raw):
    raw.setdefault("_id", None)
    raw.setdefault("name", "Beneficio")
    raw.setdefault("shortDescription", None)
    raw.setdefault("benefitType", "Beneficio")
    raw.setdefault("benefitCode", None)
    raw.setdefault("listImages", [])
    return raw


def get_benefits_by_subcategory(category):
    try:
        response = requests.get(
            API_URL,
            params={"category": category},
            timeout=10
        )
        response.raise_for_status()

        payload = response.json()
        print("API PAYLOAD TYPE:", type(payload))

        result = {}

        # -------------------------------------------------
        # CASO REAL: payload es LISTA  ✅
        # -------------------------------------------------
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue

                # Cada item tiene UNA subcategoría
                for subcategory_name, benefits in item.items():
                    if not isinstance(benefits, list):
                        continue

                    result[subcategory_name] = [
                        _normalize_benefit(b)
                        for b in benefits[:MAX_BENEFITS_PER_SUBCATEGORY]
                        if isinstance(b, dict)
                    ]

            print("NORMALIZED (FROM LIST):", result.keys())
            return result

        # -------------------------------------------------
        # CASO alterno: payload ya es DICT
        # -------------------------------------------------
        if isinstance(payload, dict):
            for subcategory_name, benefits in payload.items():
                if not isinstance(benefits, list):
                    continue

                result[subcategory_name] = [
                    _normalize_benefit(b)
                    for b in benefits[:MAX_BENEFITS_PER_SUBCATEGORY]
                    if isinstance(b, dict)
                ]

            print("NORMALIZED (FROM DICT):", result.keys())
            return result

        print("❌ Payload no soportado")
        return {}

    except Exception as e:
        print("❌ Error obteniendo beneficios:", e)
        return {}

if __name__ == '__main__':
    respuesta = get_benefits_by_subcategory("cupones")
    print(f"Respuesta: {respuesta}")