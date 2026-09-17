"""AI Chatbot API Router."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import _bearer, _verify_clerk_token, sync_user_data
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_chat_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Attempts to authenticate the user via Clerk Bearer token.
    If no token is provided or verification fails, returns None
    so the assistant can still provide general guidance gracefully.
    """
    if credentials is None or not credentials.credentials:
        return None

    try:
        payload = _verify_clerk_token(credentials.credentials)
        clerk_user_id: str = payload.get("sub", "")
        if not clerk_user_id:
            return None
        email: Optional[str] = payload.get("email")
        name: Optional[str] = payload.get("name")
        return sync_user_data(clerk_user_id, email, name, db)
    except Exception as exc:
        logger.warning(f"Optional user authentication failed: {exc}")
        return None


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the AI Meal Planner Assistant"
)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Receives user query + session history, extracts household context for
    authenticated users, and generates a context-aware nutrition response using Groq.
    """
    result = generate_chat_reply(
        message=request.message,
        conversation=request.conversation,
        db=db,
        current_user=current_user,
        household_id=request.household_id
    )

    return ChatResponse(
        reply=result["reply"],
        success=result["success"],
        error=result.get("error")
    )
