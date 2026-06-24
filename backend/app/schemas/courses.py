"""
Pydantic request/response schemas for the Courses router.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CourseCreateRequest(BaseModel):
    """Request body for creating a new course."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Course name (1–100 characters, must be unique case-insensitively)",
    )


class CourseRenameRequest(BaseModel):
    """Request body for renaming an existing course."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="New course name (1–100 characters, must be unique case-insensitively)",
    )


class CourseResponse(BaseModel):
    """Response model for a single course."""

    id: str = Field(..., description="UUID of the course")
    name: str = Field(..., description="Course display name")
    created_at: datetime = Field(..., description="UTC timestamp of creation")
    updated_at: datetime = Field(..., description="UTC timestamp of last update")

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    """Response model for listing all courses."""

    courses: list[CourseResponse] = Field(
        default_factory=list,
        description="List of courses ordered by created_at ascending",
    )
