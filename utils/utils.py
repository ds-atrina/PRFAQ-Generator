import fitz  # PyMuPDF
import json
import re
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc) 
        if not text:
            raise ValueError("No text extracted from PDF.")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def remove_links(text):
    pattern = r'https?://\S+'
    return re.sub(pattern, '', text)

# def get_openai_llm():
#     return ChatOpenAI(
#         model="o3-mini", 
#         temperature=1, 
#         timeout=120
#     )

def get_openai_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.2, 
        timeout=120
    )

def render_text_or_table_to_str(text_or_data):
    """
    Converts structured table data or markdown strings to markdown-compatible string.
    Used for string-based rendering (not direct Streamlit display).
    """
    if isinstance(text_or_data, list):
        if all(isinstance(row, dict) for row in text_or_data):
            return pd.DataFrame(text_or_data).to_markdown(index=False)
        else:
            return '\n'.join(f"- {item}" for item in text_or_data)
    return text_or_data

def convert_to_json(response):
    response_text = response.replace("```json","").replace("```","").strip()

    try:
        updated_faq = json.loads(response_text)
        return updated_faq
    except json.JSONDecodeError as e:
        return {}