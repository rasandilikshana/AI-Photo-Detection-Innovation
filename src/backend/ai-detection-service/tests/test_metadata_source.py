"""
Tests for where Layer 1 sources camera metadata from.

Regression suite for the Photoshop-export incident (submissions 35/38, 2026-08-07):
a genuine Canon CR2 paired with a legitimately edited JPEG was REJECTED as
AI_GENERATED because Photoshop's "Export As" strips EXIF and Layer 1 read camera
metadata exclusively from the JPEG. The RAW — the camera's own record, which cannot
be stripped by an export dialog — was on disk and never consulted.

The RAW is the authoritative source for camera identity and capture settings. The
JPEG's EXIF is optional; when present it must be cross-checked against the RAW,
because a JPEG declaring a *different* camera than its RAW is the real
transplant signal.

Layer 1 reads the RAW through exiftool only (it never demosaics), so a
metadata-equivalent stand-in exercises the production code path exactly.
"""

import subprocess

import pytest
from PIL import Image

from app.services.layer1_metadata import MetadataAnalyzer

CANON_TAGS = {
    "EXIF:Make": "Canon",
    "EXIF:Model": "Canon EOS 600D",
    "EXIF:LensModel": "EF-S55-250mm f/4-5.6 IS II",
    "EXIF:ExposureTime": "1/100",
    "EXIF:FNumber": "5.6",
    "EXIF:ISO": "100",
    "EXIF:FocalLength": "250",
    "EXIF:DateTimeOriginal": "2025:09:21 08:18:50",
}


def _write_tags(path, tags):
    """Write EXIF tags with exiftool. Only EXIF: tags are written, so no XMP block
    (and therefore no 'exiftool CLI' laundering flag) is introduced."""
    args = ["exiftool", "-overwrite_original", "-q"]
    args += [f"-{tag}={value}" for tag, value in tags.items()]
    args.append(str(path))
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f"exiftool failed: {result.stderr}"


def _make_image(path, size=(800, 600), fmt="JPEG"):
    Image.new("RGB", size, color=(90, 120, 90)).save(str(path), fmt)
    return path


@pytest.fixture(scope="module")
def analyzer():
    a = MetadataAnalyzer()
    if not a.exiftool_available:
        pytest.skip("exiftool is required for metadata-source tests")
    return a


@pytest.fixture
def canon_raw(tmp_path):
    """Stand-in for the submitted CR2: carries the camera's full EXIF block."""
    path = _make_image(tmp_path / "capture.tif", fmt="TIFF")
    _write_tags(path, {**CANON_TAGS, "EXIF:ExifImageWidth": "800", "EXIF:ExifImageHeight": "600"})
    return str(path)


@pytest.fixture
def stripped_jpg(tmp_path):
    """A Photoshop 'Export As' result: pixels only, every EXIF tag gone."""
    return str(_make_image(tmp_path / "edited.jpg"))


@pytest.fixture
def camera_jpg(tmp_path):
    """A straight-out-of-camera JPEG."""
    path = _make_image(tmp_path / "ooc.jpg")
    _write_tags(path, {**CANON_TAGS, "EXIF:ExifImageWidth": "800", "EXIF:ExifImageHeight": "600"})
    return str(path)


# ---------------------------------------------------------------------------
# The RAW is authoritative when the JPEG has been stripped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stripped_jpeg_with_valid_raw_is_not_rejected(analyzer, stripped_jpg, canon_raw):
    """The incident: a legitimate edited export has no EXIF, but its RAW does.
    Missing EXIF on the JPEG is not evidence of anything when the RAW is present."""
    result = await analyzer.analyze(stripped_jpg, canon_raw)

    assert result["verdict"] == "PASS", f"legitimate edit rejected: {result['flags']}"


@pytest.mark.asyncio
async def test_camera_metadata_is_read_from_the_raw(analyzer, stripped_jpg, canon_raw):
    """Downstream camera-reputation keys off this dict; it must carry the camera
    identity from the RAW rather than the stripped JPEG's empty strings."""
    result = await analyzer.analyze(stripped_jpg, canon_raw)

    assert result["metadata"]["Make"] == "Canon"
    assert result["metadata"]["Model"] == "Canon EOS 600D"
    assert result["metadata"]["DateTimeOriginal"] == "2025:09:21 08:18:50"


