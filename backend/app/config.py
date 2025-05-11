from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_CLIENT = os.getenv("MONGO_CLIENT")

CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION")

EMBEDDER_MODEL = 'all-MiniLM-L6-v2'