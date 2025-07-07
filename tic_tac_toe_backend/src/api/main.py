from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routes import router as api_router

openapi_tags = [
    {"name": "auth",        "description": "Authentication (register/login)"},
    {"name": "games",       "description": "Tic Tac Toe gameplay operations"},
    {"name": "leaderboard", "description": "Leaderboard/statistics"},
    {"name": "users",       "description": "User profile and game history"},
]

app = FastAPI(
    title="Tic Tac Toe API",
    description="REST API backend for fullstack Tic Tac Toe (auth, gameplay, leaderboard, history)",
    version="1.0.0",
    openapi_tags=openapi_tags
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    Initializes the database if needed when the FastAPI server starts.
    """
    init_db()

app.include_router(api_router)

@app.get("/")
def health_check():
    """Basic service health check endpoint"""
    return {"message": "Healthy"}
