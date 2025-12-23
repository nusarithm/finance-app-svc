from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user
    
    - **name**: User's full name
    - **username**: Unique username (3+ chars, alphanumeric, -, _)
    - **phone**: Phone number (10+ digits)
    - **password**: Password (6+ characters)
    """
    return await AuthService.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login user and get access token
    
    - **username**: User's username
    - **password**: User's password
    """
    result = await AuthService.authenticate_user(
        credentials.username, 
        credentials.password
    )
    
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=result["user"]
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Requires: Bearer token in Authorization header
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update current authenticated user information
    
    - **name**: New name (optional)
    - **phone**: New phone number (optional)
    
    Requires: Bearer token in Authorization header
    """
    return await AuthService.update_user(current_user.username, user_data)