"""
Vision Arbiter: a gated VLM tie-breaker for RAW-JPG linkage.

Geometric verification (SIFT keypoints + RANSAC homography) decides linkage in almost
every case, and it decides it reproducibly. This exists for the band it genuinely
cannot reach: frames with too little texture to yield keypoints — fog, minimalism,
long-exposure water, night sky — where "are these the same scene?" is a fair question
that code cannot answer but a human, or a vision model, can.

Two properties are deliberate and load-bearing:

**It never runs when geometry decided.** Semantic similarity is the easiest property
for a forger to satisfy: an AI image of the same subject as the RAW passes any
"same scene?" check trivially. That is the attack the linkage layer exists to catch,
so the arbiter is not consulted when keypoint geometry already answered — in either
direction.

**It can rescue but never condemn.** It may raise an inconclusive result to linked. It
may not reject. If the model reports different scenes, that reasoning is attached as
evidence and the submission stays in review for a human. A non-reproducible opinion
must not be the reason a photographer is disqualified — and an appeals process cannot
defend a verdict that changes when you re-run it.
"""

import base64
import json
import logging
import os
from typing import Dict, Optional

import cv2
import httpx
import numpy as np

logger = logging.getLogger(__name__)

PROMPT = (
    "You are comparing two photographs for a photography competition's authenticity check.\n"
    "Image A is a plain rendering of a camera RAW file. Image B is the photographer's "
    "finished export, which may be cropped, converted to black and white, and tonally reworked.\n\n"
    "Question: does image B show the same physical scene, photographed from the same "
    "position at the same moment, as image A? Ignore all differences in brightness, "
    "colour, contrast, and framing — judge only whether it is the same scene.\n\n"
    "Respond with JSON only: {\"same_scene\": bool, \"confidence\": 0.0-1.0, "
    "\"reasoning\": \"one sentence naming the specific shared or differing elements\"}\n"
    "Set confidence below 0.6 if you are unsure."
)

# Verified against the live API on 2026-08-07 with the exact request this module sends
# (two inline JPEGs + responseSchema): gemini-3.6-flash, gemini-3.5-flash,
# gemini-3.1-flash-lite and the gemini-flash-latest alias all honour the schema.
#
# Pinned rather than pointing at gemini-flash-latest on purpose: the arbiter's reasoning
# text is shown to judges, so the model behind it should not change without someone
# choosing to change it. The cost is that this default will eventually be retired — when
# it is, the 404 handler below says exactly what to do, and GEMINI_MODEL overrides it
# without a code deploy.
DEFAULT_MODEL = "gemini-3.6-flash"

# Gemini's Schema proto: type names are the uppercase enum values, not JSON Schema's
# lowercase ones.
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "same_scene": {"type": "BOOLEAN"},
        "confidence": {"type": "NUMBER"},
        "reasoning": {"type": "STRING"},
    },
    "required": ["same_scene", "confidence", "reasoning"],
}


