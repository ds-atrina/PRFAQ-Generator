from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field, PrivateAttr
from knowledge_base import CompanyKnowledgeBase

class KnowledgeBaseQuery(BaseModel):
    query: str = Field(..., description="The query string to search in the knowledge base.")

class KnowledgeBaseTool(BaseTool):
    name: str = "Knowledge Base Search Tool"
    description: str = "Retrieves information from the company's knowledge base using a query string."
    args_schema: Type[BaseModel] = KnowledgeBaseQuery
    _knowledge_base: CompanyKnowledgeBase = PrivateAttr()

    def __init__(self, knowledge_base: CompanyKnowledgeBase):
        super().__init__()
        self._knowledge_base = knowledge_base

    def _run(self, query: str) -> str:
        results = self._knowledge_base.similarity_search(query)
        # Process results to extract relevant information
        # For simplicity, returning the raw results
        return str(results)