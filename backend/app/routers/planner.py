"""
app/routers/planner.py
Study plan generation endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_study_planner
from app.schemas.planner import (
    PlannerGenerateRequest,
    StudyDaySchema,
    StudyPlanResponse,
)
from src.study_planner import StudyPlanner

router = APIRouter()


@router.post("/generate", response_model=StudyPlanResponse)
def generate_plan(
    body: PlannerGenerateRequest,
    planner: StudyPlanner = Depends(get_study_planner),
):
    """Generate a personalized day-by-day study plan."""
    plan = planner.generate_plan(
        exam_date=body.exam_date,
        daily_hours=body.daily_hours,
        topics=body.topics,
        course_id=body.course_id,
    )

    return StudyPlanResponse(
        days=[
            StudyDaySchema(
                date=day.date,
                is_revision=day.is_revision,
                topics=day.topics,
                duration_per_topic_hours=day.duration_per_topic_hours,
            )
            for day in plan.days
        ],
        is_condensed=plan.is_condensed,
        condensed_notice=plan.condensed_notice,
    )
