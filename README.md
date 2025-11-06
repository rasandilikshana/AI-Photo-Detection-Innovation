# A.V.A.R. - Aura Verification and Authentication for RAW files

**AI-Powered Authenticity Verification System for Photography Competitions**

## Overview

A.V.A.R. is a comprehensive web platform designed to safeguard photography competition integrity against AI-generated synthetic imagery. The system employs a multi-layered forensic detection approach combining metadata analysis, digital fingerprinting (PRNU, ELA, FFT), and third-party API verification to ensure only genuine photographs reach the judging stage.

## Key Innovation

The first comprehensive AI-powered authenticity verification gateway specifically designed for photography competitions, featuring:

- **RAW-to-JPG Linkage Analysis**: Forensically proves submitted JPG files are direct derivatives of submitted RAW files
- **PRNU Fingerprinting**: Detects unique sensor noise patterns that AI-generated images cannot replicate
- **Multi-layer Detection Funnel**: Efficiently filters submissions from fast programmatic checks to expensive deep analysis

## Architecture

### Microservices Architecture

```
├── AI Detection Service (Python)
│   ├── Layer 1: Metadata Analysis (EXIF forensics)
│   ├── Layer 2: Digital Fingerprint Analysis (PRNU, ELA, FFT)
│   └── Layer 3: Third-Party API Integration
├── Competition Management Service (PHP Laravel)
│   ├── User authentication & authorization
│   ├── Submission workflow
│   ├── Judging dashboard
│   └── Admin panel
├── API Gateway (Node.js/Python)
│   └── Request routing & load balancing
└── Frontend Application (Vue.js/React)
    ├── Submission portal
    ├── Judging interface
    └── Admin dashboard
```

## Tech Stack

- **AI Detection**: Python 3.12+, OpenCV, NumPy, PyWavelets, rawpy, Pillow
- **Backend**: PHP 8.2+, Laravel 10+
- **Frontend**: Vue.js 3 / React 18
- **Database**: PostgreSQL 15+
- **Message Queue**: Redis
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.12+
- PHP 8.2+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd "Rasan Research 3"

# Start all services with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# Admin Panel: http://localhost:8080
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions and architecture documentation.

## Research Context

This project is part of a dissertation research titled:
**"Aura: Developing an AI-Powered Authenticity Verification System to Safeguard Photography Competition Integrity Against Synthetic Media"**

## License

Academic Research Project - All Rights Reserved

## Author

Rasan Dilikshana (rasandilikshana@gmail.com)
