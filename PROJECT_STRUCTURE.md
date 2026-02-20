# A.V.A.R. Project Structure

This document provides an overview of the project's directory structure.

```
AI-Photo-Detection-Innovation/
├── src/
│   ├── backend/
│   │   ├── ai-detection-service/     # AI detection microservice
│   │   │   ├── app/
│   │   │   │   ├── main.py           # FastAPI application
│   │   │   │   ├── services/         # Detection services
│   │   │   │   │   ├── layer1_metadata.py      # EXIF/metadata analysis
│   │   │   │   │   ├── layer2_fingerprint.py   # PRNU, ELA, FFT analysis
│   │   │   │   │   ├── layer3_api.py           # Third-party API integration
│   │   │   │   │   └── raw_jpg_linkage.py      # RAW-JPG verification
│   │   │   │   └── utils/            # Utilities
│   │   │   ├── tests/                # Unit tests
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── competition-service/      # Competition management microservice
│   │   │   ├── app/
│   │   │   │   ├── main.py           # FastAPI application
│   │   │   │   ├── models/           # SQLAlchemy models
│   │   │   │   ├── routes/           # API endpoints
│   │   │   │   ├── schemas.py        # Pydantic schemas
│   │   │   │   └── database.py       # Database configuration
│   │   │   ├── scripts/              # Database seed scripts
│   │   │   ├── uploads/              # File uploads (gitignored)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   └── api-gateway/              # API Gateway
│   │       ├── app/
│   │       │   └── main.py           # Request routing
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   │
│   └── frontend/                     # Vue.js frontend
│       ├── src/
│       │   ├── components/           # Vue components
│       │   │   └── ui/               # UI component library
│       │   ├── views/                # Page views
│       │   ├── router/               # Vue Router config
│       │   ├── main.ts               # Application entry
│       │   └── style.css             # Global styles
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── package.json
│
├── tests/                            # Integration & E2E tests
│   ├── integration/                  # API integration tests
│   ├── e2e/                          # Playwright browser tests
│   ├── performance/                  # Locust load tests
│   ├── conftest.py                   # Pytest fixtures
│   └── requirements.txt
│
├── docs/                             # Documentation
│   ├── guides/                       # User guides
│   │   ├── CLAUDE.md                 # Developer guide
│   │   └── TESTING_GUIDE.md          # Testing instructions
│   ├── architecture/                 # System design docs
│   │   └── SYSTEM_ARCHITECTURE.md
│   ├── api/                          # API documentation
│   └── implementation/               # Implementation summaries
│
├── deployments/                      # Deployment configs
│   ├── DEPLOYMENT_GUIDE.md           # Production deployment guide
│   ├── production-setup.sh           # Setup script
│   ├── nginx-ssl.conf                # Nginx configuration
│   └── .env.production.template      # Environment template
│
├── .github/
│   └── workflows/                    # CI/CD pipelines
│       ├── ci.yml                    # Continuous Integration
│       └── release.yml               # Release automation
│
├── docker-compose.yml                # Docker orchestration
├── Makefile                          # Development commands
├── quickstart.sh                     # Quick setup script
├── README.md                         # Project overview
├── CHANGELOG.md                      # Version history
├── LICENSE                           # MIT License
└── PROJECT_STRUCTURE.md              # This file
```

## Key Directories

### Backend Services

- **ai-detection-service**: Core AI detection engine with multi-layer analysis
- **competition-service**: Competition management, user auth, judge scoring
- **api-gateway**: Request routing and service orchestration

### Frontend

- **Vue 3 + TypeScript**: Modern SPA framework
- **Tailwind CSS**: Utility-first styling
- **Responsive Design**: Mobile-first approach

### Testing

- **Unit Tests**: Service-level testing with pytest
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Browser automation with Playwright
- **Performance Tests**: Load testing with Locust

### Documentation

- Comprehensive guides for developers and users
- API documentation (auto-generated via FastAPI)
- Architecture diagrams and system design docs

## Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Multi-container orchestration |
| `Makefile` | Development command shortcuts |
| `.env.example` | Environment variable template |
| `tailwind.config.js` | Tailwind CSS configuration |
| `vite.config.ts` | Vite build configuration |
