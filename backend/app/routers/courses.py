"""
app/routers/courses.py
CRUD endpoints for Course entities.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_course_service
from app.schemas.courses import (
    CourseCreateRequest,
    CourseListResponse,
    CourseRenameRequest,
    CourseResponse,
)
from src.course_service import CourseService

router = APIRouter()


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(
    body: CourseCreateRequest,
    service: CourseService = Depends(get_course_service),
):
    """Create a new course."""
    course = service.create_course(name=body.name)
    return CourseResponse(
        id=course.id,
        name=course.name,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


@router.get("", response_model=CourseListResponse)
def list_courses(
    service: CourseService = Depends(get_course_service),
):
    """List all courses ordered by created_at ascending."""
    courses = service.list_courses()
    return CourseListResponse(
        courses=[
            CourseResponse(
                id=c.id,
                name=c.name,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in courses
        ]
    )


@router.put("/{course_id}", response_model=CourseResponse)
def rename_course(
    course_id: str,
    body: CourseRenameRequest,
    service: CourseService = Depends(get_course_service),
):
    """Rename an existing course."""
    course = service.rename_course(course_id=course_id, new_name=body.name)
    return CourseResponse(
        id=course.id,
        name=course.name,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: str,
    service: CourseService = Depends(get_course_service),
):
    """Delete a course and its associated resources (best-effort cleanup)."""
    service.delete_course(course_id=course_id)
    return None
