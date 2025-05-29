from langchain.text_splitter import RecursiveCharacterTextSplitter
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
collection_name = "1F_KB_BASE_PF"

# Ensure the collection exists
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
        chunk_size=1800,
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

        file_name = os.path.basename(pdf_path)

        points = []
        for i, chunk in enumerate(chunks):
            print(f"Embedding chunk {i+1}/{len(chunks)}")
            embedding = get_embedding(chunk)
            point_id = str(uuid.uuid4())

            # Add metadata as payload
            payload = {
                "text": chunk,
                "chunk_index": i,
                "file_name": file_name,
            }

            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        # Batch insert to Qdrant (in 100s)
        BATCH_SIZE = 100
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            connection.upsert(collection_name=collection_name, wait=True, points=batch)
            print(f"Inserted {len(batch)} points into Qdrant")

        print(f"Uploaded document: {pdf_path}")
    except Exception as e:
        print(f"Error processing '{pdf_path}': {str(e)}")      
          
def process_multiple_pdfs_in_folder(folder_path):
    # Get a list of all PDF files in the folder
    pdf_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in the provided folder.")
        return
    
    for i, pdf_path in enumerate(pdf_files):
        print(f"\n========== File {i+1}/{len(pdf_files)} ==========")
        process_and_upload_pdf(pdf_path)

# Example usage
if __name__ == "__main__":
    folder_path = "new_transformed_QA"  
    process_multiple_pdfs_in_folder(folder_path)
