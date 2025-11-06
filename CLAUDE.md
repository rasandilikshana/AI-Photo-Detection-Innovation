# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**A.V.A.R. (Aura Verification and Authentication for RAW files)** is an AI-powered authenticity verification system designed to safeguard photography competition integrity against AI-generated synthetic imagery. The system employs forensic detection techniques to ensure only genuine photographs reach the judging stage.

### Core Innovation

The system's primary innovation is **RAW-to-JPG Linkage Analysis** combined with multi-layered forensic detection:

1. **Layer 1: Metadata Analysis** - EXIF forensics to detect AI tool signatures
2. **RAW-JPG Linkage** - Proves submitted JPG is derived from submitted RAW file
3. **Layer 2: Digital Fingerprint** - PRNU, ELA, and FFT analysis
4. **Layer 3: Third-Party API** - Professional AI detection services

### Key Technical Innovation

**PRNU (Photo Response Non-Uniformity)**: AI-generated images lack genuine camera sensor noise patterns. The system extracts sensor "fingerprints" using wavelet-based denoising and compares RAW vs JPG patterns to detect submission forgery where a genuine RAW is paired with an unrelated AI-generated JPG.

## Architecture

### Microservices Architecture

```
├── AI Detection Service (Python/FastAPI) - Port 8001
│   ├── Layer 1: Metadata Analysis (EXIF, exiftool)
│   ├── RAW-JPG Linkage (PRNU, pHash, SSIM)
│   ├── Layer 2: Digital Fingerprint (PRNU, ELA, FFT)
│   └── Layer 3: Third-Party API (Hive AI, Optic)
│
├── API Gateway (Python/FastAPI) - Port 8000
│   └── Request routing & load balancing
│
├── Competition Management Service (PHP/Laravel) - Port 8080
│   ├── User authentication
│   ├── Competition workflow
│   ├── Submission management
│   └── Judging dashboard
│
└── Frontend Application (Vue.js) - Port 3000
    ├── Submission portal
    ├── Judging interface
    └── Admin panel
```

### Database & Infrastructure

- **PostgreSQL 15+**: Primary database for users, submissions, competitions
- **Redis 7+**: Caching and message queue
- **Docker Compose**: Container orchestration

## Common Commands

### Development Setup

```bash
# Clone and setup environment
git clone <repository-url>
cd "Rasan Research 3"

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and database credentials

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ai-detection-service
docker-compose logs -f competition-service
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose up -d --build ai-detection-service
```

### AI Detection Service (Python)

```bash
# Navigate to service
cd src/backend/ai-detection-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run service locally (for development)
uvicorn app.main:app --reload --port 8001

# Run tests
pytest tests/ -v
pytest tests/test_layer1_metadata.py -v  # Single test file
pytest tests/ --cov=app --cov-report=html  # With coverage

# Run specific test
pytest tests/test_layer2_fingerprint.py::test_prnu_extraction -v
```

### Competition Service (PHP/Laravel)

```bash
# Navigate to service
cd src/backend/competition-service

# Install dependencies (if running locally)
composer install

# Run migrations
php artisan migrate

# Seed database
php artisan db:seed

# Run tests
php artisan test
php artisan test --filter=SubmissionTest  # Single test

# Clear cache
php artisan cache:clear
php artisan config:clear
php artisan route:clear
```

### Frontend (Vue.js)

```bash
# Navigate to frontend
cd src/frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
npm run test:unit  # Unit tests only

# Lint code
npm run lint
npm run lint:fix  # Auto-fix issues
```

### Docker Operations

```bash
# Build all services
docker-compose build

# Start specific service
docker-compose up -d postgres redis
docker-compose up -d ai-detection-service

# Execute command in container
docker-compose exec ai-detection-service python -m pytest
docker-compose exec postgres psql -U avar_user -d avar_db

# View resource usage
docker stats

# Clean up volumes (WARNING: Deletes data)
docker-compose down -v
```

## Key Technical Details

### AI Detection Pipeline Flow

1. **Request arrives** at API Gateway (port 8000)
2. **Routed** to AI Detection Service (port 8001)
3. **Layer 1**: Metadata extracted using PIL and exiftool
   - AI signatures flagged → REJECT
   - Inconsistent/hollow metadata → SUSPICIOUS
4. **RAW-JPG Linkage** (if RAW provided):
   - pHash distance > threshold → REJECT
   - SSIM score < threshold → REJECT
   - Histogram correlation < threshold → REJECT
5. **Layer 2**: Digital Fingerprint Analysis
   - PRNU extraction via wavelet denoising (PyWavelets)
   - Null PRNU pattern → REJECT (AI-generated)
   - ELA shows uniform compression → SUSPICIOUS
   - FFT shows low high-frequency content → SUSPICIOUS
6. **Layer 3**: Third-Party API (only if QUARANTINE)
   - Hive AI score > 0.7 → REJECT
   - Score 0.4-0.7 → QUARANTINE (manual review)
   - Score < 0.4 → AUTHENTIC
7. **Final Verdict**: AUTHENTIC, REJECT, or QUARANTINE

