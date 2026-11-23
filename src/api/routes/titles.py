from fastapi import APIRouter

from src.api.deps import CurrentUser
from src.schemas.questions.title import ChatTitleRequest, ChatTitleResponse
from src.services.questions.titles import chat_title

router = APIRouter(prefix="/chat-titles", tags=["chat-titles"])


@router.post("", response_model=ChatTitleResponse)
def create_chat_title(body: ChatTitleRequest, _: CurrentUser) -> ChatTitleResponse:
    return ChatTitleResponse(title=chat_title(body.message))
