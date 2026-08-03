from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.skin_quiz_agent import get_questionnaire, score_questionnaire

router = APIRouter()


@router.get("/quiz-questions")
def quiz_questions():
    """Returns the question set for the frontend to render."""
    return {"questions": get_questionnaire()}


class QuizAnswers(BaseModel):
    answers: dict[str, str]   # {question_id: selected_option_key}


@router.post("/quiz-result")
def quiz_result(payload: QuizAnswers):
    """Scores the questionnaire and returns the resulting skin type."""
    return score_questionnaire(payload.answers)