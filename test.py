"""
Test suite for FaceInsight AI.
Run with: pytest tests/ -v
"""
import pytest
import json
import io
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image, ImageDraw


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

def make_face_image(width=640, height=640, brightness=128) -> bytes:
    """Create a minimal synthetic image with a face-like oval."""
    img = Image.new("RGB", (width, height), color=(brightness, brightness - 10, brightness - 20))
    draw = ImageDraw.Draw(img)
    # Face oval
    cx, cy = width // 2, height // 2
    draw.ellipse([cx - 120, cy - 160, cx + 120, cy + 160], fill=(210, 180, 150))
    # Eyes
    draw.ellipse([cx - 50, cy - 40, cx - 20, cy - 20], fill=(60, 40, 30))
    draw.ellipse([cx + 20, cy - 40, cx + 50, cy - 20], fill=(60, 40, 30))
    # Mouth
    draw.arc([cx - 40, cy + 40, cx + 40, cy + 80], start=0, end=180, fill=(150, 80, 80), width=3)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def make_tiny_image() -> bytes:
    img = Image.new("RGB", (100, 100), color=(100, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_dark_image() -> bytes:
    img = Image.new("RGB", (640, 640), color=(10, 10, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


MOCK_OPENAI_RESPONSE = {
    "summary": "Clear, even skin with good hydration. The most impactful area to address is brow definition and under-eye texture.",
    "skin_analysis": {
        "skin_tone": "Medium warm with golden undertone",
        "apparent_texture": "Smooth with mild texture in T-zone",
        "visible_concerns": ["Mild pore visibility at nose", "Slight under-eye shadow"],
        "hydration_assessment": "Skin appears adequately hydrated with no visible flakiness",
        "uniformity": "Even tone with minor redness at nose bridge"
    },
    "face_structure": {
        "face_shape": "Oval",
        "symmetry_notes": "Minor asymmetry in brow height — left sits approximately 3mm higher",
        "prominent_features": ["Strong jaw", "High cheekbones"],
        "proportions_note": "Facial thirds are balanced; mid-face is slightly longer"
    },
    "eye_analysis": {
        "eye_shape": "Almond",
        "eye_spacing": "Average — pupils approximately one eye-width apart",
        "brow_shape": "Straight with slight arch",
        "brow_density": "Medium — sparse at tail",
        "notable_characteristics": ["Visible under-eye shadow", "Light outer lid hooding"]
    },
    "skincare_recommendations": [
        {
            "category": "Skincare",
            "title": "Niacinamide serum (10%)",
            "description": "Apply 3–4 drops to T-zone before moisturizer. Directly targets the visible pore congestion and mild uneven texture observed at the nose.",
            "priority": 1,
            "intervention_level": "low",
            "estimated_impact": "Noticeably reduced pore appearance and smoother mid-face texture within 6–8 weeks",
            "notes": "Look for formulations with zinc PCA for enhanced pore-tightening effect"
        }
    ],
    "grooming_recommendations": [
        {
            "category": "Grooming",
            "title": "Brow tail filling",
            "description": "Use a micro-tip brow pencil to extend the sparse tail of both brows outward by 4–5mm. This addresses the visible taper observed in the outer thirds.",
            "priority": 2,
            "intervention_level": "low",
            "estimated_impact": "More defined, intentional brow frame that lifts the eye area visually",
            "notes": "Match pencil to hair color, one shade lighter for a natural finish"
        }
    ],
    "hairstyle_recommendations": [
        {
            "category": "Hairstyle",
            "title": "Soft layers with mid-part",
            "description": "For an oval face with balanced proportions, soft layers starting at the jaw preserve the natural face balance without adding width or length artificially.",
            "priority": 3,
            "intervention_level": "low",
            "estimated_impact": "Enhanced facial framing that works with natural proportions",
            "notes": None
        }
    ],
    "beard_recommendations": [
        {
            "category": "Beard",
            "title": "Light stubble — 2–3mm maintained",
            "description": "Given the already-strong jaw structure, heavy beard volume would compete. A short maintained stubble adds definition without visually shortening the face.",
            "priority": 4,
            "intervention_level": "low",
            "estimated_impact": "Cleaner, intentional look that complements the jaw",
            "notes": None
        }
    ],
    "makeup_recommendations": [
        {
            "category": "Makeup",
            "title": "Tinted SPF (30+ broad spectrum)",
            "description": "Replace or layer over moisturizer daily. Addresses the mild redness at the nose bridge and evens tone with zero weight.",
            "priority": 5,
            "intervention_level": "low",
            "estimated_impact": "Unified skin tone with sun protection — no cakey finish",
            "notes": "Formulations with iron oxides offer better visible-light protection"
        }
    ],
    "non_invasive_options": [
        {
            "category": "Non-Invasive",
            "title": "Microcurrent facial (monthly)",
            "description": "Targets the mild mid-face softness observed. Builds muscle tone over a series of sessions without downtime.",
            "priority": 6,
            "intervention_level": "medium",
            "estimated_impact": "Lifted mid-face definition after 6–8 sessions",
            "notes": "At-home devices (NuFace) can maintain results between professional sessions"
        }
    ],
    "injectables_to_discuss": [
        {
            "category": "Injectables",
            "title": "Tear trough filler — discuss with injector",
            "description": "The visible under-eye shadow has a hollowing component rather than purely pigment. A conservative amount of hyaluronic acid filler in the tear trough could address this.",
            "priority": 7,
            "intervention_level": "high",
            "estimated_impact": "Reduced under-eye shadow depth, fresher rested appearance",
            "notes": "Consult only with an injector experienced specifically in periorbital anatomy"
        }
    ],
    "procedural_surgical_consultation": [
        {
            "category": "Procedural",
            "title": "Upper eyelid assessment — oculoplastic surgeon",
            "description": "The light outer lid hooding observed is borderline. If it progresses or causes visual field concerns, a consultation with an oculoplastic surgeon is worth considering.",
            "priority": 8,
            "intervention_level": "specialist",
            "estimated_impact": "More open eye appearance if treatment is deemed appropriate",
            "notes": "Seek board-certified oculoplastic or ophthalmic plastic surgeon"
        }
    ],
    "what_not_to_do": [
        "Do not over-pluck or reshape the brows into an arch — given the naturally straight brow structure, an artificial arch will look incongruous with the bone structure",
        "Avoid heavy matte foundation across the full face — the skin texture is fine enough that a full-coverage matte product will emphasize rather than hide the T-zone texture",
        "Do not pursue a heavy beard or full goatee — the strong jaw doesn't need additional visual weight at the chin"
    ],
    "disclaimer": "This analysis is for cosmetic guidance purposes only and does not constitute medical advice, diagnosis, or treatment. Consult a licensed medical professional or dermatologist for any health concerns. Injectable and procedural suggestions are for discussion with qualified specialists only."
}


# ──────────────────────────────────────────────
# Unit tests: FaceDetectionService
# ──────────────────────────────────────────────

class TestFaceDetectionService:

    def setup_method(self):
        with patch("services.face_detection_service.FaceDetectionService._initialize_insightface"):
            from services.face_detection_service import FaceDetectionService
            self.service = FaceDetectionService()
            self.service.app = None  # Force OpenCV fallback path

    def test_quality_check_rejects_tiny_image(self):
        result = self.service.analyze_image_quality(make_tiny_image())
        assert result["passed"] is False
        assert result["score"] < 0.7
        assert any("resolution" in issue.lower() for issue in result["issues"])

    def test_quality_check_rejects_dark_image(self):
        result = self.service.analyze_image_quality(make_dark_image())
        assert result["passed"] is False
        assert any("dark" in issue.lower() for issue in result["issues"])

    def test_quality_check_rejects_invalid_bytes(self):
        result = self.service.analyze_image_quality(b"not an image")
        assert result["passed"] is False
        assert result["score"] == 0.0
        assert result["face_count"] == 0

    def test_quality_score_clamps_between_0_and_1(self):
        # A valid-size but problematic image should still have score in [0,1]
        result = self.service.analyze_image_quality(make_dark_image())
        assert 0.0 <= result["score"] <= 1.0

    def test_quality_check_structure_keys(self):
        result = self.service.analyze_image_quality(make_face_image())
        assert "passed" in result
        assert "score" in result
        assert "issues" in result
        assert "face_detected" in result
        assert "face_count" in result

    def test_get_face_crop_returns_none_on_invalid(self):
        result = self.service.get_face_crop(b"garbage")
        assert result is None


# ──────────────────────────────────────────────
# Unit tests: RecommendationEngine
# ──────────────────────────────────────────────

class TestRecommendationEngine:

    def setup_method(self):
        from services.recommendation_engine import RecommendationEngine
        self.engine = RecommendationEngine()

    def _make_items(self, specs):
        from models.schemas import RecommendationItem, InterventionLevel
        items = []
        for cat, level, priority in specs:
            items.append(RecommendationItem(
                category=cat,
                title=f"{cat} {level}",
                description="desc",
                priority=priority,
                intervention_level=InterventionLevel(level),
                estimated_impact="impact",
            ))
        return items

    def test_low_intervention_before_high(self):
        items = self._make_items([
            ("A", "high", 1),
            ("B", "low", 2),
            ("C", "specialist", 3),
            ("D", "none", 4),
        ])
        ranked = self.engine.rank_recommendations(items)
        levels = [r.intervention_level.value for r in ranked]
        assert levels == ["none", "low", "high", "specialist"]

    def test_same_level_sorted_by_priority(self):
        items = self._make_items([
            ("A", "low", 3),
            ("B", "low", 1),
            ("C", "low", 2),
        ])
        ranked = self.engine.rank_recommendations(items)
        priorities = [r.priority for r in ranked]
        assert priorities == [1, 2, 3]

    def test_rank_all_categories_processes_dict(self):
        import copy
        data = copy.deepcopy(MOCK_OPENAI_RESPONSE)
        result = self.engine.rank_all_categories(data)
        # All rec arrays should still be lists
        assert isinstance(result["skincare_recommendations"], list)
        assert isinstance(result["non_invasive_options"], list)

    def test_rank_all_categories_skips_invalid_items(self):
        data = {
            "skincare_recommendations": [
                {"category": "Skincare", "title": "T", "description": "D",
                 "priority": 1, "intervention_level": "low", "estimated_impact": "E"},
                {"broken": "item"},  # should be skipped gracefully
            ]
        }
        result = self.engine.rank_all_categories(data)
        assert len(result["skincare_recommendations"]) == 1

    def test_empty_list_stays_empty(self):
        data = {"beard_recommendations": []}
        result = self.engine.rank_all_categories(data)
        assert result["beard_recommendations"] == []


# ──────────────────────────────────────────────
# Unit tests: OpenAI JSON parsing
# ──────────────────────────────────────────────

class TestOpenAIServiceParsing:

    def setup_method(self):
        with patch("utils.config.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test"
            from services.openai_service import OpenAIService
            self.service = OpenAIService.__new__(OpenAIService)
            self.service.api_key = "sk-test"

    def test_parse_clean_json(self):
        raw = json.dumps({"key": "value"})
        result = self.service._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = self.service._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_plain_fences(self):
        raw = '```\n{"key": "value"}\n```'
        result = self.service._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_parse_invalid_json_raises(self):
        from services.openai_service import OpenAIService
        svc = OpenAIService.__new__(OpenAIService)
        svc.api_key = "sk-test"
        with pytest.raises(RuntimeError, match="Failed to parse"):
            svc._parse_json_response("this is not json at all")

    def test_parse_json_with_leading_whitespace(self):
        from services.openai_service import OpenAIService
        svc = OpenAIService.__new__(OpenAIService)
        svc.api_key = "sk-test"
        raw = '   \n  {"nested": {"a": 1}}  \n  '
        result = svc._parse_json_response(raw)
        assert result["nested"]["a"] == 1


# ──────────────────────────────────────────────
# Unit tests: Schemas / Pydantic models
# ──────────────────────────────────────────────

class TestSchemas:

    def test_recommendation_item_valid(self):
        from models.schemas import RecommendationItem, InterventionLevel
        item = RecommendationItem(
            category="Skincare",
            title="Test",
            description="A test recommendation",
            priority=1,
            intervention_level=InterventionLevel.LOW,
            estimated_impact="Good outcome",
        )
        assert item.priority == 1
        assert item.intervention_level == InterventionLevel.LOW
        assert item.notes is None

    def test_recommendation_priority_bounds(self):
        from models.schemas import RecommendationItem, InterventionLevel
        with pytest.raises(Exception):
            RecommendationItem(
                category="X", title="T", description="D",
                priority=0,  # invalid — must be >= 1
                intervention_level=InterventionLevel.LOW,
                estimated_impact="E",
            )
        with pytest.raises(Exception):
            RecommendationItem(
                category="X", title="T", description="D",
                priority=11,  # invalid — must be <= 10
                intervention_level=InterventionLevel.LOW,
                estimated_impact="E",
            )

    def test_quality_check_score_bounds(self):
        from models.schemas import QualityCheck
        with pytest.raises(Exception):
            QualityCheck(passed=True, score=1.5, issues=[], face_detected=True, face_count=1)
        with pytest.raises(Exception):
            QualityCheck(passed=True, score=-0.1, issues=[], face_detected=True, face_count=1)

    def test_full_cosmetic_report_parses(self):
        from models.schemas import CosmeticReport
        report = CosmeticReport(**MOCK_OPENAI_RESPONSE)
        assert report.summary != ""
        assert len(report.skincare_recommendations) == 1
        assert len(report.what_not_to_do) == 3
        assert "cosmetic guidance" in report.disclaimer.lower()

    def test_analysis_response_structure(self):
        from models.schemas import AnalysisResponse, QualityCheck
        qc = QualityCheck(passed=True, score=0.9, issues=[], face_detected=True, face_count=1)
        resp = AnalysisResponse(success=True, quality_check=qc)
        assert resp.success is True
        assert resp.report is None


# ──────────────────────────────────────────────
# Integration tests: FastAPI endpoints
# ──────────────────────────────────────────────

class TestAnalysisEndpoint:

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_analyze_rejects_non_image(self, client):
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_analyze_rejects_tiny_image(self, client):
        """Image passes file type check but fails quality check."""
        with patch("services.analysis_service.AnalysisService.run_full_analysis") as mock_run:
            from fastapi import HTTPException
            mock_run.side_effect = HTTPException(
                status_code=422,
                detail={"message": "Image quality check failed.", "issues": ["Too small"], "quality_score": 0.3}
            )
            response = client.post(
                "/api/v1/analyze",
                files={"file": ("test.jpg", make_tiny_image(), "image/jpeg")},
            )
        assert response.status_code == 422

    def test_analyze_full_success(self, client):
        """Mock the full pipeline and verify response structure."""
        from models.schemas import AnalysisResponse, QualityCheck, CosmeticReport

        qc = QualityCheck(passed=True, score=0.95, issues=[], face_detected=True, face_count=1)
        report = CosmeticReport(**MOCK_OPENAI_RESPONSE)
        mock_response = AnalysisResponse(
            success=True,
            quality_check=qc,
            report=report,
            raw_json=MOCK_OPENAI_RESPONSE,
        )

        with patch("services.analysis_service.AnalysisService.run_full_analysis",
                   new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            response = client.post(
                "/api/v1/analyze",
                files={"file": ("portrait.jpg", make_face_image(), "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data
        assert "quality_check" in data
        assert data["report"]["summary"] != ""
        assert isinstance(data["report"]["skincare_recommendations"], list)
        assert isinstance(data["report"]["what_not_to_do"], list)

    def test_openapi_schema_available(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_analyze_endpoint_exists(self, client):
        """Verify the endpoint exists (method not allowed is fine, 404 is not)."""
        response = client.get("/api/v1/analyze")
        assert response.status_code != 404


# ──────────────────────────────────────────────
# Integration tests: Analysis pipeline
# ──────────────────────────────────────────────

class TestAnalysisPipeline:

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(self):
        from services.analysis_service import AnalysisService

        with patch("services.face_detection_service.FaceDetectionService._initialize_insightface"):
            service = AnalysisService.__new__(AnalysisService)

            mock_detector = MagicMock()
            mock_detector.analyze_image_quality.return_value = {
                "passed": True, "score": 0.9, "issues": [],
                "face_detected": True, "face_count": 1,
            }
            mock_detector.get_face_crop.return_value = make_face_image()

            mock_openai = AsyncMock()
            mock_openai.analyze_face = AsyncMock(return_value=MOCK_OPENAI_RESPONSE)

            from services.recommendation_engine import RecommendationEngine
            mock_engine = RecommendationEngine()

            service.face_detector = mock_detector
            service.openai_service = mock_openai
            service.recommendation_engine = mock_engine

            result = await service.run_full_analysis(make_face_image(), "test.jpg")

        assert result.success is True
        assert result.quality_check.passed is True
        assert result.report is not None
        assert result.report.summary != ""

    @pytest.mark.asyncio
    async def test_pipeline_raises_on_quality_failure(self):
        from services.analysis_service import AnalysisService
        from fastapi import HTTPException

        with patch("services.face_detection_service.FaceDetectionService._initialize_insightface"):
            service = AnalysisService.__new__(AnalysisService)

            mock_detector = MagicMock()
            mock_detector.analyze_image_quality.return_value = {
                "passed": False, "score": 0.2,
                "issues": ["No face detected."],
                "face_detected": False, "face_count": 0,
            }
            service.face_detector = mock_detector
            service.openai_service = AsyncMock()
            from services.recommendation_engine import RecommendationEngine
            service.recommendation_engine = RecommendationEngine()

            with pytest.raises(HTTPException) as exc_info:
                await service.run_full_analysis(make_tiny_image(), "bad.jpg")

            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_pipeline_handles_openai_failure(self):
        from services.analysis_service import AnalysisService
        from fastapi import HTTPException

        with patch("services.face_detection_service.FaceDetectionService._initialize_insightface"):
            service = AnalysisService.__new__(AnalysisService)

            mock_detector = MagicMock()
            mock_detector.analyze_image_quality.return_value = {
                "passed": True, "score": 0.9, "issues": [],
                "face_detected": True, "face_count": 1,
            }
            mock_detector.get_face_crop.return_value = None

            mock_openai = AsyncMock()
            mock_openai.analyze_face = AsyncMock(side_effect=RuntimeError("OpenAI timeout"))

            service.face_detector = mock_detector
            service.openai_service = mock_openai
            from services.recommendation_engine import RecommendationEngine
            service.recommendation_engine = RecommendationEngine()

            with pytest.raises(HTTPException) as exc_info:
                await service.run_full_analysis(make_face_image(), "test.jpg")

            assert exc_info.value.status_code == 500
            assert "AI analysis failed" in str(exc_info.value.detail)