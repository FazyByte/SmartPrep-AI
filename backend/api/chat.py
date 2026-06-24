"""
backend/api/chat.py
Chat/RAG query endpoints for SmartPrep AI.
"""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database import get_connection, transaction
from src.models import Citation, MessagePair
from src.rag_engine import RAGEngine

router = APIRouter(prefix="/api/chat", tags=["chat"])

_engine = RAGEngine()


class ChatRequest(BaseModel):
    course_id: str
    message: str


class CitationResponse(BaseModel):
    document_name: str
    category: str
    page_number: int | None = None
    section: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    no_relevant_content: bool = False


class ChatHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationResponse] | None = None
    created_at: str


@router.post("/query", response_model=ChatResponse)
def chat_query(req: ChatRequest):
    """Send a question to the RAG engine for a course."""
    # Fetch conversation history from DB
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT role, content, citations
        FROM chat_messages
        WHERE course_id = ?
        ORDER BY created_at ASC
        """,
        (req.course_id,),
    ).fetchall()

    # Build conversation history as MessagePair list
    history: list[MessagePair] = []
    user_msg = None
    for row in rows:
        if row["role"] == "user":
            user_msg = row["content"]
        elif row["role"] == "assistant" and user_msg:
            history.append(MessagePair(user_message=user_msg, assistant_message=row["content"]))
            user_msg = None

    try:
        result = _engine.query(req.course_id, req.message, history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(exc)}")

    # Store the conversation in the database
    now = datetime.now(tz=timezone.utc).isoformat()

    # Store user message
    with transaction() as tx_conn:
        tx_conn.execute(
            "INSERT INTO chat_messages (id, course_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, NULL, ?)",
            (str(uuid.uuid4()), req.course_id, "user", req.message, now),
        )

    # Store assistant response
    citations_json = json.dumps([
        {
            "document_name": c.document_name,
            "category": c.category,
            "page_number": c.page_number,
            "section": c.section,
        }
        for c in result.citations
    ])

    with transaction() as tx_conn:
        tx_conn.execute(
            "INSERT INTO chat_messages (id, course_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), req.course_id, "assistant", result.answer, citations_json, now),
        )

    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationResponse(
                document_name=c.document_name,
                category=c.category,
                page_number=c.page_number,
                section=c.section,
            )
            for c in result.citations
        ],
        no_relevant_content=result.no_relevant_content,
    )


@router.get("/history/{course_id}", response_model=list[ChatHistoryItem])
def get_chat_history(course_id: str):
    """Get chat history for a course."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, role, content, citations, created_at
        FROM chat_messages
        WHERE course_id = ?
        ORDER BY created_at ASC
        """,
        (course_id,),
    ).fetchall()

    items: list[ChatHistoryItem] = []
    for row in rows:
        citations = None
        if row["citations"]:
            try:
                raw_citations = json.loads(row["citations"])
                citations = [
                    CitationResponse(
                        document_name=c["document_name"],
                        category=c["category"],
                        page_number=c.get("page_number"),
                        section=c.get("section"),
                    )
                    for c in raw_citations
                ]
            except (json.JSONDecodeError, KeyError):
                citations = None

        items.append(
            ChatHistoryItem(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                citations=citations,
                created_at=row["created_at"],
            )
        )

    return items


@router.delete("/history/{course_id}", status_code=204)
def clear_chat_history(course_id: str):
    """Clear chat history for a course."""
    with transaction() as conn:
        conn.execute(
            "DELETE FROM chat_messages WHERE course_id = ?",
            (course_id,),
        )
