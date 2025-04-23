import io
import os
import docx
import json
import time
from utils import extract_text_from_pdf, render_text_or_table_to_str
from langchain_openai import ChatOpenAI
from crew import PRFAQGeneratorCrew
from searxng_search import SearxNGTrustedSearchTool
from qdrant_tool import kb_qdrant_tool

# Constants
MAX_FILES = 5
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def generate_prfaq(topic, problem, solution, reference_docs=None, web_scraping_links=None, use_websearch=False):
    """
    Function to generate PR FAQ using the Crew tool.

    Args:
        topic (str): Title of the PR FAQ
        problem (str): Problem statement
        solution (str): Solution description
        reference_docs (list): List of uploaded reference documents (PDF/DOCX) as file-like objects
        web_scraping_links (list): List of reference URLs
        use_websearch (bool): Whether to use web search in generation

    Returns:
        dict: Generated PR FAQ in JSON format
    """
    # Validate inputs
    if len(topic) < 3:
        raise ValueError("Title is too short. Please enter at least 3 characters.")
    if len(problem) < 20:
        raise ValueError("Problem is too short. Please enter at least 20 characters.")
    if len(solution) < 50:
        raise ValueError("Solution is too short. Please enter at least 50 characters.")
    if reference_docs and len(reference_docs) > MAX_FILES:
        raise ValueError(f"Too many files uploaded. Max allowed: {MAX_FILES}")
    if web_scraping_links and len(web_scraping_links) > 5:
        raise ValueError(f"Too many reference links. Max allowed: 5")
    
    # Process reference documents
    reference_doc_content = []
    if reference_docs:
        for reference_doc in reference_docs:
            content = ""
            file_extension = os.path.splitext(reference_doc.name)[1].lower()
            if file_extension == ".pdf":
                content += extract_text_from_pdf(reference_doc)
            elif file_extension == ".docx":
                doc = docx.Document(io.BytesIO(reference_doc.read()))
                content += "\n".join([para.text for para in doc.paragraphs])
            else:
                raise ValueError(f"Only PDF and DOCX files are allowed. {reference_doc.name} is not a valid type.")
            reference_doc_content.append(content)

    # Define inputs for PR FAQ generation
    inputs = {
        'topic': topic,
        'problem': problem,
        'solution': solution,
        'context': 'This is some default context.',
        'content': 'This is some default content.',
        'reference_doc_content': reference_doc_content,
        'web_scraping_links': web_scraping_links or [],
        'use_websearch': use_websearch
    }

    # Generate PR FAQ using Crew
    pr_faq_crew = PRFAQGeneratorCrew(inputs)
    crew_output = pr_faq_crew.crew().kickoff(inputs=inputs)
    cleaned_json = crew_output.raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed_output = json.loads(cleaned_json)
        return parsed_output
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse generated PR FAQ: {e}")

def modify_prfaq(existing_faq, user_feedback, problem, solution):
    """
    Function to modify an existing PR FAQ based on user feedback.

    Args:
        existing_faq (dict): Existing PR FAQ in JSON format
        user_feedback (str): Feedback from the user
        problem (str): Problem statement
        solution (str): Solution description

    Returns:
        dict: Updated PR FAQ in JSON format
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Generate refined query based on feedback
    refine_prompt = f"""
        The user provided the following feedback:
        "{user_feedback}"
        The current PR FAQ is based on the following:
        Problem statement: {problem}
        Solution: {solution}

        Based on this feedback and the given context, determine the most effective search query to put in a search engine to gather relevant and latest information.
        Avoid mentioning proper nouns or dates/years in the prompt, instead use words like "latest" and general key terms from the context.
        Return ONLY the refined search query without any additional text.
    """
    refined_query_response = llm.invoke(refine_prompt)
    refined_query = refined_query_response.content.strip()

    # Perform Web and Knowledge Base Search
    kb_tool = kb_qdrant_tool
    kb_response = kb_tool.run(refined_query)
    web_tool = SearxNGTrustedSearchTool()
    web_response = web_tool.search_with_query(refined_query)

    # Use results to modify the FAQ
    prompt = f"""
        You are an intelligent assistant tasked with modifying an existing PR FAQ based on user feedback.

        The PR FAQ is generated based on the following:
        - Problem statement: {problem}
        - Solution: {solution}

        User feedback:
        "{user_feedback}"

        A search was carried out for the feedback with the refined query:
        "{refined_query}"

        The web search returned the following results. Use this information to enhance the FAQ wherever relevant:
        "{web_response}"
        
        The knowledge base search returned the following results. Use this information to enhance the FAQ wherever relevant:
        "{kb_response}"

        Instructions:
        - Modify the PR FAQ comprehensively based on the user feedback.
        - Use relevant information from the search results or knowledge base to make appropriate changes or additions.
        - Ensure that any new information aligns with the problem statement and solution provided.
        - Use proper markdown-formatted tables in FAQs for any table requests by default, unless specified otherwise in the feedback.
        - Avoid vague responses like "I don't know" or "Not specified." Use the given context to derive meaningful answers or omit such points.
        - Assume any new feedback is a FAQ unless specified otherwise.
        - DO NOT CHANGE THE FORMATTING OR STRUCTURE OF THE EXISTING PR FAQ and return the updated PR FAQ in STRICT JSON format.

        Here is the existing PR FAQ:
        ```{existing_faq}```
    """
    response = llm.invoke(prompt)
    response_text = str(response.content).replace("```json", "").replace("```", "").strip()

    try:
        updated_faq = json.loads(response_text)
        return updated_faq
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse the updated PR FAQ: {e}")

generate_prfaq(
    topic="Sample Topic",
    problem="Sample Problemdkfhldsfklhkdsfhkdfhkdfkdfkfkdsfklds",
    solution="Sample ProblemdkfhldsfklhkdsfhkdfhkdfkdfkfkdsfkldsProblemdkfhldsfklhkdsfhkdfhkdfkdfkfkdsfklds",
    reference_docs=[],
    web_scraping_links=[],
    use_websearch=True
)