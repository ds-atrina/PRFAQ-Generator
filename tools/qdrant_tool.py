import os
import requests
from tools.web_search.web_search import WebTrustedSearchTool

class QdrantTool:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("QDRANT_TOOL_API_URL") or "https://dev-aion.onefin.app/api/v1/tools/qdrant"

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
    
