from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.routers.food import router as food_router
from app.routers.household import router as household_router
from app.routers.meal_plan import router as meal_plan_router
from app.routers.chat import router as chat_router

app = FastAPI(
    title="AI Meal Planner API",
    description="Backend API for the AI Meal Planner",
    version="1.0.0",
)

# React frontend URL
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(food_router)
app.include_router(household_router)
app.include_router(meal_plan_router)
app.include_router(chat_router)



@app.get("/")
def root():
    return {
        "message": "AI Meal Planner API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Meal Planner Backend"
    }


@app.get("/api/db-health")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": str(e)
            }
        )


from typing import Optional
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import sync_user_data, _verify_clerk_token, _bearer

class UserSyncPayload(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None


@app.get("/api/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the current logged-in user.
    """
    return {
        "id": current_user.id,
        "clerk_user_id": current_user.clerk_user_id,
        "email": current_user.email,
        "name": current_user.name
    }


@app.post("/api/me")
def sync_me(
    payload: UserSyncPayload,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db)
):
    """
    Syncs user details (email, name) sent from Clerk frontend SDK into Neon Postgres database.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwt_payload = _verify_clerk_token(credentials.credentials)
    clerk_user_id: str = jwt_payload.get("sub", "")

    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    user = sync_user_data(
        clerk_user_id=clerk_user_id,
        email=payload.email,
        name=payload.name,
        db=db
    )

    return {
        "id": user.id,
        "clerk_user_id": user.clerk_user_id,
        "email": user.email,
        "name": user.name
    }