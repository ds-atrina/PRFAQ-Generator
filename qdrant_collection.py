# For creating and uploading collection -- works independtly

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient,models
from qdrant_client.http.models import PointStruct
import os
from openai import OpenAI
import uuid
import fitz
import re

client = OpenAI(
  api_key=os.environ["OPENAI_API_KEY"],  
)

qdrant_url = os.environ.get("QDRANT_URL")

connection = QdrantClient(url=qdrant_url)

connection.create_collection(
    collection_name="1finance_kb",
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)
print("Create collection reponse:", connection)

info = connection.get_collection(collection_name="1finance_kb")

print("Collection info:", info)
for get_info in info:
  print(get_info)

# extract text from pdf
def extract_text_from_pdf(pdf_path):
        text = ""

        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()

        text = re.sub(r'\s+', ' ', text)
        return text

# Chunking
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " "],
        chunk_size=1200,                      # 1000,100 for 60 page 
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# for converting chunks into embeddings
def get_embedding(text_chunks, model_id="text-embedding-ada-002"):                  
    points = []
    for idx, chunk in enumerate(text_chunks):
        response = client.embeddings.create(
            input=chunk,
            model=model_id
        )
        embeddings = response.data[0].embedding 
        point_id = str(uuid.uuid4())  # Generate a unique ID for the point

        points.append(PointStruct(id=point_id, vector=embeddings, payload={"text": chunk}))

    return points

# To insert data into qdrant database
def insert_data(get_points):
    operation_info = connection.upsert(
    collection_name="1finance_kb",
    wait=True,
    points=get_points
)
    
####
pdf_path = "1F_KB.pdf"
get_raw_text=extract_text_from_pdf(pdf_path)

chunks=get_text_chunks(get_raw_text)
vectors=get_embedding(chunks)
insert_data(vectors)