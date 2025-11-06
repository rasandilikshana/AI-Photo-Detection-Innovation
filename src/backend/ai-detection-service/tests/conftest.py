"""
Pytest configuration and fixtures for testing
"""

import pytest
import numpy as np
from PIL import Image
import tempfile
from pathlib import Path


@pytest.fixture
def sample_jpg_image():
    """Create a sample JPG image for testing"""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='blue')
        img.save(f.name, 'JPEG')
        yield f.name
        Path(f.name).unlink()


@pytest.fixture
def sample_image_array():
    """Create a sample image array for testing"""
    return np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)


@pytest.fixture
def mock_metadata():
    """Mock EXIF metadata for testing"""
    return {
        "Make": "Canon",
        "Model": "EOS R5",
        "LensModel": "RF 24-70mm F2.8",
        "ExposureTime": "1/1000",
        "FNumber": "2.8",
        "ISO": "100",
        "FocalLength": "50mm",
        "DateTimeOriginal": "2024:01:15 10:30:00"
    }


@pytest.fixture
def ai_signature_metadata():
    """Mock metadata with AI signature"""
    return {
        "Software": "Midjourney Bot",
        "Comment": "AI Generated Image"
    }
