import os
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import easyocr
from PIL import Image
import cv2
import numpy as np
from fastapi import HTTPException, status

from app.schemas.ocr import OCRTextResult, OCRResponse, ReceiptInfo


class OCRService:
    """Service for image text extraction using EasyOCR"""
    
    def __init__(self):
        self.ocr_engines = {}
        self._default_language = ['en']
    
    def _get_ocr_engine(self, languages: List[str] = ['en']) -> easyocr.Reader:
        """Get or create OCR engine for specific languages"""
        lang_key = ','.join(sorted(languages))
        
        if lang_key not in self.ocr_engines:
            try:
                # Initialize EasyOCR with specific languages
                self.ocr_engines[lang_key] = easyocr.Reader(
                    lang_list=languages,
                    gpu=False,  # Set to True if you have GPU
                    verbose=False
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to initialize OCR engine for languages {languages}: {str(e)}"
                )
        return self.ocr_engines[lang_key]
    
    def extract_text_from_image(self, image_path: str, language: str = 'en') -> OCRResponse:
        """Extract text from image using EasyOCR"""
        try:
            start_time = time.time()
            
            # Validate image file exists
            if not os.path.exists(image_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image file not found"
                )
            
            # Map language codes to EasyOCR format
            lang_mapping = {
                'en': 'en',
                'id': 'id',  # Indonesian
                'ch': 'ch_sim',  # Chinese Simplified
                'zh': 'ch_sim'
            }
            
            easyocr_lang = lang_mapping.get(language, 'en')
            
            # Get OCR engine
            ocr_engine = self._get_ocr_engine([easyocr_lang])
            
            # Read and preprocess image
            image = self._preprocess_image(image_path)
            
            # Perform OCR
            ocr_results = ocr_engine.readtext(image)
            
            # Process results
            texts = []
            raw_text_parts = []
            
            for result in ocr_results:
                bbox, text, confidence = result
                
                # Convert bbox format to match our schema
                bbox_formatted = [[int(point[0]), int(point[1])] for point in bbox]
                
                texts.append(OCRTextResult(
                    text=text,
                    confidence=confidence,
                    bbox=bbox_formatted
                ))
                raw_text_parts.append(text)
            
            processing_time = time.time() - start_time
            
            # Get image info
            with Image.open(image_path) as img:
                image_info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
            
            return OCRResponse(
                success=True,
                total_texts=len(texts),
                texts=texts,
                raw_text=" ".join(raw_text_parts),
                processing_time=processing_time,
                image_info=image_info
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {str(e)}"
            )
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Read image with OpenCV
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError("Could not read image file")
            
            # Convert to grayscale for better text detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding to improve text clarity
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            processed = cv2.medianBlur(processed, 3)
            
            return processed
            
        except Exception as e:
            # If preprocessing fails, return original image
            return cv2.imread(image_path)
    
    def extract_receipt_info(self, ocr_response: OCRResponse) -> ReceiptInfo:
        """Extract structured receipt information from OCR results"""
        raw_text = ocr_response.raw_text
        texts = [item.text for item in ocr_response.texts]
        
        # Calculate average confidence
        confidence_score = sum(item.confidence for item in ocr_response.texts) / len(ocr_response.texts) if ocr_response.texts else 0
        
        receipt_info = ReceiptInfo(
            raw_ocr_text=raw_text,
            confidence_score=confidence_score
        )
        
        # Extract merchant name (usually at the top)
        merchant_name = self._extract_merchant_name(texts)
        if merchant_name:
            receipt_info.merchant_name = merchant_name
        
        # Extract total amount
        total_amount = self._extract_total_amount(raw_text)
        if total_amount:
            receipt_info.total_amount = total_amount
        
        # Extract date
        date = self._extract_date(raw_text)
        if date:
            receipt_info.date = date
        
        # Extract items (simple extraction)
        items = self._extract_items(texts)
        receipt_info.items = items
        
        return receipt_info
    
    def _extract_merchant_name(self, texts: List[str]) -> Optional[str]:
        """Extract merchant name from text list"""
        if not texts:
            return None
        
        # Usually merchant name is one of the first few lines
        # Skip very short texts and numbers
        for text in texts[:5]:
            if len(text) > 3 and not text.isdigit() and not self._is_amount(text):
                # Clean merchant name
                cleaned = re.sub(r'[^\w\s]', '', text).strip()
                if len(cleaned) > 2:
                    return cleaned
        
        return None
    
    def _extract_total_amount(self, text: str) -> Optional[float]:
        """Extract total amount from text"""
        # Common patterns for total amount
        patterns = [
            r'total[:\s]+(\d+[.,]\d{2})',
            r'amount[:\s]+(\d+[.,]\d{2})',
            r'grand\s+total[:\s]+(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*$',  # Number at end of line
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                amount_str = matches[0].replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from text"""
        # Common date patterns
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                date_str = matches[0] if isinstance(matches[0], str) else matches[0][0]
                try:
                    # Try different date formats
                    for date_format in ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']:
                        try:
                            return datetime.strptime(date_str, date_format)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_items(self, texts: List[str]) -> List[str]:
        """Extract item names from text list"""
        items = []
        
        for text in texts:
            # Skip merchant name, amounts, dates, and very short texts
            if (len(text) > 3 and 
                not self._is_amount(text) and 
                not self._is_date(text) and 
                not text.isdigit() and
                not text.lower() in ['total', 'amount', 'tax', 'subtotal']):
                
                # Clean item text
                cleaned = re.sub(r'[^\w\s]', '', text).strip()
                if len(cleaned) > 2:
                    items.append(cleaned)
        
        return items[:10]  # Limit to first 10 items
    
    def _is_amount(self, text: str) -> bool:
        """Check if text is an amount"""
        return bool(re.match(r'\d+[.,]\d{2}', text))
    
    def _is_date(self, text: str) -> bool:
        """Check if text is a date"""
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        return bool(re.match(date_pattern, text))


# Global OCR service instance
ocr_service = OCRService()