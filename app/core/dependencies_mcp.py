from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import SecurityUtils
from app.schemas.user import UserResponse

security = HTTPBearer()


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


async def get_current_user_mcp(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """Dependency to get current authenticated user using MCP Supabase"""
    try:
        # Verify token
        token_data = SecurityUtils.verify_token(credentials.credentials)
        username = token_data["username"]
        
        # Get user from database using MCP Supabase
        query = f"SELECT * FROM users WHERE username = '{username}'"
        result = mcp_supabase_execute_sql(query=query)
        
        if not result or len(result) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = result[0]
        return _format_user_response(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )