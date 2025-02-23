from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from .models import UserCreate, UserInDB, Token
from .service import AuthService
from ..error_handling import ValidationError

router = APIRouter()

@router.post("/register", response_model=UserInDB)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends()
):
    """Register new user."""
    try:
        return await auth_service.create_user(user_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
):
    """Login user and return token."""
    try:
        return await auth_service.authenticate_user(
            form_data.username,  # Using email as username
            form_data.password
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/token/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends()
):
    """Refresh access token."""
    try:
        return await auth_service.refresh_token(refresh_token)
    except ValidationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        ) 