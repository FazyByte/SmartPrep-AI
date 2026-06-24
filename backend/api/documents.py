"""
backend/api/documents.py
Document upload, list, and delete endpoints for SmartPrep AI.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.document_service import DocumentService
from src.exceptions import (
    DuplicateFoundError,
    StorageError,
    ValidationError,
)
from src.models import DocumentCategory
from src.processor_pipeline import ProcessorPipeline

router = APIRouter(prefix="/api/documents", tags=["documents"])

_service = DocumentService()
_pipeline = ProcessorPipeline()


class DocumentResponse(BaseModel):
    id: str
    course_id: str
    display_name: str
    original_filename: str
    category: str
    file_size: int
    status: str
    uploaded_at: str


def _doc_to_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        course_id=doc.course_id,
        display_name=doc.display_name,
        original_filename=doc.original_filename,
        category=doc.category.value if hasattr(doc.category, "value") else doc.category,
        file_size=doc.file_size,
        status=doc.status.value if hasattr(doc.status, "value") else doc.status,
        uploaded_at=doc.uploaded_at.isoformat(),
    )


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    display_name: str = Form(...),
    category: str = Form(...),
    skip_duplicate_check: bool = Form(False),
):
    """Upload a document to a course."""
    try:
        doc_category = DocumentCategory(category)
    except ValueError:
        valid = ", ".join(c.value for c in DocumentCategory)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category. Must be one of: {valid}.",
        )

    file_bytes = await file.read()
    mime_type = file.content_type or "application/octet-stream"

    try:
        document = _service.upload_document(
            course_id=course_id,
            file_bytes=file_bytes,
            original_filename=file.filename or "unknown",
            display_name=display_name,
            category=doc_category,
            mime_type=mime_type,
            skip_duplicate_check=skip_duplicate_check,
        )

        # Trigger processing pipeline in background
        try:
            _pipeline.process(document.id)
        except Exception:
            pass  # Processing errors are stored in the document status

        return _doc_to_response(document)

    except DuplicateFoundError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message)


@router.get("/{course_id}", response_model=list[DocumentResponse])
def list_documents(course_id: str):
    """List all documents for a course."""
    documents = _service.list_documents(course_id)
    return [_doc_to_response(d) for d in documents]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str):
    """Delete a document."""
    try:
        _service.delete_document(document_id)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message)
