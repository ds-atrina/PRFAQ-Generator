from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
import os
from openai import OpenAI, OpenAIError
import uuid
import fitz
import re
from dotenv import load_dotenv
import time

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Qdrant
qdrant_url = os.getenv("QDRANT_URL")
connection = QdrantClient(url=qdrant_url)
collection_name = "1finance_kb_department"

# Ensure the collection exists
collection_name = "1finance_kb_department"
connection.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)
print(f"Collection '{collection_name}' initialized.")

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    text = re.sub(r'\s+', ' ', text)
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " "],
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)

def get_embedding(text, model_id="text-embedding-ada-002", retries=3):
    for attempt in range(retries):
        try:
            response = client.embeddings.create(input=text, model=model_id)
            return response.data[0].embedding
        except OpenAIError as e:
            print(f"OpenAI Error: {e}, retrying ({attempt + 1}/{retries})...")
            time.sleep(2 * (attempt + 1))
    raise Exception(f"Failed to get embedding after {retries} retries.")

def process_and_upload_pdf(pdf_path):
    print(f"\n Processing: {pdf_path}")
    try:
        raw_text = extract_text_from_pdf(pdf_path)
        chunks = get_text_chunks(raw_text)

        points = []
        for i, chunk in enumerate(chunks):
            print(f"Embedding chunk {i+1}/{len(chunks)}")
            embedding = get_embedding(chunk)
            point_id = str(uuid.uuid4())
            points.append(PointStruct(id=point_id, vector=embedding, payload={"text": chunk}))

        # Batch insert to Qdrant (in 100s)
        BATCH_SIZE = 100
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            connection.upsert(collection_name=collection_name, wait=True, points=batch)
            print(f"Inserted {len(batch)} points into Qdrant")

        print(f"Uploaded document: {pdf_path}")
    except Exception as e:
        print(f"Error processing '{pdf_path}': {str(e)}")

def process_multiple_pdfs(pdf_paths):
    for i, pdf_path in enumerate(pdf_paths):
        print(f"\n========== File {i+1}/{len(pdf_paths)} ==========")
        process_and_upload_pdf(pdf_path)
                   
# Example usage
if __name__ == "__main__":
    pdf_files = [
        "1F_KB_Documents/1 View.pdf",
        "1F_KB_Documents/1F_Department.pdf",
        "1F_KB_Documents/Assisted ITR Filing.pdf",
        "1F_KB_Documents/Data Analytics.pdf",
        "1F_KB_Documents/Debt Advisory.pdf",
        "1F_KB_Documents/Debt MF Scoring and Ranking.pdf",
        "1F_KB_Documents/Doculocker.pdf",
        "1F_KB_Documents/Engineering Playbook.pdf",
        "1F_KB_Documents/Enterprise Operating System.pdf",
        "1F_KB_Documents/Fianancial Concierge.pdf",
        "1F_KB_Documents/Finance Health Score.pdf",
        "1F_KB_Documents/Financial Planing Center.pdf",
        "1F_KB_Documents/GFPS 2024 Website.pdf",
        "1F_KB_Documents/Global Financial Planners Summit 2023.pdf",
        "1F_KB_Documents/Help & Support.pdf",
        "1F_KB_Documents/India Crypto Research.pdf",
        "1F_KB_Documents/India HR Conclave 2025.pdf",
        "1F_KB_Documents/Insurance App.pdf", 
        "1F_KB_Documents/IPO Updates.pdf",
        "1F_KB_Documents/Linkedin Newsletter.pdf",
        "1F_KB_Documents/Loan Against Insurance.pdf",
        "1F_KB_Documents/Macro Indicators.pdf",
        "1F_KB_Documents/Magazine Website.pdf", 
        "1F_KB_Documents/Moneysign CUG Event.pdf",
        "1F_KB_Documents/Moneysign v1.0.pdf",
        "1F_KB_Documents/P2P Investment V1.pdf",
        "1F_KB_Documents/PF TV YT.pdf",
        "1F_KB_Documents/PF TV YT FAQs.pdf",
        "1F_KB_Documents/PlanMyTax.pdf",
        "1F_KB_Documents/Playbook.pdf",
        "1F_KB_Documents/QFA.pdf",
        "1F_KB_Documents/Ranking Financial Products.pdf",
        "1F_KB_Documents/Real Estate Advisory.pdf",
        "1F_KB_Documents/Super App.pdf",
        "1F_KB_Documents/Website for Financial Wellbeing.pdf",
        "1F_KB_Documents/Website Insurance pages.pdf",
        "1F_KB_Documents/Websites Playbook.pdf"
      ]  # Add your PDF file paths here
    process_multiple_pdfs(pdf_files)