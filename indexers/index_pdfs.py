import os
import glob
import psycopg2
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg2 import register_vector
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
PDF_FOLDER = os.getenv("PDF_FOLDER", "./pdfs")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "rag")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "documents")

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small")

def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn

def get_mongo():
    if not MONGODB_URI:
        return None
    client = MongoClient(MONGODB_URI)
    return client[MONGODB_DB][MONGODB_COLLECTION]

def index_pdfs():
    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    conn = get_conn()
    cur = conn.cursor()
    mongo_col = get_mongo()

    for pdf_path in pdf_files:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            text = chunk.page_content
            vector = embeddings.embed_query(text)
            # Postgres
            cur.execute(
                "INSERT INTO documents (content, source, embedding) VALUES (%s, %s, %s)",
                (text, os.path.basename(pdf_path), Vector(vector))
            )
            # Mongo (optional)
            if mongo_col:
                mongo_col.insert_one({
                    "content": text,
                    "source": os.path.basename(pdf_path),
                    "embedding": vector,
                    "createdAt": datetime.utcnow(),
                })
        print(f"Indexed {pdf_path}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    index_pdfs() 