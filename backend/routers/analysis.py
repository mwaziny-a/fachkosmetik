from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging

from services.analysis_service import AnalysisService
from models.schemas import AnalysisResponse, ErrorResponse
from utils.validators import validate_image_file

router = APIRouter()
logger = logging.getLogger(__name__)
@router.post("/analyze", ...)
async def analyze_face(file: UploadFile = File(...)):
    await validate_image_file(file)
    image_bytes = await file.read()
    
    # 2. انقل إنشاء الخدمة إلى داخل الدالة هنا
    analysis_service = AnalysisService() 
    
    result = await analysis_service.run_full_analysis(image_bytes, file.filename)
    return result


@router.post(
    "/analyze", 
    response_model=AnalysisResponse, 
    summary="Analyze facial features and generate cosmetic recommendations"
)
async def analyze_face(file: UploadFile = File(...)):
    # الكود الذي عدلناه سابقاً (الـ Lazy Loading)
    await validate_image_file(file)
    image_bytes = await file.read()
    
    from services.analysis_service import AnalysisService
    analysis_service = AnalysisService()
    
    result = await analysis_service.run_full_analysis(image_bytes, file.filename)
    return result