#!/usr/bin/env python
"""Verify the vision arbiter against the real Gemini API.

The unit tests run over a fake network, so they prove the gating and failure handling
but not that Google accepts our request shape. Run this once after configuring
GEMINI_API_KEY to confirm the live wire format, then again if the model is changed.

Usage, from src/backend/ai-detection-service:

    ./venv/bin/python scripts/verify_vision_arbiter.py <raw-or-image> <jpg>

Passing a genuine RAW+JPG pair should report LINKED. Passing two unrelated images
should report UNDETERMINED — the arbiter has no rejecting verdict by design.
Exits non-zero if the API could not be reached or its reply was unusable.
"""

import asyncio
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.raw_jpg_linkage import RAWJPGLinkageAnalyzer  # noqa: E402
from app.services.vision_arbiter import VisionArbiter  # noqa: E402

RAW_SUFFIXES = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2"}


def load(path: str):
    if Path(path).suffix.lower() in RAW_SUFFIXES:
        image = RAWJPGLinkageAnalyzer()._load_raw_image(path)
    else:
        image = cv2.imread(path)
    if image is None:
        sys.exit(f"could not read {path}")
    return image


async def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    arbiter = VisionArbiter()
    print(f"model            {arbiter.model}")
    print(f"endpoint         {arbiter.endpoint}")
    print(f"key configured   {arbiter.enabled}")
    if not arbiter.enabled:
        sys.exit("\nGEMINI_API_KEY is not set — add it to .env and re-run (see .env.example)")

    image_a, image_b = load(sys.argv[1]), load(sys.argv[2])
    print(f"\nsending          {image_a.shape[1]}x{image_a.shape[0]} and "
          f"{image_b.shape[1]}x{image_b.shape[0]}, downscaled to "
          f"{arbiter.SEND_LONG_EDGE}px long edge")

    # low_texture forces the gate open; this bypasses geometry deliberately, because the
    # point is to exercise the live API call rather than the decision that precedes it.
    result = await arbiter.arbitrate(image_a, image_b, {"linked": False, "low_texture": True})

    print(f"\nreachable        {result['available']}")
    print(f"verdict          {result['verdict']}")
    print(f"confidence       {result['confidence']:.2f}")
    print(f"reasoning        {result['reasoning'] or '(none)'}")
    for flag in result["flags"]:
        print(f"  - {flag}")

    if not result["available"]:
        print("\nFAILED: the API was not reachable or its reply was unusable.")
        return 1

    print("\nOK: live request accepted and reply parsed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
