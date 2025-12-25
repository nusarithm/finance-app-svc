from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any

from app.schemas.finance import TransactionCreate, TransactionUpdate, TransactionType
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user
from app.services.finance_service import finance_service

router = APIRouter(
    prefix="/finance",
    tags=["Finance Management"],
)


@router.post("/transactions", response_model=Dict[str, Any])
async def create_transaction(
    transaction: TransactionCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        result = await finance_service.create_transaction(current_user.id, transaction)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/transactions", response_model=Dict[str, Any])
async def get_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    transaction_type: Optional[TransactionType] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        transactions = await finance_service.get_transactions(
            user_id=current_user.id, limit=limit, offset=offset, transaction_type=transaction_type
        )
        return {"success": True, "data": transactions, "count": len(transactions)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=Dict[str, Any])
async def get_transaction(transaction_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        tx = await finance_service.get_transaction_by_id(transaction_id, current_user.id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return {"success": True, "data": tx}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/transactions/{transaction_id}", response_model=Dict[str, Any])
async def update_transaction(
    transaction_id: str,
    transaction: TransactionUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        updated = await finance_service.update_transaction(transaction_id, current_user.id, transaction)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return {"success": True, "data": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/transactions/{transaction_id}", response_model=Dict[str, Any])
async def delete_transaction(transaction_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        ok = await finance_service.delete_transaction(transaction_id, current_user.id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/summary", response_model=Dict[str, Any])
async def get_summary(current_user: UserResponse = Depends(get_current_user)):
    try:
        summary = await finance_service.get_finance_summary(current_user.id)
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics(
    period: str = Query("month", description="Period: week, month, year"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get analytics data for charts and insights"""
    try:
        analytics = await finance_service.get_analytics(current_user.id, period)
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
