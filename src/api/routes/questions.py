from fastapi import APIRouter

from src.api.deps import CurrentUser, SessionDep
from src.schemas import QuestionRequest, QuestionResponse
from src.services.questions import ask_question

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=QuestionResponse)
def create_question(
    body: QuestionRequest,
    session: SessionDep,
    _: CurrentUser,
) -> QuestionResponse:
    return ask_question(session, body.question)
