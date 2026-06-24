"""
app/routers/notes.py
Notes generation endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_notes_generator
from app.schemas.notes import (
    CitationSchema,
    NoteSectionSchema,
    NotesGenerateRequest,
    NotesResponse,
    NoteTypeEnum,
)
from src.models import NoteType
from src.notes_generator import NotesGenerator

router = APIRouter()


@router.post("/{course_id}/generate", response_model=NotesResponse)
def generate_notes(
    course_id: str,
    body: NotesGenerateRequest,
    generator: NotesGenerator = Depends(get_notes_generator),
):
    """Generate notes for a topic within a course."""
    note_type = NoteType(body.note_type.value)

    output = generator.generate(
        course_id=course_id,
        topic=body.topic,
        note_type=note_type,
        document_id=body.document_id,
    )

    return NotesResponse(
        note_type=NoteTypeEnum(output.note_type.value),
        sections=[
            NoteSectionSchema(
                heading=section.heading,
                content=section.content,
                citations=[
                    CitationSchema(
                        document_name=c.document_name,
                        category=c.category,
                        page_number=c.page_number,
                        section=c.section,
                    )
                    for c in section.citations
                ],
            )
            for section in output.sections
        ],
    )
