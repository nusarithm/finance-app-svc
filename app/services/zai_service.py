import httpx
import json
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.schemas.finance import AITransactionProcessing
from app.core.config import settings


class ZAIService:
    """Service for Z.ai integration using GLM-4.5-flash model"""
    
    def __init__(self):
        # Read API key from settings or environment; do NOT hard-code secrets in source
        self.api_key = settings.zai_api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.model = "glm-4-flash"
    
    async def process_receipt_text(self, ocr_text: str) -> AITransactionProcessing:
        """Process OCR text and extract financial transaction data"""
        try:
            prompt = self._create_extraction_prompt(ocr_text)
            
            response = await self._call_zai_api(prompt)
            
            # Parse AI response
            extracted_data = self._parse_ai_response(response)
            
            return AITransactionProcessing(
                success=True,
                confidence=extracted_data.get("confidence", 0.5),
                extracted_data=extracted_data,
                suggested_category=extracted_data.get("category"),
                raw_ai_response=response
            )
            
        except Exception as e:
            return AITransactionProcessing(
                success=False,
                confidence=0.0,
                extracted_data={},
                raw_ai_response=str(e)
            )
    
    def _create_extraction_prompt(self, ocr_text: str) -> str:
        """Create prompt for financial data extraction"""
        return f"""
Analyze the following receipt/financial document text and extract key information.
Return the data in JSON format with the following structure:

{{
    "amount": <numeric_value_without_currency>,
    "merchant": "<merchant_name>",
    "date": "<YYYY-MM-DD>",
    "category": "<category_name>",
    "description": "<brief_description>",
    "confidence": <0.0_to_1.0>,
    "currency": "<currency_code>",
    "transaction_type": "expense|income",
    "items": ["<item1>", "<item2>", ...],
    "location": "<location_if_available>"
}}

Categories to choose from:
- Food & Dining
- Transportation  
- Shopping
- Bills & Utilities
- Entertainment
- Healthcare
- Education
- Salary
- Business
- Investment
- Gift
- Other

OCR Text:
{ocr_text}

Important:
1. Extract the TOTAL amount, not individual item prices
2. If no clear total is found, sum the visible amounts
3. Choose the most appropriate category
4. Set confidence based on text clarity and completeness
5. Use "expense" for most receipts, "income" for salary/business documents
6. Return valid JSON only, no additional text
"""
    
    async def _call_zai_api(self, prompt: str) -> str:
        """Call Z.ai API with the given prompt"""
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Z.ai API key is not configured. Set ZAI_API_KEY in environment or Settings.zai_api_key"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Lower temperature for more consistent extraction
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Z.ai API error: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            
            if "choices" not in result or not result["choices"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No response from Z.ai API"
                )
            
            return result["choices"][0]["message"]["content"]
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            data = json.loads(cleaned_response)
            
            # Validate and clean data
            extracted = {
                "amount": self._safe_float(data.get("amount")),
                "merchant": self._safe_string(data.get("merchant")),
                "date": self._safe_string(data.get("date")),
                "category": self._safe_string(data.get("category")),
                "description": self._safe_string(data.get("description")),
                "confidence": self._safe_float(data.get("confidence", 0.5)),
                "currency": self._safe_string(data.get("currency", "IDR")),
                "transaction_type": self._safe_string(data.get("transaction_type", "expense")),
                "items": data.get("items", []) if isinstance(data.get("items"), list) else [],
                "location": self._safe_string(data.get("location"))
            }
            
            return extracted
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract basic info with regex
            return self._fallback_extraction(response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse AI response: {str(e)}"
            )
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction when JSON parsing fails"""
        import re
        
        # Try to extract amount with regex
        amount_patterns = [
            r'(\d+[.,]\d{2})',
            r'(\d+\.?\d*)'
        ]
        
        amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1).replace(',', '.'))
                break
        
        return {
            "amount": amount,
            "merchant": None,
            "date": None,
            "category": "Other",
            "description": "AI extraction failed, manual review needed",
            "confidence": 0.1,
            "currency": "IDR",
            "transaction_type": "expense",
            "items": [],
            "location": None
        }
    
    def _safe_string(self, value: Any) -> Optional[str]:
        """Safely convert value to string"""
        if value is None or value == "":
            return None
        return str(value).strip()
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            return float(str(value).replace(',', '.'))
        except (ValueError, TypeError):
            return None


# Global Z.ai service instance
zai_service = ZAIService()