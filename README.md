# DocRead AI v3.0 — Enterprise Customer Support Agent

RAG-based AI support agent with live document ingestion, webhook integration, and admin dashboard.

## Quick Start

1. Add your Groq key to `.env`
2. `python -m venv venv && source venv/Scripts/activate`
3. `pip install -r requirements.txt`
4. `python -m app.ingest`
5. `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
6. Open `http://127.0.0.1:8000/chat`

## New in v3.0
- Admin panel with live document upload
- Webhook integration (Zendesk/Jira/Slack)
- Drag & drop document ingestion
- Real-time knowledge base updates
- Stats dashboard
- Ocean blue color theme

## API Endpoints
- POST /ask — Ask a question
- POST /upload — Upload document (live re-ingestion)
- GET /documents — List documents
- DELETE /documents/{filename} — Delete document
- POST /ticket — Create ticket (with webhook)
- GET /logs — Conversation logs
- GET /tickets — All tickets


## 📂 Project Directory Structure

```text
docread-ai-v3/
├── app/
│   ├── main.py               # Asynchronous web routing, operational routes, state logic
│   ├── agent.py              # LLM system configurations, structured prompts, core RAG execution
│   ├── ingest.py             # File parsing, Text Splitters chunk configuration, FAISS persistence
│   ├── static/               # System interface layout media logs, branding images
│   └── templates/            # Asynchronous single-page templates (Chat app / Admin UI)
├── data/
│   ├── docs/                 # Persistent document storage repository (.txt / .pdf)
│   ├── faiss_index/          # Local multi-dimensional system vector databases (Gitignored)
│   ├── chat_logs.json        # Permanent operational session tracking records
│   └── tickets.json          # System human support ticket registry
├── .env.example              # Development deployment environment configuration template
├── requirements.txt          # Production distribution dependency configuration arrays
└── README.md                 # Upgraded architectural specification manual


System Design Logic

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ User Frontend   │────▶│ FastAPI Backend  │────▶│   FAISS Store   │
│ UI Chat Panel   │     │ Core Routers API │     │ Vector Databases│
└─────────────────┘     └────────┬─────────┘     └────────┬────────┘
                                 │                        │
                  ┌──────────────┴──────────────┐         │
                  ▼                             ▼         ▼
             Context OK?                  Context Missing ➔ Catch Guardrail
          (Deliver Answer)               (Trigger Ticket ➔ Outbound Webhook JSON)

---

## 📄 License
Distributed under the ISC License. Engineered and designed with precision by **Faaiza Saand**.
