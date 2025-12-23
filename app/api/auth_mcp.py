from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.utils.security import SecurityUtils
from datetime import timedelta

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _format_user_response(user_data: dict) -> UserResponse:
    """Helper function to format user data to UserResponse"""
    return UserResponse(
        id=str(user_data["id"]),
        name=user_data["name"],
        username=user_data["username"],
        phone=user_data["phone"],
        created_at=user_data.get("created_at"),
        updated_at=user_data.get("updated_at")
    )


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user with MCP Supabase integration
    
    - **name**: User's full name
    - **username**: Unique username (3+ chars, alphanumeric, -, _)  
    - **phone**: Phone number (10+ digits)
    - **password**: Password (6+ characters)
    """
    # Hash the password
    hashed_password = SecurityUtils.hash_password(user_data.password)
    
    # This endpoint will be implemented with direct MCP calls
    # For now, return a structured response
    return {
        "message": "Registration endpoint ready for MCP integration",
        "data": {
            "name": user_data.name,
            "username": user_data.username,
            "phone": user_data.phone,
            "hashed_password": hashed_password[:10] + "..."  # Show partial hash for demo
        }
    }


@router.post("/login", response_model=Dict[str, Any])
async def login(credentials: UserLogin):
    """
    Login user with MCP Supabase integration
    
    - **username**: User's username
    - **password**: User's password
    """
    # This endpoint will be implemented with direct MCP calls
    return {
        "message": "Login endpoint ready for MCP integration",
        "username": credentials.username
    }


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info():
    """
    Get current authenticated user information
    
    This endpoint will be implemented with MCP integration
    """
    return {
        "message": "Get current user endpoint ready for MCP integration"
    }


@router.put("/me", response_model=Dict[str, Any])
async def update_current_user(user_data: UserUpdate):
    """
    Update current authenticated user information
    
    - **name**: New name (optional)
    - **phone**: New phone number (optional)
    """
    return {
        "message": "Update user endpoint ready for MCP integration",
        "updates": {
            "name": user_data.name,
            "phone": user_data.phone
        }
    }


@router.get("/users", response_model=Dict[str, Any])
async def get_all_users():
    """
    Get all users using MCP Supabase
    
    Returns list of all users without password information
    """
    return {
        "message": "Get all users endpoint ready for MCP integration"
    }