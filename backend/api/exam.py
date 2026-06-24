"""
backend/api/exam.py
Exam analysis endpoints for SmartPrep AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.exam_analyzer import ExamAnalyzer

router = APIRouter(prefix="/api/exam", tags=["exam"])

_analyzer = ExamAnalyzer()


class TopicFrequencyResponse(BaseModel):
    topic: str
    count: int


class TrendEntryResponse(BaseModel):
    topic: str
    earliest_count: int
    latest_count: int
    change: int


class ExamAnalysisResponse(BaseModel):
    topics: list[TopicFrequencyResponse]
    chapter_weightage: dict[str, float]
    trends: list[TrendEntryResponse] | None = None


@router.post("/analyze/{course_id}", response_model=ExamAnalysisResponse)
def analyze_exams(course_id: str, skip_ocr: bool = False):
    """Run exam analysis for a course's question papers."""
    try:
        result = _analyzer.analyze(course_id, skip_ocr=skip_ocr)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Exam analysis failed: {str(exc)}")

    trends = None
    if result.trends is not None:
        trends = [
            TrendEntryResponse(
                topic=t.topic,
                earliest_count=t.earliest_count,
                latest_count=t.latest_count,
                change=t.change,
            )
            for t in result.trends
        ]

    return ExamAnalysisResponse(
        topics=[
            TopicFrequencyResponse(topic=tf.topic, count=tf.count)
            for tf in result.topics
        ],
        chapter_weightage=result.chapter_weightage,
        trends=trends,
    )
