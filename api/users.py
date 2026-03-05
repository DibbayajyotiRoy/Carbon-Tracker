from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_db
from api.models import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["users"])

class UserResponse(BaseModel):
    id: str
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/me", response_model=UserResponse)
async def get_me(
    x_user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user details.
    Uses 'X-User-ID' header for simulation of authentication.
    """
    stmt = select(User).where(User.id == x_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # For this prototype, we create the user if they don't exist
        user = User(id=x_user_id, full_name="New User")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user
