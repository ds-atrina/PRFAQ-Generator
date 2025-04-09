import os
import json
import logging
from typing import Dict, Any
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel

from knowledge_base import CompanyKnowledgeBase
from utils import remove_links
from crewai_tools import ScrapeWebsiteTool
from kb_tool import KnowledgeBaseTool

# Configure logging
logging.basicConfig(level=logging.INFO)

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
        self.knowledge_base = CompanyKnowledgeBase('vector_store/')
        self.topic = inputs.get('topic')
        self.problem = inputs.get('problem')
        self.solution = inputs.get('solution')
        self.content = inputs.get('content', "Default content")
        self.context = inputs.get('context', "Default context")
        self.reference_doc_content = inputs.get('reference_doc_content', [])
        self.web_scraping_links = inputs.get('web_scraping_links', '')
        self.inputs = inputs
        self.custom_llm = LLM(
            model="o3-mini",  # Specify the model name
            reasoning_effort = "medium",
            temperature=0.6,        
            seed=42
        )

    @agent
    def web_scrape_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['web_scrape_extractor'],
            verbose=True,
            tools=[ScrapeWebsiteTool()],
            llm= self.custom_llm
        )

    @agent
    def extract_info_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['extract_info_agent'],
            verbose=True,
            llm= self.custom_llm
        )

    @agent
    def content_generation_agent(self) -> Agent:
        kb_tool = KnowledgeBaseTool(knowledge_base=self.knowledge_base)
        return Agent(
            config=self.agents_config['content_generation_agent'],
            verbose=True,
            tools=[kb_tool],
            llm= self.custom_llm
        )

    @agent
    def faq_generation_agent(self) -> Agent:
        kb_tool = KnowledgeBaseTool(knowledge_base=self.knowledge_base)
        return Agent(
            config=self.agents_config['faq_generation_agent'],
            verbose=True,
            tools=[kb_tool],
            llm= self.custom_llm
        )

    @task
    def web_scrape_extraction_task(self) -> Task:
        def task_logic(inputs):
            web_scraping_links = inputs.get("web_scraping_links", "").strip()

            # If no link is provided, return a default output and skip tool execution.
            if not web_scraping_links:
                return {"web_scrape_content": "No web link provided"}

            # Split links by comma and strip any extra spaces.
            links = [link.strip() for link in web_scraping_links.split(',')]
            
            # Initialize an empty dictionary to store results.
            scrape_results = {}
            
            # Process each link separately.
            for idx, link in enumerate(links):
                try:
                    # logging.info(f"Scraping URL {idx + 1}: {link}")
                    scrape_website_tool = ScrapeWebsiteTool(website_url=link)
                    raw_result = scrape_website_tool.run()
                    
                    # Clean up the result.
                    result = remove_links(raw_result)
                    
                    # Use the extractor agent to summarize.
                    web_scrape_extractor_agent = self.web_scrape_extractor()
                    extracted_info = web_scrape_extractor_agent.execute(task_inputs={"content": result})
                    
                    # Store the result.
                    scrape_results[link] = extracted_info if extracted_info else "Failed to summarize content"
                except Exception as e:
                    # logging.error(f"Error processing URL {link}: {e}")
                    scrape_results[link] = "Error occurred during scraping or extraction"

            return {
                "web_scrape_content": scrape_results
            }

        return Task(
            config=self.tasks_config['web_scrape_extraction_task'],
            logic=task_logic,
            output_pydantic=ScrapedContent
        )


    @task
    def extract_info_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get('topic', 'Default Topic')
            reference_doc_content = inputs.get('reference_doc_content', [])

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
            kb_tool = KnowledgeBaseTool(knowledge_base=self.knowledge_base)
            content = agent.execute(task_inputs={"topic":topic, "context":context, "problem":problem, "solution":solution})

            return {"generated_content": content}

        return Task(
            config=self.tasks_config['content_generation_task'],
            logic=task_logic,
            tools=[KnowledgeBaseTool(knowledge_base=self.knowledge_base)],
            output_pydantic=GeneratedContent,
            context=[self.web_scrape_extraction_task(), self.extract_info_task()]
        )

    @task
    def faq_generation_task(self) -> Task:
        def task_logic(inputs):
            topic = inputs.get('topic', 'Default Topic')
            content_str = inputs.get('generated_content', '').strip().strip("```json").strip("```").strip()

            try:
                content_json = json.loads(content_str)
            except json.JSONDecodeError:
                return {"error": "Generated content is not valid JSON"}

            extracted_content = {
                "IntroParagraph": content_json.get("IntroParagraph", ""),
                "CustomerProblems": content_json.get("CustomerProblems", ""),
                "Solution": content_json.get("Solution", "")
            }

            generated_content = json.dumps(extracted_content)

            # Generate FAQs using the agent
            faq_agent = self.faq_generation_agent()
            kb_tool = KnowledgeBaseTool(knowledge_base=self.knowledge_base)
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
            tools=[KnowledgeBaseTool(knowledge_base=self.knowledge_base)],
            logic=task_logic,
            output_pydantic=FAQ,
            context=[self.content_generation_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PR FAQ Generator crew"""
        # if not self.reference_doc_content and not self.:
        list_agents = [self.web_scrape_extractor(), self.extract_info_agent(), self.content_generation_agent(), self.faq_generation_agent()]
        list_tasks = [self.web_scrape_extraction_task(), self.extract_info_task(), self.content_generation_task(), self.faq_generation_task()]
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
            # verbose=True
        )
