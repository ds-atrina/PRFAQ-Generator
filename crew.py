import json
import os
import logging
from openai import OpenAI
from typing import Dict, Any
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
from utils import remove_links, get_openai_llm
from crewai_tools import ScrapeWebsiteTool, WebsiteSearchTool
# from brave_search_tool import BraveSearchTool
from searxng_search import SearxNGTrustedSearchTool
from whitelisted_sites import whitelisted_domain_list, whitelisted_site_list
from qdrant_tool import kb_qdrant_tool 
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define Pydantic models for structured outputs
class KBContent(BaseModel):
    kb_content: str

# Define Pydantic models for structured outputs
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
    CustomerProblems: str
    Solution: str
    LeadersQuote: str
    CustomerQuotes: list
    GettingStarted: str
    InternalFAQs: list
    ExternalFAQs: list

@CrewBase
class PRFAQGeneratorCrew:
    """PR FAQ Generator Crew"""

    def __init__(self, inputs: Dict[str, Any]):
        self.topic = inputs.get('topic')
        self.problem = inputs.get('problem')
        self.solution = inputs.get('solution')
        self.content = inputs.get('content', "Default content")
        self.context = inputs.get('context', "Default context")
        self.reference_doc_content = inputs.get('reference_doc_content', '')
        self.web_scraping_links = inputs.get('web_scraping_links', '')
        self.use_websearch = inputs.get('use_websearch',True)
        self.inputs = inputs
        self.whitelisted_domain_list = whitelisted_domain_list

        # self.web_search_tool = BraveSearchTool(api_key=os.getenv("BRAVE_API_KEY"))
        self.web_search_tool = SearxNGTrustedSearchTool()
        # self.web_rag_tool = WebsiteSearchTool()

    @agent
    def kb_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['kb_agent'],
            verbose=True,
            tools=[kb_qdrant_tool],  
            llm= get_openai_llm()
        )

    @agent
    def web_search_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['web_search_agent'],
            verbose=True,
            tools=[self.web_search_tool],  # Use the wrapped tool instance
            llm= get_openai_llm()
        )

    @agent
    def web_scrape_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['web_scrape_extractor'],
            verbose=True,
            tools=[ScrapeWebsiteTool()],
            llm= get_openai_llm()
        )

    @agent
    def extract_info_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['extract_info_agent'],
            verbose=True,
            llm= get_openai_llm()
        )

    @agent
    def content_generation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['content_generation_agent'],
            verbose=True,
            llm= get_openai_llm()
        )

    @agent
    def faq_generation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['faq_generation_agent'],
            verbose=True,
            # tools=[kb_qdrant_tool],
            llm= get_openai_llm()
        )
    
    @task
    def kb_retrieval_task(self) -> Task:
        def task_logic(inputs):
            # Extract inputs
            topic = inputs.get("topic", "Default Topic")
            problem = inputs.get("problem", "Default Problem")
            solution = inputs.get("solution", "Default Solution")

            # Construct the query
            query = f"Retrieve information about {topic}. The problem is: {problem}. The proposed solution is: {solution}."
            logging.info(f"Constructed query for KB: {query}")

            # Use the Qdrant tool to search the knowledge base
            kb_response = kb_qdrant_tool(question=query)

            return {"kb_content": kb_response}

        return Task(
            config=self.tasks_config['kb_retrieval_task'],
            logic=task_logic,
            output_pydantic=KBContent 
        )
    
    # @task
    # def web_search_task(self) -> Task:
    #     def task_logic(inputs):
    #         # Extract inputs
    #         product_name = inputs.get("product_name", "Default Product")
    #         product_context = inputs.get("product_context", "Default Context")
    #         topic = inputs.get("topic", "Default Topic")
    #         problem = inputs.get("problem", "Default Problem")
    #         solution = inputs.get("solution", "Default Solution")

    #         # Construct the query based on the product name and its context
    #         query = (
    #             f"Gather information related to {product_name}. "
    #             f"The product focuses on {product_context}. "
    #             f"We are investigating {topic} to address {problem} using {solution}. "
    #             "Search for trusted data sources, relevant regulations, and industry best practices."
    #         )

    #         # Use the Brave Search Tool to search within the whitelisted websites
    #         web_search_response = self.web_search_tool.run(
    #             search_query=query,
    #             topic=topic,
    #             problem=problem,
    #             solution=solution
    #         )

    #         # Return the response
    #         return {
    #             "web_search_response": web_search_response
    #         }

    #     return Task(
    #         config=self.tasks_config['web_search_task'],
    #         logic=task_logic,
    #         tools=[self.web_search_tool]  # Use the BraveSearchTool
    #     )

    @task
    def web_search_task(self) -> Task:
        def task_logic(inputs):
            # Extract inputs
            topic = inputs.get("topic", "Default Topic")
            problem = inputs.get("problem", "Default Problem")
            solution = inputs.get("solution", "Default Solution")
            
            # Construct the query
            # query = f"We plan to make {topic}. We are trying to solve {problem} using {solution}. Gather any latest, relevant information about this."

            # Use the RAG tool to search within the whitelisted websites
            web_rag_response = self.web_search_tool.run(topic=topic, problem=problem, solution=solution)

            return {
                "web_rag_response": web_rag_response
            }

        return Task(
            config=self.tasks_config['web_search_task'],
            logic=task_logic,
            tools=[self.web_search_tool]  # Only the RAG tool is needed
        )

    @task
    def web_scrape_extraction_task(self) -> Task:
        def task_logic(inputs):
            web_scraping_links = inputs.get("web_scraping_links", "").strip()

            if not web_scraping_links:
                return {"web_scrape_content": "No web link provided"}

            links = [link.strip() for link in web_scraping_links.split(',')]
            scrape_results = {}

            for idx, link in enumerate(links):
                try:
                    scrape_website_tool = ScrapeWebsiteTool(website_url=link)
                    raw_result = scrape_website_tool.run()
                    result = remove_links(raw_result)
                    web_scrape_extractor_agent = self.web_scrape_extractor()
                    extracted_info = web_scrape_extractor_agent.execute(task_inputs={"content": result})
                    scrape_results[link] = extracted_info if extracted_info else "Failed to summarize content"
                except Exception as e:
                    scrape_results[link] = "Error occurred during scraping or extraction"

            return {"web_scrape_content": scrape_results}

        return Task(
            config=self.tasks_config['web_scrape_extraction_task'],
            logic=task_logic,
            output_pydantic=ScrapedContent
        )


    @task
    def extract_info_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get('topic', 'Default Topic')
            reference_doc_content = inputs.get('reference_doc_content', '')

            extract_info_agent = self.extract_info_agent()
            extracted_info = extract_info_agent.execute(task_inputs={"topic": topic, "reference_doc_content": reference_doc_content})

            return {"extracted_reference_doc_content": extracted_info}

        return Task(
            config=self.tasks_config['extract_info_task'],
            logic=task_logic,
            output_pydantic=ExtractedInfo
        )

    @task
    def content_generation_task(self) -> Task:
        def task_logic(inputs):
            
            topic= inputs.get('topic', 'Default Topic'),
            context= inputs.get('context', 'Default Context'),
            problem= inputs.get('problem', 'Default Problem'),
            solution= inputs.get('solution', 'Default Solution'),
            # reference_document= inputs.get('extracted_reference_doc_content', ''),
            # scraped_content= inputs.get('web_scrape_content', 'No scraped content')

            agent = self.content_generation_agent()
            content = agent.execute(task_inputs={"topic":topic, "context":context, "problem":problem, "solution":solution})

            return {"generated_content": content}

        return Task(
            config=self.tasks_config['content_generation_task'],
            logic=task_logic,
            output_pydantic=GeneratedContent,
            context=[self.kb_retrieval_task(), self.web_search_task(), self.web_scrape_extraction_task(), self.extract_info_task()]
        )

    @task
    def faq_generation_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get('topic', 'Default Topic')

            # Generate FAQs using the agent
            faq_agent = self.faq_generation_agent()
            internal_faqs = faq_agent.execute(task_inputs={"query": f"Generate internal FAQs for topic: {topic}"})
            external_faqs = faq_agent.execute(task_inputs={"query": f"Generate external FAQs for topic: {topic}"})

            return {
                "Title": content_json.get("Title", ""),
                "Subtitle": content_json.get("Subtitle", ""),
                "IntroParagraph": content_json.get("IntroParagraph", ""),
                "Solution": content_json.get("Solution", ""),
                "LeadersQuote": content_json.get("LeadersQuote", ""),
                "CustomerQuotes": content_json.get("CustomerQuotes", []),
                "GettingStarted": content_json.get("GettingStarted", ""),
                "InternalFAQs": json.loads(internal_faqs) if internal_faqs else [],
                "ExternalFAQs": json.loads(external_faqs) if external_faqs else []
            }

        return Task(
            config=self.tasks_config['faq_generation_task'],
            #tools=[kb_qdrant_tool],
            logic=task_logic,
            output_pydantic=FAQ,
            context=[self.kb_retrieval_task(), self.web_search_task(), self.content_generation_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PR FAQ Generator crew"""
        list_agents = [self.kb_agent(), self.web_search_agent(), self.web_scrape_extractor(), self.extract_info_agent(), self.content_generation_agent(), self.faq_generation_agent()]
        list_tasks = [self.kb_retrieval_task(), self.web_search_task(), self.web_scrape_extraction_task(), self.extract_info_task(), self.content_generation_task(), self.faq_generation_task()]
        if not self.use_websearch:
            list_agents.remove(self.web_search_agent())
            list_tasks.remove(self.web_search_task())
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
