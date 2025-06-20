from fastapi import HTTPException, Header, Depends, APIRouter
from pydantic import BaseModel
from typing import Optional, List
from langchain_openai import ChatOpenAI  
from concurrent.futures import ThreadPoolExecutor
from postgrest import APIError
from fastapi.responses import StreamingResponse
from tools.web_search.web_search import WebTrustedSearchTool
from tools.qdrant_tool import kb_qdrant_tool
import asyncio
import os
import json
from dotenv import load_dotenv
load_dotenv()

from api.authenticate import authenticate

from graph import start_langgraph

# Load environment variables (e.g., Supabase credentials)
load_dotenv()

# Supabase client initialization
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

# Pydantic model for request body
class Request(BaseModel):
    messages: list

class ModifyRequest(BaseModel):
    messages: List
    currentPrFAQ: str

# Pydantic models for request and response validation
class PRFAQResponse(BaseModel):
    markdown_output: str
    response_to_user: str

def format_output(output):
    """Function to format PR FAQ sections."""
    pr_faq_str = ""
    pr_faq_str += f"**Title:** {output.get('Title', '')}\n\n"
    pr_faq_str += f"**Subtitle:** {output.get('Subtitle', '')}\n\n"
    pr_faq_str += f"**Introduction Paragraph:** {output.get('IntroParagraph', '')}\n\n"
    pr_faq_str += f"**Problem Statement:** {output.get('ProblemStatement', '')}\n\n"
    pr_faq_str += f"**Solution:** {output.get('Solution', '')}\n\n"
    pr_faq_str += "**Leader's Quote:** \n\n"
    pr_faq_str += "**Customer's Quote:** \n\n"

    pr_faq_str += f"\n**Competitors:**\n"
    for competitor in output.get("Competitors", []):
        name = competitor.get("name", "")
        url = competitor.get("url", "")
        pr_faq_str += f"\n- [{name}]({url})\n"

    pr_faq_str += f"\n**Internal FAQs:**\n"
    for faq in output.get("InternalFAQs", []):
        question = faq.get('Question', faq.get('question', 'Unknown Question'))
        answer = faq.get('Answer', faq.get('answer', 'No answer provided'))

        pr_faq_str += f"\n**Q: {question}**\n"
        pr_faq_str += f"\nA:\n{answer}\n"

    pr_faq_str += f"\n**External FAQs:**\n"
    for faq in output.get("ExternalFAQs", []):
        question = faq.get('Question', faq.get('question', 'Unknown Question'))
        answer = faq.get('Answer', faq.get('answer', 'No answer provided'))

        pr_faq_str += f"\n**Q: {question}**\n"
        pr_faq_str += f"\nA:\n{answer}\n"

    return pr_faq_str

def fetch_space_details(spaceid: str):
    """
    Fetch title, details (solution, problemStatement), and links from the `spaces` table for the given spaceid.
    Raises:
      RuntimeError if the Supabase API call fails (4xx/5xx).
      LookupError  if no rows exist for that spaceid.
    Returns:
      dict — containing `title`, `solution`, `problemStatement`, and `links`.
    """
    try:
        resp = (
            supabase
            .table("spaces")
            .select("title", "details", "links")
            .eq("spaceid", spaceid)
            .execute()
        )
    except APIError as e:
        raise RuntimeError(f"Supabase API error: {e}") from e

    if not resp.data:
        raise LookupError(f"No space found with id {spaceid!r}")

    # Extract the first row
    return resp.data[0]


def fetch_space_documents(spaceid: str, chatid: Optional[str]):
    """
    Fetch all content rows for the given spaceid from the `space_documents` table.
    Raises:
      RuntimeError if the Supabase API call fails (4xx/5xx).
      LookupError  if no rows exist for that spaceid.
    Returns:
      str — merged content from all rows.
    """
    try:
        resp1 = (
            supabase
            .table("space_documents")
            .select("content")
            .eq("spaceid", spaceid)
            .execute()
        )
        resp2 = (
            supabase
            .table("general_documents")
            .select("content")
            .eq("chatid", chatid)
            .execute()
        )
    except APIError as e:
        raise RuntimeError(f"Supabase API error: {e}") from e

    merged_content = ""
    if resp1.data:
        merged_content += "\n".join(row["content"] for row in resp1.data) + "\n"
    if resp2.data:
        merged_content += "\n".join(row["content"] for row in resp2.data)

    return merged_content.strip()

