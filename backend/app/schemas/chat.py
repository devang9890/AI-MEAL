from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ChatMessageItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty or only whitespace")
        return stripped


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The user's query")
    conversation: List[ChatMessageItem] = Field(
        default_factory=list,
        description="Previous turns of conversation in current session"
    )
    household_id: Optional[int] = Field(
        default=None,
        description="Optional active household ID to ground the context"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only")
        return stripped


class ChatResponse(BaseModel):
    reply: str
    success: bool = True
    sources: Optional[List[str]] = None
    error: Optional[str] = None
