from fastapi import APIRouter

from src.api.deps import CurrentUser
from src.schemas.questions.question import QuestionRequest, QuestionResponse
from src.services.questions.questions import ask_question

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=QuestionResponse)
def create_question(body: QuestionRequest, _: CurrentUser) -> QuestionResponse:
    return ask_question(body.question)
