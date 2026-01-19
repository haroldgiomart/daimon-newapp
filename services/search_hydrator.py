from services.benefits_repository import get_benefits_by_keys
from services.benefits_service import _normalize_benefit


def hydrate_search_results(pinecone_results):
    if not pinecone_results:
        return []

    # 1. Extraer keys completas desde Pinecone
    ordered_keys = [
        {
            "benefitCode": r["metadata"]["benefitCode"],
            "_id": r["id"]  # Pinecone id = _id de Dynamo
        }
        for r in pinecone_results
        if "benefitCode" in r["metadata"] and r.get("id")
    ]

    if not ordered_keys:
        return []

    # 2. Traer beneficios completos desde DynamoDB
    benefits = get_benefits_by_keys(ordered_keys)

    if not benefits:
        return []

    # 3. Mapa por clave compuesta
    benefit_map = {
        (b["benefitCode"], b["_id"]): b
        for b in benefits
    }

    # 4. Reconstruir lista manteniendo el orden por score
    hydrated = []

    for k in ordered_keys:
        key = (k["benefitCode"], k["_id"])
        benefit = benefit_map.get(key)
        if benefit:
            hydrated.append(_normalize_benefit(benefit))

    return hydrated