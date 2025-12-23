from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class OCRTextResult(BaseModel):
    """Single text detection result from OCR"""
    text: str
    confidence: float
    bbox: List[List[int]]  # Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]


class OCRResponse(BaseModel):
    """Complete OCR response"""
    success: bool
    total_texts: int
    texts: List[OCRTextResult]
    raw_text: str  # All text concatenated
    processing_time: float
    image_info: Dict[str, Any]
    

class ReceiptInfo(BaseModel):
    """Extracted receipt information"""
    merchant_name: Optional[str] = None
    total_amount: Optional[float] = None
    date: Optional[datetime] = None
    items: List[str] = []
    raw_ocr_text: str
    confidence_score: float


class OCRImageUpload(BaseModel):
    """Response after image upload"""
    success: bool
    message: str
    file_path: str
    ocr_result: Optional[OCRResponse] = None
    receipt_info: Optional[ReceiptInfo] = None


class ImageProcessingRequest(BaseModel):
    """Request for processing uploaded image"""
    image_path: str
    extract_receipt: bool = True
    language: str = "en"
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['en', 'id', 'ch', 'zh']
        if v not in allowed_languages:
            raise ValueError(f'Language must be one of: {allowed_languages}')
        return v