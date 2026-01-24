from services.embeddings import embed_text
from services.search_hydrator import hydrate_search_results
from services.pinecone_client import index  # o donde tengas el index

def semantic_intent_search(intent, user_profile_text, user_tags):

    query_text = f"""
    Intención del usuario: {intent}
    Perfil del usuario: {user_profile_text}
    Preferencias: {', '.join(user_tags)}
    Contexto: recomendar beneficios relevantes y útiles
    """

    # 🔹 TEXTO → EMBEDDING
    embedding = embed_text(query_text)

    # 🔹 EMBEDDING → PINECONE
    pinecone_results = index.query(
        vector=embedding,
        top_k=20,
        include_metadata=True
    )["matches"]

    # 🔹 HIDRATAR RESULTADOS
    return hydrate_search_results(pinecone_results)