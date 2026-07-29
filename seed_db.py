from langchain_core.documents import Document
from src.tools.knowledge_base import vector_store

def seed_database():
    mock_intel = [
        Document(
            page_content="Ransomware strain 'DarkLocker' often drops a ransom note named 'readme_to_decrypt.txt' and initiates connections to IP 198.51.100.45 over port 443.",
            metadata={"source": "Threat Intel Report 2024-05"}
        ),
        Document(
            page_content="Standard runbook for impossible travel alerts: 1. Suspend the user account. 2. Revoke all active session tokens. 3. Force a password reset.",
            metadata={"source": "Identity SOC Runbook"}
        ),
        Document(
            page_content="Suspicious PowerShell execution bypassing execution policy (e.g., -ExecutionPolicy Bypass -NoProfile) is a common indicator of compromise for fileless malware.",
            metadata={"source": "Endpoint Hunting Guide"}
        )
    ]
    
    print("Ingesting threat intelligence into local ChromaDB...")
    vector_store.add_documents(mock_intel)
    print("Ingestion complete. Database persisted.")

if __name__ == "__main__":
    seed_database()