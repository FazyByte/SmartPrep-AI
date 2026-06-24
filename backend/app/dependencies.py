"""
app/dependencies.py
FastAPI dependency injection for service instances.

Each service is instantiated once (singleton pattern) using paths from config.
Router endpoints use these via Depends().
"""

from __future__ import annotations

from functools import lru_cache

from app.config import CHROMA_DIR, UPLOADS_DIR

from src.course_service import CourseService
from src.document_service import DocumentService
from src.rag_engine import RAGEngine
from src.notes_generator import NotesGenerator
from src.quiz_generator import QuizGenerator
from src.exam_analyzer import ExamAnalyzer
from src.study_planner import StudyPlanner


@lru_cache(maxsize=1)
def get_course_service() -> CourseService:
    """Singleton CourseService instance."""
    return CourseService(chroma_path=str(CHROMA_DIR))


@lru_cache(maxsize=1)
def get_document_service() -> DocumentService:
    """Singleton DocumentService instance."""
    return DocumentService(
        chroma_path=str(CHROMA_DIR),
        uploads_path=str(UPLOADS_DIR),
    )


@lru_cache(maxsize=1)
def get_rag_engine() -> RAGEngine:
    """Singleton RAGEngine instance."""
    return RAGEngine(chroma_path=str(CHROMA_DIR))


@lru_cache(maxsize=1)
def get_notes_generator() -> NotesGenerator:
    """Singleton NotesGenerator instance."""
    return NotesGenerator(chroma_path=str(CHROMA_DIR))


@lru_cache(maxsize=1)
def get_quiz_generator() -> QuizGenerator:
    """Singleton QuizGenerator instance."""
    return QuizGenerator(chroma_path=str(CHROMA_DIR))


@lru_cache(maxsize=1)
def get_exam_analyzer() -> ExamAnalyzer:
    """Singleton ExamAnalyzer instance."""
    return ExamAnalyzer(uploads_root=str(UPLOADS_DIR))


@lru_cache(maxsize=1)
def get_study_planner() -> StudyPlanner:
    """Singleton StudyPlanner instance (with ExamAnalyzer integration)."""
    analyzer = get_exam_analyzer()
    return StudyPlanner(exam_analyzer=analyzer)
