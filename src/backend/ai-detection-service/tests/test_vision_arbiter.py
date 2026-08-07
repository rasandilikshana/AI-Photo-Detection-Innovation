"""
Tests for the vision arbiter — a gated VLM tie-breaker for RAW-JPG linkage.

Design constraints these tests enforce:

1. It runs ONLY on the band geometry cannot decide. Semantic similarity is the
   easiest property for a forger to satisfy — an AI image of the same subject as
   the RAW would pass any "is this the same scene?" check — so it must never be
   consulted when keypoint geometry already answered.
2. It can RESCUE but never CONDEMN. It may upgrade an inconclusive result to
   linked; it may not reject a submission. A non-reproducible opinion must not be
   the reason a photographer is disqualified.
3. It fails open. A third-party outage or timeout leaves the geometric verdict
   untouched rather than blocking the submission.
4. It is disabled without a key, so the pipeline is fully functional without it.
"""

import json

import httpx
import numpy as np
import pytest

from app.services.vision_arbiter import VisionArbiter


def _geometry(linked=False, crop_like=False, low_texture=False, inliers=0):
    return {
        "linked": linked, "crop_like": crop_like, "low_texture": low_texture,
        "inliers": inliers, "inlier_ratio": 0.0, "good_matches": inliers,
        "keypoints_raw": 100, "keypoints_jpg": 100, "crop_rect_norm": None,
        "crop_fraction": 0.0, "rotation_deg": 0.0, "aspect_skew": 0.0,
        "reproj_error_px": 0.0, "reason": "test",
    }


def _image(seed=0, size=(240, 320)):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, (*size, 3), dtype=np.uint8)


def _gemini_reply(same_scene: bool, reasoning: str, confidence: float = 0.9):
    payload = json.dumps({"same_scene": same_scene, "confidence": confidence, "reasoning": reasoning})
    return {"candidates": [{"content": {"parts": [{"text": payload}]}}]}


def _arbiter(handler, **kw):
    """An arbiter wired to a fake network, so the real httpx request path is exercised."""
    return VisionArbiter(api_key="test-key", transport=httpx.MockTransport(handler), **kw)


# ---------------------------------------------------------------------------
# Gating: only the undecidable band
# ---------------------------------------------------------------------------

def test_does_not_arbitrate_when_geometry_confirmed_the_crop():
    """Geometry proved linkage. Asking a VLM could only weaken a decided result."""
    assert VisionArbiter(api_key="k").should_arbitrate(_geometry(linked=True, crop_like=True, inliers=400)) is False


def test_does_not_arbitrate_when_geometry_decisively_rejects():
    """No crop of the RAW matches: the shape check failed outright. A forger pairing an
    AI image with a same-subject RAW must not get a semantic second opinion here."""
    assert VisionArbiter(api_key="k").should_arbitrate(_geometry(crop_like=False, inliers=5)) is False


def test_arbitrates_on_low_texture():
    """Fog, minimalism, long exposures: too few keypoints for geometry to decide."""
    assert VisionArbiter(api_key="k").should_arbitrate(_geometry(low_texture=True)) is True


def test_arbitrates_on_plausible_crop_with_thin_support():
    assert VisionArbiter(api_key="k").should_arbitrate(_geometry(crop_like=True, inliers=20)) is True


def test_never_arbitrates_without_a_key():
    """No key configured means the whole feature is inert, not broken."""
    arbiter = VisionArbiter(api_key="")
    assert arbiter.enabled is False
    assert arbiter.should_arbitrate(_geometry(low_texture=True)) is False


# ---------------------------------------------------------------------------
# It can rescue, but never condemn
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirms_linkage_when_the_model_recognises_the_scene():
    def handler(request):
        return httpx.Response(200, json=_gemini_reply(True, "Both show the same rock arch at dawn."))

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "LINKED"
    assert "rock arch" in result["reasoning"]


@pytest.mark.asyncio
async def test_disagreement_yields_undetermined_never_rejection():
    """The model says different scenes. That is attached as evidence for the judge, but
    it must not become a rejection — a VLM opinion cannot disqualify a photographer."""
    def handler(request):
        return httpx.Response(200, json=_gemini_reply(False, "Different subjects entirely."))

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "UNDETERMINED"
    assert result["verdict"] != "NOT_LINKED"
    assert "Different subjects" in result["reasoning"]


