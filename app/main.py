from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.agent import ask, reload_vectorstore
import json, os, shutil, requests
from datetime import datetime

app = FastAPI(
    title="DocRead AI",
    description="RAG-based AI Customer Support Agent — Enterprise Edition",
    version="3.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

LOG_FILE = "data/chat_logs.json"
TICKET_FILE = "data/tickets.json"
DOCS_PATH = "data/docs"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

os.makedirs("data", exist_ok=True)
os.makedirs(DOCS_PATH, exist_ok=True)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    chat_history: list[ChatMessage] = Field(default_factory=list)

class AnswerResponse(BaseModel):
    answer: str
    sources: list
    needs_escalation: bool
    context_used: str

class TicketRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    issue: str = Field(..., min_length=10, max_length=2000)
    chat_history: Optional[list] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


def read_json_file(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def write_json_file(filepath: str, data: list):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def log_conversation(question, answer, sources, escalated):
    logs = read_json_file(LOG_FILE)
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "sources": sources if isinstance(sources, list) else [],
        "escalated": escalated
    })
    write_json_file(LOG_FILE, logs)

def send_webhook(payload: dict):
    if not WEBHOOK_URL:
        return
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

def reingest_documents():
    from app.ingest import ingest
    ingest()
    reload_vectorstore()


@app.get("/")
def root():
    return {"status": "DocRead AI is running", "version": "3.0.0"}

@app.get("/chat")
def chat_ui():
    return FileResponse("app/static/index.html")

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    try:
        history = [{"role": m.role, "content": m.content} for m in request.chat_history]
        result = ask(request.question, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    try:
        log_conversation(request.question, result["answer"], result.get("sources", []), result.get("needs_escalation", False))
    except Exception:
        pass
    return AnswerResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        needs_escalation=result.get("needs_escalation", False),
        context_used=result.get("context_used", "")
    )

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".txt", ".pdf"]:
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported")
    save_path = os.path.join(DOCS_PATH, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    background_tasks.add_task(reingest_documents)
    return {"message": f"{file.filename} uploaded. Knowledge base updating...", "filename": file.filename}

@app.get("/documents")
def list_documents():
    files = os.listdir(DOCS_PATH)
    return {"documents": [f for f in files if f.endswith((".txt", ".pdf"))], "count": len(files)}

@app.delete("/documents/{filename}")
def delete_document(filename: str, background_tasks: BackgroundTasks):
    filepath = os.path.join(DOCS_PATH, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(filepath)
    background_tasks.add_task(reingest_documents)
    return {"message": f"{filename} deleted. Knowledge base updating..."}

@app.post("/ticket")
def create_ticket(ticket: TicketRequest):
    tickets = read_json_file(TICKET_FILE)
    ticket_id = f"TKT-{len(tickets)+1:04d}"
    ticket_data = {
        "id": ticket_id,
        "timestamp": datetime.now().isoformat(),
        "name": ticket.name,
        "email": ticket.email,
        "issue": ticket.issue,
        "chat_history": ticket.chat_history,
        "status": "open"
    }
    tickets.append(ticket_data)
    write_json_file(TICKET_FILE, tickets)
    send_webhook({
        "event": "new_support_ticket",
        "ticket_id": ticket_id,
        "customer": {"name": ticket.name, "email": ticket.email},
        "issue": ticket.issue,
        "chat_context": ticket.chat_history[-5:] if ticket.chat_history else [],
        "timestamp": datetime.now().isoformat()
    })
    return {"ticket_id": ticket_id, "message": f"Ticket {ticket_id} created successfully", "webhook_sent": bool(WEBHOOK_URL)}

@app.get("/logs")
def get_logs():
    return read_json_file(LOG_FILE)

@app.get("/tickets")
def get_tickets():
    return read_json_file(TICKET_FILE)
