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

    def _extract_message_content(self, message_content) -> str:
        if isinstance(message_content, str):
            return message_content
        if isinstance(message_content, list):
            parts = []
            for item in message_content:
                if isinstance(item, dict):
                    text_part = item.get("text")
                    if isinstance(text_part, str):
                        parts.append(text_part)
            return "\n".join(parts)
        return str(message_content or "")

    async def _repair_json_with_model(self, raw_text: str) -> dict:
        payload = {
            "model": self.MODEL,
            "temperature": 0,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Return ONLY valid JSON. Do not add any explanation.",
                },
                {
                    "role": "user",
                    "content": (
                        "Convert the following model output into valid JSON that preserves the same"
                        " meaning and structure. If keys are missing, infer minimally from context.\n\n"
                        f"RAW_OUTPUT:\n{raw_text}"
                    ),
                },
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.BASE_URL, json=payload, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"JSON repair call failed {response.status_code}: {response.text[:300]}")

        repaired_raw = self._extract_message_content(response.json()["choices"][0]["message"]["content"])
        return self._parse_json_response(repaired_raw)

    async def analyze_face(self, image_bytes: bytes) -> dict:
        b64_image = self._encode_image(image_bytes)
        payload = {
            "model": self.MODEL,
            "max_tokens": 4096,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
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

        raw = self._extract_message_content(response.json()["choices"][0]["message"]["content"])
        try:
            return self._parse_json_response(raw)
        except RuntimeError as parse_error:
            logger.warning(f"Primary JSON parse failed, attempting repair pass: {parse_error}")
            try:
                return await self._repair_json_with_model(raw)
            except Exception as repair_error:
                raise RuntimeError(f"{parse_error}; JSON repair failed: {repair_error}")

    def _parse_json_response(self, raw: str) -> dict:
        cleaned = (raw or "").strip()
        if not cleaned:
            raise RuntimeError("Failed to parse AI response as JSON: empty response content")

        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned[: cleaned.rfind("```")]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError:
                    pass
            preview = cleaned[:200].replace("\n", " ")
            raise RuntimeError(f"Failed to parse AI response as JSON: {e}. Raw preview: {preview}")