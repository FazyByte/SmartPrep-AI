"""
backend/api/planner.py
Study planner endpoints for SmartPrep AI.
"""

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.exceptions import ValidationError
from src.exam_analyzer import ExamAnalyzer
from src.study_planner import StudyPlanner

router = APIRouter(prefix="/api/planner", tags=["planner"])

_exam_analyzer = ExamAnalyzer()
_planner = StudyPlanner(exam_analyzer=_exam_analyzer)


class PlannerRequest(BaseModel):
    exam_date: str  # ISO date string (YYYY-MM-DD)
    daily_hours: float
    topics: list[str]
    course_id: str | None = None


class StudyDayResponse(BaseModel):
    date: str
    is_revision: bool
    topics: list[str]
    duration_per_topic_hours: float


class StudyPlanResponse(BaseModel):
    days: list[StudyDayResponse]
    is_condensed: bool
    condensed_notice: str | None = None


@router.post("/generate", response_model=StudyPlanResponse)
def generate_plan(req: PlannerRequest):
    """Generate a personalized study plan."""
    # Parse exam date
    try:
        exam_date = date.fromisoformat(req.exam_date)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid exam_date format. Use YYYY-MM-DD.",
        )

    try:
        plan = _planner.generate_plan(
            exam_date=exam_date,
            daily_hours=req.daily_hours,
            topics=req.topics,
            course_id=req.course_id,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(exc)}")

    return StudyPlanResponse(
        days=[
            StudyDayResponse(
                date=d.date.isoformat(),
                is_revision=d.is_revision,
                topics=d.topics,
                duration_per_topic_hours=d.duration_per_topic_hours,
            )
            for d in plan.days
        ],
        is_condensed=plan.is_condensed,
        condensed_notice=plan.condensed_notice,
    )
