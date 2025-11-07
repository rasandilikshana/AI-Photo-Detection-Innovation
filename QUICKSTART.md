# A.V.A.R. Quick Start Guide

## TL;DR - Get Everything Running in 5 Minutes

### Option 1: Docker (Recommended)

```bash
# 1. Clone and navigate to project
cd "NPAS - Third Year/Rasan Research 3"

# 2. Set environment variables (optional, has defaults)
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy (~30 seconds)
docker-compose ps

# 5. Access the application
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# Competition Service API: http://localhost:8080
# AI Detection Service: http://localhost:8001
```

### Option 2: Local Development

```bash
# 1. Start backend services with Docker
docker-compose up -d postgres redis ai-detection-service competition-service api-gateway

# 2. Start frontend locally
cd src/frontend
pnpm install
pnpm dev

# 3. Access the application
# Frontend: http://localhost:5173
# Backend services: Same as above
```

## Service Overview

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Frontend (Production) | 3000 | http://localhost:3000 | Vue.js web app (Nginx) |
| Frontend (Development) | 5173 | http://localhost:5173 | Vue.js dev server (Hot reload) |
| API Gateway | 8000 | http://localhost:8000 | Central routing & load balancing |
| Competition Service | 8080 | http://localhost:8080 | Core business logic API |
| AI Detection Service | 8001 | http://localhost:8001 | Photo verification API |
| PostgreSQL | 5432 | localhost:5432 | Database |
| Redis | 6380 | localhost:6380 | Cache & message queue |

## First Time Setup

### 1. Register a New User

1. Go to http://localhost:3000
2. Click "Sign Up" or "Get Started"
3. Fill in the registration form:
   - Email: test@example.com
   - Username: testuser
   - Password: password123
   - Full Name: Test User (optional)
   - Country: USA (optional)
4. Click "Create Account"
5. You'll be automatically logged in

### 2. Browse Competitions

1. Click "Browse Competitions" from home page
2. Or navigate to http://localhost:3000/competitions
3. View all active competitions with:
   - Status badges (Open, Closed, Judging, etc.)
   - Submission deadlines
   - Prize information
   - Requirements (RAW files, etc.)

### 3. View Competition Details

1. Click on any competition card
2. View detailed information:
   - Full description
   - Rules and guidelines
   - Submission requirements
   - Important dates
   - Prize details
3. Click "Submit Entry" to participate

### 4. Submit a Photo

1. From competition detail page, click "Submit Entry"
2. Or go to My Submissions and click competition name
3. Fill in the submission form:
   - **Title:** "My Amazing Landscape"
   - **Description:** Optional description of your photo
   - **JPG File:** Select your photo (required)
   - **RAW File:** Select RAW file (optional or required based on competition)
4. Click "Submit Entry"
5. Your submission will be analyzed by the AI detection system

### 5. View Your Submissions

1. Click "My Submissions" in the navigation
2. Or go to http://localhost:3000/my-submissions
3. View all your submissions with:
   - Status (Pending, Analyzing, Approved, Rejected)
   - Verification verdict (Authentic, Suspicious, AI Generated)
   - Confidence score
   - Camera metadata
   - Judge scores (when available)

## Common Tasks

### Create a Test Competition (As Organizer)

You'll need to use the API directly or update your user role to 'organizer':

```bash
# Using curl to create a competition
curl -X POST http://localhost:8080/api/v1/competitions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Competition",
    "description": "A test photography competition for authentic photos only",
    "submission_start": "2024-01-01T00:00:00",
    "submission_end": "2024-12-31T23:59:59",
    "max_submissions_per_user": 5,
    "require_raw_files": true,
    "allow_ai_generated": false,
    "entry_fee": 0
  }'
```

### View API Documentation

1. Competition Service: http://localhost:8080/docs
2. AI Detection Service: http://localhost:8001/docs
3. Interactive API testing available via Swagger UI

### Check Service Health

```bash
# All services
docker-compose ps

# Individual service logs
docker-compose logs -f frontend
docker-compose logs -f competition-service
docker-compose logs -f ai-detection-service

# Health checks
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8080/health  # Competition Service
curl http://localhost:8001/health  # AI Detection Service
```

### Reset Everything

