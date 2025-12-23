import os
import shutil
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse

from app.schemas.ocr import OCRResponse, ReceiptInfo, OCRImageUpload, ImageProcessingRequest
from app.services.ocr_service import ocr_service
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/ocr",
    tags=["OCR - Image Text Extraction"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def validate_image_file(filename: str) -> bool:
    """Validate if file is an allowed image type"""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


@router.post("/upload", response_model=OCRImageUpload)
async def upload_and_extract_image(
    file: UploadFile = File(...),
    language: str = Form("en"),
    extract_receipt: bool = Form(True)
):
    """
    Upload image and extract text using PaddleOCR
    
    - **file**: Image file (jpg, jpeg, png, bmp, tiff, webp)
    - **language**: OCR language ('en', 'ch', 'id')
    - **extract_receipt**: Whether to extract structured receipt info
    
    Public endpoint - no authentication required for demo
    """
    try:
        # Validate file type
        if not validate_image_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Create unique filename
        import uuid
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Perform OCR
        ocr_result = ocr_service.extract_text_from_image(file_path, language)
        
        # Extract receipt info if requested
        receipt_info = None
        if extract_receipt and ocr_result.success and ocr_result.texts:
            receipt_info = ocr_service.extract_receipt_info(ocr_result)
        os.remove(file_path)  # Clean up uploaded file after processing
        return OCRImageUpload(
            success=True,
            message="Image processed successfully",
            file_path=file_path,
            ocr_result=ocr_result,
            receipt_info=receipt_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.post("/process", response_model=OCRResponse)
async def process_image_by_path(request: ImageProcessingRequest):
    """
    Process an existing image file by path
    
    - **image_path**: Path to the image file
    - **language**: OCR language ('en', 'ch', 'id')
    - **extract_receipt**: Whether to extract receipt info
    
    Public endpoint - no authentication required for demo
    """
    try:
        # Perform OCR
        ocr_result = ocr_service.extract_text_from_image(
            request.image_path, 
            request.language
        )
        
        return ocr_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.post("/extract-receipt", response_model=ReceiptInfo)
async def extract_receipt_info(request: ImageProcessingRequest):
    """
    Extract structured receipt information from image
    
    - **image_path**: Path to the image file
    - **language**: OCR language ('en', 'ch', 'id')
    
    Public endpoint - no authentication required for demo
    """
    try:
        # Perform OCR first
        ocr_result = ocr_service.extract_text_from_image(
            request.image_path, 
            request.language
        )
        
        if not ocr_result.success or not ocr_result.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text found in image"
            )
        
        # Extract receipt info
        receipt_info = ocr_service.extract_receipt_info(ocr_result)
        
        return receipt_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract receipt info: {str(e)}"
        )


@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported OCR languages
    """
    return {
        "supported_languages": [
            {"code": "en", "name": "English"},
            {"code": "id", "name": "Indonesian"},
            {"code": "ch", "name": "Chinese Simplified"},
            {"code": "zh", "name": "Chinese Simplified (alias)"}
        ],
        "default": "en",
        "ocr_engine": "EasyOCR"
    }


@router.delete("/cleanup/{filename}")
async def cleanup_uploaded_file(filename: str):
    """
    Delete uploaded file to free up storage
    
    - **filename**: Name of the file to delete
    
    Public endpoint - no authentication required for demo
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"success": True, "message": "File deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/test", response_model=Dict[str, Any])
async def test_ocr_service():
    """
    Test OCR service availability (no authentication required)
    """
    try:
        # Test if EasyOCR can be initialized
        test_engine = ocr_service._get_ocr_engine(['en'])
        
        return {
            "success": True,
            "message": "EasyOCR service is running",
            "easyocr_available": True,
            "supported_languages": ["en", "id", "ch", "zh"],
            "upload_directory": UPLOAD_DIR,
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
            "ocr_engine": "EasyOCR",
            "gpu_enabled": False
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"OCR service error: {str(e)}",
            "easyocr_available": False,
            "ocr_engine": "EasyOCR"
        }