#!/bin/bash

# Competition Service Startup Script

echo "🏆 Starting A.V.A.R. Competition Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Create uploads directory
mkdir -p uploads

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and configure your settings!"
fi

# Run database migrations (if alembic is configured)
# echo "🗄️  Running database migrations..."
# alembic upgrade head

# Start the service
echo "🚀 Starting Competition Service on port 8080..."
echo "📖 API Documentation: http://localhost:8080/docs"
echo "❤️  Health Check: http://localhost:8080/health"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
