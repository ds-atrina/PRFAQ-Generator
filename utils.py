import fitz  # PyMuPDF
import json
import asyncio
import re

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

def convert_to_json(info):
    """Convert extracted information to JSON format."""
    return json.dumps(info, indent=4)


def remove_links(text):
    pattern = r'https?://\S+'
    return re.sub(pattern, '', text)