```bash
# Stop all services
docker-compose down

# Remove all data (databases, uploads, etc.)
docker-compose down -v

# Rebuild and restart
docker-compose up --build -d
```

## Development Workflow

### Frontend Development

```bash
cd src/frontend

# Install dependencies
pnpm install

# Start dev server (with hot reload)
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

### Adding UI Components

```bash
cd src/frontend

# Add shadcn-vue components
pnpm dlx shadcn-vue@latest add button
pnpm dlx shadcn-vue@latest add card
pnpm dlx shadcn-vue@latest add dialog
# etc.
```

### Backend Development

```bash
# Start backend services only
docker-compose up -d postgres redis ai-detection-service competition-service api-gateway

# View logs
docker-compose logs -f competition-service

# Restart a service
docker-compose restart competition-service

# Rebuild after code changes
docker-compose up --build competition-service
```

## Troubleshooting

### Frontend won't start

```bash
cd src/frontend

# Clear node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Check for port conflicts
lsof -i :5173  # or :3000 for production
```

### Can't connect to backend

```bash
# Check if backend services are running
docker-compose ps

# Check backend logs for errors
docker-compose logs competition-service

# Verify API URL in .env.development
cat src/frontend/.env.development
```

### Database issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres

# Wait for database to be ready
docker-compose ps postgres
```

### Build fails

```bash
cd src/frontend

# Check for TypeScript errors
pnpm run build

# Fix errors and rebuild
pnpm run build
```

## Production Deployment

### Using Docker

```bash
# Build all images
docker-compose build

# Start in production mode
docker-compose up -d

# Frontend available at http://your-domain:3000
# Backend available at http://your-domain:8000
```

### Environment Variables for Production

Update `.env` file:

```env
# Database
DB_PASSWORD=strong_production_password

# API Keys
HIVE_AI_API_KEY=your_hive_api_key
OPTIC_API_KEY=your_optic_api_key

# Security
JWT_SECRET_KEY=strong_random_secret_key
ENCRYPTION_KEY=strong_encryption_key

# App Settings
APP_ENV=production
APP_DEBUG=false
```

## Testing the Full Stack

### Manual Test Flow

1. **Register** → Create a new account
2. **Login** → Sign in with credentials
3. **Browse** → View competitions list
4. **Details** → Click on a competition
5. **Submit** → Upload a photo with RAW file
6. **View** → Check My Submissions for status
7. **Verify** → Wait for AI analysis results

### Expected Behavior

- Registration should complete in < 2s
- Login should redirect to competitions
- Competitions should load in < 1s
- Photo upload should show progress
- AI analysis completes in 5-30s depending on complexity
- Status updates automatically (refresh page for now)

## Performance Benchmarks

### Frontend
- Initial load: ~200ms (cached)
- Page navigation: ~50ms
- Build time: ~20s
- Bundle size: ~250KB (gzipped: ~88KB)

### Backend
- API response time: < 100ms (typical)
- Authentication: < 50ms
- Photo upload: depends on file size
- AI analysis: 5-30s

### Docker
- Cold start: ~30-60s (all services)
- Hot restart: ~5-10s (single service)

## Next Steps

1. **Customize** - Modify colors, branding in `tailwind.config.js`
2. **Add Features** - Create new views/components as needed
3. **Configure** - Update environment variables for your setup
4. **Deploy** - Follow production deployment guide
5. **Scale** - Add load balancers, CDN, etc.

## Useful Commands

```bash
# Docker
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose ps                 # List running services
docker-compose logs -f <service>  # View logs
docker-compose restart <service>  # Restart a service
docker-compose build <service>    # Rebuild a service

# Frontend
pnpm dev                         # Start dev server
pnpm build                       # Build for production
pnpm preview                     # Preview production build

# Database
docker-compose exec postgres psql -U avar_user -d avar_competitions

# Cleanup
docker-compose down -v           # Remove volumes
docker system prune              # Clean up Docker
```

## Support

- Frontend Issues: Check browser console and network tab
- Backend Issues: Check `docker-compose logs`
- Database Issues: Check PostgreSQL logs
- For detailed documentation, see [FRONTEND_SETUP.md](FRONTEND_SETUP.md)

---

**Ready to start?** Run `docker-compose up -d` and visit http://localhost:3000
