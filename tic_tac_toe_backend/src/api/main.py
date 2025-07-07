from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routes import router as api_router

openapi_tags = [
    {"name": "games",       "description": "Tic Tac Toe gameplay operations"},
    {"name": "leaderboard", "description": "Leaderboard/statistics"},
    {"name": "history",     "description": "Public game history"},
]

app = FastAPI(
    title="Tic Tac Toe API",
    description="REST API backend for fullstack Tic Tac Toe (gameplay, leaderboard, history - no authentication)",
    version="1.0.0",
    openapi_tags=openapi_tags
)

# PUBLIC_INTERFACE
# Add robust production CORS settings.
# • allow_credentials: False (browsers block if True with "*")
# • allow_origins: ["*"] for development, or set front-end base URL for strict production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For public demo, allow all. Change to only frontend domain in real production
    allow_credentials=False,  # IMPORTANT: True with "*" is a browser CORS violation (Forbidden by Fetch spec)
    allow_methods=["GET", "POST", "OPTIONS"],  # Only needed HTTP verbs; add others if needed
    allow_headers=["*"],  # Allow all for open API, or specify custom headers
    expose_headers=["Content-Type", "Authorization"],  # Expose key headers if frontend needs them
    max_age=600,  # Optional: browsers cache CORS preflight for faster repeated requests
)

@app.on_event("startup")
def on_startup():
    """
    Initializes the database if needed when the FastAPI server starts.
    """
    init_db()

app.include_router(api_router)

# PUBLIC_INTERFACE
@app.get("/cors-test")
def cors_test():
    """
    Returns a simple JSON object and custom header so that frontends can verify that CORS is working.
    """
    from fastapi.responses import JSONResponse

    headers = {"X-Test-Header": "fastapi-cors-ok"}
    return JSONResponse(content={"cors": "ok"}, headers=headers)

@app.get("/")
def health_check():
    """Basic service health check endpoint"""
    return {"message": "Healthy"}
