#!/usr/bin/env python3
"""
SigLIP2 AI vs Human Image Detector - Benchmark Script
Tests model performance and resource usage on current hardware

Usage:
    python benchmark_siglip2.py [--test-image /path/to/image.jpg]
"""

import os
import sys
import time
import argparse
import tempfile
import urllib.request
from pathlib import Path

def get_system_info():
    """Get system information"""
    print("\n" + "="*60)
    print("SYSTEM INFORMATION")
    print("="*60)

    # CPU info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = f.read()
            cpu_model = [line.split(':')[1].strip() for line in cpu_info.split('\n')
                        if 'model name' in line]
            if cpu_model:
                print(f"CPU: {cpu_model[0]}")
            cpu_count = len([line for line in cpu_info.split('\n') if 'processor' in line])
            print(f"CPU Cores: {cpu_count}")
    except:
        print("CPU: Unable to detect")

    # Memory info
    try:
        with open('/proc/meminfo', 'r') as f:
            mem_info = f.read()
            total = int([line.split()[1] for line in mem_info.split('\n')
                        if 'MemTotal' in line][0]) / 1024 / 1024
            available = int([line.split()[1] for line in mem_info.split('\n')
                           if 'MemAvailable' in line][0]) / 1024 / 1024
            print(f"RAM Total: {total:.2f} GB")
            print(f"RAM Available: {available:.2f} GB")
            print(f"RAM Usage: {((total - available) / total * 100):.1f}%")
    except:
        print("Memory: Unable to detect")

    # Check for GPU
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("GPU: NVIDIA GPU detected")
        else:
            print("GPU: No NVIDIA GPU (CPU inference only)")
    except:
        print("GPU: No NVIDIA GPU (CPU inference only)")

    print("="*60)


def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "="*60)
    print("DEPENDENCY CHECK")
    print("="*60)

    required = ['torch', 'transformers', 'PIL', 'accelerate']
    missing = []

    for pkg in required:
        try:
            if pkg == 'PIL':
                import PIL
                print(f"  [OK] Pillow: {PIL.__version__}")
            elif pkg == 'torch':
                import torch
                print(f"  [OK] PyTorch: {torch.__version__}")
                print(f"       CUDA available: {torch.cuda.is_available()}")
            elif pkg == 'transformers':
                import transformers
                print(f"  [OK] Transformers: {transformers.__version__}")
            elif pkg == 'accelerate':
                import accelerate
                print(f"  [OK] Accelerate: {accelerate.__version__}")
        except ImportError:
            print(f"  [MISSING] {pkg}")
            missing.append(pkg)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install transformers torch Pillow accelerate")
        return False

    print("="*60)
    return True


def benchmark_model_loading():
    """Benchmark model loading time and memory usage"""
    print("\n" + "="*60)
    print("MODEL LOADING BENCHMARK")
    print("="*60)

    import torch
    from transformers import AutoImageProcessor, SiglipForImageClassification
    import gc

    MODEL_ID = "Ateeqq/ai-vs-human-image-detector"

    # Get initial memory
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024
    except:
        mem_before = 0

    print(f"Memory before loading: {mem_before:.2f} MB")
    print(f"Loading model: {MODEL_ID}")

    # Time model loading
    start_time = time.time()

    try:
        processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        load_processor_time = time.time() - start_time
        print(f"  Processor loaded: {load_processor_time:.2f}s")

        start_model = time.time()
        model = SiglipForImageClassification.from_pretrained(MODEL_ID)
        load_model_time = time.time() - start_model
        print(f"  Model loaded: {load_model_time:.2f}s")

        total_load_time = time.time() - start_time
        print(f"  Total load time: {total_load_time:.2f}s")

        # Set to eval mode
        model.eval()

        # Check memory after loading
        try:
            mem_after = process.memory_info().rss / 1024 / 1024
            print(f"Memory after loading: {mem_after:.2f} MB")
            print(f"Model memory usage: {mem_after - mem_before:.2f} MB")
        except:
            pass

        # Count parameters
        param_count = sum(p.numel() for p in model.parameters())
        print(f"Model parameters: {param_count / 1e6:.2f}M")

        print("="*60)
        return model, processor, True

    except Exception as e:
        print(f"ERROR loading model: {e}")
        print("="*60)
        return None, None, False


def create_test_image():
    """Create or download a test image"""
    # Create a simple test image with PIL
    from PIL import Image
    import numpy as np

    # Create a simple gradient image (simulates a photo)
    width, height = 512, 512
    img_array = np.zeros((height, width, 3), dtype=np.uint8)

    # Add some patterns
    for y in range(height):
        for x in range(width):
            img_array[y, x, 0] = int(255 * x / width)  # Red gradient
            img_array[y, x, 1] = int(255 * y / height)  # Green gradient
            img_array[y, x, 2] = 128  # Blue constant

    img = Image.fromarray(img_array)

    # Save to temp file
    temp_path = tempfile.mktemp(suffix='.jpg')
    img.save(temp_path, quality=95)

    return temp_path


