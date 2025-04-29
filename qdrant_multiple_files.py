from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
import os
from openai import OpenAI
import uuid
import fitz
import re
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# Initialize OpenAI client and Qdrant connection

qdrant_url = os.getenv("QDRANT_URL")
connection = QdrantClient(url=qdrant_url)

# Ensure the collection exists
collection_name = "1finance_kb_test"
connection.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)
print(f"Collection '{collection_name}' initialized.")

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    text = re.sub(r'\s+', ' ', text)
    return text

# Function to split text into smaller chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " "],
        chunk_size=2000,  # Adjust chunk size as needed
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Function to convert text chunks into embeddings
def get_embedding(text_chunks, model_id="text-embedding-ada-002"):
    points = []
    for chunk in text_chunks:
        response = client.embeddings.create(
            input=chunk,
            model=model_id
        )
        embeddings = response.data[0].embedding
        point_id = str(uuid.uuid4())  # Generate a unique ID for each chunk
        points.append(PointStruct(id=point_id, vector=embeddings, payload={"text": chunk}))
    return points

# Function to insert embeddings into Qdrant
def insert_data(points):
    operation_info = connection.upsert(
        collection_name=collection_name,
        wait=True,
        points=points
    )
    print("Data upsert operation info:", operation_info)

# Function to process and upload a single PDF
def process_and_upload_pdf(pdf_path):
    print(f"Processing document: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    chunks = get_text_chunks(raw_text)
    embeddings = get_embedding(chunks)
    insert_data(embeddings)
    print(f"Document '{pdf_path}' uploaded successfully.")

# Main function to process multiple PDF files
def process_multiple_pdfs(pdf_paths):
    for pdf_path in pdf_paths:
        process_and_upload_pdf(pdf_path)
                   
# Example usage
if __name__ == "__main__":
    pdf_files = [
        "1 Finance Knowledge Base Documents/1 View.pdf",
        "1 Finance Knowledge Base Documents/Assisted ITR Filing.pdf",
        "1 Finance Knowledge Base Documents/Data Analytics.pdf",
        "1 Finance Knowledge Base Documents/Debt Advisory.pdf",
        "1 Finance Knowledge Base Documents/Debt MF Scoring and Ranking.pdf",
        "1 Finance Knowledge Base Documents/Doculocker.pdf",
        "1 Finance Knowledge Base Documents/Engineering Playbook.pdf",
        "1 Finance Knowledge Base Documents/Enterprise Operating System.pdf",
        "1 Finance Knowledge Base Documents/Finance Health Score.pdf",
        "1 Finance Knowledge Base Documents/Financial Planning Center.pdf",
        "1 Finance Knowledge Base Documents/Financial Concierge.pdf",
        "1 Finance Knowledge Base Documents/GFPS 2024 Website.pdf",
        "1 Finance Knowledge Base Documents/Global Financial Planners Summit 2023.pdf",
        "1 Finance Knowledge Base Documents/Help & Support.pdf",
        "1 Finance Knowledge Base Documents/India HR Conclave 2025.pdf",
        "1 Finance Knowledge Base Documents/India Crypto Research.pdf",
        "1 Finance Knowledge Base Documents/Insurance App.pdf", 
        "1 Finance Knowledge Base Documents/IPO Updates.pdf",
        "1 Finance Knowledge Base Documents/Linkedin Newsletter.pdf",
        "1 Finance Knowledge Base Documents/Loan Against Insurance.pdf",
        "1 Finance Knowledge Base Documents/Macro Indicators.pdf",
        "1 Finance Knowledge Base Documents/Magazine Website.pdf", 
        "1 Finance Knowledge Base Documents/Moneysign CUG Event.pdf",
        "1 Finance Knowledge Base Documents/Moneysign v1.0.pdf",
        "1 Finance Knowledge Base Documents/P2P Investment V1.pdf",
        "1 Finance Knowledge Base Documents/PF TV YT.pdf",
        "1 Finance Knowledge Base Documents/PF TV YT FAQs.pdf",
        "1 Finance Knowledge Base Documents/PlanMyTax.pdf",
        "1 Finance Knowledge Base Documents/Playbook.pdf",
        "1 Finance Knowledge Base Documents/QFA.pdf",
        "1 Finance Knowledge Base Documents/Ranking Financial Products.pdf",
        "1 Finance Knowledge Base Documents/Real Estate Advisory.pdf",
        "1 Finance Knowledge Base Documents/Super App.pdf",
        "1 Finance Knowledge Base Documents/Website for Financial Wellbeing.pdf",
        "1 Finance Knowledge Base Documents/Website Insurance pages.pdf",
        "1 Finance Knowledge Base Documents/Websites Playbook.pdf"
      ]  # Add your PDF file paths here
    process_multiple_pdfs(pdf_files)