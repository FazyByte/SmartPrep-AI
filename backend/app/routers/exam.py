"""
app/routers/exam.py
Exam analysis endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_exam_analyzer
from app.schemas.exam import (
    ExamAnalysisResponse,
    ExamAnalyzeRequest,
    TopicFrequencySchema,
    TrendEntrySchema,
)
from src.exam_analyzer import ExamAnalyzer

router = APIRouter()


@router.post("/{course_id}/analyze", response_model=ExamAnalysisResponse)
def analyze_exam(
    course_id: str,
    body: ExamAnalyzeRequest,
    analyzer: ExamAnalyzer = Depends(get_exam_analyzer),
):
    """Analyze exam patterns from Question Paper documents in a course."""
    result = analyzer.analyze(
        course_id=course_id,
        skip_ocr=body.skip_ocr,
    )

    trends: list[TrendEntrySchema] | None = None
    if result.trends is not None:
        trends = [
            TrendEntrySchema(
                topic=t.topic,
                earliest_count=t.earliest_count,
                latest_count=t.latest_count,
                change=t.change,
            )
            for t in result.trends
        ]

    return ExamAnalysisResponse(
        topics=[
            TopicFrequencySchema(topic=tf.topic, count=tf.count)
            for tf in result.topics
        ],
        chapter_weightage=result.chapter_weightage,
        trends=trends,
    )
