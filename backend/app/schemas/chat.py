"""
Pydantic request/response schemas for the Chat router.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessagePairSchema(BaseModel):
    """A single conversation turn."""

    user_message: str = Field(..., description="The student's message")
    assistant_message: str = Field(..., description="The assistant's response")


class ChatQueryRequest(BaseModel):
    """Request body for a RAG chat query."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The student's question",
    )
    conversation_history: list[MessagePairSchema] = Field(
        default_factory=list,
        description="Previous conversation turns (max 10 used internally)",
    )


class ChatSummarizeRequest(BaseModel):
    """Request body for a topic summary."""

    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The topic to summarize",
    )


class GeneralAnswerRequest(BaseModel):
    """Request body for a general knowledge answer (no RAG)."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The student's question to answer from general knowledge",
    )


class CitationSchema(BaseModel):
    """A source citation."""

    document_name: str = Field(..., description="Name of the source document")
    category: str = Field(..., description="Document category")
    page_number: int | None = Field(None, description="Page number if available")
    section: str | None = Field(None, description="Section heading if available")


class ChatResponse(BaseModel):
    """Response model for a RAG chat query or topic summary."""

    answer: str = Field(..., description="The generated answer text")
    citations: list[CitationSchema] = Field(
        default_factory=list,
        description="Source citations for the answer",
    )
    no_relevant_content: bool = Field(
        False,
        description="True if no relevant content was found in the course",
    )
