from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db

app = FastAPI(
    title="AI Meal Planner API",
    description="Backend API for the AI Meal Planner",
    version="1.0.0",
)

# React frontend URL
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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