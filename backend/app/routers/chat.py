"""
app/routers/chat.py
RAG chat query and topic summary endpoints with persistent history.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.dependencies import get_rag_engine
from app.schemas.chat import (
    ChatQueryRequest,
    ChatResponse,
    ChatSummarizeRequest,
    CitationSchema,
    GeneralAnswerRequest,
)
from src.database import get_connection, transaction
from src.models import MessagePair
from src.rag_engine import RAGEngine

router = APIRouter()


def _save_message(course_id: str, role: str, content: str, citations: list | None = None) -> dict:
    """Persist a chat message to SQLite and return it as a dict."""
    msg_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()
    citations_json = json.dumps([c.dict() if hasattr(c, 'dict') else c for c in citations]) if citations else None

    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_messages (id, course_id, role, content, citations, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, course_id, role, content, citations_json, now),
    )
    return {"id": msg_id, "course_id": course_id, "role": role, "content": content, "citations": citations_json, "created_at": now}


@router.get("/{course_id}/history")
def get_chat_history(course_id: str):
    """Retrieve all chat messages for a course, ordered by created_at."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, course_id, role, content, citations, created_at "
        "FROM chat_messages WHERE course_id = ? ORDER BY created_at ASC",
        (course_id,),
    ).fetchall()

    messages = []
    for row in rows:
        citations_raw = row["citations"]
        citations = json.loads(citations_raw) if citations_raw else None
        messages.append({
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "citations": citations,
            "created_at": row["created_at"],
        })

    return {"messages": messages}


@router.delete("/{course_id}/history", status_code=204)
def clear_chat_history(course_id: str):
    """Delete all chat messages for a course."""
    conn = get_connection()
    conn.execute("DELETE FROM chat_messages WHERE course_id = ?", (course_id,))
    return None


@router.post("/{course_id}/query", response_model=ChatResponse)
def chat_query(
    course_id: str,
    body: ChatQueryRequest,
    engine: RAGEngine = Depends(get_rag_engine),
):
    """Answer a student's question using retrieval-augmented generation."""
    # Save user message
    _save_message(course_id, "user", body.question)

    # Load recent history from DB for context (last 10 pairs)
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM chat_messages "
        "WHERE course_id = ? ORDER BY created_at ASC",
        (course_id,),
    ).fetchall()

    # Build MessagePair list from DB history (pair user+assistant messages)
    history: list[MessagePair] = []
    i = 0
    while i < len(rows) - 1:
        if rows[i]["role"] == "user" and rows[i + 1]["role"] == "assistant":
            history.append(MessagePair(
                user_message=rows[i]["content"],
                assistant_message=rows[i + 1]["content"],
            ))
            i += 2
        else:
            i += 1

    # Keep only last 10 pairs for context
    history = history[-10:]

    result = engine.query(
        course_id=course_id,
        question=body.question,
        conversation_history=history,
    )

    # Save assistant response
    citations_dicts = [
        {"document_name": c.document_name, "category": c.category,
         "page_number": c.page_number, "section": c.section}
        for c in result.citations
    ]

    answer_content = result.answer if not result.no_relevant_content else ""
    _save_message(course_id, "assistant", answer_content, citations_dicts if citations_dicts else None)

    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationSchema(
                document_name=c.document_name,
                category=c.category,
                page_number=c.page_number,
                section=c.section,
            )
            for c in result.citations
        ],
        no_relevant_content=result.no_relevant_content,
    )


@router.post("/{course_id}/summarize", response_model=ChatResponse)
def chat_summarize(
    course_id: str,
    body: ChatSummarizeRequest,
    engine: RAGEngine = Depends(get_rag_engine),
):
    """Generate a topic summary using retrieval-augmented generation."""
    result = engine.summarize_topic(
        course_id=course_id,
        topic=body.topic,
    )

    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationSchema(
                document_name=c.document_name,
                category=c.category,
                page_number=c.page_number,
                section=c.section,
            )
            for c in result.citations
        ],
        no_relevant_content=result.no_relevant_content,
    )


@router.post("/{course_id}/general", response_model=ChatResponse)
def general_answer(
    course_id: str,
    body: GeneralAnswerRequest,
):
    """Answer a question using LLM general knowledge (no RAG retrieval)."""
    import ollama as ollama_client
    from app.config import CHAT_MODEL

    prompt = (
        "You are a helpful academic assistant. Answer the following question "
        "clearly and accurately using your general knowledge. Provide a "
        "well-structured, educational answer suitable for a university student.\n\n"
        f"Question: {body.question}\n\n"
        "Answer:"
    )

    try:
        response = ollama_client.chat(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )

        if isinstance(response, dict):
            message = response.get("message", {})
            answer = message.get("content", "") if isinstance(message, dict) else ""
        else:
            message = getattr(response, "message", None)
            answer = getattr(message, "content", "") if message else ""

    except Exception as exc:
        answer = f"Sorry, I couldn't generate an answer: {str(exc)}"

    # Save to chat history
    _save_message(course_id, "user", body.question)
    _save_message(course_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        citations=[],
        no_relevant_content=False,
    )
