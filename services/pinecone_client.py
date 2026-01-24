import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# Inicializa cliente Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

# Nombre del índice
INDEX_NAME = os.environ.get("PINECONE_INDEX", "daimon-benefits")

# Obtiene el índice
index = pc.Index(INDEX_NAME)