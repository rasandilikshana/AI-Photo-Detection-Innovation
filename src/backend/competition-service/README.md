# A.V.A.R. Competition Service

Competition Management Microservice for the A.V.A.R. (Aura Verification and Authentication for RAW files) system.

## Overview

This service handles:
- User authentication and authorization (JWT)
- Competition creation and management
- Photo submission workflow
- Judge assignment and scoring
- Results publication

## Tech Stack

- **Python 3.12**
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Database
- **Redis** - Caching and session management
- **JWT** - Authentication tokens
- **Pydantic** - Data validation

## Quick Start

### Local Development

```bash
cd src/backend/competition-service

# Make start script executable
chmod +x start.sh

# Start the service
./start.sh
```

The service will be available at:
- **API**: http://localhost:8080
- **Interactive Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **Health Check**: http://localhost:8080/health

### Docker

```bash
# From project root
docker-compose up competition-service
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/avar_competitions

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service URLs
AI_DETECTION_SERVICE_URL=http://localhost:8001
API_GATEWAY_URL=http://localhost:8000
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/logout` - Logout

### Competitions

- `POST /api/v1/competitions` - Create competition (organizer/admin only)
- `GET /api/v1/competitions` - List competitions
- `GET /api/v1/competitions/{id}` - Get competition by ID
- `GET /api/v1/competitions/slug/{slug}` - Get competition by slug
- `PATCH /api/v1/competitions/{id}` - Update competition
- `DELETE /api/v1/competitions/{id}` - Delete competition

### Submissions

- `POST /api/v1/submissions` - Submit photo to competition
- `GET /api/v1/submissions` - List submissions
- `GET /api/v1/submissions/{id}` - Get submission by ID
- `DELETE /api/v1/submissions/{id}` - Delete submission

### Users

- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user by ID

## Database Models

### User
- Authentication credentials (email, password)
- Profile information (name, phone, country, bio)
- Role (participant, judge, organizer, admin)

### Competition
- Basic info (title, description, rules)
- Dates (submission period, judging period)
- Settings (max submissions, RAW requirements, AI policy)
- Prizes

### Submission
- Photo files (JPG + optional RAW)
- AI verification results
- Scores from judges
- Metadata (camera, lens, settings)

### Score
- Judge ratings (composition, technical, creativity)
- Comments
- Overall score

## Authentication Flow

1. User registers: `POST /api/v1/auth/register`
2. User logs in: `POST /api/v1/auth/login` → Returns JWT tokens
3. Use access token in header: `Authorization: Bearer {token}`
4. Refresh token when expired

## Submission Flow

1. User selects competition
2. Uploads JPG + RAW files
3. System validates files
4. AI Detection Service analyzes submission
5. Results stored in database
6. Submission visible to judges
7. Judges score submission
8. Results published

## Development

### Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Code Formatting

```bash
black app/
isort app/
flake8 app/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Project Structure

```
competition-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── schemas.py           # Pydantic models
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── competition.py
│   │   ├── submission.py
│   │   ├── judge.py
│   │   └── score.py
│   ├── routes/              # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── competitions.py
│   │   └── submissions.py
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── auth.py          # JWT & password hashing
│       └── security.py      # Security utilities
├── tests/                   # Test suite
├── uploads/                 # File uploads
├── requirements.txt         # Dependencies
├── Dockerfile              # Docker image
├── .env.example            # Environment template
└── start.sh                # Startup script
```

## Security

- Passwords hashed with bcrypt
- JWT tokens for authentication
- File upload validation
- SQL injection protection (SQLAlchemy)
- CORS configuration
- Rate limiting (planned)

## Performance

- Async database operations
- Connection pooling
- Redis caching (planned)
- File upload optimization

## Integration

### AI Detection Service

```python
import httpx

async def analyze_submission(jpg_path, raw_path=None):
    async with httpx.AsyncClient() as client:
        files = {"jpg_file": open(jpg_path, "rb")}
        if raw_path:
            files["raw_file"] = open(raw_path, "rb")
        
        response = await client.post(
            f"{AI_DETECTION_SERVICE_URL}/api/v1/analyze",
            files=files
        )
        return response.json()
```

## Monitoring

- Health check endpoint: `/health`
- Logging with Python logging module
- Structured logs (JSON format)
- Error tracking (future: Sentry integration)

## License

Part of A.V.A.R. dissertation project - NPAS Third Year

## Author

Rasan Dilikshana
Email: rasandilikshana@gmail.com

## AI Pair Programming

Built with assistance from Claude (Anthropic)
