import uuid
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from .config import EMBEDDER_MODEL

model = SentenceTransformer(EMBEDDER_MODEL)

def generate_uuid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def get_timestamp():
    return datetime.now()

def embedd_text(text):
    if not text or not isinstance(text, str):
        return
    try:
        embeddings = model.encode(text)
        return embeddings
    except:
        return
    