@pytest.mark.asyncio
async def test_stripped_jpeg_is_reported_as_informational_not_as_missing_camera(
    analyzer, stripped_jpg, canon_raw
):
    """The judge should read 'sourced from the RAW', not eight 'Missing ...' flags
    that imply the submission has no provenance."""
    result = await analyzer.analyze(stripped_jpg, canon_raw)

    assert not any("metadata completely stripped" in f for f in result["flags"])
    assert any("sourced from the RAW" in f for f in result["flags"])


# ---------------------------------------------------------------------------
# The JPEG's own EXIF is cross-checked, not trusted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_jpeg_declaring_a_different_camera_than_the_raw_is_flagged(
    analyzer, tmp_path, canon_raw
):
    """A JPEG whose EXIF names a different body than the RAW it ships with did not
    come from that RAW. This is the transplant signal that matters."""
    jpg = _make_image(tmp_path / "foreign.jpg")
    _write_tags(jpg, {**CANON_TAGS, "EXIF:Model": "Canon EOS 5D Mark IV"})

    result = await analyzer.analyze(str(jpg), canon_raw)

    assert result["verdict"] in ("SUSPICIOUS", "REJECT"), f"got {result['verdict']}"
    assert any("Canon EOS 5D Mark IV" in f and "Canon EOS 600D" in f for f in result["flags"]), (
        f"disagreement not reported: {result['flags']}"
    )


@pytest.mark.asyncio
async def test_jpeg_capture_date_disagreeing_with_the_raw_is_flagged(analyzer, tmp_path, canon_raw):
    """Same body, different exposure: the JPEG's metadata came from another frame."""
    jpg = _make_image(tmp_path / "otherframe.jpg")
    _write_tags(jpg, {**CANON_TAGS, "EXIF:DateTimeOriginal": "2024:01:02 11:00:00"})

    result = await analyzer.analyze(str(jpg), canon_raw)

    assert result["verdict"] in ("SUSPICIOUS", "REJECT"), f"got {result['verdict']}"
    assert any("DateTimeOriginal" in f for f in result["flags"])


@pytest.mark.asyncio
async def test_matching_camera_jpeg_and_raw_still_pass(analyzer, camera_jpg, canon_raw):
    """The happy path must stay clean: agreeing metadata, no flags."""
    result = await analyzer.analyze(camera_jpg, canon_raw)

    assert result["verdict"] == "PASS"
    assert result["metadata"]["Model"] == "Canon EOS 600D"


# ---------------------------------------------------------------------------
# Trusting the RAW must not open a hole
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_signature_in_the_raw_is_detected(analyzer, stripped_jpg, tmp_path):
    """If the RAW becomes the trusted source, it must also be scanned. A synthetic
    DNG advertising its generator has to be caught."""
    raw = _make_image(tmp_path / "synthetic.tif", fmt="TIFF")
    _write_tags(raw, {**CANON_TAGS, "EXIF:Software": "Stable Diffusion XL"})

    result = await analyzer.analyze(stripped_jpg, str(raw))

    assert result["verdict"] == "REJECT"
    assert result["ai_signatures_found"] >= 1


@pytest.mark.asyncio
async def test_ai_signature_in_the_jpeg_still_rejects_when_the_raw_is_clean(
    analyzer, tmp_path, canon_raw
):
    """Regression guard: sourcing metadata from the RAW must not stop the JPEG
    from being scanned for generator signatures."""
    jpg = _make_image(tmp_path / "generated.jpg")
    _write_tags(jpg, {"EXIF:Software": "Midjourney v6"})

    result = await analyzer.analyze(str(jpg), canon_raw)

    assert result["verdict"] == "REJECT"
    assert result["ai_signatures_found"] >= 1


@pytest.mark.asyncio
async def test_stripped_jpeg_with_no_raw_is_still_rejected(analyzer, stripped_jpg):
    """Without a RAW there is nothing to fall back on, so the JPEG stays
    authoritative and a bare file is still rejected."""
    result = await analyzer.analyze(stripped_jpg, None)

    assert result["verdict"] == "REJECT"
