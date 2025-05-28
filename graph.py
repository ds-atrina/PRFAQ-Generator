from langgraph.graph import StateGraph, END
from typing import Dict, Any, Callable
from utils.utils import remove_links, get_openai_llm, convert_to_json
from tools.web_search.web_search import WebTrustedSearchTool
from tools.qdrant_tool import kb_qdrant_tool
from tools.context_fusion_tool import ContextFusionTool
from tools.scrape_website_tool import ScrapeWebsiteTool
import logging
from concurrent.futures import ThreadPoolExecutor
import os
from prompt.prfaq import CONTENT_GENERATION_PROMPT, QUESTION_GENERATION_PROMPT, ANSWER_GENERATION_PROMPT

# --- LangGraph Shared State ---
State = Dict[str, Any]

def stream_thinking_step(state: State, step: str, detail: str, streaming_callback: Callable = None) -> None:
    """
    Optionally stream the current thinking step to frontend via a callback.
    """
    thinking_data = {"step": step, "detail": detail}
    # Store for later (for tracing in the final state)
    if "thinking_steps" not in state:
        state["thinking_steps"] = []
    state["thinking_steps"].append(thinking_data)
    # Optionally stream it
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
    kb_content = kb_qdrant_tool._run(question=query, top_k=10)
    stream_thinking_step(state, "kb_retrieval", "Parsing and extracting key info from KB content...", streaming_callback)

    prompt = f"Extract key info from the following knowledge base content on '{topic}', problem statement '{problem}' and solution '{solution}':\n{kb_content}"
    extracted = llm.invoke(prompt)
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
            scraper = ScrapeWebsiteTool(website_url=link)
            result = remove_links(scraper.run())
            scrape_results[link] = result
        except Exception:
            scrape_results[link] = "Error occurred during scraping"
    topic = state.get("topic", "Default Topic")
    problem = state.get("problem", "Default Problem")
    solution = state.get("solution", "Default Solution")
    stream_thinking_step(state, "web_scrape", f"Extracting info from scraped content...", streaming_callback)
    prompt = f"Extract key info from the following scraped web content on '{topic}', problem statement '{problem}' and solution '{solution}':\n{scrape_results}"
    extracted = llm.invoke(prompt)
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
    query=llm.invoke(f"""Generate a query to find competitors for the topic {topic} solving the problem of {problem} with solution {solution}. 
                        Give only the query as output without any extra text. eg. competitors document moderation system financial document handling moderation images text safe compliance parser""")
    
    web_tool = WebTrustedSearchTool()
    competitor_results = web_tool._run(query=query.content, trust=False,read_content=False, top_k=20, onef_search=False)

    prompt = CONTENT_GENERATION_PROMPT(topic, problem, solution, chat_history, reference_doc_content, web_scrape_content, kb_content, competitor_results)
    result = llm.invoke(prompt)
    result = convert_to_json(result.content)
    print(f"Generated PR/FAQ Content: {result}")
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
    all_questions = internal_q + external_q

    results = []
    tool = ContextFusionTool()

    with ThreadPoolExecutor(max_workers=os.getenv('THREAD_POOL_WORKERS', 12)) as executor:
        futures = [executor.submit(tool._run, q+ f"in the context of {topic}", state.get("use_websearch", False)) for q in all_questions]
        for future in futures:
            results.append(future.result())
            logging.info(f"Processed question: {future.result()}")

    response= "\n\n".join(results)
    
    prompt = ANSWER_GENERATION_PROMPT(topic, problem, solution, chat_history, reference_doc_content, web_scrape_content, generated_content, response)
    response = llm.invoke(prompt)
    response = convert_to_json(response.content)
    stream_thinking_step(state, "answer_faqs", "PRFAQ generated!", streaming_callback)
    
    return {
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
    final_output = workflow.invoke(inputs)
    return final_output

def print_streaming_callback(data):
    print(f"[STEP] {data['step']}: {data['detail']}")

# === Run the graph ===

if __name__ == "__main__":
    inputs = {
        "topic": "Generative AI PR Tool",
        "problem": "Manual FAQ generation is slow",
        "solution": "Automated LangGraph-based generator",
        "reference_doc_content": "...",
        "web_scraping_links": "https://example.com, https://another.com",
        "chat_history": ["Generate this PR/FAQ for me"],
        "use_websearch": True,
    }
