from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from .models import UserInDB, UserUpdate
from .service import AuthService
from ..error_handling import ValidationError, ResourceNotFoundError
from .dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserInDB)
async def get_current_user_profile(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get current user profile."""
    return current_user

@router.put("/me", response_model=UserInDB)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: UserInDB = Depends(get_current_user),
    auth_service: AuthService = Depends()
):
    """Update user profile."""
    try:
        return await auth_service.update_user(current_user.id, update_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me/projects", response_model=List[Dict])
async def get_user_projects(
    current_user: UserInDB = Depends(get_current_user),
    auth_service: AuthService = Depends()
):
    """Get user's projects."""
    try:
        return await auth_service.get_user_projects(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/me", status_code=204)
async def delete_account(
    current_user: UserInDB = Depends(get_current_user),
    auth_service: AuthService = Depends()
):
    """Delete user account."""
    try:
        await auth_service.delete_user(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 