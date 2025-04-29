from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from postgrest import APIError
import os
import json
from dotenv import load_dotenv
load_dotenv()
from crew import PRFAQGeneratorCrew

# Load environment variables (e.g., Supabase credentials)
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="PRFAQ Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Supabase client initialization
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic model for request body
class Request(BaseModel):
    messages: list

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

@app.post("/prfaq", response_model=PRFAQResponse)
async def generate_prfaq(
    request: Request,
    x_space_id: str = Header(..., alias="x-space-id", description="Space ID for which the PR FAQ needs to be generated"),
    x_thread_id: Optional[str] = Header(None, alias="x-thread-id", description="Thread ID for tracking the request"),
    x_command: Optional[str] = Header(None, alias="x-command", description="Command in use"),
    x_web_search: Optional[str] = Header("false", alias="x-web-search", description="Boolean flag to use web search")
):
    """
    Generate a PR FAQ for a given spaceid by fetching data from the Supabase database.
    """
    try:
        # Parse body to extract messages
        messages = request.messages
        if messages:
            try:
                messages = json.loads(messages)
            except (json.JSONDecodeError, TypeError):
                messages = messages if isinstance(messages, list) else []
        else:
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
            "use_websearch": x_web_search.lower() == "true",  # Convert string to boolean
        }

        # Instantiate and kickoff the PR FAQ generation
        crew_instance = PRFAQGeneratorCrew(inputs)
        result = crew_instance.crew().kickoff(inputs=inputs)

        # Parse the result
        cleaned_json = result.raw.replace("```json", "").replace("```", "").strip()
        parsed_output = json.loads(cleaned_json)
        markdown = format_output(parsed_output)
        user_response = parsed_output.get("UserResponse", "Here's the generated document for you:")

        return {
            "markdown_output": markdown,
            "response_to_user": user_response
        }

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8082))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
