from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from app.schemas.finance import (
    TransactionCreate, TransactionUpdate, TransactionResponse, 
    TransactionType, FinanceSummary
)

from app.core.database import supabase
from fastapi import HTTPException, status
from decimal import Decimal


class FinanceService:
    """Service layer for simplified finance operations using MCP Supabase"""

    async def create_transaction(
        self, 
        user_id: str, 
        transaction: TransactionCreate
    ) -> Dict[str, Any]:
        """Create a new transaction"""
        transaction_data = {
            "user_id": user_id,
            "type": str(transaction.type),
            "amount": str(transaction.amount),
            "notes": transaction.notes,
        }
        if getattr(transaction, "category_id", None):
            transaction_data["category_id"] = transaction.category_id
        if getattr(transaction, "transaction_date", None):
            transaction_data["transaction_date"] = transaction.transaction_date.isoformat()

        try:
            result = supabase.table("transactions").insert(transaction_data).select("*").execute()
            if result.error or not result.data:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error))
            created = result.data[0]
            return {
                "id": str(created["id"]),
                "user_id": str(created["user_id"]),
                "type": created["type"],
                "amount": Decimal(str(created["amount"])),
                "notes": created.get("notes"),
                "category_id": str(created.get("category_id")) if created.get("category_id") else None,
                "transaction_date": created.get("transaction_date"),
                "created_at": created.get("created_at")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create transaction: {str(e)}")

    async def get_transactions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Dict[str, Any]]:
        """Get user transactions with filters"""
        
        try:
            query = supabase.table("transactions").select("*")
            query = query.eq("user_id", user_id)
            if transaction_type:
                query = query.eq("type", str(transaction_type))
            # range is inclusive
            start = offset
            end = offset + limit - 1
            result = query.order("created_at", desc=True).range(start, end).execute()
            if result.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error))
            rows = result.data or []
            # Normalize types
            for r in rows:
                r["id"] = str(r.get("id"))
                r["user_id"] = str(r.get("user_id"))
                r["amount"] = Decimal(str(r.get("amount"))) if r.get("amount") is not None else None
                # attach category info if available
                if r.get("category_id"):
                    try:
                        cat_res = supabase.table("categories").select("*").eq("id", r.get("category_id")).execute()
                        if cat_res.data:
                            cat = cat_res.data[0]
                            r["category"] = {
                                "id": str(cat.get("id")),
                                "name": cat.get("name"),
                                "type": cat.get("type"),
                                "icon": cat.get("icon"),
                                "color": cat.get("color")
                            }
                    except Exception:
                        r["category"] = None
            return rows
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch transactions: {str(e)}")

    async def get_transaction_by_id(self, transaction_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific transaction by ID"""
        
        try:
            result = supabase.table("transactions").select("*").eq("id", transaction_id).eq("user_id", user_id).execute()
            if result.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error))
            if not result.data:
                return None
            row = result.data[0]
            row["id"] = str(row.get("id"))
            row["user_id"] = str(row.get("user_id"))
            row["amount"] = Decimal(str(row.get("amount"))) if row.get("amount") is not None else None
            if row.get("category_id"):
                try:
                    cat_res = supabase.table("categories").select("*").eq("id", row.get("category_id")).execute()
                    if cat_res.data:
                        cat = cat_res.data[0]
                        row["category"] = {
                            "id": str(cat.get("id")),
                            "name": cat.get("name"),
                            "type": cat.get("type"),
                            "icon": cat.get("icon"),
                            "color": cat.get("color")
                        }
                except Exception:
                    row["category"] = None
            return row
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch transaction: {str(e)}")

    async def update_transaction(
        self, 
        transaction_id: str, 
        user_id: str, 
        transaction: TransactionUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update existing transaction"""
        
        update_data = {}
        
        if transaction.type is not None:
            update_data["type"] = transaction.type
        if transaction.amount is not None:
            update_data["amount"] = str(transaction.amount)
        if transaction.notes is not None:
            update_data["notes"] = transaction.notes
        if getattr(transaction, "category_id", None) is not None:
            update_data["category_id"] = transaction.category_id
        if getattr(transaction, "transaction_date", None) is not None:
            update_data["transaction_date"] = transaction.transaction_date.isoformat()
            
        try:
            if not update_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided for update")
            result = supabase.table("transactions").update(update_data).eq("id", transaction_id).eq("user_id", user_id).select("*").execute()
            if result.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error))
            if not result.data:
                return None
            updated = result.data[0]
            updated["id"] = str(updated.get("id"))
            updated["user_id"] = str(updated.get("user_id"))
            updated["amount"] = Decimal(str(updated.get("amount"))) if updated.get("amount") is not None else None
            return updated
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update transaction: {str(e)}")

    async def delete_transaction(self, transaction_id: str, user_id: str) -> bool:
        """Delete transaction"""
        
        try:
            result = supabase.table("transactions").delete().eq("id", transaction_id).eq("user_id", user_id).execute()
            if result.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error))
            # result.data might be [] or include deleted rows; interpret empty as not found
            if not result.data:
                return False
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete transaction: {str(e)}")

    async def get_finance_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive finance summary"""
        
        # Note: Replace with actual MCP Supabase queries
        # Example queries:
        # 1. SELECT SUM(amount) FROM transactions WHERE user_id = $1 AND type = 'income'
        # 2. SELECT SUM(amount) FROM transactions WHERE user_id = $1 AND type = 'expense'
        # 3. SELECT COUNT(*) FROM transactions WHERE user_id = $1
        # 4. SELECT * FROM transactions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10
        
        try:
            # Fetch income and expense sums
            income_res = supabase.table("transactions").select("amount").eq("user_id", user_id).eq("type", "income").execute()
            expense_res = supabase.table("transactions").select("amount").eq("user_id", user_id).eq("type", "expense").execute()
            all_res = supabase.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()

            if income_res.error or expense_res.error or all_res.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(income_res.error or expense_res.error or all_res.error))

            total_income = sum((Decimal(str(r.get("amount"))) for r in (income_res.data or []) if r.get("amount") is not None), Decimal("0.00"))
            total_expenses = sum((Decimal(str(r.get("amount"))) for r in (expense_res.data or []) if r.get("amount") is not None), Decimal("0.00"))
            recent = all_res.data or []
            for r in recent:
                r["id"] = str(r.get("id"))
                r["amount"] = Decimal(str(r.get("amount"))) if r.get("amount") is not None else None
                if r.get("category_id"):
                    try:
                        cat_res = supabase.table("categories").select("*").eq("id", r.get("category_id")).execute()
                        if cat_res.data:
                            cat = cat_res.data[0]
                            r["category"] = {
                                "id": str(cat.get("id")),
                                "name": cat.get("name"),
                                "type": cat.get("type"),
                                "icon": cat.get("icon"),
                                "color": cat.get("color")
                            }
                    except Exception:
                        r["category"] = None

            # Count total transactions
            count_res = supabase.table("transactions").select("id").eq("user_id", user_id).execute()
            transaction_count = len(count_res.data) if count_res.data else 0

            # Optionally fetch top categories (simple count by category)
            try:
                cat_counts = supabase.rpc("realtime_category_counts", {"p_user_id": user_id}).execute()
            except Exception:
                cat_counts = None

            return {
                "user_id": user_id,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_amount": (total_income - total_expenses),
                "transaction_count": transaction_count,
                "recent_transactions": recent
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to compute summary: {str(e)}")

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Return list of categories"""
        try:
            res = supabase.table("categories").select("*").order("name", desc=False).execute()
            if res.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(res.error))
            cats = res.data or []
            out = []
            for c in cats:
                out.append({
                    "id": str(c.get("id")),
                    "name": c.get("name"),
                    "slug": c.get("slug"),
                    "description": c.get("description"),
                    "type": c.get("type"),
                    "icon": c.get("icon"),
                    "color": c.get("color")
                })
            return out
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get categories: {str(e)}")

    async def get_analytics(self, user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get analytics data for charts and insights"""
        try:
            # Calculate date range based on period
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if period == "week":
                start_date = now - timedelta(days=7)
                group_by = "day"
            elif period == "month":
                start_date = now - timedelta(days=30)
                group_by = "day"
            elif period == "year":
                start_date = now - timedelta(days=365)
                group_by = "month"
            else:
                start_date = now - timedelta(days=30)
                group_by = "day"
            
            # Get transactions in date range
            transactions_res = supabase.table("transactions").select("*").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute()
            
            if transactions_res.error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(transactions_res.error))
            
            transactions = transactions_res.data or []
            
            # Process data for charts
            income_by_period = {}
            expense_by_period = {}
            category_expenses = {}
            
            for tx in transactions:
                tx_date = tx.get("transaction_date") or tx.get("created_at")
                if not tx_date:
                    continue
                    
                dt = datetime.fromisoformat(tx_date.replace('Z', '+00:00'))
                
                if group_by == "day":
                    period_key = dt.strftime("%Y-%m-%d")
                else:  # month
                    period_key = dt.strftime("%Y-%m")
                
                amount = Decimal(str(tx.get("amount", 0)))
                tx_type = tx.get("type")
                
                if tx_type == "income":
                    income_by_period[period_key] = income_by_period.get(period_key, Decimal(0)) + amount
                elif tx_type == "expense":
                    expense_by_period[period_key] = expense_by_period.get(period_key, Decimal(0)) + amount
                    
                    # Track category expenses
                    category_id = tx.get("category_id")
                    if category_id:
                        category_expenses[category_id] = category_expenses.get(category_id, Decimal(0)) + amount
            
            # Convert to chart format
            all_periods = set(list(income_by_period.keys()) + list(expense_by_period.keys()))
            chart_data = []
            
            for period_key in sorted(all_periods):
                chart_data.append({
                    "period": period_key,
                    "income": float(income_by_period.get(period_key, Decimal(0))),
                    "expense": float(expense_by_period.get(period_key, Decimal(0)))
                })
            
            # Get category details for top expenses
            category_details = []
            for cat_id, amount in sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)[:4]:
                try:
                    cat_res = supabase.table("categories").select("*").eq("id", cat_id).execute()
                    if cat_res.data:
                        cat = cat_res.data[0]
                        category_details.append({
                            "category": cat.get("name", "Unknown"),
                            "amount": float(amount),
                            "percentage": 0,  # Will calculate after getting total
                            "color": cat.get("color", "#666666")
                        })
                except Exception:
                    continue
            
            # Calculate percentages
            total_expense = sum(float(cat["amount"]) for cat in category_details)
            for cat in category_details:
                cat["percentage"] = round((cat["amount"] / total_expense * 100) if total_expense > 0 else 0, 1)
            
            return {
                "chart_data": chart_data,
                "category_data": category_details,
                "total_spending": float(sum(expense_by_period.values())),
                "total_income": float(sum(income_by_period.values())),
                "period": period
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get analytics: {str(e)}")


# Global instance
finance_service = FinanceService()