"""
Tests for geometric RAW-JPG linkage verification.

Regression suite for the monochrome-crop incident (submission 38, 2026-08-07): a
genuine Canon CR2 paired with a legitimate black-and-white crop of itself scored
pHash 94 / SSIM 0.27 / histogram 0.03 and was reported as "possible AI substitution".

The predecessor (_gradient_crop_match, rigid Sobel-magnitude template correlation)
scored 0.79-0.93 on synthetic fixtures and only 0.356 on that real file. The reason
those fixtures lied: they applied a gamma curve to the *same pixels*, but a real
black-and-white conversion RE-WEIGHTS THE COLOUR CHANNELS. An edge between red and
green foliage that is strong under standard luminance weights can vanish under a
red-heavy mono mix, and flat areas can become edges. Every fixture here therefore
converts to monochrome with non-standard channel weights, which is the transform
that actually has to survive.

Geometry replaces correlation: SIFT keypoints, Lowe ratio matching, then a RANSAC
homography whose shape is checked for physical plausibility. It is a voting method
needing consensus from a few dozen keypoints out of thousands, so it tolerates the
keypoints that channel remixing destroys.
"""

import cv2
import numpy as np
import pytest

from app.services.raw_jpg_linkage import RAWJPGLinkageAnalyzer


@pytest.fixture
def linkage():
    return RAWJPGLinkageAnalyzer()


def _scene(seed: int, size=(720, 1080)) -> np.ndarray:
    """A synthetic BGR photograph.

    Modelled on how real photographs behave: a shared luminance structure carrying
    most of the detail, plus modest independent per-channel texture. Fully
    independent channels would be unrealistic — remixing them would then produce an
    essentially uncorrelated image, which no method could or should match.
    """
    rng = np.random.default_rng(seed)
    h, w = size

    luminance = rng.integers(0, 255, (h, w), dtype=np.uint8).astype(np.float32)
    luminance = cv2.GaussianBlur(luminance, (0, 0), 3.0)
    luminance = cv2.normalize(luminance, None, 15, 240, cv2.NORM_MINMAX)

    channels = []
    for _ in range(3):
        texture = rng.integers(0, 255, (h, w), dtype=np.uint8).astype(np.float32)
        texture = cv2.GaussianBlur(texture, (0, 0), 2.0)
        texture = cv2.normalize(texture, None, -30, 30, cv2.NORM_MINMAX)
        channels.append(np.clip(luminance + texture, 0, 255).astype(np.uint8))

    return cv2.merge(channels)


def _mono_edit(bgr: np.ndarray, gamma: float = 1.8) -> np.ndarray:
    """Convert to black and white with a red-heavy channel mix, then crush the tones.

    Deliberately unlike cv2.COLOR_BGR2GRAY's 0.114/0.587/0.299 BGR weights — this is
    the darkroom-style mix a photographer actually applies, and the transform the
    previous edge-correlation approach could not survive.
    """
    b, g, r = cv2.split(bgr.astype(np.float32))
    mono = 0.05 * b + 0.10 * g + 0.85 * r
    mono = np.clip(((mono / 255.0) ** gamma) * 255.0, 0, 255).astype(np.uint8)
    return cv2.cvtColor(mono, cv2.COLOR_GRAY2BGR)


# ---------------------------------------------------------------------------
# The incident: a monochrome crop of the RAW must be recognised as linked
# ---------------------------------------------------------------------------

def test_finds_genuine_crop_under_channel_remixed_mono(linkage):
    """Submission 38's transform: an 80%-width crop converted to black and white
    with a red-heavy mix and the tones crushed."""
    raw = _scene(7)
    jpg = _mono_edit(raw[:, 108:972])  # 80% of width, full height

    result = linkage._feature_homography_match(raw, jpg)

    assert result["linked"] is True, f"genuine mono crop not linked: {result}"
    assert result["crop_like"] is True
    assert result["inliers"] >= linkage.min_inliers_linked


def test_crop_rectangle_locates_the_crop_within_the_raw(linkage):
    """The rectangle is what the judge UI draws on the RAW preview, so it has to be
    right, not merely present. Normalised to the RAW frame so it survives the
    half-size demosaic and any preview resolution."""
    raw = _scene(11)
    jpg = _mono_edit(raw[:, 108:972])

    result = linkage._feature_homography_match(raw, jpg)
    x, y, w, h = result["crop_rect_norm"]

    assert x == pytest.approx(0.10, abs=0.03), f"crop x wrong: {result['crop_rect_norm']}"
    assert w == pytest.approx(0.80, abs=0.05), f"crop width wrong: {result['crop_rect_norm']}"
    assert y == pytest.approx(0.0, abs=0.03)
    assert h == pytest.approx(1.0, abs=0.05)