def benchmark_inference(model, processor, image_path=None, num_runs=5):
    """Benchmark inference speed"""
    print("\n" + "="*60)
    print("INFERENCE BENCHMARK")
    print("="*60)

    import torch
    from PIL import Image

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    model.to(device)

    # Load or create test image
    if image_path and os.path.exists(image_path):
        print(f"Using test image: {image_path}")
        image = Image.open(image_path).convert("RGB")
    else:
        print("Creating synthetic test image...")
        temp_path = create_test_image()
        image = Image.open(temp_path).convert("RGB")
        print(f"Test image size: {image.size}")

    print(f"Running {num_runs} inference passes...")

    # Preprocessing benchmark
    start_prep = time.time()
    inputs = processor(images=image, return_tensors="pt").to(device)
    prep_time = time.time() - start_prep
    print(f"Preprocessing time: {prep_time*1000:.2f}ms")

    # Warmup run
    with torch.no_grad():
        _ = model(**inputs)

    # Timed runs
    inference_times = []
    for i in range(num_runs):
        start = time.time()
        with torch.no_grad():
            outputs = model(**inputs)
        elapsed = time.time() - start
        inference_times.append(elapsed)

        # Get prediction
        logits = outputs.logits
        predicted_class_idx = logits.argmax(-1).item()
        probabilities = torch.softmax(logits, dim=-1)
        confidence = probabilities[0, predicted_class_idx].item()

    avg_time = sum(inference_times) / len(inference_times)
    min_time = min(inference_times)
    max_time = max(inference_times)

    print(f"\nInference Results:")
    print(f"  Average: {avg_time*1000:.2f}ms")
    print(f"  Min: {min_time*1000:.2f}ms")
    print(f"  Max: {max_time*1000:.2f}ms")
    print(f"  Throughput: {1/avg_time:.2f} images/second")

    # Show prediction
    predicted_label = model.config.id2label[predicted_class_idx]
    print(f"\nTest Prediction:")
    print(f"  Label: {predicted_label}")
    print(f"  Confidence: {confidence*100:.2f}%")

    for i, label in model.config.id2label.items():
        prob = probabilities[0, i].item()
        print(f"    {label}: {prob*100:.2f}%")

    print("="*60)

    return {
        "avg_inference_ms": avg_time * 1000,
        "min_inference_ms": min_time * 1000,
        "max_inference_ms": max_time * 1000,
        "throughput_ips": 1 / avg_time,
        "preprocessing_ms": prep_time * 1000,
    }


def run_memory_stress_test(model, processor):
    """Test memory under load"""
    print("\n" + "="*60)
    print("MEMORY STRESS TEST")
    print("="*60)

    import torch
    from PIL import Image
    import gc

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    try:
        import psutil
        process = psutil.Process(os.getpid())
        has_psutil = True
    except:
        has_psutil = False

    # Create test images of different sizes
    test_sizes = [(256, 256), (512, 512), (1024, 1024), (2048, 2048)]

    for size in test_sizes:
        # Create test image
        img_array = (torch.rand(size[1], size[0], 3) * 255).numpy().astype('uint8')
        image = Image.fromarray(img_array)

        if has_psutil:
            mem_before = process.memory_info().rss / 1024 / 1024

        try:
            start = time.time()
            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            elapsed = time.time() - start

            if has_psutil:
                mem_after = process.memory_info().rss / 1024 / 1024
                print(f"  {size[0]}x{size[1]}: {elapsed*1000:.0f}ms, Memory: {mem_after:.0f}MB (+{mem_after-mem_before:.0f}MB)")
            else:
                print(f"  {size[0]}x{size[1]}: {elapsed*1000:.0f}ms")

        except Exception as e:
            print(f"  {size[0]}x{size[1]}: FAILED - {e}")

        gc.collect()

    print("="*60)


def generate_report(system_info, load_success, inference_results):
    """Generate final benchmark report"""
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)

    if not load_success:
        print("MODEL LOADING: FAILED")
        print("\nRecommendation: Use Hugging Face Inference API instead")
        print("="*60)
        return

    print("MODEL LOADING: SUCCESS")

    if inference_results:
        avg_ms = inference_results['avg_inference_ms']
        throughput = inference_results['throughput_ips']

        print(f"\nPerformance:")
        print(f"  Average inference: {avg_ms:.0f}ms")
        print(f"  Throughput: {throughput:.2f} images/sec")
        print(f"  Preprocessing: {inference_results['preprocessing_ms']:.0f}ms")

        print(f"\nFeasibility Assessment:")
        if avg_ms < 1000:
            print("  [EXCELLENT] Sub-second inference - great for production")
        elif avg_ms < 3000:
            print("  [GOOD] 1-3 second inference - acceptable for background processing")
        elif avg_ms < 10000:
            print("  [ACCEPTABLE] 3-10 second inference - works for async processing")
        else:
            print("  [SLOW] >10 second inference - consider Hugging Face API")

        print(f"\nRecommendation for A.V.A.R. Integration:")
        if avg_ms < 5000:
            print("  - Local inference is VIABLE for this server")
            print("  - Add as Layer 3 in AI Detection Service")
            print("  - Load model once at service startup")
            print("  - Process submissions in background task")
        else:
            print("  - Local inference is SLOW - consider alternatives:")
            print("    1. Hugging Face Inference API (recommended)")
            print("    2. Upgrade server (more RAM/CPU)")
            print("    3. Use model quantization (INT8)")

    print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Benchmark SigLIP2 AI Detector')
    parser.add_argument('--test-image', type=str, help='Path to test image')
    parser.add_argument('--num-runs', type=int, default=5, help='Number of inference runs')
    parser.add_argument('--skip-stress', action='store_true', help='Skip memory stress test')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("SigLIP2 AI vs Human Image Detector - Benchmark")
    print("Model: Ateeqq/ai-vs-human-image-detector")
    print("="*60)

    # System info
    get_system_info()

    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and run again.")
        sys.exit(1)

    # Benchmark model loading
    model, processor, load_success = benchmark_model_loading()

    inference_results = None
    if load_success:
        # Benchmark inference
        inference_results = benchmark_inference(
            model, processor,
            args.test_image,
            args.num_runs
        )

        # Memory stress test
        if not args.skip_stress:
            run_memory_stress_test(model, processor)

    # Generate report
    generate_report(None, load_success, inference_results)


if __name__ == "__main__":
    main()
