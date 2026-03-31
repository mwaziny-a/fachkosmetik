from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging

from services.analysis_service import AnalysisService
from models.schemas import AnalysisResponse, ErrorResponse
from utils.validators import validate_image_file

router = APIRouter()
logger = logging.getLogger(__name__)
analysis_service = AnalysisService()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze facial features and generate cosmetic recommendations",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        422: {"model": ErrorResponse, "description": "Image quality issue"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    },
)
async def analyze_face(file: UploadFile = File(...)):
    await validate_image_file(file)
    image_bytes = await file.read()
    result = await analysis_service.run_full_analysis(image_bytes, file.filename)
    return result