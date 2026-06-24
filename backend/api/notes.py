"""
backend/api/notes.py
Notes generation endpoints for SmartPrep AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.exceptions import DocumentNotReadyError, InfoMessage
from src.models import NoteType
from src.notes_generator import NotesGenerator

router = APIRouter(prefix="/api/notes", tags=["notes"])

_generator = NotesGenerator()


class NotesRequest(BaseModel):
    course_id: str
    topic: str
    note_type: str  # "Short Summary", "Detailed Summary", "Revision Notes", "Formula Sheet"
    document_id: str | None = None


class CitationResponse(BaseModel):
    document_name: str
    category: str
    page_number: int | None = None
    section: str | None = None


class NoteSectionResponse(BaseModel):
    heading: str | None = None
    content: str
    citations: list[CitationResponse]


class NotesResponse(BaseModel):
    note_type: str
    sections: list[NoteSectionResponse]


@router.post("/generate", response_model=NotesResponse)
def generate_notes(req: NotesRequest):
    """Generate notes for a topic in a course."""
    # Parse note type
    try:
        note_type = NoteType(req.note_type)
    except ValueError:
        valid = ", ".join(nt.value for nt in NoteType)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid note_type. Must be one of: {valid}.",
        )

    try:
        result = _generator.generate(
            course_id=req.course_id,
            topic=req.topic,
            note_type=note_type,
            document_id=req.document_id,
        )
    except DocumentNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InfoMessage as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Notes generation failed: {str(exc)}")

    return NotesResponse(
        note_type=result.note_type.value,
        sections=[
            NoteSectionResponse(
                heading=section.heading,
                content=section.content,
                citations=[
                    CitationResponse(
                        document_name=c.document_name,
                        category=c.category,
                        page_number=c.page_number,
                        section=c.section,
                    )
                    for c in section.citations
                ],
            )
            for section in result.sections
        ],
    )
