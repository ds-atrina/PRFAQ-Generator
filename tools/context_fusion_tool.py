from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, List, Type
from tools.qdrant_tool import kb_qdrant_tool
from tools.web_search.web_search import WebTrustedSearchTool  
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import json
from langchain_openai import ChatOpenAI  
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

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

    def preprocess_questions_with_llm(self, question: str, topic: str) -> Dict[str, str]:
        """
        Use the LLM to generate search queries for both KB and web search.

        Args:
            question (str): The question to process.
            topic (str): The topic to provide context for.

        Returns:
            Dict[str, str]: A dictionary with keys 'kbsearchquery' and 'websearchquery'.
        """
        prompt = (
            f"You are an AI assistant. Given a question and a topic, decide whether the question requires "
            f"a web search. The company KB will be used to answer the question, you can suggest a query to search the web to suport or enhance the answer with quantitative or qualitative data from trusted sources. You can leave the query empty if not search is deemed necessary."
            f"Do not try to search for information about the company on the web. Just give a query that can help search the web for enhancing the answer to the given question.\n\n"
            f"Question: {question}\n"
            f"Topic: {topic}\n\n"
            f"Provide the output in this JSON format:\n"
            f"{{\"websearchquery\": \"<query for web>\"}}"
        )
        response = llm.invoke(prompt)
        response_text = str(response.content)
        response_text = response_text.replace("```json","").replace("```","").strip()
        response = json.loads(response_text)
        print(f"Question:{question}\nLLM Response: {response}")
        return response

    def _run(self, internal: List[str], external: List[str], use_websearch: bool, topic: str) -> str:
        """
        Fetch context for each question in 'internal' and 'external' lists.

        Args:
            internal (List[str]): List of internal questions.
            external (List[str]): List of external questions.
            use_websearch (bool): Whether to use web search or not.
            topic (str): The topic to provide context for.

        Returns:
            str: A context-rich string grouped by question.
        """
        def get_context_for_question(question: str, use_websearch: bool, topic: str) -> str:
            kb_context = kb_qdrant_tool.run(question+ f"in the context of {topic}", 3)
            if not use_websearch:
                return (
                    f"Question: {question}\n"
                    f"--- Internal KB Results ---\n{kb_context}\n"
                )
            try:
                # Preprocess the question using the LLM
                queries = self.preprocess_questions_with_llm(question, topic)
                web_query = queries.get("websearchquery", "")

                # Fetch context from web if enabled
                if web_query:
                    web_context = WebTrustedSearchTool().run(query=web_query, trust=True, read_content=False, top_k=5)
                    return (
                        f"Question: {question}\n"
                        f"--- Internal KB Results ---\n{kb_context}\n"
                        f"--- Web Search Results ---\n{web_context}\n"
                    )
            except Exception as e:
                web_context = WebTrustedSearchTool().run(query=question, trust=True, read_content=False, top_k=5)
                return (
                    f"Question: {question}\n"
                    f"--- Internal KB Results ---\n{kb_context}\n"
                    f"--- Web Search Results ---\n{web_context}\n"
                )

            return (
                f"Question: {question}\n"
                f"--- Internal KB Results ---\n{kb_context}\n"
            )

        all_questions = internal + external

        results = []
        with ThreadPoolExecutor(max_workers=os.getenv('THREAD_POOL_WORKERS', 12)) as executor:
            futures = [executor.submit(get_context_for_question, q, use_websearch, topic) for q in all_questions]
            for future in futures:
                results.append(future.result())
                logging.info(f"Processed question: {future.result()}")

        return "\n\n".join(results)