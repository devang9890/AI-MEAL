from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    