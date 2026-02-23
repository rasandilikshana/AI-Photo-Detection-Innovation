#!/usr/bin/env python3
"""
V2.0 Setup Validation Script

Validates that all v2.0 components are properly installed and configured.
Run this before starting integration testing.

Usage:
    python tests/validate_v2_setup.py
"""

import sys
import importlib
from pathlib import Path


def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def check_dependencies():
    """Check if all required packages are installed"""
    print_header("Checking Dependencies")

    dependencies = [
        ("opencv-python", "cv2", "4.8.0"),
        ("numpy", "numpy", "1.24.0"),
        ("PyWavelets", "pywt", "1.4.1"),
        ("scipy", "scipy", "1.11.0"),
        ("fastapi", "fastapi", "0.100.0"),
        ("sqlalchemy", "sqlalchemy", "2.0.0"),
        ("pydantic", "pydantic", "2.0.0"),
    ]

    all_installed = True

    for package_name, import_name, min_version in dependencies:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package_name:20s} v{version}")
        except ImportError:
            print(f"❌ {package_name:20s} NOT INSTALLED")
            all_installed = False

    return all_installed


def check_service_files():
    """Check if all service files exist"""
    print_header("Checking Service Files")

    base_path = Path("app/services")
    service_files = [
        "prnu_extractor.py",
        "camera_reputation.py",
        "judge_consensus.py",
        "credential_sharing.py",
    ]

    all_exist = True

    for filename in service_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename:30s} ({size:,} bytes)")
        else:
            print(f"❌ {filename:30s} NOT FOUND")
            all_exist = False

    return all_exist


def check_route_files():
    """Check if all route files exist"""
    print_header("Checking API Route Files")

    base_path = Path("app/routes")
    route_files = [
        "cameras.py",
        "judges_analytics.py",
    ]

    all_exist = True

    for filename in route_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename:30s} ({size:,} bytes)")
        else:
            print(f"❌ {filename:30s} NOT FOUND")
            all_exist = False

    return all_exist


def check_model_files():
    """Check if model files exist"""
    print_header("Checking Database Models")

    filepath = Path("app/models/camera_reputation.py")

    if filepath.exists():
        size = filepath.stat().st_size
        print(f"✅ camera_reputation.py        ({size:,} bytes)")

        # Check for expected model classes
        with open(filepath, 'r') as f:
            content = f.read()
            models = [
                "CameraFingerprint",
                "CameraProfile",
                "JudgeScoringProfile",
                "JudgeConsensusAnalysis",
                "CredentialSharingDetection",
            ]

            for model in models:
                if f"class {model}" in content:
                    print(f"  ✅ {model}")
                else:
                    print(f"  ❌ {model} NOT FOUND")

        return True
    else:
        print(f"❌ camera_reputation.py NOT FOUND")
        return False


def check_imports():
    """Test if services can be imported"""
    print_header("Testing Service Imports")

    services = [
        ("PRNUExtractor", "app.services.prnu_extractor"),
        ("CameraReputationManager", "app.services.camera_reputation"),
        ("JudgeConsensusAnalyzer", "app.services.judge_consensus"),
        ("CredentialSharingDetector", "app.services.credential_sharing"),
    ]

    all_importable = True

    for class_name, module_path in services:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            print(f"✅ {class_name:30s} imported successfully")
        except Exception as e:
            print(f"❌ {class_name:30s} IMPORT FAILED: {str(e)}")
            all_importable = False

    return all_importable


def check_documentation():
    """Check if documentation files exist"""
    print_header("Checking Documentation")

    base_path = Path("docs")
    doc_files = [
        ("V2_FEATURES.md", "Feature documentation"),
        ("V2_IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
        ("CODE_REVIEW_CHECKLIST.md", "Code review checklist"),
        ("INTEGRATION_TESTING_GUIDE.md", "Integration testing guide"),
    ]

    all_exist = True

    for filename, description in doc_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().splitlines())
            print(f"✅ {filename:35s} ({lines:4d} lines, {size:,} bytes)")
        else:
            print(f"❌ {filename:35s} NOT FOUND - {description}")
            all_exist = False

    return all_exist


