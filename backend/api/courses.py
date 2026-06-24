"""
backend/api/courses.py
Course CRUD endpoints for SmartPrep AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.course_service import CourseService
from src.exceptions import DuplicateNameError, StorageError, ValidationError

router = APIRouter(prefix="/api/courses", tags=["courses"])

_service = CourseService()


class CreateCourseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CourseResponse(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str


def _course_to_response(course) -> CourseResponse:
    return CourseResponse(
        id=course.id,
        name=course.name,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat(),
    )


@router.post("/", response_model=CourseResponse, status_code=201)
def create_course(req: CreateCourseRequest):
    """Create a new course."""
    try:
        course = _service.create_course(req.name)
        return _course_to_response(course)
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message)


@router.get("/", response_model=list[CourseResponse])
def list_courses():
    """List all courses ordered by creation date."""
    courses = _service.list_courses()
    return [_course_to_response(c) for c in courses]


@router.put("/{course_id}", response_model=CourseResponse)
def rename_course(course_id: str, req: CreateCourseRequest):
    """Rename an existing course."""
    try:
        course = _service.rename_course(course_id, req.name)
        return _course_to_response(course)
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message)


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: str):
    """Delete a course and all associated data."""
    try:
        _service.delete_course(course_id)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message)
