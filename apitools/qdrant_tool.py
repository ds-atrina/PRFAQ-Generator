import os
import requests
import openai
from tools.web_search.web_search import WebTrustedSearchTool

class QdrantTool:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("QDRANT_TOOL_API_URL") or "http://localhost:3000/api/v1/tools/qdrant"

    def run(self, question: str, top_k: int = 5) -> dict:
        
        try:
            web_tool = WebTrustedSearchTool()
            payload = {"question": question, "selectedDomains": web_tool.choose_onef_domains(question),"topK": top_k, "collectionName": "1F_KB_BASE_PF"}
            # print(payload)
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error calling QdrantTool API: {e}")
            return {"error": str(e)}

# Usage:
kb_qdrant_tool = QdrantTool()

if __name__ == "__main__":
    result = kb_qdrant_tool.run("What is the leave policy at 1Finance?")
    print(result)
    
# import os
# from openai import OpenAI
# from qdrant_client import QdrantClient
# from tools.web_search.web_search import WebTrustedSearchTool
# from tools.base_tool.base_tool import BaseTool
# from dotenv import load_dotenv

# import time
# import httpx 
# from qdrant_client.http.exceptions import ResponseHandlingException

# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# qdrant_url = os.environ.get("QDRANT_URL")
# connection = QdrantClient(url=qdrant_url, timeout=30)

# class QdrantTool(BaseTool):
#     def __init__(self):
#         super().__init__(name="QdrantTool", description="A tool for querying the 1Finance knowledge base and company sites and blogs.")
    
#     def qdrant_tool(self, question: str, top_k: int, max_retries: int = 3, base_delay: float = 2.0) -> dict:
#         """Useful to answer questions based on the 1Finance PDF knowledge base, with retries on timeout."""

#         # Create embedding for the question
#         response = client.embeddings.create(
#             input=question,
#             model="text-embedding-ada-002"
#         )
#         embedding = response.data[0].embedding

#         retries = 0
#         while retries < max_retries:
#             try:
#                 search_result = connection.query_points(
#                     collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
#                     query=embedding,
#                     limit=top_k,
#                     with_payload=True
#                 )
#                 return search_result

#             except (httpx.ReadTimeout, ResponseHandlingException) as e:
#                 print(f"Qdrant query timeout or error: {e}. Retrying {retries + 1}/{max_retries} ...")
#                 retries += 1
#                 sleep_time = base_delay * (2 ** (retries - 1))  # exponential backoff
#                 time.sleep(sleep_time)

#             except Exception as e:
#                 print(f"Unexpected error querying Qdrant: {e}")
#                 break

#         # After retries exhausted, return a fallback response or raise
#         print("Qdrant query failed after retries.")
#         return {"error": "Qdrant query failed after multiple attempts due to timeout or connectivity issues."}


#     def _run(self, question: str, top_k:int = 5) -> dict:
#         return {
#             "knowledge_base": self.qdrant_tool(question, top_k),
#             "1f_sites": WebTrustedSearchTool()._run(
#             query=question, trust=False, read_content=True, top_k=5, onef_search=True)
#         }

# # Initialize the tool instance
# kb_qdrant_tool = QdrantTool()