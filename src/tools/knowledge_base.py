import os 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import tool


embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')


DB_DIR = os.path.join(os.path.dirname(__file__),"..","..","chroma_db")


vector_store = Chroma(
    collection_name="soc_threat_intel",
    embedding_function = embeddings,
    persist_directory=DB_DIR
)


@tool

def search_threat_intel(query: str)-> str:
    """
    Query the SOC knowledge base for threat intelligence, historical incidents, known malware signatures, and remediation runbooks.

    args:
        query : the search term or description of the threat.
    """

    try:

        results = vector_store.similarity_search(query, k=3)

        if not results:
            return "No relevant threat intelligence found in the knowledge base."

        formatted_results = "\n\n".join([f"SOURCE: {doc.metadata.get('source', 'Unknown')}\nINFO: {doc.page_content}" for doc in results])
        return formatted_results

    except Exception as e:
        return f"Error querying the knowledge base : {str(e)}"
    