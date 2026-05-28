# RAG Agent — Full Stack Monorepo

FastAPI + LangGraph + Gemini Flash 2.5 backend with a Next.js 15 frontend.
Full auth, per-user conversations, per-conversation document uploads, and
complete persistence across logouts and refreshes.

---

## Stack

| Layer      | Tech |
|------------|------|
| Backend    | FastAPI · LangGraph · Gemini Flash 2.5 |
| Database   | PostgreSQL (users, conversations, messages) |
| Vector DB  | PGVector / Postgres (per-conversation collections) |
| Auth       | JWT (access + refresh tokens) |
| Frontend   | Next.js 15 · TypeScript · Tailwind CSS |
| State      | Zustand (persisted to localStorage) |

---

## RAG behavior

- Uploads are split into citeable evidence chunks with source and PDF page metadata.
- Retrieval fetches a broader candidate set, filters weak matches, and removes near-duplicates before generation.
- Answers based on retrieved evidence must include citations such as `[E1]`.
- When the documents do not support an answer, the assistant abstains rather than guessing.
- Grader feedback informs follow-up retrieval or generation attempts.
- `backend/evals/` contains a starter benchmark format and scorer for retrieval, citation, and abstention regressions.

Retrieval can be tuned with `RETRIEVAL_TOP_K`, `RETRIEVAL_CANDIDATE_K`,
`RETRIEVAL_SCORE_THRESHOLD`, and `RETRIEVAL_DIVERSITY_THRESHOLD`.

---

## Folder structure

```
rag-fullstack/
├── backend/                  ← FastAPI app
│   ├── app/
│   │   ├── api/routes/       ← auth, chat, conversations, ingest, health
│   │   ├── core/             ← config, logging, security, database
│   │   ├── graph/            ← LangGraph nodes, edges, builder, state
│   │   ├── models/           ← SQLAlchemy ORM models + Pydantic schemas
│   │   ├── services/         ← vector store, conversation service
│   │   └── utils/            ← document chunker
│   ├── alembic/              ← DB migrations
│   ├── .env.example
│   ├── requirements.txt
│   └── main.py
│
├── frontend/                 ← Next.js 15 app
│   ├── app/
│   │   ├── login/            ← Login page
│   │   ├── register/         ← Register page
│   │   └── chat/[id]/        ← Chat page (dynamic per conversation)
│   ├── components/
│   │   ├── auth/             ← Auth forms
│   │   ├── chat/             ← ChatWindow, MessageBubble, Input…
│   │   ├── layout/           ← Sidebar, ChatLayout
│   │   └── ui/               ← Shared primitives
│   ├── hooks/                ← useChat, useConversations, useAuth
│   ├── lib/                  ← API client, utils
│   ├── store/                ← Zustand stores (persisted)
│   └── types/                ← TypeScript types mirroring backend schemas
│
└── docker-compose.yml        ← One command to run everything
```

---

## Quick start

### Option A — Docker (recommended)

```bash
cp backend/.env.example backend/.env
# Add your GOOGLE_API_KEY and replace SECRET_KEY before deployment

docker-compose up --build
# Backend  → http://localhost:8000
# Frontend → http://localhost:3000
# Browser API requests are proxied by Next.js through /api/*
```

### Option B — Manual

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in GOOGLE_API_KEY + DATABASE_URL
alembic upgrade head         # run DB migrations
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                  # → http://localhost:3000
```

When running the frontend manually, `.env.local` points API requests directly
to `http://localhost:8000`. In Docker, leave `NEXT_PUBLIC_API_URL` empty so
the browser uses Next.js `/api/*` proxy routes.

---

## Auth flow

1. Register at `/register` → stored in Postgres, password bcrypt-hashed
2. Login → receive `access_token` (15 min) + `refresh_token` (7 days)
3. Tokens stored in Zustand (persisted to localStorage)
4. Every API request sends `Authorization: Bearer <access_token>`
5. Auto-refresh when access token expires
6. All conversations, messages, and uploaded documents are scoped to the user
# RAG-Agent
# RAG-Agent
# RAG-Agent
