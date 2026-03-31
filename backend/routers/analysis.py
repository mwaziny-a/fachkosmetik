from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

# تأكد أن المسارات تبدأ بـ backend إذا كان الملف بالخارج
from backend.models.schemas import AnalysisResponse, ErrorResponse
from utils.validators import validate_image_file

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/analyze", 
    # أزلنا النقاط الثلاث ووضعنا المعاملات بأسماء واضحة
    response_model=AnalysisResponse, 
    summary="Analyze facial features and generate cosmetic recommendations",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        422: {"model": ErrorResponse, "description": "Image quality issue"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    }
)
async def analyze_face(file: UploadFile = File(...)):
    # التحقق من الملف
    await validate_image_file(file)
    image_bytes = await file.read()
    
    # تحميل الخدمة هنا (Lazy Loading) لتجنب مشكلة الذاكرة في Render
    from backend.services.analysis_service import AnalysisService
    analysis_service = AnalysisService()
    
    result = await analysis_service.run_full_analysis(image_bytes, file.filename)
    return result