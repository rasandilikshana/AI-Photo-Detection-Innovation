"""
Tests for RAW provenance verification — is the RAW a genuine sensor record?

Regression suite for submission 45 (production, 2026-08-07): a synthetic JPEG paired
with a synthetic DNG was APPROVED as AUTHENTIC at 1.00 confidence. Every layer passed,
because every layer asked a *consistency* question — does the JPEG match the RAW, does
the metadata match the pixels — and the attacker had fabricated both files together, so
they were perfectly consistent with each other.

Nothing asked whether the RAW itself came from a camera. It plainly did not:

    Software:     tifffile.py            a Python library wrote it
    FileType:     DNG                    the declared Canon EOS R5 writes CR3
    Frame:        2048 x 2228 (4.6MP)    an R5 sensor is 8192 x 5464 (45MP)
    Aspect:       1.088                  no camera sensor has that aspect ratio

These checks close that gap. The hardest requirement is NOT catching the fake — it is
not catching real photographers, because two legitimate workflows look superficially
similar: Adobe DNG Converter and Lightroom produce DNGs from Canon/Nikon files, and
Leica, Pentax, Ricoh, Apple and Google cameras write DNG natively. Both must pass.
"""

import pytest

from app.services.raw_provenance import RawProvenanceAnalyzer

CANON_R5_SENSOR = (8192, 5464)


@pytest.fixture
def provenance():
    return RawProvenanceAnalyzer()


def _raw(file_type="CR3", make="Canon", model="Canon EOS R5", width=8192, height=5464, **extra):
    """Grouped exiftool-style metadata for a RAW file."""
    meta = {
        "File:FileType": file_type,
        "IFD0:Make": make,
        "IFD0:Model": model,
        "IFD0:ImageWidth": width,
        "IFD0:ImageHeight": height,
    }
    meta.update(extra)
    return meta


# ---------------------------------------------------------------------------
# Check 3: written by a library, not a camera
# ---------------------------------------------------------------------------

def test_library_written_raw_is_flagged(provenance):
    """The tell that gave submission 45 away, sitting in plain sight in its EXIF."""
    strong, flags = provenance.analyze(_raw(file_type="DNG", **{"IFD0:Software": "tifffile.py"}))

    assert strong >= 1
    assert any("tifffile" in f.lower() for f in flags), flags


@pytest.mark.parametrize("writer", [
    "tifffile.py", "Pillow", "PIL", "imageio", "libtiff", "GDAL 3.4.1", "OpenCV", "rawpy",
])
def test_all_known_library_writers_are_flagged(provenance, writer):
    strong, _ = provenance.analyze(_raw(file_type="DNG", **{"IFD0:Software": writer}))
    assert strong >= 1, f"{writer!r} should be flagged as a non-camera writer"


def test_camera_raw_with_no_software_tag_is_clean(provenance):
    """Cameras generally write no Software tag into the RAW at all."""
    strong, flags = provenance.analyze(_raw())
    assert strong == 0, flags


@pytest.mark.parametrize("writer", [
    "Adobe DNG Converter 16.1", "Adobe Photoshop Lightroom Classic 13.2",
    "Adobe Camera Raw 16.2", "Capture One 23", "darktable 4.6", "RawTherapee 5.10",
])
def test_legitimate_raw_processors_are_not_flagged(provenance, writer):
    """Photographers convert and process RAWs. These are not library writers."""
    strong, flags = provenance.analyze(_raw(file_type="DNG", **{"IFD0:Software": writer}))
    assert strong == 0, f"{writer!r} must not be flagged: {flags}"


# ---------------------------------------------------------------------------
# Check 2: container must match the declared manufacturer
# ---------------------------------------------------------------------------

def test_canon_body_shipping_a_bare_dng_is_flagged(provenance):
    """A Canon body writes CR2/CR3. A DNG with no conversion provenance did not come
    out of one — and DNG is what an attacker can actually write."""
    strong, flags = provenance.analyze(_raw(file_type="DNG"))

    assert strong >= 1
    assert any("DNG" in f and "Canon" in f for f in flags), flags


