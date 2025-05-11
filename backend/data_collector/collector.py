from mail_collector import get_gmail_messages 
from slack_collector import get_all_messages



slack_messages = get_all_messages()


'''
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
        "company_name": data.get("company_name", "unknown")
    }'''


gmail_emails = [ 
    {
        "text": email.snippet,
        "department": "unknown",
        "source": email.sender,
        "created_at": email.date,
        "access_level": "3",
        "company_name": "infinidev",
    }
    
    for email in get_gmail_messages()]

#call /add_document api 

import requests
import json
import time


def add_document_to_api(documents):
    url = "http://http://127.0.0.1:5000/add_document"  # Replace with your API endpoint
    headers = {
        "Content-Type": "application/json"
    }
    for document in documents:
        response = requests.post(url, headers=headers, data=json.dumps(document))
        
        if response.status_code == 200:
            print("Document added successfully:", response.json())
        else:
            print("Failed to add document:", response.status_code, response.text)
        
if __name__ == "__main__":
    # Add emails and messages to the API
    while True:
        add_document_to_api(gmail_emails)
        add_document_to_api(slack_messages)
        time.sleep(7 * 24 * 60 * 60)  # Sleep for 1 week
