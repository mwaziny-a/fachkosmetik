import cv2
import numpy as np
from typing import List, Optional
import logging
import io
from PIL import Image

logger = logging.getLogger(__name__)


class FaceDetectionService:
    def __init__(self):
        self.app = None
        self._initialize_insightface()

    def _initialize_insightface(self):
        try:
            from insightface.app import FaceAnalysis
            self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace initialized successfully")
        except Exception as e:
            logger.warning(f"InsightFace not available ({e}). Using OpenCV fallback.")
            self.app = None

    def _opencv_face_detect(self, img_array: np.ndarray) -> int:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        return len(faces)

    def analyze_image_quality(self, image_bytes: bytes) -> dict:
        issues: List[str] = []
        face_count = 0
        score = 1.0

        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(pil_img)
        except Exception as e:
            return {"passed": False, "score": 0.0, "issues": [f"Cannot decode image: {e}"],
                    "face_detected": False, "face_count": 0}

        h, w = img_array.shape[:2]
        if w < 300 or h < 300:
            issues.append("Image resolution is too low (minimum 300×300 pixels).")
            score -= 0.3

        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        if cv2.Laplacian(gray, cv2.CV_64F).var() < 80:
            issues.append("Image appears blurry. Please use a sharper photo.")
            score -= 0.25

        brightness = gray.mean()
        if brightness < 50:
            issues.append("Image is too dark. Better lighting will improve accuracy.")
            score -= 0.2
        elif brightness > 220:
            issues.append("Image is overexposed. Avoid strong direct flash.")
            score -= 0.15

        face_count = (
            len(self.app.get(img_array)) if self.app else self._opencv_face_detect(img_array)
        )

        if face_count == 0:
            issues.append("No face detected. Please upload a clear frontal portrait.")
            score -= 0.5
        elif face_count > 1:
            issues.append(f"{face_count} faces detected. Please upload a single-person image.")
            score -= 0.3

        score = max(0.0, min(1.0, score))
        return {
            "passed": face_count == 1 and score >= 0.4,
            "score": round(score, 2),
            "issues": issues,
            "face_detected": face_count > 0,
            "face_count": face_count,
        }

    def get_face_crop(self, image_bytes: bytes) -> Optional[bytes]:
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(pil_img)
        except Exception:
            return None

        if self.app:
            faces = self.app.get(img_array)
            if not faces:
                return None
            bbox = faces[0].bbox.astype(int)
            x1, y1, x2, y2 = bbox
        else:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            detected = cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
            if len(detected) == 0:
                return None
            x, y, fw, fh = detected[0]
            x1, y1, x2, y2 = x, y, x + fw, y + fh

        h, w = img_array.shape[:2]
        pad = int(max(x2 - x1, y2 - y1) * 0.35)
        cropped = img_array[max(0, y1 - pad):min(h, y2 + pad),
                            max(0, x1 - pad):min(w, x2 + pad)]
        buf = io.BytesIO()
        Image.fromarray(cropped).save(buf, format="JPEG", quality=92)
        return buf.getvalue()