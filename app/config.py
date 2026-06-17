from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DOCS_PATH = "data/docs"
FAISS_INDEX_PATH = "data/faiss_index"
MODEL_NAME = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
