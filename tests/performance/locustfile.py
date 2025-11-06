"""
Performance and Load Testing with Locust
Simulates concurrent users submitting photos for analysis
"""

from locust import HttpUser, task, between, events
from pathlib import Path
import random
import time


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"


class PhotoSubmissionUser(HttpUser):
    """
    Simulates a user submitting photos for AI detection analysis
    """

    # Wait between 1-5 seconds between tasks
    wait_time = between(1, 5)

    def on_start(self):
        """Initialize test images on user start"""
        self.test_images = list(FIXTURES_DIR.glob("*.jpg"))

        if not self.test_images:
            print("Warning: No test images found in fixtures/images/")
            # Create a simple test image
            from PIL import Image
            import numpy as np

            FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
            test_img_path = FIXTURES_DIR / "load_test.jpg"

            if not test_img_path.exists():
                img = Image.fromarray(
                    np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)
                )
                img.save(test_img_path, "JPEG")

            self.test_images = [test_img_path]

    @task(3)
    def submit_for_analysis(self):
        """
        Submit a photo for full analysis (most common operation)
        Weight: 3 (happens 3x more often than other tasks)
        """
        image_path = random.choice(self.test_images)

        with open(image_path, 'rb') as f:
            files = {'jpg_file': (image_path.name, f, 'image/jpeg')}

            with self.client.post(
                "/api/v1/analyze",
                files=files,
                catch_response=True,
                timeout=120,
                name="/api/v1/analyze [Full Analysis]"
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    verdict = data.get('verdict', 'UNKNOWN')
                    processing_time = data.get('processing_time_ms', 0)

                    response.success()

                    # Log metrics
                    events.request.fire(
                        request_type="METRIC",
                        name=f"Analysis Result: {verdict}",
                        response_time=processing_time,
                        response_length=len(response.content),
                        exception=None,
                        context={}
                    )
                else:
                    response.failure(f"Analysis failed with status {response.status_code}")

    @task(1)
    def metadata_only_check(self):
        """
        Quick metadata-only analysis (fast operation)
        Weight: 1
        """
        image_path = random.choice(self.test_images)

        with open(image_path, 'rb') as f:
            files = {'jpg_file': (image_path.name, f, 'image/jpeg')}

            with self.client.post(
                "/api/v1/analyze/metadata-only",
                files=files,
                catch_response=True,
                timeout=30,
                name="/api/v1/analyze/metadata-only [Quick Check]"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Metadata check failed: {response.status_code}")

    @task(1)
    def health_check(self):
        """
        Check service health
        Weight: 1
        """
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    response.success()
                else:
                    response.failure(f"Service unhealthy: {data}")
            else:
                response.failure(f"Health check failed: {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates an admin user monitoring the system
    Lower frequency, monitoring-focused tasks
    """

    wait_time = between(5, 15)

    @task
    def check_system_status(self):
        """Admin checking system status"""
        self.client.get("/", name="/ [System Info]")

    @task
    def view_api_docs(self):
        """Admin viewing API documentation"""
        self.client.get("/docs", name="/docs [API Docs]")


# Custom event handlers for detailed reporting

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration at start"""
    print("\n" + "=" * 60)
    print("A.V.A.R. Performance Test Starting")
    print("=" * 60)
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary at test end"""
    stats = environment.stats

    print("\n" + "=" * 60)
    print("Performance Test Summary")
    print("=" * 60)
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")
    print("=" * 60 + "\n")

    # Performance benchmarks
    if stats.total.avg_response_time > 10000:  # 10 seconds
        print("⚠️  WARNING: Average response time exceeds 10 seconds")

    if stats.total.fail_ratio > 0.05:  # 5% failure rate
        print("⚠️  WARNING: Failure rate exceeds 5%")

    if stats.total.total_rps < 1:
        print("⚠️  WARNING: Low throughput (< 1 RPS)")


# Performance test scenarios

class StressTestUser(HttpUser):
    """
    Stress test: Rapid-fire requests to find breaking point
    """

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def rapid_metadata_checks(self):
        """Rapid metadata-only checks"""
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        test_img = FIXTURES_DIR / "stress_test.jpg"

        if not test_img.exists():
            from PIL import Image
            import numpy as np
            img = Image.fromarray(np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8))
            img.save(test_img, "JPEG")

        with open(test_img, 'rb') as f:
            files = {'jpg_file': ('stress.jpg', f, 'image/jpeg')}
            self.client.post("/api/v1/analyze/metadata-only", files=files, timeout=30)


class SpikeTestUser(HttpUser):
    """
    Spike test: Sudden burst of activity
    """

    wait_time = between(0, 1)

    @task
    def burst_analysis(self):
        """Burst of analysis requests"""
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        test_img = FIXTURES_DIR / "spike_test.jpg"

        if not test_img.exists():
            from PIL import Image
            import numpy as np
            img = Image.fromarray(np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8))
            img.save(test_img, "JPEG")

        with open(test_img, 'rb') as f:
            files = {'jpg_file': ('spike.jpg', f, 'image/jpeg')}
            self.client.post("/api/v1/analyze", files=files, timeout=120)
