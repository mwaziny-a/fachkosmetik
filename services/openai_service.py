import base64
import json
import logging
import httpx

from prompts.analysis_prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE
from utils.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    BASE_URL = "https://api.openai.com/v1/chat/completions"
    MODEL = "gpt-4o"

    def __init__(self):
        self.api_key = settings.openai_api_key
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set.")

    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    async def analyze_face(self, image_bytes: bytes) -> dict:
        b64_image = self._encode_image(image_bytes)
        payload = {
            "model": self.MODEL,
            "max_tokens": 4096,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT_TEMPLATE},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(self.BASE_URL, json=payload, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text[:300]}")

        raw = response.json()["choices"][0]["message"]["content"]
        return self._parse_json_response(raw)

    def _parse_json_response(self, raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned[: cleaned.rfind("```")]
            cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse AI response as JSON: {e}")