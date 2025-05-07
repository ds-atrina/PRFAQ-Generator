import json
import os
import logging
from langchain_openai import ChatOpenAI
from typing import Dict, Any
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
from utils import remove_links, get_openai_llm
from crewai_tools import ScrapeWebsiteTool, WebsiteSearchTool
from web_search import WebTrustedSearchTool
from whitelisted_sites import whitelisted_domain_list, whitelisted_site_list
from qdrant_tool import kb_qdrant_tool
from context_fusion_tool import ContextFusionTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define Pydantic models for structured outputs
class KBContent(BaseModel):
    kb_content: str

class ExtractedInfo(BaseModel):
    extracted_reference_doc_content: str

class ScrapedContent(BaseModel):
    web_scrape_content: str

class GeneratedContent(BaseModel):
    generated_content: str

class FAQ(BaseModel):
    Title: str
    Subtitle: str
    IntroParagraph: str
    ProblemStatement: str
    Solution: str
    Competitors: list
    InternalFAQs: list
    ExternalFAQs: list
    UserResponse: str

class FAQQuestions(BaseModel):
    internal_questions: list
    external_questions: list

@CrewBase
class PRFAQGeneratorCrew:
    """PR FAQ Generator Crew"""

    def __init__(self, inputs: Dict[str, Any]):
        self.topic = inputs.get("topic")
        self.problem = inputs.get("problem")
        self.solution = inputs.get("solution")
        self.chat_history = inputs.get("chat_history", [""])
        self.reference_doc_content = inputs.get("reference_doc_content", "")
        self.web_scraping_links = inputs.get("web_scraping_links", "")
        self.use_websearch = inputs.get("use_websearch", False)
        self.inputs = inputs
        self.whitelisted_domain_list = whitelisted_domain_list
        self.web_search_tool = WebTrustedSearchTool()

    @agent
    def kb_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["kb_agent"],
            verbose=True,
            tools=[kb_qdrant_tool],
            llm=get_openai_llm()
        )

    @agent
    def web_scrape_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config["web_scrape_extractor"],
            verbose=True,
            tools=[ScrapeWebsiteTool()],
            llm=get_openai_llm()
        )

    @agent
    def extract_info_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["extract_info_agent"],
            verbose=True,
            llm=get_openai_llm()
        )

    @agent
    def content_generation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["content_generation_agent"],
            verbose=True,
            tools=[self.web_search_tool],
            llm=get_openai_llm()
        )

    @agent
    def faq_question_generator(self) -> Agent:
        return Agent(
            config=self.agents_config["faq_question_generator"],
            verbose=True,
            llm=get_openai_llm()
        )

    @agent
    def faq_answer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["faq_answer_agent"],
            verbose=True,
            llm=get_openai_llm()
        )

    @task
    def kb_retrieval_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get("topic", "Default Topic")
            problem = inputs.get("problem", "Default Problem")
            solution = inputs.get("solution", "Default Solution")

            query = f"Retrieve all information about {topic}. The problem is: {problem}. The proposed solution is: {solution}."
            logging.info(f"Constructed query for KB: {query}")

            kb_response = kb_qdrant_tool(question=query, top_k=7)
            return {"kb_content": kb_response}

        return Task(
            config=self.tasks_config["kb_retrieval_task"],
            logic=task_logic,
            output_pydantic=KBContent
        )

    @task
    def web_scrape_extraction_task(self) -> Task:
        def task_logic(inputs):
            web_scraping_links = inputs.get("web_scraping_links", "").strip()
            if not web_scraping_links:
                return {"web_scrape_content": "No web link provided"}

            links = [link.strip() for link in web_scraping_links.split(",")]
            scrape_results = {}
            for link in links:
                try:
                    scrape_website_tool = ScrapeWebsiteTool(website_url=link)
                    raw_result = scrape_website_tool.run()
                    result = remove_links(raw_result)
                    scrape_results[link] = result
                except Exception as e:
                    scrape_results[link] = "Error occurred during scraping"

            return {"web_scrape_content": scrape_results}

        return Task(
            config=self.tasks_config["web_scrape_extraction_task"],
            logic=task_logic,
            output_pydantic=ScrapedContent
        )

    @task
    def extract_info_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get("topic", "Default Topic")
            reference_doc_content = inputs.get("reference_doc_content", "")

            extract_info_agent = self.extract_info_agent()
            extracted_info = extract_info_agent.execute(task_inputs={"topic": topic, "reference_doc_content": reference_doc_content})

            return {"extracted_reference_doc_content": extracted_info}

        return Task(
            config=self.tasks_config["extract_info_task"],
            logic=task_logic,
            output_pydantic=ExtractedInfo
        )

    @task
    def content_generation_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get("topic", "Default Topic")
            problem = inputs.get("problem", "Default Problem")
            solution = inputs.get("solution", "Default Solution")
            chat_history = inputs.get("chat_history", [""])

            agent = self.content_generation_agent()
            content = agent.execute(task_inputs={"topic": topic, "problem": problem, "solution": solution, "chat_history": chat_history})

            return {"generated_content": content}

        return Task(
            config=self.tasks_config["content_generation_task"],
            logic=task_logic,
            tools=[self.web_search_tool],
            output_pydantic=GeneratedContent,
            context=[self.kb_retrieval_task(), self.web_scrape_extraction_task(), self.extract_info_task()]
        )

    @task
    def generate_faq_questions_task(self) -> Task:
        def task_logic(inputs):
            chat_history = inputs.get("chat_history", [""])
            faq_agent = self.faq_question_generator()
            question_json = faq_agent.execute(task_inputs={"chat_history": chat_history})
            return question_json

        return Task(
            config=self.tasks_config["generate_faq_questions_task"],
            logic=task_logic
        )

    @task
    def answer_faqs_with_context_task(self) -> Task:
        def task_logic(inputs):
            content_generation_json = inputs.get("content_generation_task", {})
            faq_questions_json = inputs.get("generate_faq_questions_task", {})

            if not faq_questions_json or \
               "internal_questions" not in faq_questions_json or \
               "external_questions" not in faq_questions_json:
                raise ValueError("Invalid input for FAQ questions. Ensure 'internal_questions' and 'external_questions' are present.")

            internalq = faq_questions_json.get("internal_questions", [])
            externalq = faq_questions_json.get("external_questions", [])


            context_tool = ContextFusionTool()
            context_results = context_tool.run({
                "internal": internalq,
                "external": externalq,
                "use_websearch": self.use_websearch,
                "topic": self.topic
            })


            internal_faqs, external_faqs = [], []
            for block in context_results.split("\n\n"):
                if not block.startswith("Question:"):
                    continue
                lines = block.split("\n")
                question = lines[0].replace("Question: ", "").strip()
                answer = "\n".join(lines[1:]).strip()
                entry = {"Question": question, "Answer": answer}
                if question in internalq:
                    internal_faqs.append(entry)
                else:
                    external_faqs.append(entry)

            return {
                "Title": content_generation_json.get("Title", ""),
                "Subtitle": content_generation_json.get("Subtitle", ""),
                "IntroParagraph": content_generation_json.get("IntroParagraph", ""),
                "ProblemStatement": content_generation_json.get("ProblemStatement", ""),
                "Solution": content_generation_json.get("Solution", ""),
                "Competitors": content_generation_json.get("Competitors", []),
                "InternalFAQs": internal_faqs,
                "ExternalFAQs": external_faqs,
                "UserResponse": (
                    "Here is the final PRFAQ with answers "
                    "generated using internal knowledge and recent updates."
                )
            }

        return Task(
            config=self.tasks_config["answer_faqs_with_context_task"],
            logic=task_logic,
            tools=[ContextFusionTool()],
            context=[self.extract_info_task(), self.web_scrape_extraction_task(), self.content_generation_task(), self.generate_faq_questions_task()]
        )

    @crew
    def crew(self) -> Crew:
        list_agents = [
            self.kb_agent(),
            self.web_scrape_extractor(),
            self.extract_info_agent(),
            self.content_generation_agent(),
            self.faq_question_generator(),
            self.faq_answer_agent()
        ]
        list_tasks = [
            self.kb_retrieval_task(),
            self.web_scrape_extraction_task(),
            self.extract_info_task(),
            self.content_generation_task(),
            self.generate_faq_questions_task(),
            self.answer_faqs_with_context_task()
        ]

        if not self.reference_doc_content:
            list_agents.remove(self.extract_info_agent())
            list_tasks.remove(self.extract_info_task())
        if not self.web_scraping_links:
            list_agents.remove(self.web_scrape_extractor())
            list_tasks.remove(self.web_scrape_extraction_task())

        return Crew(
            agents=list_agents,
            tasks=list_tasks,
            process=Process.sequential,
            verbose=True
        )