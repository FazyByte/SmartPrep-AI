"""
Pydantic request/response schemas for the Study Planner router.
"""

import datetime as _dt

from pydantic import BaseModel, Field


class PlannerGenerateRequest(BaseModel):
    """Request body for generating a study plan."""

    exam_date: _dt.date = Field(
        ...,
        description="The date of the exam (must be strictly in the future)",
    )
    daily_hours: float = Field(
        ...,
        ge=0.5,
        le=24.0,
        description="Hours available per day for studying (0.5–24.0, multiples of 0.5)",
    )
    topics: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of topics to cover (1–50 items)",
    )
    course_id: str | None = Field(
        None,
        description="Optional course ID for frequency-weighted distribution",
    )


class StudyDaySchema(BaseModel):
    """A single day in the generated study schedule."""

    date: _dt.date = Field(..., description="The calendar date")
    is_revision: bool = Field(..., description="Whether this is a revision day")
    topics: list[str] = Field(..., description="Topics assigned to this day")
    duration_per_topic_hours: float = Field(
        ..., description="Hours allocated per topic (rounded to nearest 0.5)"
    )


class StudyPlanResponse(BaseModel):
    """Response model for a generated study plan."""

    days: list[StudyDaySchema] = Field(
        ..., description="Day-by-day study schedule"
    )
    is_condensed: bool = Field(
        ..., description="True if this is a last-minute condensed plan"
    )
    condensed_notice: str | None = Field(
        None,
        description="Informational notice about the condensed plan or frequency fallback",
    )
