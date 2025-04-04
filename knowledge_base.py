
import os
import chromadb
import uuid
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List
from utils import extract_text_from_pdf  

class CompanyKnowledgeBase:
    def __init__(self, vector_store_path="./vector_store"):
        self.vector_store_path = vector_store_path
        self.client = chromadb.PersistentClient(path=self.vector_store_path)
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(api_key=os.getenv('OPENAI_API_KEY'))
        self.vector_store = self.load_or_create_vector_store()

    def load_or_create_vector_store(self):
        """Loads or creates a vector store collection."""
        collection = self.client.get_or_create_collection("kb_collection", embedding_function=self.embedding_function)
        return collection

    def add_document(self, document, metadata):
        """Adds a document chunk to the vector store."""
        document_id = str(uuid.uuid4())
        self.vector_store.add(ids=[document_id], documents=[document], metadatas=[metadata])

    def similarity_search(self, query):
        """Performs a similarity search on the knowledge base."""
        results = self.vector_store.query(query_texts=[query], n_results=5)
        return results

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 20) -> List[str]:
        """
        Splits the text into overlapping chunks to improve retrieval accuracy.

        - `chunk_size`: Number of characters per chunk.
        - `overlap`: Number of characters to overlap between consecutive chunks.
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap  # Move start forward with overlap

        return chunks

    def add_pdf(self, pdf_input):
        """Extracts text from a PDF and adds it to the knowledge base in chunks."""
        if isinstance(pdf_input, str):  # If it's a file path
            with open(pdf_input, "rb") as file:
                all_text = extract_text_from_pdf(file)
        else:  # If it's a file-like object (e.g., Streamlit upload)
            all_text = extract_text_from_pdf(pdf_input)

        if not all_text.strip():
            print(f"Warning: No text extracted from {pdf_input}")
            return

        # Chunk the extracted text
        chunks = self.chunk_text(all_text)

        # Store each chunk in the knowledge base
        for idx, chunk in enumerate(chunks):
            metadata = {
                "source": "pdf",
                "path": str(pdf_input),
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }
            self.add_document(chunk, metadata)

        print(f"✅ Successfully added {len(chunks)} chunks from the PDF to the knowledge base.")

    def is_document_in_kb(self, pdf_path: str) -> bool:
        """Checks if a PDF is already in the knowledge base."""
        results = self.vector_store.query(query_texts=[pdf_path], n_results=1)
        for meta in results.get("metadatas", []):
            if meta and meta[0].get("path") == pdf_path:
                return True
        return False
