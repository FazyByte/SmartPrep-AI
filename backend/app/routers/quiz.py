"""
app/routers/quiz.py
Quiz generation and MCQ scoring endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.dependencies import get_quiz_generator
from app.schemas.quiz import (
    DifficultyEnum,
    MCQQuestionSchema,
    OpenQuestionSchema,
    QuestionFeedbackSchema,
    QuestionTypeEnum,
    QuizAttemptCreateRequest,
    QuizAttemptSchema,
    QuizAttemptsResponse,
    QuizGenerateRequest,
    QuizResponse,
    QuizScoreRequest,
    QuizScoreResponse,
    QuizStatsResponse,
)
from src.database import get_connection
from src.models import (
    Difficulty,
    MCQQuestion,
    OpenQuestion,
    QuestionType,
    Quiz,
)
from src.quiz_generator import QuizGenerator

router = APIRouter()


@router.post("/{course_id}/generate", response_model=QuizResponse)
def generate_quiz(
    course_id: str,
    body: QuizGenerateRequest,
    generator: QuizGenerator = Depends(get_quiz_generator),
):
    """Generate a quiz from the course's uploaded content."""
    question_type = QuestionType(body.question_type.value)
    difficulty = Difficulty(body.difficulty.value)

    quiz = generator.generate_quiz(
        course_id=course_id,
        question_type=question_type,
        difficulty=difficulty,
        topic=body.topic,
        count=body.count,
    )

    questions: list[MCQQuestionSchema | OpenQuestionSchema] = []
    for q in quiz.questions:
        if isinstance(q, MCQQuestion):
            questions.append(
                MCQQuestionSchema(
                    question=q.question,
                    options=q.options,
                    correct_index=q.correct_index,
                    explanations=q.explanations,
                    source_category=q.source_category,
                )
            )
        elif isinstance(q, OpenQuestion):
            questions.append(
                OpenQuestionSchema(
                    question=q.question,
                    question_type=q.question_type,
                    model_answer=q.model_answer,
                    outline_answer=q.outline_answer,
                )
            )

    return QuizResponse(
        questions=questions,
        fallback_message=quiz.fallback_message,
    )


@router.post("/score", response_model=QuizScoreResponse)
def score_quiz(
    body: QuizScoreRequest,
    generator: QuizGenerator = Depends(get_quiz_generator),
):
    """Score an MCQ quiz and produce per-question feedback."""
    # Reconstruct domain Quiz from the request schema
    domain_questions: list[MCQQuestion | OpenQuestion] = []
    for q in body.quiz.questions:
        if isinstance(q, MCQQuestionSchema):
            domain_questions.append(
                MCQQuestion(
                    question=q.question,
                    options=q.options,
                    correct_index=q.correct_index,
                    explanations=q.explanations,
                    source_category=q.source_category,
                )
            )
        elif isinstance(q, OpenQuestionSchema):
            domain_questions.append(
                OpenQuestion(
                    question=q.question,
                    question_type=q.question_type,
                    model_answer=q.model_answer,
                    outline_answer=q.outline_answer,
                )
            )

    domain_quiz = Quiz(
        questions=domain_questions,
        fallback_message=body.quiz.fallback_message,
    )

    result = generator.score_mcq(quiz=domain_quiz, answers=body.answers)

    return QuizScoreResponse(
        score_pct=result.score_pct,
        per_question=[
            QuestionFeedbackSchema(
                question_index=fb.question_index,
                is_correct=fb.is_correct,
                correct_index=fb.correct_index,
                explanation=fb.explanation,
            )
            for fb in result.per_question
        ],
    )



# ---------------------------------------------------------------------------
# Quiz Performance Tracking
# ---------------------------------------------------------------------------


@router.post("/{course_id}/attempts", response_model=QuizAttemptSchema)
def save_quiz_attempt(course_id: str, body: QuizAttemptCreateRequest):
    """Save a quiz attempt for performance tracking."""
    conn = get_connection()
    attempt_id = str(uuid.uuid4())
    attempted_at = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO quiz_attempts (id, course_id, question_type, topic, score_pct, total_questions, correct_count, attempted_at, quiz_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id,
            course_id,
            body.question_type,
            body.topic,
            body.score_pct,
            body.total_questions,
            body.correct_count,
            attempted_at,
            body.quiz_data,
        ),
    )

    return QuizAttemptSchema(
        id=attempt_id,
        course_id=course_id,
        question_type=body.question_type,
        topic=body.topic,
        score_pct=body.score_pct,
        total_questions=body.total_questions,
        correct_count=body.correct_count,
        attempted_at=attempted_at,
        quiz_data=body.quiz_data,
    )


@router.get("/{course_id}/attempts", response_model=QuizAttemptsResponse)
def get_quiz_attempts(course_id: str):
    """Get all quiz attempts for a course, ordered by most recent first."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, course_id, question_type, topic, score_pct, total_questions, correct_count, attempted_at, quiz_data
        FROM quiz_attempts
        WHERE course_id = ?
        ORDER BY attempted_at DESC
        """,
        (course_id,),
    ).fetchall()

    attempts = [
        QuizAttemptSchema(
            id=row["id"],
            course_id=row["course_id"],
            question_type=row["question_type"],
            topic=row["topic"],
            score_pct=row["score_pct"],
            total_questions=row["total_questions"],
            correct_count=row["correct_count"],
            attempted_at=row["attempted_at"],
            quiz_data=row["quiz_data"],
        )
        for row in rows
    ]

    return QuizAttemptsResponse(attempts=attempts)


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptSchema)
def get_quiz_attempt_detail(attempt_id: str):
    """Get a single quiz attempt by ID, including full quiz_data."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, course_id, question_type, topic, score_pct, total_questions, correct_count, attempted_at, quiz_data
        FROM quiz_attempts
        WHERE id = ?
        """,
        (attempt_id,),
    ).fetchone()

    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    return QuizAttemptSchema(
        id=row["id"],
        course_id=row["course_id"],
        question_type=row["question_type"],
        topic=row["topic"],
        score_pct=row["score_pct"],
        total_questions=row["total_questions"],
        correct_count=row["correct_count"],
        attempted_at=row["attempted_at"],
        quiz_data=row["quiz_data"],
    )


@router.get("/stats", response_model=QuizStatsResponse)
def get_quiz_stats():
    """Get overall quiz statistics across all courses."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COUNT(*) as total_attempts,
            COALESCE(AVG(score_pct), 0) as average_score,
            COALESCE(MAX(score_pct), 0) as best_score,
            COALESCE(SUM(total_questions), 0) as total_questions_answered
        FROM quiz_attempts
        """
    ).fetchone()

    return QuizStatsResponse(
        total_attempts=row["total_attempts"],
        average_score=round(row["average_score"], 1),
        best_score=round(row["best_score"], 1),
        total_questions_answered=row["total_questions_answered"],
    )
