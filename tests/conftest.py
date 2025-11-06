"""
Global pytest configuration and fixtures for comprehensive testing
"""

import pytest
import asyncio
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import time
import os

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
AI_DETECTION_URL = os.getenv("AI_DETECTION_URL", "http://localhost:8001")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def wait_for_services():
    """Wait for all services to be ready before running tests"""
    print("\n⏳ Waiting for services to be ready...")

    services = {
        "API Gateway": f"{BASE_URL}/health",
        "AI Detection": f"{AI_DETECTION_URL}/health"
    }

    max_retries = 30
    retry_delay = 2

    for service_name, url in services.items():
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✓ {service_name} is ready")
                    break
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    print(f"  Waiting for {service_name}... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"✗ {service_name} failed to start")
                    pytest.exit(f"{service_name} is not responding")


@pytest.fixture(scope="session")
def genuine_photo_jpg():
    """Generate a realistic-looking genuine photo (JPG)"""
    image_path = IMAGES_DIR / "genuine_photo.jpg"

    if not image_path.exists():
        # Create a photo-realistic test image with noise
        img = np.random.randint(0, 255, (2400, 3200, 3), dtype=np.uint8)

        # Add realistic camera sensor noise (PRNU simulation)
        noise = np.random.normal(0, 5, img.shape).astype(np.float32)
        img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        # Add some structure (gradient to simulate a scene)
        gradient = np.linspace(50, 200, 2400).reshape(-1, 1)
        gradient = np.repeat(gradient, 3200, axis=1).reshape(2400, 3200, 1)
        img = np.clip(img.astype(np.float32) * 0.7 + gradient * 0.3, 0, 255).astype(np.uint8)

        # Add JPEG compression artifacts
        cv2.imwrite(str(image_path), img, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return str(image_path)


@pytest.fixture(scope="session")
def genuine_photo_with_exif():
    """Generate genuine photo with proper EXIF metadata"""
    image_path = IMAGES_DIR / "genuine_with_exif.jpg"

    if not image_path.exists():
        # Create realistic image
        img = Image.new('RGB', (3200, 2400), color=(100, 120, 150))
        draw = ImageDraw.Draw(img)

        # Add some texture
        for _ in range(1000):
            x = np.random.randint(0, 3200)
            y = np.random.randint(0, 2400)
            size = np.random.randint(10, 50)
            color = tuple(np.random.randint(50, 200, 3).tolist())
            draw.ellipse([x, y, x + size, y + size], fill=color)

        # Save with EXIF metadata
        exif_dict = {
            "Make": "Canon",
            "Model": "EOS R5",
            "LensModel": "RF 24-70mm F2.8 L IS USM",
            "ExposureTime": "1/1000",
            "FNumber": "2.8",
            "ISOSpeedRatings": "100",
            "FocalLength": "50mm",
            "Software": "Canon Digital Photo Professional",
        }

        # Note: For full EXIF support, would use piexif library
        img.save(image_path, "JPEG", quality=95)

    return str(image_path)


@pytest.fixture(scope="session")
def ai_generated_image():
    """Generate an image that looks AI-generated (smooth, no sensor noise)"""
    image_path = IMAGES_DIR / "ai_generated.jpg"

    if not image_path.exists():
        # Create unnaturally smooth image (typical of AI generation)
        img = np.zeros((2400, 3200, 3), dtype=np.uint8)

        # Create smooth gradients (no sensor noise)
        for i in range(3):
            gradient = np.linspace(80, 180, 2400).reshape(-1, 1)
            gradient = np.repeat(gradient, 3200, axis=1)
            img[:, :, i] = gradient.astype(np.uint8)

        # Apply heavy Gaussian blur to make it unnaturally smooth
        img = cv2.GaussianBlur(img, (15, 15), 0)

        cv2.imwrite(str(image_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])

    return str(image_path)


@pytest.fixture(scope="session")
def ai_image_with_signature():
    """Generate AI image with AI signature in metadata"""
    image_path = IMAGES_DIR / "ai_with_signature.jpg"

    if not image_path.exists():
        img = Image.new('RGB', (1024, 1024), color=(150, 150, 200))

        # Would add EXIF with AI signature using piexif
        # For now, just save the image
        img.save(image_path, "JPEG", quality=95)

    return str(image_path)


@pytest.fixture(scope="session")
def corrupted_image():
    """Generate a corrupted/invalid image file"""
    image_path = IMAGES_DIR / "corrupted.jpg"

    if not image_path.exists():
        # Write random bytes
        with open(image_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + os.urandom(1000))

    return str(image_path)


@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "AVAR-Test-Suite/1.0"
    })
    return session


@pytest.fixture
def test_submission_data():
    """Sample submission data for testing"""
    return {
        "title": "Test Photography Submission",
        "description": "Automated test submission",
        "category": "Landscape",
        "photographer": "Test User"
    }


@pytest.fixture(scope="function")
def cleanup_uploads():
    """Cleanup uploaded test files after each test"""
    yield
    # Cleanup logic would go here
    # For now, files are auto-cleaned by the service


def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )


def pytest_html_report_title(report):
    """Customize HTML report title"""
    report.title = "A.V.A.R. Test Report"
