"""
Authentication router — Mock implementation for frontend development.

Provides identity endpoints without full OAuth/JWT complexity.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.api.schemas.responses import UserResponse
from app.models.db_models import User
from app.infrastructure.seeds import LUCHO_ID

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile (Mock)",
)
async def get_me(db: AsyncSession = Depends(get_db)) -> UserResponse:
    """
    Returns the fixed 'Lucho' user for frontend simulation.
    """
    user = await db.get(User, LUCHO_ID)
    if not user:
        raise HTTPException(status_code=404, detail="Seed user not found. Please restart the app.")
    return user
