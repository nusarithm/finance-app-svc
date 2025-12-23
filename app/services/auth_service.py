from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.database import supabase
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.utils.security import SecurityUtils
from datetime import timedelta


class AuthService:
    @staticmethod
    async def register_user(user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if username already exists
            existing_user = supabase.table("users").select("username").eq("username", user_data.username).execute()
            
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            # Hash the password
            hashed_password = SecurityUtils.hash_password(user_data.password)
            
            # Prepare user data for insertion
            user_insert = {
                "name": user_data.name,
                "username": user_data.username,
                "phone": user_data.phone,
                "password": hashed_password
            }
            
            # Insert user into database
            result = supabase.table("users").insert(user_insert).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            created_user = result.data[0]
            
            return {
                "message": "User registered successfully",
                "user": UserResponse(
                    id=str(created_user["id"]),
                    name=created_user["name"],
                    username=created_user["username"],
                    phone=created_user["phone"],
                    created_at=created_user.get("created_at"),
                    updated_at=created_user.get("updated_at")
                )
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return token"""
        try:
            # Get user from database
            user_result = supabase.table("users").select("*").eq("username", username).execute()
            
            if not user_result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user = user_result.data[0]
            
            # Verify password
            if not SecurityUtils.verify_password(password, user["password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=30)  # You can get this from settings
            access_token = SecurityUtils.create_access_token(
                data={"sub": user["username"]}, 
                expires_delta=access_token_expires
            )
            
            # Create user response
            user_response = UserResponse(
                id=str(user["id"]),
                name=user["name"],
                username=user["username"],
                phone=user["phone"],
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at")
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication failed: {str(e)}"
            )
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[UserResponse]:
        """Get user by username"""
        try:
            user_result = supabase.table("users").select("*").eq("username", username).execute()
            
            if not user_result.data:
                return None
            
            user = user_result.data[0]
            
            return UserResponse(
                id=str(user["id"]),
                name=user["name"],
                username=user["username"],
                phone=user["phone"],
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at")
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}"
            )
    
    @staticmethod
    async def update_user(username: str, user_data: UserUpdate) -> UserResponse:
        """Update user information"""
        try:
            # Prepare update data
            update_data = {}
            if user_data.name is not None:
                update_data["name"] = user_data.name
            if user_data.phone is not None:
                update_data["phone"] = user_data.phone
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data provided for update"
                )
            
            # Update user in database
            result = supabase.table("users").update(update_data).eq("username", username).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            updated_user = result.data[0]
            
            return UserResponse(
                id=str(updated_user["id"]),
                name=updated_user["name"],
                username=updated_user["username"],
                phone=updated_user["phone"],
                created_at=updated_user.get("created_at"),
                updated_at=updated_user.get("updated_at")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Update failed: {str(e)}"
            )