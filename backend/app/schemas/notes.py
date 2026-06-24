"""
Pydantic request/response schemas for the Notes router.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NoteTypeEnum(str, Enum):
    """Available note generation formats."""

    SHORT_SUMMARY = "Short Summary"
    DETAILED_SUMMARY = "Detailed Summary"
    REVISION_NOTES = "Revision Notes"
    FORMULA_SHEET = "Formula Sheet"


class NotesGenerateRequest(BaseModel):
    """Request body for generating notes."""

    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The topic to generate notes about",
    )
    note_type: NoteTypeEnum = Field(
        ...,
        description="The output format for the generated notes",
    )
    document_id: str | None = Field(
        None,
        description="Optional specific document to generate notes from",
    )


class CitationSchema(BaseModel):
    """A source citation within a notes section."""

    document_name: str = Field(..., description="Source document name")
    category: str = Field(..., description="Document category")
    page_number: int | None = Field(None, description="Page number if available")
    section: str | None = Field(None, description="Section heading if available")


class NoteSectionSchema(BaseModel):
    """A single section of generated notes."""

    heading: str | None = Field(None, description="Section heading")
    content: str = Field(..., description="Section content text")
    citations: list[CitationSchema] = Field(
        default_factory=list,
        description="Citations for this section",
    )


class NotesResponse(BaseModel):
    """Response model for generated notes."""

    note_type: NoteTypeEnum = Field(..., description="The note format that was generated")
    sections: list[NoteSectionSchema] = Field(
        ..., description="List of note sections with content and citations"
    )
