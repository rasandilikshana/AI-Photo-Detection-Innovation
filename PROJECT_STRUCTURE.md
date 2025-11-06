# A.V.A.R. Project Structure

Complete directory structure and file organization following best practices.

## Directory Tree

```
Rasan Research 3/
│
├── docs/                                 # 📚 All Documentation
│   ├── README.md                        # Documentation index
│   ├── IMPLEMENTATION_SUMMARY.md        # Complete implementation summary
│   ├── guides/                          # Developer guides
│   │   ├── CLAUDE.md                    # Comprehensive developer guide
│   │   ├── TESTING_GUIDE.md            # Testing quick start
│   │   ├── TESTING.md                   # Detailed testing documentation
│   │   └── COMMANDS_REFERENCE.md        # All available commands
│   ├── architecture/                    # Architecture documentation
│   │   └── SYSTEM_ARCHITECTURE.md       # System design & architecture
│   ├── api/                             # API documentation
│   │   └── (Future API docs)
│   └── research/                        # Research documentation
│       └── (Research notes & papers)
│
├── documents/                            # 📄 Original Research Documents
│   ├── AI Photo Detection Innovation Roadmap.docx
│   ├── Dissertation Plan.docx
│   ├── Estimated Cost.docx
│   └── Proposed Timetable.docx
│
├── src/                                  # 💻 Source Code
│   └── backend/
│       ├── ai-detection-service/        # Main AI detection microservice
│       │   ├── app/
│       │   │   ├── __init__.py
│       │   │   ├── main.py              # FastAPI application entry
│       │   │   ├── services/            # Detection layer implementations
│       │   │   │   ├── __init__.py
│       │   │   │   ├── layer1_metadata.py        # EXIF analysis
│       │   │   │   ├── layer2_fingerprint.py     # PRNU, ELA, FFT
│       │   │   │   ├── layer3_api.py             # Third-party APIs
│       │   │   │   └── raw_jpg_linkage.py        # RAW-JPG verification
│       │   │   └── utils/               # Utility modules
│       │   │       ├── __init__.py
│       │   │       ├── logger.py         # Logging configuration
│       │   │       └── file_handler.py   # File operations
│       │   ├── tests/                   # Unit tests
│       │   │   ├── __init__.py
│       │   │   ├── conftest.py          # Test fixtures
│       │   │   └── test_layer1_metadata.py
│       │   ├── uploads/                 # Temporary upload directory
│       │   ├── Dockerfile               # Container definition
│       │   ├── requirements.txt         # Python dependencies
│       │   └── pytest.ini               # Pytest configuration
│       │
│       ├── api-gateway/                 # API Gateway service
│       │   ├── app/
│       │   │   └── main.py              # Gateway application
│       │   ├── Dockerfile
│       │   └── requirements.txt
│       │
│       ├── competition-service/         # (Future) Competition management
│       │   └── (Laravel application)
│       │
│       └── shared/                      # Shared utilities
│
├── src/frontend/                        # (Future) Frontend application
│   └── (Vue.js/React app)
│
├── tests/                                # 🧪 Integration & E2E Tests
│   ├── conftest.py                      # Global test fixtures
│   ├── pytest.ini                       # Pytest configuration
│   ├── requirements.txt                 # Testing dependencies
│   ├── run_tests.sh                     # Automated test runner
│   ├── integration/                     # Integration tests
│   │   └── test_ai_detection_api.py     # API integration tests
│   ├── e2e/                             # End-to-end browser tests
│   │   └── test_submission_workflow.py   # Playwright tests
│   ├── performance/                     # Performance tests
│   │   └── locustfile.py                 # Load testing scenarios
│   └── fixtures/                        # Test data
│       └── images/                       # Test images
│
├── deployments/                         # (Future) Deployment configurations
│   ├── kubernetes/
│   ├── terraform/
│   └── ansible/
│
├── config/                              # Configuration files
│   └── (Service configurations)
│
├── .git/                                # Git repository
├── .gitignore                           # Git exclusions
├── .env                                 # Environment variables (DO NOT COMMIT)
├── .env.example                         # Environment template
│
├── docker-compose.yml                   # Docker orchestration
├── Makefile                             # Build & development commands
├── VERSION                              # Current version number
├── CHANGELOG.md                         # Version history & changes
│
├── README.md                            # Project overview
├── PROJECT_STRUCTURE.md                 # This file
│
├── quickstart.sh                        # Automated setup script
├── run_local.sh                         # Local development runner
└── stop_local.sh                        # Stop local services
```

## File Organization Principles

### 1. Separation of Concerns

- **Source code** (`src/`) - Production code only
- **Tests** (`tests/`) - All testing code
- **Documentation** (`docs/`) - All documentation
- **Configuration** (root & `config/`) - Configuration files
- **Deployment** (`deployments/`) - Deployment artifacts

### 2. Service Isolation

Each microservice is self-contained:
```
service-name/
├── app/           # Application code
├── tests/         # Service-specific tests
├── Dockerfile     # Container definition
└── requirements.txt # Dependencies
```

### 3. Documentation Organization

```
docs/
├── guides/        # How-to guides & tutorials
├── architecture/  # System design documents
├── api/           # API specifications
└── research/      # Research papers & notes
```