def test_uncropped_mono_conversion_is_linked_at_full_frame(linkage):
    """A black-and-white conversion with no crop: still linked, crop fraction ~1."""
    raw = _scene(3)
    jpg = _mono_edit(raw)

    result = linkage._feature_homography_match(raw, jpg)

    assert result["linked"] is True
    assert result["crop_fraction"] == pytest.approx(1.0, abs=0.08)


def test_accepts_rotated_crop(linkage):
    """Photographers rotate. A 90-degree rotation is a legitimate export, so the
    plausibility check must allow it while still rejecting arbitrary angles."""
    raw = _scene(5)
    jpg = _mono_edit(cv2.rotate(raw[:, 108:972], cv2.ROTATE_90_CLOCKWISE))

    result = linkage._feature_homography_match(raw, jpg)

    assert result["linked"] is True, f"rotated crop rejected: {result}"
    assert result["crop_like"] is True


# ---------------------------------------------------------------------------
# Substitution and impossible geometry must not pass
# ---------------------------------------------------------------------------

def test_rejects_unrelated_scene(linkage):
    """The attack this layer exists to catch: a different image submitted with a
    genuine RAW. Tonally identical treatment must not save it."""
    raw = _scene(1)
    jpg = _mono_edit(_scene(99))

    result = linkage._feature_homography_match(raw, jpg)

    assert result["linked"] is False, f"unrelated scene linked: {result}"
    assert result["inliers"] < linkage.min_inliers_linked


def test_rejects_perspective_warp_that_is_not_a_crop(linkage):
    """Guards the plausibility check specifically. A perspective-warped derivative
    shares plenty of keypoints, so RANSAC finds a confident homography — but a crop
    cannot introduce perspective, so this must not be accepted as linkage."""
    raw = _scene(13)
    h, w = raw.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[0, 0], [w, 0], [w * 0.72, h], [w * 0.28, h]])  # strong keystone
    warped = cv2.warpPerspective(raw, cv2.getPerspectiveTransform(src, dst), (w, h))
    jpg = _mono_edit(warped)

    result = linkage._feature_homography_match(raw, jpg)

    assert result["crop_like"] is False, f"keystone warp accepted as a crop: {result}"
    assert result["linked"] is False


def test_rejects_horizontally_stretched_derivative(linkage):
    """A non-uniform rescale changes the aspect ratio, which a crop cannot do."""
    raw = _scene(17)
    stretched = cv2.resize(raw, (int(raw.shape[1] * 1.45), raw.shape[0]))
    jpg = _mono_edit(stretched)

    result = linkage._feature_homography_match(raw, jpg)

    assert result["crop_like"] is False, f"aspect distortion accepted: {result}"


# ---------------------------------------------------------------------------
# Degenerate inputs: report inconclusive, never crash or emit NaN
# ---------------------------------------------------------------------------

def test_flat_image_reports_low_texture_without_crashing(linkage):
    """A near-featureless frame (fog, heavy black crush) yields too few keypoints for
    geometry to decide. That is the low-texture tie-break case, not a rejection."""
    raw = np.full((600, 900, 3), 40, dtype=np.uint8)
    jpg = np.full((600, 900, 3), 40, dtype=np.uint8)

    result = linkage._feature_homography_match(raw, jpg)

    assert result["low_texture"] is True
    assert result["linked"] is False
    assert all(np.isfinite(result[k]) for k in ("inlier_ratio", "crop_fraction"))
    assert result["crop_rect_norm"] is None


def test_low_texture_is_distinguished_from_substitution(linkage):
    """Both fail to link, but they need different handling: low texture escalates to
    the arbiter, an unrelated scene is rejected outright."""
    textured = _scene(23)

    flat = linkage._feature_homography_match(np.full_like(textured, 60), np.full_like(textured, 60))
    unrelated = linkage._feature_homography_match(textured, _mono_edit(_scene(77)))

    assert flat["low_texture"] is True
    assert unrelated["low_texture"] is False


def test_result_is_json_serialisable(linkage):
    """The result is persisted into verification_details; numpy scalars and NaN break
    JSON serialisation, which has bitten this pipeline before."""
    import json

    raw = _scene(29)
    result = linkage._feature_homography_match(raw, _mono_edit(raw[:, 108:972]))

    json.dumps(result)  # must not raise


# ---------------------------------------------------------------------------
# What the judge UI is given to draw
# ---------------------------------------------------------------------------

def test_unedited_pair_presents_the_whole_frame(linkage):
    """The fast path never runs geometry, but the UI still needs a rectangle: an
    unedited pair matched at full frame."""
    assert linkage._present_crop(None) == ([0.0, 0.0, 1.0, 1.0], 1.0)


