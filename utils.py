import fitz  # PyMuPDF
import json
import asyncio
import re
import pandas as pd
from crewai import LLM

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc)  # Ensure text extraction mode is specified
        if not text:
            raise ValueError("No text extracted from PDF.")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def remove_links(text):
    pattern = r'https?://\S+'
    return re.sub(pattern, '', text)

def get_openai_llm():
    return LLM(
        model="openai/o3-mini",
        reasoning_effort = "medium",
        temperature=0.2,        
        seed=42
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