def test_canon_dng_from_adobe_converter_is_accepted(provenance):
    """THE false positive that would punish real photographers. Converting a CR3 to DNG
    is a mainstream workflow and must pass untouched."""
    strong, flags = provenance.analyze(_raw(
        file_type="DNG",
        **{"IFD0:Software": "Adobe DNG Converter 16.1",
           "IFD0:OriginalRawFileName": "IMG_4471.CR3"},
    ))

    assert strong == 0, f"Adobe-converted DNG must not be flagged: {flags}"


def test_canon_dng_carrying_original_raw_filename_is_accepted(provenance):
    """OriginalRawFileName is written by DNG converters and records the source file.
    Its presence alone is legitimate conversion provenance."""
    strong, flags = provenance.analyze(_raw(
        file_type="DNG", **{"IFD0:OriginalRawFileName": "IMG_4471.CR3"}
    ))
    assert strong == 0, flags


@pytest.mark.parametrize("make,model,w,h", [
    ("Leica", "LEICA M11", 9528, 6328),
    ("PENTAX", "PENTAX K-3 Mark III", 6192, 4128),
    ("RICOH", "RICOH GR III", 6048, 4032),
    ("Apple", "iPhone 15 Pro", 8064, 6048),
    ("Google", "Pixel 8 Pro", 8160, 6144),
])
def test_brands_that_write_dng_natively_are_accepted(provenance, make, model, w, h):
    """Leica, Pentax, Ricoh, Apple ProRAW and Pixel all emit DNG straight from the
    camera. Flagging them would reject entire manufacturers."""
    strong, flags = provenance.analyze(_raw(file_type="DNG", make=make, model=model, width=w, height=h))
    assert strong == 0, f"{make} writes DNG natively: {flags}"


def test_proprietary_container_matching_its_make_is_clean(provenance):
    for file_type, make in [("CR2", "Canon"), ("CR3", "Canon"), ("NEF", "NIKON CORPORATION"),
                            ("ARW", "SONY"), ("RAF", "FUJIFILM"), ("ORF", "OLYMPUS CORPORATION")]:
        strong, flags = provenance.analyze(_raw(file_type=file_type, make=make, model=f"{make} test",
                                                width=6000, height=4000))
        assert strong == 0, f"{make}/{file_type}: {flags}"


def test_container_from_the_wrong_manufacturer_is_flagged(provenance):
    """A Nikon body cannot produce a Canon CR3."""
    strong, flags = provenance.analyze(_raw(file_type="CR3", make="NIKON CORPORATION",
                                            model="NIKON Z9", width=8256, height=5504))
    assert strong >= 1, flags


def test_unknown_manufacturer_is_not_flagged(provenance):
    """We must not reject cameras we have no table entry for."""
    strong, flags = provenance.analyze(_raw(file_type="XYZ", make="Obscure Optics",
                                            model="Model Q", width=6000, height=4000))
    assert strong == 0, flags


# ---------------------------------------------------------------------------
# Check 1: sensor geometry
# ---------------------------------------------------------------------------

def test_frame_aspect_matching_no_real_sensor_is_flagged(provenance):
    """Submission 45's actual geometry: 2048x2228, aspect 1.088. Real sensors are 3:2,
    4:3, 16:9, 1:1 or 5:4. This check needs no camera database at all."""
    strong, flags = provenance.analyze(_raw(file_type="DNG", width=2048, height=2228))

    assert strong >= 1
    assert any("aspect" in f.lower() for f in flags), flags


