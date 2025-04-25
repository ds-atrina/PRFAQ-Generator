from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from postgrest import APIError
import os
import json

from crew import PRFAQGeneratorCrew

# Load environment variables (e.g., Supabase credentials)
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="PRFAQ Generator API")

# Supabase client initialization
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic models for request and response validation
class PRFAQResponse(BaseModel):
    markdown_output: str

def format_output(output):
    """Function to format PR FAQ sections."""
    pr_faq_str = ""
    pr_faq_str += f"**Title:** {output.get('Title', '')}\n\n"
    pr_faq_str += f"**Subtitle:** {output.get('Subtitle', '')}\n\n"
    pr_faq_str += f"**Introduction Paragraph:** {output.get('IntroParagraph', '')}\n\n"
    pr_faq_str += f"**Customer Problems:** {output.get('CustomerProblems', '')}\n\n"
    pr_faq_str += f"**Solution:** {output.get('Solution', '')}\n\n"
    pr_faq_str += f"**Leader's Quote:** {output.get('LeadersQuote', '')}\n\n"
    pr_faq_str += f"**Getting Started:** {output.get('GettingStarted', '')}\n\n"
    pr_faq_str += f"**Customer Quotes:**\n"
    for quote in output.get("CustomerQuotes", []):
        pr_faq_str += f"\n*{quote}*\n"

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


def fetch_space_documents(spaceid: str):
    """
    Fetch all content rows for the given spaceid from the `space_documents` table.
    Raises:
      RuntimeError if the Supabase API call fails (4xx/5xx).
      LookupError  if no rows exist for that spaceid.
    Returns:
      str — merged content from all rows.
    """
    try:
        resp = (
            supabase
            .table("space_documents")
            .select("content")
            .eq("spaceid", spaceid)
            .execute()
        )
    except APIError as e:
        raise RuntimeError(f"Supabase API error: {e}") from e

    if not resp.data:
        raise LookupError(f"No documents found for spaceid {spaceid!r}")

    # Merge all content into a single string
    merged_content = "\n".join(row["content"] for row in resp.data)
    return merged_content


@app.get("/prfaq", response_model=PRFAQResponse)
async def generate_prfaq(
    spaceid: str = Header(..., description="Space ID for which the PR FAQ needs to be generated"),
    threadid: Optional[str] = Header(None, description="Thread ID for tracking the request"),
    use_websearch: Optional[bool] = Header(False, description="Boolean flag to use web search")
):
    """
    Generate a PR FAQ for a given spaceid by fetching data from the Supabase database.
    """
    try:
        # Fetch space details
        space = fetch_space_details(spaceid)
        title = space["title"]
        solution = space["details"].get("solution", "")
        problem_statement = space["details"].get("problemStatement", "")
        links = space.get("links", "")

        # Fetch and merge content from space_documents
        reference_content = fetch_space_documents(spaceid)

        # Prepare inputs for the Crew AI
        inputs = {
            "topic": title,
            "problem": problem_statement,
            "solution": solution,
            "web_scraping_links": links,
            "reference_doc_content": reference_content,
            "use_websearch": use_websearch  # Pass the boolean flag
        }

        # Instantiate and kickoff the PR FAQ generation
        crew_instance = PRFAQGeneratorCrew(inputs)
        result = crew_instance.crew().kickoff(inputs=inputs)

        # Parse the result
        cleaned_json = result.raw.replace("```json", "").replace("```", "").strip()
        parsed_output = json.loads(cleaned_json)
        markdown = format_output(parsed_output)

        return {
            "markdown_output": markdown
        }

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api-db:app", host="0.0.0.0", port=port, reload=True)