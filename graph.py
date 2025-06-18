from langgraph.graph import StateGraph, END
from typing import Dict, Any, Callable
from utils.utils import remove_links, get_openai_llm, convert_to_json
from tools.web_search.web_search import WebTrustedSearchTool
from tools.qdrant_tool import kb_qdrant_tool
from tools.scrape_website_tool import ScrapeWebsiteTool
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from prompts.prfaq import CONTENT_GENERATION_PROMPT, QUESTION_GENERATION_PROMPT, ANSWER_GENERATION_PROMPT
from datetime import datetime

# --- LangGraph Shared State ---
State = Dict[str, Any]

def stream_thinking_step(state: State, step: str, detail: str, streaming_callback: Callable = None) -> None:
    """
    Stream the current thinking step to frontend with AI-generated sub-steps.
    """
    llm = get_openai_llm()
    
    # Generate thinking steps based on the current function
    step_prompt = f"""
    As an AI assistant working on: {detail}
    Share 3 natural thoughts about what you need to do next. For example:
    "First, I'll gather all the relevant information"
    "Then I need to analyze the key points"
    "Finally, I'll organize everything into a clear structure"
    
    Keep responses casual and natural. Just share the thoughts without any prefixes or formatting.
    """     
    thinking_steps = llm.invoke(step_prompt).content.split(",")

    #print(f"raw response----- {thinking_steps}")

    # Clean up and filter empty lines
    thinking_steps = [
        t.strip().strip('"').strip("'")
        for t in thinking_steps 
        if t.strip() and not t.startswith(("-", "*", "•", "1.", "2.", "3."))
    ]

    #print(f"cleaned response----- {thinking_steps}")

    # Join into a single string with newline separators
    detail_text = "\n".join(thinking_steps)

    thinking_data = {
        "step": step, 
        "detail": detail_text
    }

    if "thinking_steps" not in state:
        state["thinking_steps"] = []
    state["thinking_steps"].append(thinking_data)

    if streaming_callback:
        streaming_callback(thinking_data)

# --- Node Functions (Tasks) ---

def kb_retrieval_node(state: State, streaming_callback) -> State:
    stream_thinking_step(state, "kb_retrieval", "Retrieving relevant knowledge base information...", streaming_callback)

    llm = get_openai_llm()
    topic = state.get("topic", "Default Topic")
    problem = state.get("problem", "Default Problem")
    solution = state.get("solution", "Default Solution")

    query = f"Retrieve all information about {topic}. The problem is: {problem}. The proposed solution is: {solution}."
    logging.info(f"KB Query: {query}")
    kb_content = kb_qdrant_tool.run(question=query, top_k=10)
    stream_thinking_step(state, "kb_retrieval", "Parsing and extracting key info from KB content...", streaming_callback)

    prompt = f"Extract key info from the following knowledge base content on '{topic}', problem statement '{problem}' and solution '{solution}':\n{kb_content}"
    extracted = llm.invoke(prompt)
    print(f"\n\nExtracted KB Content: {extracted.content}")
    return {**state, "kb_content": extracted.content}


def web_scrape_node(state: State, streaming_callback) -> State:
    stream_thinking_step(state, "web_scrape", "Scraping provided web links and extracting key info...", streaming_callback)
    llm = get_openai_llm()
    web_scraping_links = state.get("web_scraping_links", [])
    if not web_scraping_links:
        return {**state, "web_scrape_content": "No web link provided"}
    
    scrape_results = {}
    for link in web_scraping_links:
        try:
            scraper = ScrapeWebsiteTool()
            result = remove_links(scraper.run(website_url=link))
            scrape_results[link] = result
        except Exception:
            scrape_results[link] = "Error occurred during scraping"
    topic = state.get("topic", "Default Topic")
    problem = state.get("problem", "Default Problem")
    solution = state.get("solution", "Default Solution")
    stream_thinking_step(state, "web_scrape", f"Extracting info from scraped content...", streaming_callback)
    prompt = f"Extract key info from the following scraped web content on '{topic}', problem statement '{problem}' and solution '{solution}':\n{scrape_results}"
    extracted = llm.invoke(prompt)
    print(f"\n\nExtracted Web Scrape Content: {extracted.content}")
    return {**state, "web_scrape_content": extracted.content}


def extract_info_node(state: State, streaming_callback) -> State:
    stream_thinking_step(state, "extract_info", "Extracting info from reference document...", streaming_callback)
    llm = get_openai_llm()
    reference_doc = state.get("reference_doc_content", "")
    topic = state.get("topic", "Default Topic")
    problem = state.get("problem", "Default Problem")
    solution = state.get("solution", "Default Solution")
    prompt = f"Extract key info from the following scraped web content on '{topic}', problem statement '{problem}' and solution '{solution}':\n{reference_doc}"
    extracted = llm.invoke(prompt)
    print(f"\n\nExtracted Reference Document Content: {extracted.content}")
    return {**state, "extracted_reference_doc_content": extracted.content}


