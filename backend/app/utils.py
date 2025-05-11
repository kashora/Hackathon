import uuid
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from .config import EMBEDDER_MODEL
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List
from .db import chroma_collection, documents
import json
from dotenv import load_dotenv
import pickle

load_dotenv() # to load gemini API key

model = SentenceTransformer(EMBEDDER_MODEL)
query_builder = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

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

def get_different_prompts(chat_history: List[List[str]]):
    if not chat_history or not len(chat_history) > 0:
        return
    
    user_prompts = [prompt[1] for prompt in chat_history if prompt[0] == "user"]
    if not user_prompts or not len(user_prompts) > 0:
        return
    
    combined_query = " | ".join(user_prompts)

    template = """You are a helpful assistant that generates multiple search queries based on a user input prompts history for a task. \n
    Generate multiple search queries related to the user prompts, only include in your response the 4 queries, : {query} \n
    Output (4 queries):"""
    prompt_rag_fusion = ChatPromptTemplate.from_template(template)
    
    generate_queries = (
        prompt_rag_fusion 
        | query_builder
        | StrOutputParser()
        | (lambda x: x.split("\n"))
    )
    query_list = generate_queries.invoke({"query": combined_query})

    return query_list

def get_relevant_documents_ids(prompt_embeddings, max_num_of_docs, minimum_score = 0.65) -> List[str]:
    results = chroma_collection.query(
        query_embeddings=[prompt_embeddings],  # your_embedding is a list of floats
        n_results=max_num_of_docs
    )
    ids = results.get("ids", [[]])[0]
    scores = results.get("distances", [[]])[0]
    relevant_ids = [doc_id for doc_id, score in zip(ids, scores) if score > minimum_score]
    return relevant_ids

def reciprocal_rank_fusion(results: list[list], k=60):
    """ Reciprocal_rank_fusion that takes multiple lists of ranked documents 
        and an optional parameter k used in the RRF formula """
    
    fused_scores = {}

    for docs in results:
        for rank, doc in enumerate(docs):
            _ = doc.pop("created_at")
            doc_bytes = json.dumps(doc) # Keep as bytes
            if doc_bytes not in fused_scores:
                fused_scores[doc_bytes] = 0
            fused_scores[doc_bytes] += 1 / (rank + k)

    reranked_results = [
        json.loads(doc_bytes)
        for doc_bytes, _ in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]

    return reranked_results


def get_documents_per_prompt(prompt, max_num_of_docs: int = 10):
    prompt_embeddings = embedd_text(prompt)
    if not len(list(prompt_embeddings)) > 0:
        return
    
    data_ids = get_relevant_documents_ids(prompt_embeddings, max_num_of_docs)

    fetched_documents = list(documents.find({"_id": {"$in": data_ids}}))

    return fetched_documents or []

def get_all_relevant_documents(prompt_list: List[str], max_num_of_all_docs: int = 20) -> List:
    all_documents = []
    for prompt in prompt_list:
        all_documents.append(get_documents_per_prompt(prompt))
    
    all_documents_reranked = reciprocal_rank_fusion(all_documents)

    return all_documents_reranked[:max_num_of_all_docs]

def retrieve_from_db(chat_history: List[List[str]]):

    preprocessed_prompts = get_different_prompts(chat_history)
    if not preprocessed_prompts:
        return

    relevant_documents = get_all_relevant_documents(preprocessed_prompts)

    try:
        stringified_documents = json.dumps(relevant_documents)
        return stringified_documents
    except Exception as e:
        return