### 4. Test Organization

```
tests/
├── unit/          # (In service directories)
├── integration/   # Cross-service tests
├── e2e/           # End-to-end workflows
└── performance/   # Load & stress tests
```

## File Naming Conventions

### Python Files
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `CapitalizedWords` (in code)
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Test files**: `test_*.py`

### Documentation
- **Root docs**: `UPPERCASE.md` (README.md, CHANGELOG.md)
- **Guide docs**: `Descriptive_Name.md`
- **Use underscores**: For multi-word names

### Configuration
- **Docker**: `docker-compose.yml`, `Dockerfile`
- **Python**: `requirements.txt`, `pytest.ini`
- **Make**: `Makefile`

## Key Files Explained

### Root Level

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start |
| `CHANGELOG.md` | Version history |
| `VERSION` | Current version number |
| `PROJECT_STRUCTURE.md` | This file |
| `docker-compose.yml` | Multi-container orchestration |
| `Makefile` | Development commands |
| `.gitignore` | Git exclusions |
| `.env.example` | Environment template |

### Scripts

| File | Purpose |
|------|---------|
| `quickstart.sh` | Automated setup (Docker) |
| `run_local.sh` | Run services locally |
| `stop_local.sh` | Stop local services |
| `tests/run_tests.sh` | Run test suite |

### Source Code

| Directory | Purpose |
|-----------|---------|
| `src/backend/ai-detection-service/` | Core AI detection |
| `src/backend/api-gateway/` | Request routing |
| `src/backend/competition-service/` | (Future) Competition mgmt |
| `src/frontend/` | (Future) User interface |

### Documentation

| File | Purpose |
|------|---------|
| `docs/README.md` | Documentation index |
| `docs/IMPLEMENTATION_SUMMARY.md` | Complete summary |
| `docs/guides/CLAUDE.md` | Developer guide |
| `docs/guides/TESTING_GUIDE.md` | Testing quick start |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | System design |

## Directory Purposes

### `/src` - Source Code
Production code organized by service. Each service is independent and deployable.

### `/docs` - Documentation
All documentation in one place. Organized by type (guides, architecture, API, research).

### `/tests` - Testing
Integration and E2E tests that span multiple services. Unit tests are co-located with code.

### `/documents` - Research
Original research documents (Word files). Read-only, version controlled.

### `/deployments` - Deployment
Infrastructure as Code, deployment scripts, configuration for different environments.

### `/config` - Configuration
Shared configuration files, environment-specific settings.

## Best Practices Followed

### 1. Don't Repeat Yourself (DRY)
- Shared utilities in `/src/backend/shared`
- Reusable test fixtures in `conftest.py`
- Common configurations in environment files

### 2. Single Responsibility
- Each service has one purpose
- Each module has clear responsibility
- Tests are organized by what they test

### 3. Dependency Management
- `requirements.txt` for each service
- Separate dev/test dependencies
- Lock files for reproducibility

### 4. Version Control
- `.gitignore` excludes build artifacts
- `.env` excluded, `.env.example` included
- Meaningful commit messages

### 5. Documentation as Code
- Documentation in version control
- Markdown for portability
- Auto-generated API docs

### 6. Testing Strategy
- Unit tests with code
- Integration tests separate
- Test data in fixtures
- Automated test running

## Adding New Components

### New Microservice

```bash
mkdir -p src/backend/new-service/{app,tests}
cd src/backend/new-service

# Create structure
touch app/__init__.py
touch app/main.py
touch Dockerfile
touch requirements.txt
touch tests/__init__.py

# Update docker-compose.yml
# Add to documentation
```

### New Documentation

```bash
# Choose appropriate directory
cd docs/guides  # For guides
cd docs/api     # For API docs
cd docs/architecture  # For architecture

# Create file
touch NEW_DOCUMENT.md

# Update docs/README.md index
```

### New Test Suite

```bash
cd tests

# Create test file
touch integration/test_new_feature.py

# Add fixtures to conftest.py if needed
# Update run_tests.sh if needed
```

## File Size Guidelines

- **Source files**: < 500 lines (split if larger)
- **Test files**: < 300 lines per file
- **Documentation**: < 1000 lines per file
- **Configuration**: < 200 lines

## Ignored Files (.gitignore)

### Python
- `__pycache__/`, `*.pyc`
- `venv/`, `env/`
- `.pytest_cache/`

### Node
- `node_modules/`
- `dist/`

### PHP/Laravel
- `vendor/`
- `.env`

### Build Artifacts
- `build/`, `dist/`
- `*.egg-info/`

### IDEs
- `.vscode/`, `.idea/`
- `*.swp`

### Logs & Temp
- `*.log`
- `/tmp/`

### Secrets
- `.env`
- `*.key`, `*.pem`

## Maintenance

### Weekly
- Review and update CHANGELOG.md
- Check for deprecated dependencies
- Clean up temporary files

### Monthly
- Update documentation
- Review test coverage
- Check for security updates

### Quarterly
- Major dependency updates
- Architecture review
- Performance audit

---

**Version**: 1.0.0
**Last Updated**: November 6, 2025
**Maintained By**: Rasan Dilikshana
**Structure**: Production-ready microservices architecture
