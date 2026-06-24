"""
Pydantic request/response schemas for the Exam Analysis router.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExamAnalyzeRequest(BaseModel):
    """Request body for exam pattern analysis."""

    skip_ocr: bool = Field(
        False,
        description="If True, skip OCR for scanned pages and use only the text layer",
    )


class TopicFrequencySchema(BaseModel):
    """A topic with its frequency count."""

    topic: str = Field(..., description="Topic name")
    count: int = Field(..., description="Number of occurrences across question papers")


class TrendEntrySchema(BaseModel):
    """Change in a topic's frequency between earliest and latest year."""

    topic: str = Field(..., description="Topic name")
    earliest_count: int = Field(..., description="Count in the earliest year")
    latest_count: int = Field(..., description="Count in the latest year")
    change: int = Field(..., description="Difference (latest - earliest)")


class ExamAnalysisResponse(BaseModel):
    """Response model for exam analysis results."""

    topics: list[TopicFrequencySchema] = Field(
        ...,
        description="Top topics sorted by frequency (max 20)",
    )
    chapter_weightage: dict[str, float] = Field(
        ...,
        description="Topic to percentage weightage mapping",
    )
    trends: list[TrendEntrySchema] | None = Field(
        None,
        description="Trend entries (None if fewer than 3 year-distinct papers)",
    )