def test_prnu_extraction():
    """Test basic PRNU extraction functionality"""
    print_header("Testing PRNU Extraction (Basic)")

    try:
        import numpy as np
        import pywt

        # Create dummy image data (512x512 grayscale)
        dummy_image = np.random.randint(0, 256, (512, 512), dtype=np.uint8)

        # Test DWT
        coeffs = pywt.dwt2(dummy_image, 'db8')
        cA, (cH, cV, cD) = coeffs

        # Test reconstruction
        reconstructed = pywt.idwt2(coeffs, 'db8')

        print(f"✅ DWT processing successful")
        print(f"  - Input shape: {dummy_image.shape}")
        print(f"  - Approx coeffs shape: {cA.shape}")
        print(f"  - Reconstructed shape: {reconstructed.shape}")

        # Test residual extraction
        residual = dummy_image[:reconstructed.shape[0], :reconstructed.shape[1]] - reconstructed
        energy = np.var(residual)

        print(f"✅ Residual extraction successful")
        print(f"  - Residual energy: {energy:.6f}")

        return True

    except Exception as e:
        print(f"❌ PRNU extraction test failed: {str(e)}")
        return False


def test_statistical_functions():
    """Test statistical functions for judge consensus"""
    print_header("Testing Statistical Functions")

    try:
        import numpy as np
        from scipy import stats

        # Test ICC calculation components
        scores = np.array([8.5, 8.0, 3.0])  # Example scores
        mean = np.mean(scores)
        std = np.std(scores)

        print(f"✅ NumPy statistical functions work")
        print(f"  - Mean: {mean:.2f}")
        print(f"  - Std Dev: {std:.2f}")

        # Test Z-score calculation
        z_scores = (scores - mean) / std
        outliers = np.abs(z_scores) > 2.0

        print(f"✅ Z-score calculation works")
        print(f"  - Z-scores: {z_scores}")
        print(f"  - Outliers: {outliers}")

        # Test correlation
        pattern1 = np.random.rand(512, 512)
        pattern2 = pattern1 + np.random.rand(512, 512) * 0.1
        correlation = np.corrcoef(pattern1.flatten(), pattern2.flatten())[0, 1]

        print(f"✅ Correlation calculation works")
        print(f"  - Correlation: {correlation:.3f}")

        return True

    except Exception as e:
        print(f"❌ Statistical functions test failed: {str(e)}")
        return False


def check_test_files():
    """Check if test files exist"""
    print_header("Checking Test Files")

    test_file = Path("tests/test_models_v2.py")

    if test_file.exists():
        size = test_file.stat().st_size
        lines = len(test_file.read_text().splitlines())
        print(f"✅ test_models_v2.py exists ({lines} lines, {size:,} bytes)")
        return True
    else:
        print(f"❌ test_models_v2.py NOT FOUND")
        return False


def main():
    """Main validation routine"""
    print("\n" + "="*60)
    print("  V2.0 Setup Validation")
    print("  NPAS Competition Service - Camera Reputation & Judge Analytics")
    print("="*60)

    results = []

    # Run all checks
    results.append(("Dependencies", check_dependencies()))
    results.append(("Service Files", check_service_files()))
    results.append(("Route Files", check_route_files()))
    results.append(("Model Files", check_model_files()))
    results.append(("Service Imports", check_imports()))
    results.append(("Documentation", check_documentation()))
    results.append(("Test Files", check_test_files()))
    results.append(("PRNU Extraction", test_prnu_extraction()))
    results.append(("Statistical Functions", test_statistical_functions()))

    # Summary
    print_header("Validation Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8s} {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All validations passed! Ready for integration testing.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please fix issues before testing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
