from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.utils.security import SecurityUtils
from datetime import timedelta


class SupabaseService:
    """Service class for Supabase database operations using MCP"""
    
    @staticmethod
    def _format_user_response(user_data: dict) -> UserResponse:
        """Helper method to format user data to UserResponse"""
        return UserResponse(
            id=str(user_data["id"]),
            name=user_data["name"],
            username=user_data["username"],
            phone=user_data["phone"],
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )


class AuthService:
    """Authentication service using Supabase MCP"""
    
    @staticmethod
    async def register_user(user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user using MCP Supabase"""
        try:
            # Check if username already exists
            check_query = f"SELECT username FROM users WHERE username = '{user_data.username}'"
            
            # This will be handled by the MCP tool call in the route
            # For now, we'll use a placeholder response format
            existing_check = await AuthService._execute_query(check_query)
            
            if existing_check and len(existing_check) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            # Hash the password
            hashed_password = SecurityUtils.hash_password(user_data.password)
            
            # Insert new user
            insert_query = f"""
            INSERT INTO users (name, username, phone, password)
            VALUES ('{user_data.name}', '{user_data.username}', '{user_data.phone}', '{hashed_password}')
            RETURNING id, name, username, phone, created_at, updated_at
            """
            
            result = await AuthService._execute_query(insert_query)
            
            if not result or len(result) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            created_user = result[0]
            
            return {
                "message": "User registered successfully",
                "user": SupabaseService._format_user_response(created_user)
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
        """Authenticate user and return token using MCP Supabase"""
        try:
            # Get user from database
            query = f"SELECT * FROM users WHERE username = '{username}'"
            result = await AuthService._execute_query(query)
            
            if not result or len(result) == 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user = result[0]
            
            # Verify password
            if not SecurityUtils.verify_password(password, user["password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=30)
            access_token = SecurityUtils.create_access_token(
                data={"sub": user["username"]}, 
                expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": SupabaseService._format_user_response(user)
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
        """Get user by username using MCP Supabase"""
        try:
            query = f"SELECT * FROM users WHERE username = '{username}'"
            result = await AuthService._execute_query(query)
            
            if not result or len(result) == 0:
                return None
            
            user = result[0]
            return SupabaseService._format_user_response(user)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}"
            )
    
    @staticmethod
    async def update_user(username: str, user_data: UserUpdate) -> UserResponse:
        """Update user information using MCP Supabase"""
        try:
            # Build update query
            update_fields = []
            if user_data.name is not None:
                update_fields.append(f"name = '{user_data.name}'")
            if user_data.phone is not None:
                update_fields.append(f"phone = '{user_data.phone}'")
            
            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data provided for update"
                )
            
            query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE username = '{username}'
            RETURNING id, name, username, phone, created_at, updated_at
            """
            
            result = await AuthService._execute_query(query)
            
            if not result or len(result) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            updated_user = result[0]
            return SupabaseService._format_user_response(updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Update failed: {str(e)}"
            )
    
    @staticmethod
    async def get_all_users() -> List[UserResponse]:
        """Get all users (admin function)"""
        try:
            query = "SELECT id, name, username, phone, created_at, updated_at FROM users ORDER BY created_at DESC"
            result = await AuthService._execute_query(query)
            
            if not result:
                return []
            
            return [SupabaseService._format_user_response(user) for user in result]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get users: {str(e)}"
            )
    
    @staticmethod
    async def _execute_query(query: str) -> List[Dict[str, Any]]:
        """Execute SQL query using MCP Supabase - this is a placeholder"""
        # This method will be replaced with actual MCP calls in the route handlers
        # For now, it's a placeholder to maintain the service structure
        raise NotImplementedError("This method should be called via MCP tools in route handlers")