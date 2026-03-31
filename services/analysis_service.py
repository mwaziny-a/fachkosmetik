import logging
from typing import Optional
from fastapi import HTTPException

from services.face_detection_service import FaceDetectionService
from services.openai_service import OpenAIService
from services.recommendation_engine import RecommendationEngine
from models.schemas import AnalysisResponse, QualityCheck, CosmeticReport

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self):
        self.face_detector = FaceDetectionService()
        self.openai_service = OpenAIService()
        self.recommendation_engine = RecommendationEngine()

    async def run_full_analysis(self, image_bytes: bytes, filename: Optional[str] = None) -> AnalysisResponse:
        logger.info(f"Starting analysis: {filename or 'unknown'}")

        quality_data = self.face_detector.analyze_image_quality(image_bytes)
        quality_check = QualityCheck(**quality_data)

        if not quality_check.passed:
            raise HTTPException(
                status_code=422,
                detail={"message": "Image quality check failed.", "issues": quality_check.issues, "quality_score": quality_check.score},
            )

        analysis_image = self.face_detector.get_face_crop(image_bytes) or image_bytes

        try:
            raw_json = await self.openai_service.analyze_face(analysis_image)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")

        try:
            ranked_json = self.recommendation_engine.rank_all_categories(raw_json)
        except Exception as e:
            logger.warning(f"Ranking failed: {e}")
            ranked_json = raw_json

        try:
            report = CosmeticReport(**ranked_json)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to structure AI response: {e}")

        return AnalysisResponse(success=True, quality_check=quality_check, report=report, raw_json=ranked_json)