from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, List, Type
from qdrant_tool import kb_qdrant_tool
from web_search import WebTrustedSearchTool  
from concurrent.futures import ThreadPoolExecutor
import logging
import os

# Define the input schema
class ContextFusionInputSchema(BaseModel):
    internal: List[str] = Field(..., description="List of internal questions.")
    external: List[str] = Field(..., description="List of external questions.")
    use_websearch: bool = Field(False, description="Whether to use web search or not")
    topic: str = Field("", description="The topic or the name of the product required to answer the questions in context of.")

class ContextFusionTool(BaseTool):
    name: str = "Context Fusion Tool"
    description: str = (
        "Fetch relevant context for questions by combining web search and "
        "internal KB results into a single, context-rich, markdown formatted string per question."
    )
    args_schema: Type[BaseModel] = ContextFusionInputSchema

    def _run(self, internal: List[str], external:List[str], use_websearch:bool, topic: str) -> str:
        """
        Fetch context for each question in 'internal' and 'external' lists.

        Args:
            inputs (Dict[str, List[str]]): A dictionary with 'internal' and 'external' question lists.

        Returns:
            str: A context-rich string grouped by question.
        """

        def get_context_for_question(question: str, use_websearch:bool, topic: str) -> str:
            try:
                kb_context = kb_qdrant_tool.run(question+f" in the context of {topic}", 3)
                if use_websearch:
                    web_context = WebTrustedSearchTool().run(query=question, trust=True, read_content=False, top_k=5)
                    return (
                    f"Question: {question}\n"
                    f"--- Internal KB Results ---\n{kb_context}\n"
                    f"--- Web Search Results ---\n{web_context}\n"
                )
                else:
                    return (
                        f"Question: {question}\n"
                        f"--- Internal KB Results ---\n{kb_context}\n"
                    )
            except Exception as e:
                return f"Question: {question}\nError fetching context: {str(e)}"

        all_questions = internal + external

        results = []
        with ThreadPoolExecutor(max_workers=os.getenv('THREAD_POOL_WORKERS', 12)) as executor:
            futures = [executor.submit(get_context_for_question, q, use_websearch, topic) for q in all_questions]
            for future in futures:
                results.append(future.result())
                logging.info(f"Processed question: {future.result()}")

        return "\n\n".join(results)