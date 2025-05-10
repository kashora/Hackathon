from flask import Blueprint, request, jsonify
from app.db import employees, documents, chroma_collection
from app.utils import generate_uuid, get_timestamp, embedd_text, retrieve_from_db
from .orchestrator_agent import run_orchestration
from .config import MONGO_URI
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def welcome_route():
    return "Welcome to the backend"

@main_bp.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.json

    if not data.get("email") or not data.get("username"):
        return jsonify({"error": "Email and username are required."}), 400
    
    if employees.find_one({"$or": [{"email": data.get("email")}, {"username": data.get("username")}]}):
        return jsonify({"error": "Username or email already exists."}), 400
    
    emp_id = generate_uuid("emp")
    employee = {
        "_id": emp_id,
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "hashed_password": data["hashed_password"],
        "role": data["role"],
        "corporate_level": data["access_level"],
        "department": data["department"]
    }
    employees.insert_one(employee)
    return jsonify({"message": "Employee added", "id": emp_id})

@main_bp.route('/add_document', methods=['POST'])
def add_document():
    data = request.json
    doc_id = generate_uuid("data")
    doc_text = data.get("text")
    if not doc_text:
        return jsonify({"error": "No document text received."}), 400
    document = {
        "_id": doc_id,
        "text": doc_text,
        "department": data.get("department", "unknown"),
        "source": data.get("source", "unknown"),
        "created_at": get_timestamp(),
        "employees": data.get("employees"),
        "access_level": data.get("access_level"),
        "metadata": data.get("metadata"),
        "company_name": data.get("company_name", "unknown")
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
        }],
        embeddings=[embedding]
    )
    return jsonify({"message": "Document added", "id": doc_id})

@main_bp.route('/neurocorp', methods=['POST'])
def corporate_brain():
    prompts = request.json["prompts"]
    # user_access_level = request.json.get("access_level", 5)
    
    knowledge_base = retrieve_from_db(prompts)

    agents_res = run_orchestration(prompts, knowledge_base)

    return agents_res
    
