from fastapi import APIRouter
from app.api import auth, auth_mcp, ocr, finance

api_router = APIRouter()

# Include auth routers
api_router.include_router(auth.router, prefix="/legacy")  # Keep original auth as legacy
# api_router.include_router(auth_mcp.router)  # Use MCP-based auth as primary

# Include OCR router
api_router.include_router(ocr.router)

# Include Finance router
api_router.include_router(finance.router)