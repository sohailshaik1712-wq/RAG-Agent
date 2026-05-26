"""app/models/schemas.py — Pydantic request/response models."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, EmailStr


# ── Auth ──────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id:         str
    email:      str
    username:   str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Conversations ─────────────────────────────────────────────

class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=200)


class ConversationUpdate(BaseModel):
    title: str = Field(..., max_length=200)


class DocumentOut(BaseModel):
    id:           str
    filename:     str
    chunks_created: int
    uploaded_at:  datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id:         str
    title:      str
    created_at: datetime
    updated_at: datetime
    documents:  list[DocumentOut] = []

    model_config = {"from_attributes": True}


# ── Messages ──────────────────────────────────────────────────

class MessageOut(BaseModel):
    id:         str
    role:       Literal["user", "assistant"]
    content:    str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(ConversationOut):
    messages: list[MessageOut] = []


# ── Chat ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    conversation_id: str
    message:         str = Field(..., min_length=1, max_length=4000)


class ChatStreamEvent(BaseModel):
    type: Literal["token", "metadata", "done", "error"]
    data: str | dict = ""


# ── Ingest ────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    status:         Literal["success", "error"]
    filename:       str
    chunks_created: int
    message:        str


# ── Health ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  Literal["ok", "degraded"]
    version: str = "2.0.0"
