"""main.py — FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.graph.builder import build_graph
from app.api.routes import auth, conversations, chat, ingest
from app.models.schemas import HealthResponse

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting")
    build_graph()          # Compile graph once at startup
    logger.info("app_ready")
    yield
    logger.info("app_shutdown")


settings = get_settings()

app = FastAPI(
    title="RAG Agent API",
    description="Self-correcting RAG chatbot — FastAPI + LangGraph + Gemini Flash 2.5",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(ingest.router)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(status="ok")