def generate_content_node(state: State, streaming_callback) -> State:
    stream_thinking_step(state, "generate_content", "Generating PR/FAQ content leveraging all available information...", streaming_callback)
    llm = get_openai_llm()
    topic = state.get("topic")
    problem = state.get("problem")
    solution = state.get("solution")
    chat_history = state.get("chat_history", ["Generate this PR/FAQ for me"])

    kb_content = state.get("kb_content", "")
    web_scrape_content = state.get("web_scrape_content", "")
    reference_doc_content = state.get("extracted_reference_doc_content", "")
    query=llm.invoke(f"""Provided you with the topic {topic}, problem statement {problem} and a solution {solution}.
                        Your task is to generate a single, concise, and keyword-rich search query that can be used by a web search tool to discover similar or competing products or services in the market.
                        The query must:
                        - Understand the topic, problem, and solution.
                        - Reflect the real functionality described in the solution.
                        - Use practical, discoverable keywords people would actually search.
                        - Form a focused, real-world query like one a user would type into Google to find competitors or alternatives.
                        - Be specific enough to surface tools or services addressing the same use case.
                        Return only the search query string. Do not include explanations, extra formatting, or labels.
                     
                        ### Just an example, the input can vary:

                        **Input:**
                        Topic: Doculocker  
                        Problem Statement: To implement a document moderation system to ensure uploaded documents are free from adult, illegal, or inappropriate content. The system will analyze both images and embedded text to maintain compliance and uphold a safe, trustworthy platform for financial document handling.  
                        Solution: Develop a solution that automatically verifies whether an uploaded document — Word (doc/docx) and Excel (csv/xlsx) — is free from unsafe content, including but not limited to adult, illegal, violent, hateful, discriminatory, or offensive material. The system will analyze both images and embedded text to accurately classify documents as safe or flag them for further review, ensuring compliance and maintaining a standard of trust and safety on the platform.

                        **EXPECTED QUERY OUTPUT:**
                        Products/Services for detecting adult or violent content from images in Word and Excel documents using text and image moderation

                        **Why this query works:**
                        It leads to relevant services like:
                        - **Amazon Rekognition**
                        - **Google Cloud Vision API**
                        - **Microsoft Azure Content Moderator**
                        """)
    
    print(f"query for competitor-----------------{query.content}")
    web_tool = WebTrustedSearchTool()
    competitor_results = web_tool.run(query=query.content, trust=False,read_content=False, top_k=20, onef_search=False)

    prompt = CONTENT_GENERATION_PROMPT(topic, problem, solution, chat_history, reference_doc_content, web_scrape_content, kb_content, competitor_results)
    result = llm.invoke(prompt)
    result = convert_to_json(result.content)
    print(f"\n\nGenerated PR/FAQ Content: {result}")
    stream_thinking_step(state, "generate_content", "PR/FAQ introduction generated.", streaming_callback)
    return {**state, "generated_content": result}


def generate_questions_node(state: State, streaming_callback) -> State:
    stream_thinking_step(state, "generate_questions", "Generating exhaustive internal and external FAQ questions...", streaming_callback)
    llm = get_openai_llm()
    topic = state.get("topic")
    problem = state.get("problem")
    solution = state.get("solution")
    chat_history = state.get("chat_history", ["Generate this PR/FAQ for me"])
    prompt =   QUESTION_GENERATION_PROMPT(topic, problem, solution, chat_history)
    result = llm.invoke(prompt)
    result = convert_to_json(result.content)
    stream_thinking_step(state, "generate_questions", "Questions generated.", streaming_callback)
    return {**state, "faq_questions": result}

def save_tool_output(topic: str, problem: str, solution: str, results: list, internal_count: int) -> str:
    # Create tool_output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "tool_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean topic name for filename
    safe_topic = "".join(x for x in topic if x.isalnum() or x in (' ', '-', '_')).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_topic}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Topic: {topic}\n")
        f.write("="*50 + "\n\n")
        f.write(f"Problem Statement:\n{problem}\n")
        f.write("="*50 + "\n\n")
        f.write(f"Solution:\n{solution}\n")
        f.write("="*50 + "\n\n")
        
        # Internal Questions
        f.write("INTERNAL QUESTIONS\n")
        f.write("="*50 + "\n\n")
        for result in results[:internal_count]:
            f.write(f"Question: {result['question']}\n\n")
            f.write("Knowledge Base Results:\n")
            f.write(f"{result['kb_result']}\n\n")
            if result['web_result']:
                f.write("Web Search Results:\n")
                f.write(f"{result['web_result']}\n")
            f.write("-"*50 + "\n\n")
            
        # External Questions
        f.write("EXTERNAL QUESTIONS\n")
        f.write("="*50 + "\n\n")
        for result in results[internal_count:]:
            f.write(f"Question: {result['question']}\n\n")
            f.write("Knowledge Base Results:\n")
            f.write(f"{result['kb_result']}\n\n")
            if result['web_result']:
                f.write("Web Search Results:\n")
                f.write(f"{result['web_result']}\n")
            f.write("-"*50 + "\n\n")
    
    return filepath

