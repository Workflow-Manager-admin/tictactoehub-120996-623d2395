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
# CORS configuration and diagnostic logging for debugging persistent frontend fetch errors.
import logging

def _diagnose_cors_config(origins, allow_methods, allow_headers, allow_credentials):
    logging.info(
        "CORS Middleware settings: origins=%s | allow_methods=%s | allow_headers=%s | allow_credentials=%s",
        origins, allow_methods, allow_headers, allow_credentials
    )

# In production, should restrict origins, but for debug/development allow any.
CORS_ORIGINS = ["*"]
CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["*"]
CORS_ALLOW_CREDENTIALS = False

_diagnose_cors_config(CORS_ORIGINS, CORS_METHODS, CORS_HEADERS, CORS_ALLOW_CREDENTIALS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
    expose_headers=["Content-Type", "Authorization"],
    max_age=600,
)

@app.on_event("startup")
def on_startup():
    """
    Initializes the database if needed when the FastAPI server starts.
    """
    logging.info("FastAPI BACKEND STARTING on port 3001 (ensure HTTPS if frontend uses HTTPS).")
    logging.info(
        f"API docs available at /docs. CORS settings: allow_origins={CORS_ORIGINS}, allow_methods={CORS_METHODS}, allow_headers={CORS_HEADERS}, allow_credentials={CORS_ALLOW_CREDENTIALS}"
    )
    init_db()

app.include_router(api_router)

# PUBLIC_INTERFACE
@app.get("/cors-test")
def cors_test():
    """
    Returns a simple JSON object and custom header so that frontends can verify that CORS is working.
    Use this endpoint from the frontend to check for CORS issues. Returns 200 and a test header.
    """
    from fastapi.responses import JSONResponse

    headers = {"X-Test-Header": "fastapi-cors-ok"}
    return JSONResponse(content={"cors": "ok"}, headers=headers)

@app.get("/")
def health_check():
    """Basic service health check endpoint"""
    return {"message": "Healthy"}

# Recommendation for next debugging step (as code comment/documentation):
# 1. If fetch from frontend https://...:4000 to backend https://...:3001/cors-test (or /leaderboard) fails, confirm:
#    a. Browser fetches use HTTPS for both (no http/https mismatch).
#    b. Backend is running and responding at :3001 (check /, /cors-test direct in browser/Postman/curl).
#    c. CORS preflight OPTIONS gets a 200 and correct headers.
#    d. No frontend code is sending cookies/credentials (unless allow_credentials=True with explicit domain).
# 2. Examine Chrome DevTools/Network tab: what CORS header errors or "blocked by CORS policy" messages appear?
# 3. Try curl -i https://<host>:3001/cors-test and confirm Access-Control-Allow-Origin: * and correct HTTP status.
# 4. If all above is correct but fetch fails, double check the base API URL in frontend code (must match https/protocol/host/port).
# 5. If debugging in cloud/sandbox, ensure no network firewall blocks port 3001 from :4000.
