import os
from functools import wraps
from openai import OpenAI
from qdrant_client import QdrantClient
from tools.web_search.web_search import WebTrustedSearchTool
import uuid
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()
# Define the `tool` decorator if it cannot be imported
def tool(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.tool_name = name
        return wrapper
    return decorator

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_url = os.environ.get("QDRANT_URL")
connection = QdrantClient(url=qdrant_url)

@tool("Answer Q&A from Finance Knowledgebase")
def qdrant_tool(question: str, top_k:int) -> str:
    """Useful to answer questions based on the 1Finance PDF knowledge base."""

    response = client.embeddings.create(
        input=question,
        model="text-embedding-ada-002"
    )
    embedding = response.data[0].embedding

    search_result = connection.query_points(
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
        query=embedding,
        limit=top_k,
        with_payload=True
    )

    return search_result

class QdrantTool(BaseTool):
    def __init__(self):
        super().__init__(name="QdrantTool", description="A tool for querying the 1Finance knowledge base and company sites and blogs.")

    def _run(self, question: str, top_k:int = 5) -> dict:
        return {
            "knowledge_base": qdrant_tool(question, top_k),
            # "1f_sites": WebTrustedSearchTool()._run(
            # query=question, trust=False, read_content=True, top_k=5, onef_search=True)
        }

# Initialize the tool instance
kb_qdrant_tool = QdrantTool()