def answer_faq_node(state: State, streaming_callback) -> State:
    stream_thinking_step(state, "answer_faqs", "Answering all generated FAQs using all available information...", streaming_callback)
    llm = get_openai_llm()
    questions = state.get("faq_questions", {})
    generated_content = state.get("generated_content", {})
    topic = state.get("topic")
    problem = state.get("problem")
    solution = state.get("solution")
    internal_q = questions.get("internal_questions", [])
    external_q = questions.get("external_questions", [])
    web_scrape_content = state.get("web_scrape_content", "")
    reference_doc_content = state.get("extracted_reference_doc_content", "")
    chat_history = state.get("chat_history", ["Generate this PR/FAQ for me"])
    
    web_tool = WebTrustedSearchTool()
    kb_tool = kb_qdrant_tool

    max_workers = int(os.getenv('THREAD_POOL_WORKERS', 12))

    def process_question(question, topic, use_websearch):
        full_question = question + f" in the context of {topic}"
        kb_result = kb_tool.run(full_question)
        web_result = None
        if use_websearch:
            web_result = web_tool.run(
                query=full_question,
                trust=True,
                read_content=False,
                top_k=5,
                onef_search=False
            )
        return {
            "question": question,
            "kb_result": kb_result,
            "web_result": web_result
        }
    
    # Process internal_questions preserving order
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        internal_futures = [
            executor.submit(process_question, q, topic, state.get("use_websearch", False))
            for q in internal_q
        ]
        internal_results = [future.result() for future in internal_futures]
        print(f"Internallll result---{internal_results}")            ################
        
    # Process external_questions preserving order
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        external_futures = [
            executor.submit(process_question, q, topic, state.get("use_websearch", False))
            for q in external_q
        ]
        external_results = [future.result() for future in external_futures]
        print(f"Externallll result---{external_results}")                ####################

     # Save results to file with internal question count
    all_results = internal_results + external_results
    output_file = save_tool_output(
        topic=topic,
        problem=problem,
        solution=solution,
        results=all_results,
        internal_count=len(internal_results)  # Pass count of internal questions
    )
    print(f"\nTool output saved to: {output_file}")

    # Debug printing for processed questions
    for result in internal_results + external_results:
        print(f"\n\nProcessed Question: {result['question']}")
        print(f"-----------Knowledge Base Results:-----------\n {result['kb_result']}")
        print(f"-----------Web Search Results:-----------\n {result['web_result']}")

    # Pass the processed FAQs separated into internal and external sections to the prompt
    prompt = ANSWER_GENERATION_PROMPT(
        topic, problem, solution, chat_history,
        {"internal_questions": internal_results, "external_questions": external_results},
        web_scrape_content, reference_doc_content
    )

    response = llm.invoke(prompt)
    print(f"FAQ RAW LLM--------------------{response.content}")               #################################
    response = convert_to_json(response.content)
    stream_thinking_step(state, "answer_faqs", "PRFAQ generated!", streaming_callback)
    
    prfaq = {
        **state,
        "Title": generated_content.get("Title", ""),
        "Subtitle": generated_content.get("Subtitle", ""),
        "IntroParagraph": generated_content.get("IntroParagraph", ""),
        "ProblemStatement": generated_content.get("ProblemStatement", ""),
        "Solution": generated_content.get("Solution", ""),
        "Competitors": generated_content.get("Competitors", []),
        "InternalFAQs": response.get("InternalFAQs", ""),
        "ExternalFAQs": response.get("ExternalFAQs", ""),
        "UserResponse": response.get("UserResponse", "Here is the generated PR/FAQ document on topic and your provided inputs. Please review and let me know if any changes are needed")
    }
    return prfaq

# --- LangGraph Workflow ---
def start_langgraph(inputs, streaming_callback):
    builder = StateGraph(State)
    # Wrapper for injecting streaming callback into nodes
    def wrap(fn):
        return lambda state: fn(state, streaming_callback)

    builder.add_node("kb_retrieval", wrap(kb_retrieval_node))

    if inputs.get("web_scraping_links", ""):
        builder.add_node("web_scrape", wrap(web_scrape_node))
        builder.add_edge("kb_retrieval", "web_scrape")
        last_task = "web_scrape"
    else:
        last_task = "kb_retrieval"

    if inputs.get("reference_doc_content", ""):
        builder.add_node("extract_info", wrap(extract_info_node))
        builder.add_edge(last_task, "extract_info")
        last_task = "extract_info"

    builder.add_node("generate_content", wrap(generate_content_node))
    builder.add_edge(last_task, "generate_content")

    builder.add_node("generate_questions", wrap(generate_questions_node))
    builder.add_edge("generate_content", "generate_questions")

    builder.add_node("answer_faqs", wrap(answer_faq_node))
    builder.add_edge("generate_questions", "answer_faqs")

    builder.set_entry_point("kb_retrieval")
    builder.add_edge("answer_faqs", END)

    workflow = builder.compile()
    final_output = workflow.invoke(inputs, config={"streaming_callback": None})
    return final_output

def print_streaming_callback(data):
    print(f"[STEP] {data['step']}: {data['detail']}")
