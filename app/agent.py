from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.config import FAISS_INDEX_PATH, GROQ_API_KEY, MODEL_NAME, EMBEDDING_MODEL

SYSTEM_PROMPT = """You are DocRead AI, a professional customer support agent.
You answer questions ONLY based on the provided context from the knowledge base.

Rules:
- If the answer is in the context, answer clearly and professionally
- If the answer is NOT in the context, say exactly:
  "I don't have enough information to answer that. Please contact our support team directly."
- Never make up information
- Keep answers concise and helpful

Context:
{context}
"""

vectorstore = None
llm = None


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def get_vectorstore():
    global vectorstore
    if vectorstore is None:
        embeddings = get_embeddings()
        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    return vectorstore


def reload_vectorstore():
    global vectorstore
    vectorstore = None
    get_vectorstore()
    print("Vectorstore reloaded successfully")


def get_llm():
    global llm
    if llm is None:
        llm = ChatGroq(
            model=MODEL_NAME,
            api_key=GROQ_API_KEY,
            temperature=0.2
        )
    return llm


def ask(question: str, chat_history: list = []) -> dict:
    vs = get_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": 4})
    docs = retriever.invoke(question)

    context = "\n\n".join([doc.page_content for doc in docs])
    sources = list(set([doc.metadata.get("source", "knowledge base") for doc in docs]))
    source_names = [s.split("\\")[-1].split("/")[-1] for s in sources]

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
    for h in chat_history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    response = get_llm().invoke(messages)
    answer = response.content

    needs_escalation = any(phrase in answer.lower() for phrase in [
        "don't have enough information",
        "cannot find",
        "not sure",
        "contact our support"
    ])

    return {
        "answer": answer,
        "sources": source_names,
        "needs_escalation": needs_escalation,
        "context_used": context[:200] + "..." if len(context) > 200 else context
    }