def test_confirmed_crop_presents_its_rectangle(linkage):
    raw = _scene(41)
    geometry = linkage._feature_homography_match(raw, _mono_edit(raw[:, 108:972]))

    rect, fraction = linkage._present_crop(geometry)

    assert rect == geometry["crop_rect_norm"]
    assert fraction == pytest.approx(0.8, abs=0.06)


def test_failed_match_presents_no_rectangle(linkage):
    """A rejected homography still leaves numbers in crop_rect_norm. Publishing them
    would have the judge UI draw a confident box around nothing."""
    raw = _scene(43)
    geometry = linkage._feature_homography_match(raw, _mono_edit(_scene(97)))
    assert geometry["linked"] is False

    assert linkage._present_crop(geometry) == (None, 0.0)


# ---------------------------------------------------------------------------
# Arbiter wiring: consulted only on the undecidable band, and only ever rescues
# ---------------------------------------------------------------------------

def _counting_arbiter(same_scene: bool, confidence: float = 0.92):
    """A real arbiter over a fake network, so gating and the HTTP path both run."""
    import json as _json

    import httpx

    from app.services.vision_arbiter import VisionArbiter

    calls = []

    def handler(request):
        calls.append(str(request.url))
        payload = _json.dumps(
            {"same_scene": same_scene, "confidence": confidence, "reasoning": "the same ridge line"}
        )
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": payload}]}}]})

    return VisionArbiter(api_key="test-key", transport=httpx.MockTransport(handler)), calls


@pytest.mark.asyncio
async def test_arbiter_rescues_geometry_it_could_not_decide(linkage):
    """A low-texture frame geometry cannot judge, which the arbiter recognises."""
    linkage.arbiter, calls = _counting_arbiter(same_scene=True)
    flat = np.full((400, 600, 3), 50, dtype=np.uint8)
    geometry = linkage._feature_homography_match(flat, flat)

    verdict, confidence, arbitration = await linkage._arbitrate_if_needed(
        flat, flat, geometry, "SUSPICIOUS", 0.3, []
    )

    assert len(calls) == 1
    assert verdict == "PASS"
    assert confidence >= 0.9
    assert arbitration["verdict"] == "LINKED"


@pytest.mark.asyncio
async def test_arbiter_disagreement_does_not_reject(linkage):
    """The model says different scenes. That stays in review for a human — a
    non-reproducible opinion must not disqualify a photographer."""
    linkage.arbiter, calls = _counting_arbiter(same_scene=False)
    flat = np.full((400, 600, 3), 50, dtype=np.uint8)
    geometry = linkage._feature_homography_match(flat, flat)

    verdict, _, arbitration = await linkage._arbitrate_if_needed(flat, flat, geometry, "SUSPICIOUS", 0.3, [])

    assert len(calls) == 1
    assert verdict == "SUSPICIOUS", "arbiter must not be able to reject"
    assert arbitration["verdict"] == "UNDETERMINED"


@pytest.mark.asyncio
async def test_arbiter_not_consulted_when_geometry_confirmed_the_crop(linkage):
    linkage.arbiter, calls = _counting_arbiter(same_scene=True)
    raw = _scene(31)
    geometry = linkage._feature_homography_match(raw, _mono_edit(raw[:, 108:972]))
    assert geometry["linked"] is True

    verdict, _, arbitration = await linkage._arbitrate_if_needed(raw, raw, geometry, "PASS", 0.9, [])

    assert calls == [], "geometry already decided; the arbiter adds nothing"
    assert verdict == "PASS"
    assert arbitration is None


@pytest.mark.asyncio
async def test_arbiter_not_consulted_when_geometry_found_no_matching_crop(linkage):
    """The substitution case. A semantic second opinion is exactly what an AI image of
    the same subject would exploit, so it must not be offered one."""
    linkage.arbiter, calls = _counting_arbiter(same_scene=True)
    raw = _scene(37)
    geometry = linkage._feature_homography_match(raw, _mono_edit(_scene(91)))
    assert geometry["crop_like"] is False

    verdict, _, arbitration = await linkage._arbitrate_if_needed(raw, raw, geometry, "REJECT", 0.0, [])

    assert calls == []
    assert verdict == "REJECT"
    assert arbitration is None


@pytest.mark.asyncio
async def test_arbiter_absent_leaves_the_geometric_verdict_untouched(linkage):
    """Default construction has no API key, so the pipeline runs unchanged without it."""
    flat = np.full((400, 600, 3), 50, dtype=np.uint8)
    geometry = linkage._feature_homography_match(flat, flat)

    assert linkage.arbiter.enabled is False
    verdict, confidence, arbitration = await linkage._arbitrate_if_needed(
        flat, flat, geometry, "SUSPICIOUS", 0.3, []
    )

    assert (verdict, confidence, arbitration) == ("SUSPICIOUS", 0.3, None)
