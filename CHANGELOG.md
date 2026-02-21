# Changelog

All notable changes to the A.V.A.R. project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-02-21

### Added
- **Judge Dashboard UX Enhancements**
  - Dropdown filter menus replacing button-based filters (Status, Verdict, Scored)
  - Clickable submission cards - entire card navigates to scoring page
  - Pagination with 12 items per page and full navigation controls
  - Competition-aware navigation preserving context via URL query params
  - Route watcher for same-component navigation handling

- **Score Submission Page Improvements**
  - Image lightbox viewer with full-screen capability
  - Smooth zoom controls with 10% increments (10%-500%)
  - Corrective action buttons for quick judge operations
  - Back button preserves competition context

### Fixed
- Navigation issue when clicking "Judge Panel" from competition-specific URL
- Vue Router same-component navigation not resetting state

### Changed
- Filter buttons converted to cleaner dropdown menu components
- Submission cards now fully clickable with event propagation control

---

## [1.3.0] - 2026-02-21

### Added
- **Production Deployment**
  - Live deployment at avar.studio
  - DigitalOcean Droplet hosting (Singapore)
  - Let's Encrypt SSL certificates (auto-renewing)
  - Nginx reverse proxy configuration
  - UFW Firewall and Fail2Ban security

- **GitHub Actions CI/CD**
  - Docker image builds on release
  - Push to Docker Hub on release tags
  - Telegram notifications for releases
  - Automated deployment workflow

- **Deployment Documentation**
  - Production deployment guide
  - Nginx SSL configuration templates
  - Environment variable templates

### Changed
- Updated server IP from 64.23.136.61 to 165.245.178.225
- Fixed deployment path to /var/www/avar/src/frontend/dist/

---

## [1.2.0] - 2026-02-20

### Added
- **Score Audit Log System**
  - Complete tracking of all scoring actions
  - IP address, User-agent, Session ID logging
  - Credential sharing detection capabilities
  - Audit log viewer in Admin Panel and Judge Dashboard

- **Admin Panel**
  - User management with role assignment
  - Competition oversight dashboard
  - System-wide statistics
  - Score audit log access

- **Organizer Panel**
  - Competition creation wizard
  - Competition management interface
  - Submission tracking for own competitions

### Fixed
- JWT token refresh handling
- Role-based navigation guards

---

## [1.1.0] - 2026-02-15

### Added
- **Vue 3 Frontend Application**
  - TypeScript with Composition API
  - Mobile responsive design (hamburger menu, responsive grids)
  - Role-based authentication (Participant, Judge, Organizer, Admin)
  - Real-time submission status updates

- **Judge Dashboard**
  - Score submissions with multi-criteria system
  - Composition (40%), Technical (30%), Creativity (30%)
  - View AI detection results
  - Filter submissions by competition and status

- **Competition Management**
  - CRUD operations with slug-based URLs
  - Competition browsing interface
  - Submission portal with multi-file uploads (JPG + RAW)

- **User Authentication**
  - JWT tokens with bcrypt password hashing
  - Login and registration interfaces
  - Role-based access control navigation guards

### Changed
- Competition Service migrated from PHP Laravel to Python FastAPI

---

## [1.0.0] - 2025-11-06

### Added
- **Core AI Detection Service**
  - Layer 1: Metadata Analysis with EXIF forensics
  - Layer 2: Digital Fingerprint Analysis (PRNU, ELA, FFT)
  - Layer 3: Third-party API Integration (Hive AI)
  - RAW-JPG Linkage Verification System

- **Infrastructure**
  - Docker containerization with docker-compose
  - PostgreSQL database setup
  - Redis caching layer
  - API Gateway for request routing

- **Testing Suite**
  - 50+ Unit tests
  - 30+ Integration tests
  - Playwright E2E browser tests
  - Locust performance/load tests
  - Automated test runner (run_tests.sh)
  - HTML test reporting

- **Documentation**
  - Comprehensive developer guide (CLAUDE.md)
  - Testing guide (TESTING_GUIDE.md)
  - Commands reference (COMMANDS_REFERENCE.md)
  - System architecture documentation
  - API documentation (auto-generated)
  - Implementation summary

- **Development Tools**
  - Makefile with 25+ commands
  - Quick start script (quickstart.sh)
  - Local development runner (run_local.sh)
  - Service stop script (stop_local.sh)
  - Git configuration

- **Features**
  - Multi-layer detection pipeline
  - Early rejection optimization
  - Concurrent request handling
  - Background file cleanup
  - Structured logging
  - Health check endpoints

### Technical Specifications
- Python 3.12+ support
- FastAPI 0.104.1
- OpenCV 4.8.1
- PyWavelets 1.5.0
- PostgreSQL 15+
- Redis 7+
- Docker containerization

### Performance
- Layer 1: 50-200ms response time
- Full Pipeline: 2-10 seconds
- Supports 10+ concurrent requests
- 80%+ code coverage

### Research Contribution
- Novel RAW-JPG linkage methodology
- PRNU sensor fingerprinting implementation
- Production-ready microservices architecture
- Comprehensive testing framework

---

## [Unreleased]

### Planned for v1.5.0
- [ ] Real-time WebSocket updates for submission status
- [ ] Batch processing capabilities for bulk submissions
- [ ] Custom AI signature database

### Planned for v2.0.0
- [ ] Machine learning model integration
- [ ] Kubernetes orchestration
- [ ] Advanced analytics dashboard
- [ ] Mobile application (React Native/Flutter)
- [ ] Multi-language support (i18n)
- [ ] Public leaderboard feature

---

## Version History

### Version Numbering
- **MAJOR**: Incompatible API changes
- **MINOR**: New features, backwards-compatible
- **PATCH**: Bug fixes, backwards-compatible

### Release Notes Format
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

**Current Version**: 1.4.0
**Release Date**: February 21, 2026
**Status**: Production Ready (Live at avar.studio)
**Author**: Rasan Dilikshana
**License**: Academic Research Project
