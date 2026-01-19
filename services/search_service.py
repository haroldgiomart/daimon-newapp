import os
from openai import OpenAI
from pinecone import Pinecone
from services.search_hydrator import hydrate_search_results
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX"])


def search_benefits_from_text(user_query, user_profile_text, user_tags):
    """
    Convierte texto → embedding → Pinecone → DynamoDB
    Devuelve beneficios completos listos para renderizar
    """

    # 1. Construir texto contextual
    query_text = f"""
    Búsqueda del usuario: {user_query}
    Gustos del usuario: {user_profile_text}
    """

    # 2. TEXTO → EMBEDDING (OpenAI)
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    ).data[0].embedding

    # 3. EMBEDDING → PINECONE
    pinecone_results = index.query(
        vector=embedding,
        top_k=10,
        include_metadata=True,
        filter={
            "status": "available",
            "country": "colombia"
        }
    ).get("matches", [])

    if not pinecone_results:
        return []

    # 4. IDs → DynamoDB (hidratación)
    return hydrate_search_results(pinecone_results)