from pydantic import BaseModel, Field


class ChatTitleRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ChatTitleResponse(BaseModel):
    title: str
