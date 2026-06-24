"""
app/services/__init__.py
Re-exports service classes from src/ for convenient access.
"""

from src.course_service import CourseService
from src.document_service import DocumentService
from src.rag_engine import RAGEngine
from src.notes_generator import NotesGenerator
from src.quiz_generator import QuizGenerator
from src.exam_analyzer import ExamAnalyzer
from src.study_planner import StudyPlanner
from src.processor_pipeline import ProcessorPipeline

__all__ = [
    "CourseService",
    "DocumentService",
    "RAGEngine",
    "NotesGenerator",
    "QuizGenerator",
    "ExamAnalyzer",
    "StudyPlanner",
    "ProcessorPipeline",
]
