from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    income = "income"  # Pemasukan
    expense = "expense"  # Pengeluaran


class TransactionCreate(BaseModel):
    type: TransactionType = Field(..., description="Type: income (pemasukan) or expense (pengeluaran)")
    amount: Decimal = Field(..., gt=0, description="Total amount (must be positive)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    class Config:
        json_encoders = {
            Decimal: str
        }
        schema_extra = {
            "example": {
                "type": "expense",
                "amount": "50000.00",
                "notes": "Makan siang di restoran"
            }
        }


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    amount: Optional[Decimal] = Field(None, gt=0, description="Total amount")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    class Config:
        json_encoders = {
            Decimal: str
        }


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: TransactionType
    amount: Decimal
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class FinanceSummary(BaseModel):
    user_id: str
    total_income: Decimal
    total_expenses: Decimal
    net_amount: Decimal
    transaction_count: int
    recent_transactions: List[TransactionResponse]

    class Config:
        json_encoders = {
            Decimal: str
        }