### Critical Implementation Details

#### PRNU Extraction (Layer 2)

Located in: [src/backend/ai-detection-service/app/services/layer2_fingerprint.py](src/backend/ai-detection-service/app/services/layer2_fingerprint.py)

```python
# Uses Discrete Wavelet Transform (DWT) with db8 wavelet
coeffs = pywt.dwt2(image, 'db8')
# Soft thresholding denoising
# PRNU = original - denoised
# Variance < 0.02 → AI-generated (no sensor noise)
```

#### RAW-JPG Linkage

Located in: [src/backend/ai-detection-service/app/services/raw_jpg_linkage.py](src/backend/ai-detection-service/app/services/raw_jpg_linkage.py)

- Demosaics RAW using `rawpy` library
- Compares via three methods (all must agree):
  1. Perceptual hash (pHash) - Hamming distance ≤ 10
  2. SSIM (Structural Similarity) ≥ 0.85
  3. Color histogram correlation ≥ 0.90

#### Supported RAW Formats

Canon (.cr2, .cr3), Nikon (.nef), Sony (.arw), Olympus (.orf), Panasonic (.rw2), DNG (.dng), Fujifilm (.raf), Pentax (.pef), Leica (.rwl), Hasselblad (.3fr)

### Environment Variables

Required in `.env`:

```bash
# Database
DB_PASSWORD=secure_password

# AI Detection APIs (Layer 3)
HIVE_AI_API_KEY=your_hive_api_key      # Required for Layer 3
OPTIC_API_KEY=your_optic_api_key       # Optional fallback

# Application
APP_ENV=development
APP_DEBUG=true

# Security
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key

# File Upload Limits
MAX_FILE_SIZE=100M
MAX_RAW_SIZE=200M
```

### File Structure

```
src/backend/ai-detection-service/
├── app/
│   ├── main.py                      # FastAPI application entry
│   ├── services/
│   │   ├── layer1_metadata.py       # EXIF analysis
│   │   ├── raw_jpg_linkage.py       # RAW-JPG correlation
│   │   ├── layer2_fingerprint.py    # PRNU, ELA, FFT
│   │   └── layer3_api.py            # Third-party APIs
│   └── utils/
│       ├── logger.py                # Logging configuration
│       └── file_handler.py          # File upload/cleanup
├── tests/                           # Pytest test suite
├── requirements.txt                 # Python dependencies
└── Dockerfile                       # Container definition
```

## Development Workflow

### Adding New Detection Method

1. Create new analyzer in `app/services/`
2. Implement `async def analyze(image_path: str) -> Dict` method
3. Return structure: `{"verdict": str, "confidence": float, "flags": List[str]}`
4. Integrate into `app/main.py` analysis pipeline
5. Add tests in `tests/test_new_analyzer.py`
6. Update this documentation

### Testing Analysis Locally

```bash
# Use curl or httpie to test endpoint
curl -X POST http://localhost:8001/api/v1/analyze \
  -F "jpg_file=@test_image.jpg" \
  -F "raw_file=@test_image.cr3"

# Or use Python requests
python -c "
import requests
files = {
    'jpg_file': open('test.jpg', 'rb'),
    'raw_file': open('test.cr3', 'rb')
}
response = requests.post('http://localhost:8001/api/v1/analyze', files=files)
print(response.json())
"
```

### Debugging Tips

1. **Check service logs**: `docker-compose logs -f ai-detection-service`
2. **Inspect uploaded files**: Files stored temporarily in `uploads/<submission_id>/`
3. **Test individual layers**: Use `/api/v1/analyze/metadata-only` endpoint
4. **Database inspection**: `docker-compose exec postgres psql -U avar_user -d avar_db`
5. **Redis inspection**: `docker-compose exec redis redis-cli`

### Performance Considerations

- **Layer 1**: ~50-200ms (fast, always runs)
- **RAW-JPG Linkage**: ~500-2000ms (medium, if RAW provided)
- **Layer 2 PRNU**: ~2-5 seconds (slow, computationally intensive)
- **Layer 3 API**: ~1-10 seconds (depends on external API)

**Optimization**: Early rejection in Layer 1 avoids expensive Layer 2/3 analysis.

## Research Context

This is a dissertation project for:

**Title**: "Aura: Developing an AI-Powered Authenticity Verification System to Safeguard Photography Competition Integrity Against Synthetic Media"

**Research Objectives**:
- Detect AI-generated images (Midjourney, DALL-E, Stable Diffusion)
- Protect photography competition integrity
- Streamline competition workflow
- Validate detection accuracy across AI models

**Key Innovation**: First comprehensive RAW-to-JPG linkage verification system specifically designed for photography competitions, preventing attackers from submitting genuine RAW files paired with unrelated AI-generated JPG files.

## API Documentation

Once services are running:

- **AI Detection API Docs**: http://localhost:8001/docs
- **API Gateway Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Admin Panel**: http://localhost:8080

## Author

Rasan Dilikshana
Email: rasandilikshana@gmail.com
GitHub: rasandilikshana

## License

Academic Research Project - All Rights Reserved
