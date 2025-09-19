import os
import logging
import hashlib
import psycopg2
from typing import List, Tuple
from langchain_openai import OpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from pgvector import Vector
import redis

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "pgvector")  # 'pgvector' or 'mongo'

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small")
llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None

# Helper: get DB connection
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn

# Optional Mongo backend (skeleton)
def mongo_retrieve(query_vec: List[float], k: int) -> List[Tuple[str, str]]:
    raise NotImplementedError("MongoDB vector retrieval requires Atlas Vector Search setup.")


def pg_retrieve(query_vec: List[float], k: int, source: str | None) -> List[Tuple[str, str]]:
    conn = get_conn()
    cur = conn.cursor()
    if source is None:
        cur.execute(
            """
            SELECT content, source FROM documents
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (Vector(query_vec), k),
        )
    else:
        cur.execute(
            """
            SELECT content, source FROM documents
            WHERE source = %s
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (source, Vector(query_vec), k),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def answer_query(question, source="all", k=5):
    query_vec = embeddings.embed_query(question)

    # Cache key
    key_basis = f"{source}:{question}".encode("utf-8")
    cache_key = "rag:" + hashlib.sha256(key_basis).hexdigest()

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info("Cache hit")
            import json
            return json.loads(cached)

    # Retrieve
    source_filter = None if source == "all" else source
    if VECTOR_BACKEND == "pgvector":
        rows = pg_retrieve(query_vec, k, source_filter)
    else:
        rows = mongo_retrieve(query_vec, k)

    context = "\n".join([row[0] for row in rows])
    sources = [row[1] for row in rows]
    prompt = f"""Context:\n{context}\n\nQuestion: {question}\nAnswer based only on the context above."""
    answer = llm.invoke(prompt)
    result = {"result": answer, "sources": sources}

    if redis_client:
        import json
        redis_client.setex(cache_key, 600, json.dumps(result))

    return result 