@router.post("/generate", response_model=PRFAQResponse)
async def generate_prfaq(
    request: Request,
    x_space_id: str = Header(..., alias="x-space-id", description="Space ID for which the PR FAQ needs to be generated"),
    x_thread_id: Optional[str] = Header(None, alias="x-thread-id", description="Thread ID for tracking the request"),
    x_command: Optional[str] = Header(None, alias="x-command", description="Command in use"),
    x_web_search: Optional[str] = Header("False", alias="x-web-search", description="Boolean flag to use web search"),
    # user: str = Depends(authenticate)
):
    """
    Generate a PR FAQ for a given spaceid by fetching data from the Supabase database.
    """
    try:
        # Parse body to extract messages
        messages = request.messages
        if not messages:
            messages = ["Generate PR/FAQ for me"]
        # Fetch space details
        space = fetch_space_details(x_space_id)
        title = space["title"]
        solution = space["details"].get("solution", "")
        problem_statement = space["details"].get("problemStatement", "")
        links = space.get("links", "")

        # Fetch and merge content from space_documents
        reference_content = fetch_space_documents(x_space_id, x_thread_id)

        # Prepare inputs for the Crew AI
        inputs = {
            "topic": title,
            "problem": problem_statement,
            "solution": solution,
            "chat_history": messages, 
            "web_scraping_links": links,
            "reference_doc_content": reference_content,
            "use_websearch": x_web_search.lower()=='true'  # Convert string to boolean
        }
        
        # Instantiate and kickoff the PR FAQ generation
        result = start_langgraph(inputs, None)

        markdown = format_output(result)
        user_response = result.get("UserResponse", "Here's the generated document for you:")

        return {
            "markdown_output": markdown,
            "response_to_user": user_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

def sse_format(data, event=None):
    """Format a dict as an SSE event string."""
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data)}\n\n"

