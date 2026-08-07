"""
RAW Provenance Analysis: is the submitted RAW a genuine sensor record?

Every other check in this pipeline verifies CONSISTENCY — does the JPEG's metadata
describe its pixels, does it match the RAW's metadata, is the JPEG geometrically a crop
of the RAW. Consistency checking is necessary but it has a structural blind spot: an
attacker who fabricates the JPEG and the RAW *together* produces two files that are
perfectly consistent with each other, and passes everything.

That is not hypothetical. Production submission 45 (2026-08-07) was approved AUTHENTIC
at 1.00 confidence with a synthetic JPEG and a synthetic DNG. It announced itself four
ways, none of which anything looked at:

    Software:  tifffile.py           a Python library wrote it, not a camera
    FileType:  DNG                   the declared Canon EOS R5 writes CR3
    Frame:     2048 x 2228 (4.6MP)   an R5 sensor is 8192 x 5464 (45MP)
    Aspect:    1.088                 no camera sensor has that aspect ratio

This module asks the provenance question instead. It works from metadata alone (no
pixel decoding), so it is cheap enough to run on every submission.

DESIGN CONSTRAINT — false positives are worse than false negatives here. A rejected
photographer loses their competition entry, while a fake that slips past this still
faces the linkage, fingerprint and third-party layers. So every check abstains when it
lacks the knowledge to be sure: unknown manufacturers, unknown camera models and
legitimate conversion workflows all pass untouched. The two workflows that look
superficially like the attack, and must never be flagged, are Adobe DNG Converter /
Lightroom output from Canon and Nikon files, and the manufacturers whose cameras write
DNG natively.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RawProvenanceAnalyzer:
    """Verifies a RAW file is plausibly a camera's own record of a capture."""

    # Software strings that mean a program wrote this file rather than a camera. Cameras
    # write no Software tag into RAW at all; photo tools write their own product names.
    # A general-purpose imaging or array library in a RAW's Software tag has no
    # legitimate explanation.
    LIBRARY_WRITERS = [
        "tifffile", "pillow", "imageio", "libtiff", "gdal", "numpy", "scipy",
        "opencv", "cv2", "rawpy", "libraw", "scikit-image", "skimage", "matplotlib",
        "imagemagick", "graphicsmagick", "python",
    ]

    # Checked as a whole word so "PIL" does not match inside "Pilot" or "compiled".
    LIBRARY_WRITERS_EXACT = ["pil"]

    # Legitimate RAW processors and converters. Checked BEFORE the library list, because
    # some ship with an imaging library's name somewhere in their version string.
    LEGITIMATE_PROCESSORS = [
        "adobe", "lightroom", "camera raw", "dng converter", "photoshop",
        "capture one", "captureone", "phase one", "dxo", "iridient", "rawtherapee",
        "darktable", "luminar", "on1", "affinity", "gimp", "exiftool",
        "silkypix", "sigma photo pro", "canon digital photo professional", "nikon",
    ]

    # Containers each manufacturer's cameras actually produce. Brands absent from this
    # table are never flagged on container grounds.
    EXPECTED_CONTAINERS = {
        "canon": {"CR2", "CR3", "CRW", "TIF", "TIFF"},
        "nikon": {"NEF", "NRW", "TIF", "TIFF"},
        "sony": {"ARW", "SR2", "SRF"},
        "fujifilm": {"RAF"},
        "olympus": {"ORF"},
        "om digital solutions": {"ORF"},
        "panasonic": {"RW2", "RAW"},
        "leica": {"DNG", "RWL", "RAW"},
        "pentax": {"PEF", "DNG"},
        "ricoh": {"PEF", "DNG"},
        "sigma": {"X3F", "DNG"},
        "hasselblad": {"3FR", "FFF", "DNG"},
        "phase one": {"IIQ", "TIF", "TIFF"},
        "mamiya": {"MEF", "IIQ"},
        "epson": {"ERF"},
        "kodak": {"DCR", "KDC"},
        "minolta": {"MRW"},
        "samsung": {"SRW", "DNG"},
        "apple": {"DNG"},
        "google": {"DNG"},
        "dji": {"DNG"},
        "gopro": {"GPR", "DNG"},
        "nokia": {"DNG"},
        "oneplus": {"DNG"},
        "xiaomi": {"DNG"},
        "motorola": {"DNG"},
        "zeiss": {"DNG"},
    }

    # Tags a DNG converter writes. Any of them is evidence of a real conversion rather
    # than a fabricated container.
    CONVERSION_PROVENANCE_TAGS = [
        "OriginalRawFileName", "OriginalRawFileData", "OriginalRawFileDigest",
        "DNGPrivateData", "PreviewApplicationName", "RawDataUniqueID",
    ]

    # Aspect ratios physical image sensors are built in. Deliberately table-free: it
    # applies to every camera, including ones we have never heard of. 5% tolerance
    # absorbs the optically-black margin recorded in a RAW frame.
    SENSOR_ASPECTS = [3 / 2, 4 / 3, 16 / 9, 1.0, 5 / 4, 16 / 10, 3 / 1]
    ASPECT_TOLERANCE = 0.05

    # Nominal full-sensor dimensions for bodies we can speak to. Unknown models are not
    # checked — absence from this table is not evidence of anything. Extend freely.
    SENSOR_SIZES = {
        "canon eos r5": (8192, 5464),
        "canon eos r5 mark ii": (8736, 5824),
        "canon eos r6": (5472, 3648),
        "canon eos r6 mark ii": (6960, 4640),
        "canon eos r3": (6096, 4064),
        "canon eos r7": (6960, 4640),
        "canon eos r8": (6000, 4000),
        "canon eos r100": (6000, 4000),
        "canon eos 5d mark iv": (6720, 4480),
        "canon eos 6d mark ii": (6240, 4160),
        "canon eos 90d": (6960, 4640),
        "canon eos 600d": (5184, 3456),
        "canon eos 700d": (5184, 3456),
        "canon eos 800d": (6000, 4000),
        "canon eos 1500d": (6000, 4000),
        "nikon z9": (8256, 5504),
        "nikon z8": (8256, 5504),
        "nikon z6": (6048, 4024),
        "nikon z6_2": (6048, 4024),
        "nikon z7": (8256, 5504),
        "nikon z7_2": (8256, 5504),
        "nikon d850": (8256, 5504),
        "nikon d780": (6048, 4024),
        "sony ilce-1": (8640, 5760),
        "sony ilce-7m4": (7008, 4672),
        "sony ilce-7rm5": (9504, 6336),
        "sony ilce-7m3": (6000, 4000),
        "sony ilce-6400": (6000, 4000),
        "fujifilm x-t5": (7728, 5152),
        "fujifilm x-h2": (7728, 5152),
        "fujifilm gfx100 ii": (11648, 8736),
        "leica m11": (9528, 6328),
        "pentax k-3 mark iii": (6192, 4128),
        "ricoh gr iii": (6048, 4032),
        "om system om-1": (5184, 3888),
        "panasonic dc-s5m2": (6000, 4000),
    }

    # A recorded frame may exceed the nominal sensor by this much because of masked
    # border pixels; anything beyond it in either direction is a real contradiction.
    SIZE_TOLERANCE = 0.06

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tag(grouped: Dict, name: str) -> Optional[str]:
        """Read a tag by its bare name from grouped exiftool output ('IFD0:Make')."""
        for key, value in grouped.items():
            if key.split(":")[-1] == name and value not in (None, ""):
                return value
        return None

    def _writer_software(self, grouped: Dict) -> str:
        parts = [
            self._tag(grouped, tag) or ""
            for tag in ("Software", "ProcessingSoftware", "CreatorTool", "HistorySoftwareAgent")
        ]
        return " ".join(str(p) for p in parts).strip()

    def _file_type(self, grouped: Dict) -> str:
        return str(self._tag(grouped, "FileType") or "").upper()

    def _make_key(self, grouped: Dict) -> str:
        """Normalise 'NIKON CORPORATION' / 'OLYMPUS CORPORATION' to a table key."""
        make = str(self._tag(grouped, "Make") or "").strip().lower()
        for known in self.EXPECTED_CONTAINERS:
            if make.startswith(known) or known in make:
                return known
        return ""

    def _frame_size(self, grouped: Dict) -> Optional[Tuple[int, int]]:
        w, h = self._tag(grouped, "ImageWidth"), self._tag(grouped, "ImageHeight")
        try:
            w, h = int(w), int(h)
        except (TypeError, ValueError):
            return None
        return (w, h) if w > 0 and h > 0 else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def needs_pixel_review(self, grouped: Dict) -> bool:
        """Whether this RAW should have its pixels examined by the third-party layer.

        DNG is the one RAW container an attacker can readily author, and a fabricated one
        that is internally consistent passes every metadata check by construction. So a
        DNG earns pixel scrutiny even when its provenance looks clean, while
        straight-from-camera proprietary formats keep the cheap path.
        """
        return bool(grouped) and self._file_type(grouped) == "DNG"

    def analyze(self, grouped: Dict) -> Tuple[int, List[str]]:
        """Check whether the RAW is plausibly a camera's own record.

        Args:
            grouped: exiftool -G1 output for the RAW file

        Returns:
            (strong_indicator_count, flags)
        """
        if not grouped:
            return 0, []

        strong = 0
        flags: List[str] = []

        for check in (self._check_writer, self._check_container, self._check_geometry):
            try:
                count, messages = check(grouped)
                strong += count
                flags.extend(messages)
            except Exception as e:  # a malformed RAW must not break the pipeline
                logger.warning(f"RAW provenance check {check.__name__} failed: {str(e)}")

        return strong, flags

    # ------------------------------------------------------------------
    # Check 3: who wrote the file
    # ------------------------------------------------------------------

    def _check_writer(self, grouped: Dict) -> Tuple[int, List[str]]:
        software = self._writer_software(grouped)
        if not software:
            return 0, []  # cameras write no Software tag into RAW

        lowered = software.lower()

        # Recognised photo tools first: some carry a library name in their version string.
        if any(proc in lowered for proc in self.LEGITIMATE_PROCESSORS):
            return 0, []

        words = set(lowered.replace("/", " ").replace("-", " ").replace(".", " ").split())
        hit = next((lib for lib in self.LIBRARY_WRITERS if lib in lowered), None)
        if hit is None:
            hit = next((lib for lib in self.LIBRARY_WRITERS_EXACT if lib in words), None)

        if hit:
            return 1, [
                f"PROVENANCE: RAW was written by '{software}' — a general-purpose imaging "
                "library, not a camera or a photo editor. Camera RAW files are not "
                "produced by software libraries."
            ]
        return 0, []

    # ------------------------------------------------------------------
    # Check 2: container vs declared manufacturer
    # ------------------------------------------------------------------

    def _check_container(self, grouped: Dict) -> Tuple[int, List[str]]:
        make_key = self._make_key(grouped)
        file_type = self._file_type(grouped)
        if not make_key or not file_type:
            return 0, []  # unknown manufacturer: nothing to contradict

        expected = self.EXPECTED_CONTAINERS[make_key]
        if file_type in expected:
            return 0, []

        make = self._tag(grouped, "Make")

        if file_type == "DNG":
            # Converting a proprietary RAW to DNG is a mainstream workflow, so only a DNG
            # with NO conversion provenance is suspect.
            software = self._writer_software(grouped).lower()
            if any(proc in software for proc in self.LEGITIMATE_PROCESSORS):
                return 0, []
            if any(self._tag(grouped, tag) for tag in self.CONVERSION_PROVENANCE_TAGS):
                return 0, []

            return 1, [
                f"PROVENANCE: DNG container declaring a {make} body, which writes "
                f"{'/'.join(sorted(expected))}. No DNG-converter provenance is present "
                "(no converter software, no OriginalRawFileName) — consistent with a "
                "fabricated RAW rather than a converted one."
            ]

        return 1, [
            f"PROVENANCE: {file_type} container declaring a {make} body, which writes "
            f"{'/'.join(sorted(expected))} — this container does not come from this manufacturer."
        ]

    # ------------------------------------------------------------------
    # Check 1: sensor geometry
    # ------------------------------------------------------------------

    def _check_geometry(self, grouped: Dict) -> Tuple[int, List[str]]:
        size = self._frame_size(grouped)
        if size is None:
            return 0, []

        width, height = size
        strong, flags = 0, []

        # 1a. Aspect ratio — applies to every camera, no table needed.
        aspect = width / height
        if not any(
            abs(aspect - a) / a <= self.ASPECT_TOLERANCE or abs(aspect - 1 / a) / (1 / a) <= self.ASPECT_TOLERANCE
            for a in self.SENSOR_ASPECTS
        ):
            strong += 1
            flags.append(
                f"PROVENANCE: RAW frame is {width}x{height}, aspect ratio {aspect:.3f} — "
                "no camera sensor is built in this shape (sensors are 3:2, 4:3, 16:9, 1:1 or 5:4)."
            )

        # 1b. Declared body's known resolution, when we have one.
        model = str(self._tag(grouped, "Model") or "").strip().lower()
        nominal = self.SENSOR_SIZES.get(model)
        if nominal:
            exp_w, exp_h = nominal
            # Compare on megapixels so portrait/landscape recording order does not matter.
            actual_mp, expected_mp = width * height, exp_w * exp_h
            if abs(actual_mp - expected_mp) / expected_mp > (1 + self.SIZE_TOLERANCE) ** 2 - 1:
                strong += 1
                flags.append(
                    f"PROVENANCE: declared {self._tag(grouped, 'Model')} has a "
                    f"{exp_w}x{exp_h} sensor ({expected_mp / 1e6:.1f}MP) but the RAW frame is "
                    f"{width}x{height} ({actual_mp / 1e6:.1f}MP) — this body cannot produce this frame."
                )

        return strong, flags
