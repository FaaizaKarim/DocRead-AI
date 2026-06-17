from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.config import DOCS_PATH, FAISS_INDEX_PATH, EMBEDDING_MODEL
import os


def load_documents():
    docs = []
    for filename in os.listdir(DOCS_PATH):
        filepath = os.path.join(DOCS_PATH, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
        elif filename.endswith(".txt"):
            loader = TextLoader(filepath)
        else:
            continue
        docs.extend(loader.load())
    return docs


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def ingest():
    print("Loading documents...")
    docs = load_documents()
    if not docs:
        print("No documents found in data/docs/")
        return
    print(f"Loaded {len(docs)} document(s). Splitting...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"Creating embeddings for {len(chunks)} chunks...")
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"Done! Index saved to {FAISS_INDEX_PATH}")


if __name__ == "__main__":
    ingest()
