"""
backend/api/quiz.py
Quiz generation and scoring endpoints for SmartPrep AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.exceptions import ValidationError
from src.models import Difficulty, MCQQuestion, OpenQuestion, QuestionType
from src.quiz_generator import QuizGenerator

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

_generator = QuizGenerator()


class QuizRequest(BaseModel):
    course_id: str
    question_type: str  # "MCQ", "True/False", "Short Answer", "Viva", "Long Answer"
    difficulty: str  # "Easy", "Medium", "Hard"
    topic: str
    count: int = 5


class MCQQuestionResponse(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanations: dict[str, str]
    source_category: str


class OpenQuestionResponse(BaseModel):
    question: str
    question_type: str
    model_answer: str | None = None
    outline_answer: str | None = None


class QuizResponse(BaseModel):
    questions: list[MCQQuestionResponse | OpenQuestionResponse]
    fallback_message: str | None = None


class ScoreRequest(BaseModel):
    quiz: QuizResponse
    answers: dict[int, str]  # question_index -> selected answer


class QuestionFeedbackResponse(BaseModel):
    question_index: int
    is_correct: bool
    correct_index: int
    explanation: str


class ScoreResponse(BaseModel):
    score_pct: float
    per_question: list[QuestionFeedbackResponse]


@router.post("/generate", response_model=QuizResponse)
def generate_quiz(req: QuizRequest):
    """Generate a quiz for a topic in a course."""
    # Parse question type
    try:
        question_type = QuestionType(req.question_type)
    except ValueError:
        valid = ", ".join(qt.value for qt in QuestionType)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid question_type. Must be one of: {valid}.",
        )

    # Parse difficulty
    try:
        difficulty = Difficulty(req.difficulty)
    except ValueError:
        valid = ", ".join(d.value for d in Difficulty)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid difficulty. Must be one of: {valid}.",
        )

    try:
        quiz = _generator.generate_quiz(
            course_id=req.course_id,
            question_type=question_type,
            difficulty=difficulty,
            topic=req.topic,
            count=req.count,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(exc)}")

    # Convert questions to response format
    questions: list[MCQQuestionResponse | OpenQuestionResponse] = []
    for q in quiz.questions:
        if isinstance(q, MCQQuestion):
            questions.append(
                MCQQuestionResponse(
                    question=q.question,
                    options=q.options,
                    correct_index=q.correct_index,
                    explanations={str(k): v for k, v in q.explanations.items()},
                    source_category=q.source_category,
                )
            )
        elif isinstance(q, OpenQuestion):
            questions.append(
                OpenQuestionResponse(
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


@router.post("/score", response_model=ScoreResponse)
def score_quiz(req: ScoreRequest):
    """Score an MCQ quiz."""
    from src.models import Quiz as QuizModel

    # Reconstruct the Quiz object from the request
    mcq_questions: list[MCQQuestion] = []
    for q in req.quiz.questions:
        if isinstance(q, MCQQuestionResponse):
            mcq_questions.append(
                MCQQuestion(
                    question=q.question,
                    options=q.options,
                    correct_index=q.correct_index,
                    explanations={int(k): v for k, v in q.explanations.items()},
                    source_category=q.source_category,
                )
            )

    if not mcq_questions:
        raise HTTPException(status_code=422, detail="No MCQ questions to score.")

    quiz_model = QuizModel(questions=mcq_questions, fallback_message=None)
    result = _generator.score_mcq(quiz_model, req.answers)

    return ScoreResponse(
        score_pct=result.score_pct,
        per_question=[
            QuestionFeedbackResponse(
                question_index=f.question_index,
                is_correct=f.is_correct,
                correct_index=f.correct_index,
                explanation=f.explanation,
            )
            for f in result.per_question
        ],
    )
