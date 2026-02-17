"""
API Routes for Competition Service
"""

from fastapi import APIRouter
from app.routes import auth, competitions, submissions, users, scores

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    competitions.router, prefix="/competitions", tags=["Competitions"]
)
api_router.include_router(
    submissions.router, prefix="/submissions", tags=["Submissions"]
)
api_router.include_router(
    scores.router, prefix="/scores", tags=["Scoring"]
)

__all__ = ["api_router"]
