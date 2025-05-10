from flask import Blueprint, request, jsonify
from app.db import employees, documents, chroma_collection
from app.utils import generate_uuid, get_timestamp, embedd_text
from .config import MONGO_URI
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def welcome_route():
    return "Welcome to the backend"

@main_bp.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.json
    emp_id = generate_uuid("emp")
    employee = {
        "_id": emp_id,
        "name": data["name"],
        "email": data["email"],
        "role": data["role"],
        "access_level": data["access_level"],
        "department": data["department"]
    }
    employees.insert_one(employee)
    return jsonify({"message": "Employee added", "id": emp_id})

@main_bp.route('/add_document', methods=['POST'])
def add_document():
    data = request.json
    doc_id = generate_uuid("doc")
    doc_text = data["text"]
    document = {
        "_id": doc_id,
        "title": data["title"],
        "text": doc_text,
        "source": data.get("source", "unknown"),
        "created_at": get_timestamp(),
        "author_id": data["author_id"],
        "access_level": data["access_level"],
        "metadata": data["metadata"]
    }
    documents.insert_one(document)
    embedding = embedd_text(doc_text)
    chroma_collection.add(
        ids=[doc_id],
        documents=[doc_text],
        metadatas=[{
            "doc_id": doc_id,
            "access_level": data["access_level"],
            "department": data["metadata"]["department"]
        }]
    )
    return jsonify({"message": "Document added", "id": doc_id})

@main_bp.route('/search', methods=['POST'])
def search_documents():
    query = request.json["query"]
    user_access_level = request.json["access_level"]

    results = chroma_collection.query(
        query_texts=[query],
        n_results=5
    )

    filtered = []
    for i, metadata in enumerate(results['metadatas'][0]):
        if metadata["access_level"] <= user_access_level:
            doc_id = metadata["doc_id"]
            doc = documents.find_one({"_id": doc_id})
            if doc:
                filtered.append({
                    "title": doc["title"],
                    "text": doc["text"],
                    "source": doc["source"],
                    "department": metadata["department"]
                })

    return jsonify({"results": filtered})
