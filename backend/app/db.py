from pymongo import MongoClient
import chromadb
from chromadb import HttpClient
from .config import MONGO_URI, MONGO_CLIENT, CHROMA_COLLECTION


# MongoDB setup
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_CLIENT]
employees = mongo_db["employees"]
documents = mongo_db["data"]

# ChromaDB setup
chroma_client = HttpClient(host="localhost", port=8000)
chroma_collection = chroma_client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    metadata={"hnsw:space": "cosine"})