@pytest.mark.asyncio
async def test_low_model_confidence_does_not_confirm_linkage():
    def handler(request):
        return httpx.Response(200, json=_gemini_reply(True, "Possibly similar.", confidence=0.3))

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "UNDETERMINED"


# ---------------------------------------------------------------------------
# Fails open
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fails_open_on_http_error():
    def handler(request):
        return httpx.Response(500, text="upstream exploded")

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "UNDETERMINED"
    assert result["available"] is False


@pytest.mark.asyncio
async def test_fails_open_on_timeout():
    def handler(request):
        raise httpx.ReadTimeout("too slow", request=request)

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "UNDETERMINED"
    assert result["available"] is False


@pytest.mark.asyncio
async def test_fails_open_on_unparseable_reply():
    def handler(request):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "not json"}]}}]})

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "UNDETERMINED"


@pytest.mark.asyncio
async def test_tolerates_markdown_fenced_json():
    """Models wrap JSON in code fences despite being asked not to."""
    fenced = "```json\n" + json.dumps({"same_scene": True, "confidence": 0.95, "reasoning": "Same ridge line."}) + "\n```"

    def handler(request):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": fenced}]}}]})

    result = await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    assert result["verdict"] == "LINKED"


# ---------------------------------------------------------------------------
# Request shape
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sends_key_header_and_two_downscaled_jpegs():
    captured = {}

    def handler(request):
        captured["key"] = request.headers.get("x-goog-api-key")
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_gemini_reply(True, "ok"))

    await _arbiter(handler, model="gemini-2.5-flash").arbitrate(
        _image(1, size=(3000, 4000)), _image(2, size=(3000, 4000)), _geometry(low_texture=True)
    )

    assert captured["key"] == "test-key"
    assert "gemini-2.5-flash:generateContent" in captured["url"]

    parts = captured["body"]["contents"][0]["parts"]
    images = [p for p in parts if "inline_data" in p]
    assert len(images) == 2, "both the RAW rendering and the JPEG must be sent"
    assert all(p["inline_data"]["mime_type"] == "image/jpeg" for p in images)
    # Downscaled before sending: a 4000px frame must not go out at full size
    assert all(len(p["inline_data"]["data"]) < 900_000 for p in images)


@pytest.mark.asyncio
async def test_generation_config_uses_camelcase_so_google_honours_it():
    """The Gemini REST API expects camelCase inside generationConfig. snake_case keys are
    accepted by the endpoint but silently ignored, so the model would answer in prose and
    every reply would fail to parse — a failure only reproducible against the live API."""
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_gemini_reply(True, "ok"))

    await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    config = captured["body"]["generationConfig"]
    assert "responseMimeType" in config, f"snake_case would be ignored by Google: {list(config)}"
    assert config["responseMimeType"] == "application/json"
    assert "response_mime_type" not in config


@pytest.mark.asyncio
async def test_response_schema_constrains_the_reply_shape():
    """Asking for JSON in the prompt is a request; a responseSchema is a constraint."""
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_gemini_reply(True, "ok"))

    await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    schema = captured["body"]["generationConfig"]["responseSchema"]
    assert schema["type"] == "OBJECT"
    assert set(schema["required"]) == {"same_scene", "confidence", "reasoning"}
    assert schema["properties"]["same_scene"]["type"] == "BOOLEAN"


@pytest.mark.asyncio
async def test_prompt_asks_about_scene_correspondence_not_ai_generation():
    """Whether the image is AI-generated is Layer 3's question. Conflating the two here
    would double-count one signal and invite the arbiter to condemn."""
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_gemini_reply(True, "ok"))

    await _arbiter(handler).arbitrate(_image(1), _image(2), _geometry(low_texture=True))

    prompt = " ".join(p["text"] for p in captured["body"]["contents"][0]["parts"] if "text" in p).lower()
    assert "same" in prompt and "scene" in prompt
    assert "ai-generated" not in prompt and "artificial" not in prompt