@pytest.mark.parametrize("w,h", [
    (8192, 5464),   # 3:2
    (5184, 3456),   # 3:2
    (4608, 3456),   # 4:3
    (5464, 8192),   # 3:2 portrait
    (4000, 4000),   # 1:1 medium format
    (5120, 2880),   # 16:9
    (5000, 4000),   # 5:4
])
def test_real_sensor_aspects_are_accepted(provenance, w, h):
    strong, flags = provenance.analyze(_raw(make="Obscure Optics", model="Model Q",
                                            file_type="XYZ", width=w, height=h))
    assert strong == 0, f"{w}x{h}: {flags}"


def test_known_body_with_the_wrong_frame_size_is_flagged(provenance):
    """The decisive check for submission 45: a 45MP Canon EOS R5 cannot produce a
    4.6MP frame."""
    strong, flags = provenance.analyze(_raw(file_type="CR3", width=2048, height=2228))

    assert strong >= 1
    assert any("8192" in f and "2048" in f for f in flags), flags


def test_known_body_with_its_real_frame_size_is_clean(provenance):
    strong, flags = provenance.analyze(_raw(file_type="CR3", width=8192, height=5464))
    assert strong == 0, flags


def test_known_body_tolerates_masked_border_margin(provenance):
    """RAW frames include optically-black margin, so the recorded frame is slightly
    larger than the nominal sensor. That must not be flagged."""
    strong, flags = provenance.analyze(_raw(file_type="CR3", width=8280, height=5520))
    assert strong == 0, flags


def test_unknown_body_frame_size_is_not_checked(provenance):
    """No table entry means no resolution claim to contradict — only aspect applies."""
    strong, flags = provenance.analyze(_raw(file_type="CR3", make="Canon",
                                            model="Canon EOS Hypothetical 99", width=3000, height=2000))
    assert strong == 0, flags


# ---------------------------------------------------------------------------
# Check 6: DNG containers get pixel scrutiny regardless
# ---------------------------------------------------------------------------

def test_dng_requests_pixel_review_even_when_provenance_is_clean(provenance):
    """A DNG is the one container an attacker can readily write, so even a
    legitimate-looking one should have its pixels examined by Layer 3."""
    assert provenance.needs_pixel_review(_raw(file_type="DNG",
        **{"IFD0:Software": "Adobe DNG Converter 16.1"})) is True


def test_proprietary_container_does_not_request_pixel_review(provenance):
    """Straight-from-camera CR3/NEF/ARW keep the cheap path."""
    for file_type in ("CR2", "CR3", "NEF", "ARW", "RAF"):
        assert provenance.needs_pixel_review(_raw(file_type=file_type)) is False, file_type


def test_no_raw_metadata_requests_no_review_and_flags_nothing(provenance):
    """Submissions without a RAW are Layer 1's problem, not this analyser's."""
    assert provenance.analyze({}) == (0, [])
    assert provenance.needs_pixel_review({}) is False


# ---------------------------------------------------------------------------
# The real synthetic DNG, end to end (skipped when the fixture is absent)
# ---------------------------------------------------------------------------

SYNTHETIC_DNG = "/home/rasan/Downloads/test/1_5_AVAR_high_realism_synthetic_Canon_R5_test.dng"
GENUINE_CR2 = "/home/rasan/Downloads/test/Twisted Crowns-2511305-Mono.CR2"


@pytest.mark.parametrize("path,expect_flagged", [(SYNTHETIC_DNG, True), (GENUINE_CR2, False)])
def test_against_the_real_files(provenance, path, expect_flagged):
    import subprocess
    from pathlib import Path

    if not Path(path).exists():
        pytest.skip(f"fixture not present: {path}")

    import json
    out = subprocess.run(["exiftool", "-j", "-a", "-G1", path], capture_output=True, text=True, timeout=30)
    grouped = json.loads(out.stdout)[0]

    strong, flags = provenance.analyze(grouped)

    if expect_flagged:
        assert strong >= 2, f"the synthetic DNG should trip several checks, got {strong}: {flags}"
    else:
        assert strong == 0, f"a genuine Canon CR2 must be clean, got: {flags}"
