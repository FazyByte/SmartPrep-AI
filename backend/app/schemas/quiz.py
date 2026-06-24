"""
Pydantic request/response schemas for the Quiz router.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class QuestionTypeEnum(str, Enum):
    """Supported question types."""

    MCQ = "MCQ"
    TRUE_FALSE = "True/False"
    SHORT_ANSWER = "Short Answer"
    VIVA = "Viva"
    LONG_ANSWER = "Long Answer"


class DifficultyEnum(str, Enum):
    """Difficulty levels."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class QuizGenerateRequest(BaseModel):
    """Request body for generating a quiz."""

    question_type: QuestionTypeEnum = Field(
        ..., description="Type of questions to generate"
    )
    difficulty: DifficultyEnum = Field(
        ..., description="Difficulty level for the questions"
    )
    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Topic to generate questions about",
    )
    count: int = Field(
        ...,
        ge=1,
        le=50,
        description="Number of questions to generate (1–50)",
    )


class MCQQuestionSchema(BaseModel):
    """A multiple-choice question."""

    question: str = Field(..., description="The question text")
    options: list[str] = Field(..., description="Exactly 4 answer options")
    correct_index: int = Field(
        ..., ge=0, le=3, description="0-based index of the correct option"
    )
    explanations: dict[int, str] = Field(
        ..., description="Per-option explanations keyed by option index"
    )
    source_category: str = Field(
        ..., description="Source category (Question Paper, Textbook, Notes)"
    )


class OpenQuestionSchema(BaseModel):
    """An open-ended question (short answer, viva, long answer)."""

    question: str = Field(..., description="The question text")
    question_type: str = Field(..., description="The question format")
    model_answer: str | None = Field(
        None, description="Model answer (for Short Answer and Viva)"
    )
    outline_answer: str | None = Field(
        None, description="Outline answer (for Long Answer)"
    )


class QuizResponse(BaseModel):
    """Response model for a generated quiz."""

    questions: list[MCQQuestionSchema | OpenQuestionSchema] = Field(
        ..., description="List of generated questions"
    )
    fallback_message: str | None = Field(
        None,
        description="Informational message when content was insufficient",
    )


class QuizScoreRequest(BaseModel):
    """Request body for scoring an MCQ quiz."""

    quiz: QuizResponse = Field(..., description="The quiz to score")
    answers: dict[int, str] = Field(
        ...,
        description="Student answers keyed by question index (0-based)",
    )


class QuestionFeedbackSchema(BaseModel):
    """Per-question feedback after scoring."""

    question_index: int = Field(..., description="0-based question index")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    correct_index: int = Field(..., description="Index of the correct option")
    explanation: str = Field(..., description="Explanation for the correct answer")


class QuizScoreResponse(BaseModel):
    """Response model for quiz scoring results."""

    score_pct: float = Field(..., description="Score as a percentage (0–100)")
    per_question: list[QuestionFeedbackSchema] = Field(
        ..., description="Per-question feedback"
    )


class QuizAttemptCreateRequest(BaseModel):
    """Request body for saving a quiz attempt."""

    question_type: str = Field(..., description="Type of quiz taken")
    topic: str = Field(..., min_length=1, max_length=500, description="Topic tested")
    score_pct: float = Field(..., ge=0, le=100, description="Score percentage")
    total_questions: int = Field(..., ge=1, description="Total questions in the quiz")
    correct_count: int = Field(..., ge=0, description="Number of correct answers")
    quiz_data: str | None = Field(None, description="JSON string of {questions, answers, result}")


class QuizAttemptSchema(BaseModel):
    """A saved quiz attempt."""

    id: str
    course_id: str
    question_type: str
    topic: str
    score_pct: float
    total_questions: int
    correct_count: int
    attempted_at: str
    quiz_data: str | None = None


class QuizAttemptsResponse(BaseModel):
    """Response model for quiz attempts list."""

    attempts: list[QuizAttemptSchema]


class QuizStatsResponse(BaseModel):
    """Overall quiz statistics."""

    total_attempts: int
    average_score: float
    best_score: float
    total_questions_answered: int
