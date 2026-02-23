# A.V.A.R. V2.0 Production Deployment Guide

Complete guide for deploying A.V.A.R. V2.0 with Camera Reputation, Judge Consensus, and Credential Sharing Detection features.

**Version**: 2.0.0  
**Last Updated**: 2026-02-24  
**Target**: Production Environment

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Database Migration](#database-migration)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Health Checks](#health-checks)
8. [Post-Deployment Testing](#post-deployment-testing)
9. [Rollback Procedure](#rollback-procedure)
10. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **CPU**: 4+ cores (8+ recommended for PRNU processing)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 50GB+ (100GB+ for 1000+ submissions with PRNU)
- **Network**: SSL certificate for HTTPS

### Software Requirements
- **Docker**: 24.0.0+
- **Docker Compose**: 2.20.0+
- **PostgreSQL**: 15+ (or via Docker)
- **Redis**: 7+ (or via Docker)
- **Nginx**: 1.18+ (reverse proxy)

### Dependencies (For Non-Docker Deployment)
```bash
# Python 3.12+
python3 --version

# Required packages
pip install \
  fastapi==0.104.0 \
  sqlalchemy[asyncio]==2.0.0 \
  alembic==1.12.0 \
  opencv-python==4.8.0 \
  numpy==1.24.0 \
  PyWavelets==1.4.1 \
  scipy==1.11.0 \
  uvicorn[standard]==0.24.0

# Node.js 20+ (for frontend)
node --version
pnpm --version
```

---

## Pre-Deployment Checklist

### Code Review
- [ ] Review all code on `feature/v2-innovations` branch
- [ ] Run code quality checks: `black`, `isort`, `flake8`, `mypy`
- [ ] Review security scan results
- [ ] Check for secrets in code (API keys, passwords)

### Testing
- [ ] Run unit tests: `pytest tests/ -v`
- [ ] Run V2.0 tests: `pytest tests/test_models_v2.py -v`
- [ ] Run validation script: `python tests/validate_v2_setup.py`
- [ ] Run integration tests per INTEGRATION_TESTING_GUIDE.md
- [ ] Test all 17 new API endpoints manually
- [ ] Test Vue components in browser
- [ ] Performance testing with realistic data

### Documentation
- [ ] README.md updated
- [ ] CHANGELOG.md updated
- [ ] API documentation generated
- [ ] Environment variables documented

### Backups
- [ ] Backup production database
- [ ] Backup environment files
- [ ] Backup SSL certificates
- [ ] Document current version for rollback

---

## Database Migration

### Step 1: Backup Current Database

```bash
# PostgreSQL backup
pg_dump -U avar_user -h localhost avar_db > backup_pre_v2_$(date +%Y%m%d).sql

# Verify backup
ls -lh backup_pre_v2_*.sql
```

### Step 2: Review Migration Files

```bash
cd src/backend/competition-service

# Check pending migrations
alembic current
alembic history

# Review migration scripts for V2.0
cat alembic/versions/*_v2_*.py
```

### Step 3: Run Migrations

```bash
# Dry run (check SQL)
alembic upgrade head --sql

# Apply migrations
alembic upgrade head

# Verify tables created
psql -U avar_user -d avar_db -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN (
  'camera_fingerprints',
  'camera_profiles',
  'judge_scoring_profiles',
  'judge_consensus_analyses',
  'credential_sharing_detections'
);"
```

Expected output:
```
          table_name          
------------------------------
 camera_fingerprints
 camera_profiles
 judge_scoring_profiles
 judge_consensus_analyses
 credential_sharing_detections
(5 rows)
```

### Step 4: Verify Indexes

```bash
psql -U avar_user -d avar_db -c "
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename LIKE '%camera%' OR tablename LIKE '%judge%' OR tablename LIKE '%credential%'
ORDER BY tablename;"
```

---

## Backend Deployment

### Option A: Docker Deployment (Recommended)

#### Step 1: Build Images

```bash
cd src/backend/competition-service

# Build backend image
docker build -t avar-backend:2.0.0 .

# Tag for registry (if using)
docker tag avar-backend:2.0.0 registry.example.com/avar-backend:2.0.0

# Push to registry
docker push registry.example.com/avar-backend:2.0.0
```

#### Step 2: Update Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  competition-service:
    image: avar-backend:2.0.0
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads
    ports:
      - "8080:8080"
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8080
      "

  postgres:
    image: postgres:15
    restart: always
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    restart: always
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

#### Step 3: Deploy

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Stop old containers
docker-compose -f docker-compose.prod.yml down

# Start new containers
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f competition-service
```

### Option B: Manual Deployment

```bash
cd src/backend/competition-service

# Install dependencies
pip install -r requirements.txt
pip install opencv-python numpy PyWavelets scipy

# Run migrations
alembic upgrade head

# Start service with gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080 \
  --timeout 120 \
  --log-level info
```

### Step 4: Verify Backend

```bash
# Health check
curl http://localhost:8080/health

# Check V2.0 endpoints
curl http://localhost:8080/docs

# Test validation script
cd src/backend/competition-service
python tests/validate_v2_setup.py
```

---

## Frontend Deployment

### Step 1: Build Frontend

```bash
cd src/frontend

# Install dependencies
pnpm install

# Build for production
VITE_API_URL=https://avar.studio/api/v1 pnpm build

# Verify build
ls -lh dist/
```

### Step 2: Deploy to Web Server

#### Option A: Docker

```bash
# Build frontend image
docker build -t avar-frontend:2.0.0 .

# Run container
docker run -d \
  --name avar-frontend \
  -p 3000:80 \
  avar-frontend:2.0.0
```

#### Option B: Nginx Static Hosting

```bash
# Copy build to nginx directory
sudo cp -r dist/* /var/www/avar.studio/

# Verify ownership
sudo chown -R www-data:www-data /var/www/avar.studio/
```

### Step 3: Update Nginx Configuration

```nginx
# /etc/nginx/sites-available/avar.studio
server {
    listen 443 ssl http2;
    server_name avar.studio;

    ssl_certificate /etc/letsencrypt/live/avar.studio/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/avar.studio/privkey.pem;

    root /var/www/avar.studio;
    index index.html;

    # Frontend (Vue SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # AI Detection Service
    location /detect/ {
        proxy_pass http://localhost:8001;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

```bash
# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## Environment Configuration

### Backend Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://avar_user:password@localhost:5432/avar_db

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (optional)
HIVE_AI_API_KEY=your-hive-api-key
OPTIC_API_KEY=your-optic-api-key

# CORS
CORS_ORIGINS=["https://avar.studio"]

# File Upload
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=/app/uploads
```

### Frontend Environment Variables

```env
# .env.production
VITE_API_URL=https://avar.studio/api/v1
VITE_APP_NAME=A.V.A.R.
VITE_APP_VERSION=2.0.0
```

---

## Health Checks

### Backend Health Check Endpoints

```bash
# Basic health
curl https://avar.studio/api/v1/health

# Database check
curl https://avar.studio/api/v1/health/db

# Redis check
curl https://avar.studio/api/v1/health/redis
```

### V2.0 Specific Checks

```bash
# Check if V2.0 routes registered
curl https://avar.studio/api/v1/docs | grep -i "camera"
curl https://avar.studio/api/v1/docs | grep -i "judge"

# Test validation script
docker exec avar-backend python tests/validate_v2_setup.py
```

Expected output:
```
✅ PASS   Dependencies
✅ PASS   Service Files
✅ PASS   Route Files
✅ PASS   Model Files
✅ PASS   Service Imports
✅ PASS   Documentation
✅ PASS   Test Files
```

---

## Post-Deployment Testing

### 1. Smoke Tests

```bash
# Test authentication
curl -X POST https://avar.studio/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@avar.com","password":"Admin@123!"}'

# Save token
TOKEN="eyJ..."

# Test V2.0 endpoints
curl https://avar.studio/api/v1/cameras/statistics \
  -H "Authorization: Bearer $TOKEN"

curl https://avar.studio/api/v1/judges-analytics/competition/1/bias-report \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Integration Tests

Follow the complete guide: `src/backend/competition-service/docs/INTEGRATION_TESTING_GUIDE.md`

```bash
# Run integration test suite
cd src/backend/competition-service
pytest tests/integration/ -v --env=production
```

### 3. Frontend Tests

```bash
# Open browser to https://avar.studio
# Login as admin
# Navigate to each page:
- My Submissions (check camera reputation badges)
- Judge Dashboard (check consensus indicators)
- Admin Panel > Bias Report (check dashboard)
- Admin Panel > Security (check credential alerts)
```

### 4. Performance Tests

```bash
# PRNU extraction time
time curl -X POST https://avar.studio/api/v1/cameras/fingerprints/123 \
  -H "Authorization: Bearer $TOKEN"

# Expected: 2-4 seconds

# Consensus analysis time
time curl https://avar.studio/api/v1/judges-analytics/consensus/456 \
  -H "Authorization: Bearer $TOKEN"

# Expected: 100-300ms
```

---

## Rollback Procedure

### If V2.0 Deployment Fails

#### Step 1: Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

#### Step 2: Restore Database

```bash
# Drop V2.0 tables (if needed)
psql -U avar_user -d avar_db -c "
DROP TABLE IF EXISTS credential_sharing_detections CASCADE;
DROP TABLE IF EXISTS judge_consensus_analyses CASCADE;
DROP TABLE IF EXISTS judge_scoring_profiles CASCADE;
DROP TABLE IF EXISTS camera_profiles CASCADE;
DROP TABLE IF EXISTS camera_fingerprints CASCADE;
"

# Restore from backup
psql -U avar_user -d avar_db < backup_pre_v2_20260224.sql
```

#### Step 3: Deploy Previous Version

```bash
# Checkout previous version
git checkout v1.4.0

# Build and deploy
docker-compose -f docker-compose.prod.yml up -d
```

#### Step 4: Verify Rollback

```bash
# Check version
curl https://avar.studio/api/v1/version

# Check services
docker-compose -f docker-compose.prod.yml ps
```

---

## Monitoring & Maintenance

### Metrics to Monitor

1. **PRNU Extraction**
   - Processing time (target: 2-4s)
   - Memory usage (target: <50MB per extraction)
   - Success rate (target: >95%)

2. **Database**
   - Query performance (<50ms for indexed queries)
   - Storage growth (~256KB per fingerprint)
   - Connection pool usage

3. **API Performance**
   - Response times for V2.0 endpoints
   - Error rates
   - Request counts

### Log Monitoring

```bash
# Backend logs
docker logs -f --tail=100 avar-backend

# Filter for V2.0 operations
docker logs avar-backend | grep -E "PRNU|consensus|credential"

# Check for errors
docker logs avar-backend | grep ERROR
```

### Database Maintenance

```bash
# Check table sizes
psql -U avar_user -d avar_db -c "
SELECT 
  schemaname, 
  tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Vacuum analyze
psql -U avar_user -d avar_db -c "VACUUM ANALYZE;"

# Reindex if needed
psql -U avar_user -d avar_db -c "REINDEX DATABASE avar_db;"
```

### Performance Optimization

```bash
# Monitor PRNU extraction
SELECT COUNT(*), AVG(prnu_energy), verified 
FROM camera_fingerprints 
GROUP BY verified;

# Monitor consensus analysis
SELECT consensus_verdict, COUNT(*) 
FROM judge_consensus_analyses 
GROUP BY consensus_verdict;

# Monitor credential sharing alerts
SELECT risk_level, COUNT(*) 
FROM credential_sharing_detections 
WHERE alert_triggered = true 
GROUP BY risk_level;
```

---

## Troubleshooting

### Issue 1: PRNU Extraction Failing

**Symptoms**: 500 errors on `/cameras/fingerprints/{id}`

**Solutions**:
```bash
# Check opencv installation
docker exec avar-backend python -c "import cv2; print(cv2.__version__)"

# Check PyWavelets
docker exec avar-backend python -c "import pywt; print(pywt.__version__)"

# Check scipy
docker exec avar-backend python -c "import scipy; print(scipy.__version__)"

# Check memory
docker stats avar-backend
```

### Issue 2: Consensus Analysis Not Triggering

**Symptoms**: Submissions not flagged, no consensus data

**Solutions**:
```bash
# Check judge count
psql -U avar_user -d avar_db -c "
SELECT submission_id, COUNT(*) 
FROM scores 
WHERE submission_id = 123 
GROUP BY submission_id;"

# Manually trigger analysis
curl -X POST https://avar.studio/api/v1/judges-analytics/consensus/{submission_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Issue 3: High Memory Usage

**Symptoms**: Server running out of memory

**Solutions**:
```bash
# Check PRNU cache (should be cleared)
docker exec avar-backend python -c "
from app.stores.v2Analytics import useV2AnalyticsStore
store = useV2AnalyticsStore()
store.clearAllCache()
"

# Restart service
docker-compose -f docker-compose.prod.yml restart competition-service
```

---

## Security Checklist

- [ ] SSL/TLS enabled (HTTPS only)
- [ ] Firewall configured (UFW/iptables)
- [ ] Database passwords strong and unique
- [ ] JWT secret key rotated
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] File upload validation enabled
- [ ] Fail2ban configured for SSH
- [ ] Regular security updates applied
- [ ] Backup encryption enabled

---

## Support

**Documentation**: See `src/backend/competition-service/docs/` for:
- V2_FEATURES.md
- CODE_REVIEW_CHECKLIST.md
- INTEGRATION_TESTING_GUIDE.md

**Issues**: https://github.com/rasandilikshana/AI-Photo-Detection-Innovation/issues

**Contact**: rasandilikshana@gmail.com

---

**Deployment Guide Version**: 2.0.0  
**Last Updated**: 2026-02-24  
**Tested On**: Ubuntu 22.04 LTS, Docker 24.0.7