class VisionArbiter:
    """Breaks linkage ties that keypoint geometry cannot resolve."""

    # Only a confident positive is allowed to move a verdict.
    MIN_CONFIDENCE = 0.6

    # Sent at this size: enough for scene recognition, small enough to stay cheap and
    # to keep two encoded frames off a 2GB host's memory budget.
    SEND_LONG_EDGE = 1024
    JPEG_QUALITY = 85

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        transport: Optional[httpx.BaseTransport] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self._transport = transport
        self.enabled = bool(self.api_key)

        if self.enabled:
            logger.info(f"Vision arbiter enabled (model: {self.model})")
        else:
            logger.info("Vision arbiter disabled - GEMINI_API_KEY not configured")

    @property
    def endpoint(self) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def should_arbitrate(self, geometry: Optional[Dict]) -> bool:
        """True only for results geometry could not decide.

        Not consulted when geometry confirmed the crop (nothing to add) and not when it
        decisively found no matching crop (a semantic second opinion is exactly what a
        same-subject forgery would exploit).
        """
        if not self.enabled or not geometry:
            return False
        if geometry.get("linked"):
            return False
        return bool(geometry.get("low_texture") or geometry.get("crop_like"))

    def _encode(self, image: np.ndarray) -> str:
        h, w = image.shape[:2]
        scale = min(1.0, self.SEND_LONG_EDGE / float(max(h, w)))
        if scale < 1.0:
            image = cv2.resize(image, (int(round(w * scale)), int(round(h * scale))),
                               interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), self.JPEG_QUALITY])
        if not ok:
            raise ValueError("failed to encode image for the vision arbiter")
        return base64.b64encode(buf.tobytes()).decode("ascii")

    @staticmethod
    def _parse(text: str) -> Dict:
        """Extract the JSON verdict, tolerating the code fences models add anyway."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.lstrip().lower().startswith("json"):
                cleaned = cleaned.lstrip()[4:]
        return json.loads(cleaned.strip())

    def _unavailable(self, reason: str) -> Dict:
        return {
            "available": False,
            "verdict": "UNDETERMINED",
            "confidence": 0.0,
            "reasoning": "",
            "flags": [f"Vision arbiter unavailable: {reason}"],
        }

    async def arbitrate(self, raw_image: np.ndarray, jpg_image: np.ndarray, geometry: Dict) -> Dict:
        """Ask whether the JPEG depicts the same scene as the RAW.

        Returns a verdict of LINKED (confident scene correspondence) or UNDETERMINED.
        There is deliberately no rejecting verdict.
        """
        if not self.enabled:
            return self._unavailable("no API key configured")

        try:
            body = {
                "contents": [{
                    "parts": [
                        {"text": PROMPT},
                        {"inline_data": {"mime_type": "image/jpeg", "data": self._encode(raw_image)}},
                        {"inline_data": {"mime_type": "image/jpeg", "data": self._encode(jpg_image)}},
                    ]
                }],
                # camelCase is required: the endpoint accepts snake_case keys here but
                # silently ignores them, so the model would reply in prose instead of
                # JSON. The schema makes the shape a constraint rather than a request.
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json",
                    "responseSchema": RESPONSE_SCHEMA,
                },
            }

            async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
                response = await client.post(
                    self.endpoint,
                    headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                    json=body,
                )

            if response.status_code == 404:
                # Google retires models. Because this component fails open, a stale model
                # name would otherwise disable it permanently with only "HTTP 404" in the
                # log — which is what happened to the shipped gemini-2.5-flash default on
                # 2026-08-07. A 404 is a configuration fault, not a transient one, so say
                # what to change. ListModels does not help on its own: retired models are
                # still listed there, they only fail on use.
                detail = ""
                try:
                    detail = response.json().get("error", {}).get("message", "")
                except ValueError:
                    pass
                logger.error(
                    f"Vision arbiter model '{self.model}' rejected with 404 - set GEMINI_MODEL "
                    f"to a current vision model and restart. Google said: {detail}"
                )
                return self._unavailable(
                    f"model '{self.model}' is not usable - set GEMINI_MODEL to a current "
                    f"vision model and restart ({detail or 'HTTP 404'})"
                )

            if response.status_code != 200:
                return self._unavailable(f"HTTP {response.status_code}")

            parts = response.json()["candidates"][0]["content"]["parts"]
            answer = self._parse(" ".join(p["text"] for p in parts if "text" in p))

            same_scene = bool(answer.get("same_scene"))
            confidence = float(answer.get("confidence", 0.0))
            reasoning = str(answer.get("reasoning", "")).strip()

            if same_scene and confidence >= self.MIN_CONFIDENCE:
                return {
                    "available": True,
                    "verdict": "LINKED",
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "flags": [
                        f"Vision arbiter recognises the same scene in both files "
                        f"(confidence {confidence:.0%}): {reasoning}"
                    ],
                }

            # Either the model disagrees or it is unsure. Neither rejects the submission;
            # both leave it for a human with the model's reasoning attached.
            return {
                "available": True,
                "verdict": "UNDETERMINED",
                "confidence": confidence,
                "reasoning": reasoning,
                "flags": [
                    f"Vision arbiter could not confirm the scene matches "
                    f"(same_scene={same_scene}, confidence {confidence:.0%}): {reasoning}"
                ],
            }

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning(f"Vision arbiter request failed: {str(e)}")
            return self._unavailable(f"request failed: {type(e).__name__}")
        except (KeyError, IndexError, ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"Vision arbiter reply unusable: {str(e)}")
            return self._unavailable(f"unusable reply: {type(e).__name__}")
