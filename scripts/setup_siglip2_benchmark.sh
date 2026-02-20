#!/bin/bash
# Setup script for SigLIP2 benchmark on production server
# Run this BEFORE running the benchmark

echo "=========================================="
echo "SigLIP2 Benchmark Setup"
echo "=========================================="

# Check current memory
echo ""
echo "Current System Status:"
free -h
echo ""

# Check if we're in a virtual environment or need to create one
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creating virtual environment for benchmark..."
    python3 -m venv /tmp/siglip2_benchmark_env
    source /tmp/siglip2_benchmark_env/bin/activate
    echo "Virtual environment activated"
else
    echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip

# Install PyTorch CPU version (smaller, no CUDA needed)
echo "Installing PyTorch (CPU version)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
echo "Installing transformers and dependencies..."
pip install transformers accelerate Pillow psutil

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To run benchmark:"
echo "  source /tmp/siglip2_benchmark_env/bin/activate"
echo "  python benchmark_siglip2.py"
echo ""
echo "Or test with a real image:"
echo "  python benchmark_siglip2.py --test-image /path/to/image.jpg"
