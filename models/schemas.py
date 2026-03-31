from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class InterventionLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SPECIALIST = "specialist"


class RecommendationItem(BaseModel):
    category: str
    title: str
    description: str
    priority: int = Field(..., ge=1, le=10)
    intervention_level: InterventionLevel
    estimated_impact: str
    notes: Optional[str] = None


class SkinAnalysis(BaseModel):
    skin_tone: str
    apparent_texture: str
    visible_concerns: List[str]
    hydration_assessment: str
    uniformity: str


class FaceStructureAnalysis(BaseModel):
    face_shape: str
    symmetry_notes: str
    prominent_features: List[str]
    proportions_note: str


class EyeAnalysis(BaseModel):
    eye_shape: str
    eye_spacing: str
    brow_shape: str
    brow_density: str
    notable_characteristics: List[str]


class QualityCheck(BaseModel):
    passed: bool
    score: float = Field(..., ge=0.0, le=1.0)
    issues: List[str]
    face_detected: bool
    face_count: int


class CosmeticReport(BaseModel):
    summary: str
    skin_analysis: SkinAnalysis
    face_structure: FaceStructureAnalysis
    eye_analysis: EyeAnalysis
    skincare_recommendations: List[RecommendationItem]
    grooming_recommendations: List[RecommendationItem]
    hairstyle_recommendations: List[RecommendationItem]
    beard_recommendations: List[RecommendationItem]
    makeup_recommendations: List[RecommendationItem]
    non_invasive_options: List[RecommendationItem]
    injectables_to_discuss: List[RecommendationItem]
    procedural_surgical_consultation: List[RecommendationItem]
    what_not_to_do: List[str]
    disclaimer: str


class AnalysisResponse(BaseModel):
    success: bool
    quality_check: QualityCheck
    report: Optional[CosmeticReport] = None
    raw_json: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None