"""
Pydantic request/response schemas for the Documents router.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentCategoryEnum(str, Enum):
    """Valid document categories."""

    TEXTBOOK = "Textbook"
    NOTES = "Notes"
    LAB_MANUAL = "Lab Manual"
    QUESTION_PAPER = "Question Paper"
    SYLLABUS = "Syllabus"


class ProcessingStatusEnum(str, Enum):
    """Document processing statuses."""

    PROCESSING = "processing"
    READY = "ready"
    PROCESSING_FAILED = "processing_failed"


class DocumentResponse(BaseModel):
    """Response model for a single document."""

    id: str = Field(..., description="UUID of the document")
    course_id: str = Field(..., description="UUID of the parent course")
    display_name: str = Field(..., description="Student-assigned display name")
    original_filename: str = Field(..., description="Original upload filename")
    category: DocumentCategoryEnum = Field(..., description="Document category")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    status: ProcessingStatusEnum = Field(..., description="Processing status")
    error_details: dict[str, Any] | None = Field(
        None, description="Error details if processing failed"
    )
    uploaded_at: datetime = Field(..., description="UTC timestamp of upload")
    processed_at: datetime | None = Field(
        None, description="UTC timestamp when processing completed"
    )

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Response model for listing documents in a course."""

    documents: list[DocumentResponse] = Field(
        default_factory=list,
        description="List of documents ordered by uploaded_at ascending",
    )
