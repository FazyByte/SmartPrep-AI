"""
app/routers/documents.py
Upload, list, delete, and retry-processing endpoints for Documents.
"""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.dependencies import get_document_service
from app.schemas.documents import (
    DocumentCategoryEnum,
    DocumentListResponse,
    DocumentResponse,
    ProcessingStatusEnum,
)
from src.document_service import DocumentService
from src.models import DocumentCategory
from src.processor_pipeline import ProcessorPipeline
from app.config import UPLOADS_DIR, CHROMA_DIR
from src.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _process_in_background(document_id: str) -> None:
    """Run the processing pipeline in a background thread."""
    try:
        pipeline = ProcessorPipeline(
            uploads_root=str(UPLOADS_DIR),
            chroma_path=str(CHROMA_DIR),
        )
        pipeline.process(document_id)
        logger.info(
            f"Background processing completed for document '{document_id}'",
            extra={"operation": "bg_process", "id": document_id},
        )
    except Exception as exc:
        logger.error(
            f"Background processing failed for document '{document_id}': {exc}",
            extra={"operation": "bg_process", "id": document_id},
        )


@router.post("/{course_id}/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    course_id: str,
    file: UploadFile = File(...),
    display_name: str = Form(...),
    category: DocumentCategoryEnum = Form(...),
    skip_duplicate_check: bool = Form(False),
    service: DocumentService = Depends(get_document_service),
):
    """Upload a document to a course. Processing runs in background."""
    file_bytes = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    original_filename = file.filename or "unknown"

    doc_category = DocumentCategory(category.value)

    document = service.upload_document(
        course_id=course_id,
        file_bytes=file_bytes,
        original_filename=original_filename,
        display_name=display_name,
        category=doc_category,
        mime_type=mime_type,
        skip_duplicate_check=skip_duplicate_check,
    )

    # Trigger processing in background thread (non-blocking)
    thread = threading.Thread(
        target=_process_in_background,
        args=(document.id,),
        daemon=True,
    )
    thread.start()

    return DocumentResponse(
        id=document.id,
        course_id=document.course_id,
        display_name=document.display_name,
        original_filename=document.original_filename,
        category=DocumentCategoryEnum(document.category.value),
        file_size=document.file_size,
        mime_type=document.mime_type,
        status=ProcessingStatusEnum(document.status.value),
        error_details=document.error_details,
        uploaded_at=document.uploaded_at,
        processed_at=document.processed_at,
    )


@router.get("/{course_id}", response_model=DocumentListResponse)
def list_documents(
    course_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """List all documents for a course, ordered by uploaded_at ascending."""
    docs = service.list_documents(course_id)
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=d.id,
                course_id=d.course_id,
                display_name=d.display_name,
                original_filename=d.original_filename,
                category=DocumentCategoryEnum(d.category.value),
                file_size=d.file_size,
                mime_type=d.mime_type,
                status=ProcessingStatusEnum(d.status.value),
                error_details=d.error_details,
                uploaded_at=d.uploaded_at,
                processed_at=d.processed_at,
            )
            for d in docs
        ]
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """Delete a document with best-effort cleanup of file and embeddings."""
    service.delete_document(document_id=document_id)
    return None


@router.get("/{course_id}/status/{document_id}")
def get_document_status(
    course_id: str,
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """Get the current processing status of a document."""
    docs = service.list_documents(course_id)
    doc = next((d for d in docs if d.id == document_id), None)
    if doc is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.status.value, "error_details": doc.error_details}


@router.post("/{document_id}/retry", status_code=202)
def retry_processing(document_id: str):
    """Retry processing for a failed document. Returns immediately."""
    thread = threading.Thread(
        target=_process_in_background,
        args=(document_id,),
        daemon=True,
    )
    thread.start()
    return {"message": "Processing restarted", "document_id": document_id}