@router.post("/logging")
async def generate_prfaq_logs(
    request: Request,
    x_space_id: str = Header(..., alias="x-space-id"),
    x_thread_id: Optional[str] = Header(None, alias="x-thread-id"),
    x_command: Optional[str] = Header(None, alias="x-command"),
    x_web_search: Optional[str] = Header("False", alias="x-web-search"),
    # user: str = Depends(authenticate),
):
    """
    SSE Streaming endpoint for PRFAQ generation.
    Yields "step" events for each thinking step, and a final "result" event for the output.
    """
    # Fetch space and docs as in your current code...
    try:
        # # Parse body to extract messages (adjust as needed)
        messages = request.messages
        if not messages:
            messages = ["Generate PR/FAQ for me"]

        space = fetch_space_details(x_space_id)
        title = space["title"]
        solution = space["details"].get("solution", "")
        problem_statement = space["details"].get("problemStatement", "")
        links = space.get("links", "")

        reference_content = fetch_space_documents(x_space_id, x_thread_id)

        inputs = {
            "topic": title,
            "problem": problem_statement,
            "solution": solution,
            "chat_history": messages,
            "web_scraping_links": links,
            "reference_doc_content": reference_content,
            "use_websearch": x_web_search.lower() == 'true'
        }

        async def event_generator():
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue()

            def streaming_callback(data):
                asyncio.run_coroutine_threadsafe(queue.put(data), loop)

            def run_workflow():
                result = start_langgraph(inputs, streaming_callback=streaming_callback)
                asyncio.run_coroutine_threadsafe(queue.put({"__final__": result}), loop)

            executor = ThreadPoolExecutor(max_workers=10)
            loop.run_in_executor(executor, run_workflow)

            while True:
                data = await queue.get()
                if "__final__" in data:
                    yield sse_format({"result": data["__final__"]}, event="result")
                    break
                else:
                    yield sse_format(data, event="step")

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/modify", response_model=PRFAQResponse)
async def modify_faq(
    request: ModifyRequest,
    x_space_id: str = Header(..., alias="x-space-id", description="Space ID for which the modification is being performed"),
    x_thread_id: Optional[str] = Header(None, alias="x-thread-id", description="Thread ID for tracking the request"),
    x_command: Optional[str] = Header(None, alias="x-command", description="Command in use"),
    x_web_search: Optional[str] = Header("False", alias="x-web-search", description="Boolean flag to use web search"),
    # user: str = Depends(authenticate),
):
    """
    Modify an existing PR FAQ based on user feedback and additional context.
    """
    try:
        # Extract inputs from the request
        messages = request.messages
        current_prfaq = request.currentPrFAQ

        # Fetch space details
        space = fetch_space_details(x_space_id)  # Assuming this function is defined elsewhere
        title = space["title"]
        solution = space["details"].get("solution", "")
        problem_statement = space["details"].get("problemStatement", "")

        # Initialise LLM
        llm = ChatOpenAI(model="o4-mini", temperature=1, openai_api_key=os.getenv("OPENAI_API_KEY"))

        # Refine the search query based on user feedback
        refine_prompt = f"""
            Based on the user feedback and the given context of topic, problem statement, and solution:
            The user provided the following feedback: "{messages[-1]}"
            Topic: {title}
            Problem statement: {problem_statement}
            Solution: {solution}

        - Based on this feedback and the given context of topic, problem statement and solution, determine the most effective search query to put in a search engine to gather relevant and latest information user feeback query around the topic, problem or solution.
        - Create a search query that balances specificity and breadth: it should aim to gather **detailed, structured information** that can answer the user feedback precisely (for example, cost breakdowns, competitor feature tables, regional insights), while also being broad enough to capture related insights.
        - You can consider India for location-specific searches if required unless mentioned otherwise.
        - Avoid mentioning proper nouns or dates/years in the prompt, instead use words like "latest" and general key terms from the context. 
        - Prioritise Indian market context by default unless stated otherwise.
        - If the query involves costing or pricing, explicitly add "India" and "cost breakdown" or "pricing table" in the search query.
        - Return ONLY the refined search query as a string without any additional text.      
        """

        # Perform Web Search and Knowledge Base Search
        refined_query_response = llm.invoke(refine_prompt)
        refined_query = refined_query_response.content.strip()

        kb_response = kb_qdrant_tool.run(refined_query)
        web_response = ""
        if x_web_search.lower() == 'true':
            web_tool = WebTrustedSearchTool()
            web_response = web_tool.run(
                query=refined_query,
                trust=True,
                read_content=False,
                top_k=5,
                onef_search=False
            )

        # Modify the FAQ using the refined query and search results
        prompt = f"""
            You are an intelligent assistant tasked with modifying/updating an existing PR FAQ based on user feedback and returning it in the said JSON format.

            The PR FAQ is generated based on the following:
            - Problem statement: {problem_statement}
            - Solution: {solution}

            User feedback:
            "{messages[-1]}"

            A search was carried out for the feedback with the refined query:
            "{refined_query}"

            The response from knowledge base search is as follows:
            {kb_response}

            The response from web search is as follows:
            {web_response}

            Chat history for context:
            ```{messages}```

            Here is the existing PR FAQ in markdown format:
            ```{current_prfaq}```

            Instructions:
            - Modify the PR FAQ comprehensively based on the user feedback, ensure the PR FAQ is consistent throughout and any changes or additions are reflected throughout the prfaq.
            - Change the UserResponse field according to the user's feedback. It should be a reply to the user's message.
            - Use information from the search results, knowledge base or chat history to make the required changes or additions in the PR FAQ. Give relevant, latest and comprehensive answers from the retrieved information.
            - Ensure that any new information aligns with the problem statement and solution provided.
            - [STRICT] Whenever the user feedback requests a table, ensure that the response **must include a well-formatted markdown table.** If the retrieved information lacks a table, extract the relevant data points and **format them into a table yourself.**
            - For cost/pricing-related feedback, always assume the country context is India (unless otherwise stated) and provide costs in INR. Avoid using USD or other currencies unless specified.
            - Prioritise Indian market context by default unless the user specifies otherwise.
            - Assume any new feedback is a FAQ unless specified otherwise.
            - [STRICT] DO NOT CHANGE THE FORMATTING OR THE STRUCTURE OF THE EXISTING PR FAQ and return the entire (ALL FIELDS WITHOUT OMITTING ANY, AS THEY ARE WITH UPDATES, IF ANY), updated PR FAQ in STRICT JSON format: Use double quotes to wrap keys and values.
                Title: str
                Subtitle: str
                IntroParagraph: str
                ProblemStatement: str
                Solution: str
                Competitors: list (list of dicts with name and url)
                InternalFAQs: list (list of dicts with Question and Answer)
                ExternalFAQs: list (list of dicts with Question and Answer)
                UserResponse: str
            eg. {{
                    "Title": "Revolutionizing AI Assistants",
                    "Subtitle": "Introducing the Next-Gen AI for Business Solutions",
                    "IntroParagraph": "In today's digital age, businesses need smarter AI solutions to streamline workflows and improve efficiency. Our new AI assistant is here to revolutionize the way companies operate.",
                    "ProblemStatement": "Many businesses struggle with automating repetitive tasks, improving customer support, and handling large volumes of inquiries efficiently.",
                    "Solution": "Our AI assistant leverages cutting-edge NLP and machine learning to provide seamless automation, personalized responses, and real-time insights.",
                    "Competitors": [
                        {{
                        "name":"Amazon Rekognition", 
                        "url":"https://docs.aws.amazon.com/rekognition/"
                        }}, 
                        {{
                        "name":"Google Cloud Vision API", 
                        "url":"https://cloud.google.com/vision/docs/detecting-safe-search"
                        }}
                    ],
                    "InternalFAQs": [
                        {{
                            "Question": "How does the AI assistant integrate with existing tools?",
                            "Answer": "It seamlessly integrates with platforms like \n-Slack \n-Microsoft Teams \n-CRM systems via APIs."
                        }},
                        {{
                            "Question": "What kind of training data is required?",
                            "Answer": "The AI assistant can be **fine-tuned** with company-specific data for enhanced performance."
                        }}
                    ],
                    "ExternalFAQs": [
                        {{
                            "Question": "Is the AI assistant secure?",
                            "Answer": "Yes, we use industry-standard encryption and compliance measures to ensure data security."
                        }},
                        {{
                            "Question": "Can the AI assistant handle multiple languages?",
                            "Answer": "Absolutely! It's developed in a way that supports multiple languages and can be customized based on user needs."
                        }},
                        {{
                            "Question": "Can I use Markdown-style tables?",
                            "Answer": "| Feature         | Benefit        |\n|------------------|----------------|\n| Auto-Generate    | Saves time     |\n| LLM-Driven       | Context aware  |"
                        }},
                        {{
                            "Question": "Can I also return JSON-style tables?",
                            "Answer": [
                                {{"Input Type": "Markdown Table", "Support": "Yes"}},
                                {{"Input Type": "JSON Table", "Support": "Yes"}}
                            ]
                        }}
                    ],
                    "UserResponse": "Here is the generated PR/FAQ document on topic and your provided inputs. Please review and let me know if any changes are needed."
                }}
            - Avoid vague responses like "I don't know" or "Not specified." Use the given context to derive meaningful answers or omit such points.
            - While generating the FAQs and answers, follow these stylistic and tone guidelines:
                - Use British English (e.g., "capitalise," "colour").
                - Keep language human, positive and transparent.
                - Ensure the tone is formal yet personable, clear, and consistent with brand values.
                - Avoid technical jargon unless necessary, and explain all abbreviations/acronyms.
        """
        response = llm.invoke(prompt)
        response_text = str(response.content.strip())

        try:
            cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
            parsed_output = json.loads(cleaned_json)
            markdown = format_output(parsed_output)
            user_response = parsed_output.get("UserResponse", "Here's the modified document according to your request:")
            return {"markdown_output": markdown, "response_to_user": user_response}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse the updated PR FAQ: {e}")

    except LookupError as e:
        raise HTTPException(status_code=404, detail=f"Resource not found: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"A runtime error occurred: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8082))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
