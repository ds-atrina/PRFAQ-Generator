import os
from functools import wraps
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance
from qdrant_client.http.models import PointStruct, VectorParams
import uuid
from crewai.tools import BaseTool

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
def qdrant_tool(question: str) -> str:
    """Useful to answer questions based on the 1Finance PDF knowledge base."""

    response = client.embeddings.create(
        input=question,
        model="text-embedding-ada-002"
    )
    embedding = response.data[0].embedding

    search_result = connection.query_points(
        collection_name="1finance_kb",
        query=embedding,
        limit=6,
        with_payload=True
    )

    return search_result

class QdrantTool(BaseTool):
    def __init__(self):
        super().__init__(name="QdrantTool", description="A tool for querying the 1Finance knowledge base.")

    def _run(self, question: str) -> str:
        return qdrant_tool(question)

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async execution is not supported for this tool.")

# Initialize the tool instance
kb_qdrant_tool = QdrantTool()