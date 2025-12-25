from fastapi import APIRouter
from app.api import auth, finance

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/legacy") 
api_router.include_router(finance.router)