# A.V.A.R. System Architecture

## Overview

A.V.A.R. is built using a modern microservices architecture with clear separation of concerns and scalability in mind.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (Vue.js/React - Port 3000)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP/REST
                           ↓
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                 (FastAPI - Port 8000)                        │
│  • Request Routing                                           │
│  • Load Balancing                                            │
│  • Rate Limiting                                             │
└─────────┬────────────────────────────────────┬───────────────┘
          │                                    │
          │ HTTP                               │ HTTP
          ↓                                    ↓
┌─────────────────────────┐      ┌────────────────────────────┐
│  AI Detection Service   │      │  Competition Service       │
│  (FastAPI - Port 8001)  │      │  (Laravel - Port 8080)     │
│                         │      │                            │
│  • Layer 1: Metadata    │      │  • User Management         │
│  • RAW-JPG Linkage      │      │  • Competition Workflow    │
│  • Layer 2: Fingerprint │      │  • Submission Management   │
│  • Layer 3: API         │      │  • Judging System          │
└────────┬────────────────┘      └────────┬───────────────────┘
         │                                │
         │                                │
         ↓                                ↓
┌─────────────────────────────────────────────────────────────┐
│                   Shared Infrastructure                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │ File Storage │      │
│  │  (Port 5432) │  │ (Port 6379)  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. AI Detection Service (Core)

**Technology**: Python 3.12, FastAPI, OpenCV, PyWavelets

**Responsibilities**:
- EXIF metadata analysis
- RAW-JPG linkage verification
- PRNU sensor fingerprinting
- ELA compression analysis
- FFT frequency analysis
- Third-party API integration

**Endpoints**:
- `POST /api/v1/analyze` - Full analysis
- `POST /api/v1/analyze/metadata-only` - Quick check
- `GET /health` - Health check

**Performance**:
- Layer 1: 50-200ms
- Full Pipeline: 2-10 seconds
- Concurrent: 10+ requests

### 2. API Gateway

**Technology**: Python 3.12, FastAPI

**Responsibilities**:
- Centralized routing
- Request/response transformation
- Load balancing (future)
- Rate limiting (future)
- Authentication (future)

**Benefits**:
- Single entry point
- Service abstraction
- Simplified client integration
- Monitoring centralization

### 3. Competition Service (Future)

**Technology**: PHP 8.2+, Laravel 10+

**Responsibilities**:
- User authentication & authorization
- Competition creation & management
- Submission workflow
- Judge assignment & scoring
- Results publication

### 4. Frontend Application (Future)

**Technology**: Vue.js 3 / React 18

**Components**:
- Submission portal
- Judge dashboard
- Admin panel
- Results viewer

### 5. Infrastructure

#### PostgreSQL Database
- User data
- Competitions
- Submissions
- Analysis results
- Judging scores

#### Redis Cache
- Session management
- Request caching
- Message queue
- Real-time data

#### File Storage
- Uploaded images (JPG, RAW)
- Temporary processing files
- Analysis results
- Generated reports

## Data Flow

### Photo Submission Workflow

```
1. User Upload
   ↓
2. API Gateway (authentication, validation)
   ↓
3. Competition Service (save submission record)
   ↓
4. AI Detection Service
   ├─ Layer 1: Metadata → Quick rejection possible
   ├─ RAW-JPG Linkage → Forgery detection
   ├─ Layer 2: Fingerprint → Deep analysis
   └─ Layer 3: API (if needed) → Final verdict
   ↓
5. Verdict: AUTHENTIC / REJECT / QUARANTINE
   ↓
6. Database Update
   ↓
7. Notification to User
   ↓
8. If AUTHENTIC → Judging Queue
   If REJECT → Rejection Notice
   If QUARANTINE → Admin Review
```

### Analysis Pipeline (AI Detection Service)

```
┌─────────────────────┐
│   File Upload       │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ Layer 1: Metadata   │  ←── FAST (50-200ms)
│ - EXIF extraction   │
│ - AI signatures     │
│ - Camera validation │
└──────────┬──────────┘
           │
      PASS │ REJECT → Return verdict
           ↓
┌─────────────────────┐
│ RAW-JPG Linkage     │  ←── MEDIUM (500-2000ms)
│ - pHash comparison  │
│ - SSIM analysis     │
│ - Histogram match   │
└──────────┬──────────┘
           │
      PASS │ REJECT → Return verdict
           ↓
┌─────────────────────┐
│ Layer 2: Fingerprint│  ←── SLOW (2-5s)
│ - PRNU extraction   │
│ - ELA analysis      │
│ - FFT analysis      │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
AUTHENTIC    SUSPICIOUS
    │             │
    │             ↓
    │      ┌─────────────────────┐
    │      │ Layer 3: API        │  ←── VERY SLOW (1-10s)
    │      │ - Hive AI           │
    │      │ - Confidence score  │
    │      └──────┬──────────────┘
    │             │
    │      ┌──────┴──────┐
    │      │             │
    │   AUTHENTIC    REJECT
    │      │             │
    └──────┴─────────────┘
           │
           ↓
    ┌─────────────────────┐
    │  Return Final       │
    │  Verdict            │
    └─────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

**AI Detection Service**:
- Stateless design
- Can scale to multiple instances
- Load balancer distributes requests
- Each instance independent

**Database**:
- Read replicas for queries
- Connection pooling
- Caching layer (Redis)

### Vertical Scaling

**AI Detection**:
- CPU-intensive operations (PRNU, FFT)
- More cores = faster processing
- GPU acceleration possible (future)

### Queue-Based Processing

**Future Enhancement**:
```
User Upload → Queue → Worker Pool → Database
                ↓
         Multiple workers process in parallel
```

Benefits:
- Async processing
- Better resource utilization
- Graceful degradation
- Priority queuing

## Security Architecture

### Authentication & Authorization

**JWT-based authentication**:
```
User → Login → JWT Token → Authenticated Requests
```

**Role-based access control**:
- Admin: Full access
- Judge: Judging interface
- Participant: Submission only
- Guest: Read-only

### Data Protection

**In Transit**:
- HTTPS/TLS encryption
- Secure WebSocket (future)

**At Rest**:
- Database encryption
- Encrypted file storage
- Secure credential storage

**API Security**:
- Rate limiting
- CORS configuration
- Input validation
- SQL injection prevention
- XSS protection

## Deployment Architecture

### Development
```
Local Machine
├── Python virtual environments
├── Local PostgreSQL (optional)
└── Local Redis (optional)
```

### Staging
```
Docker Containers
├── docker-compose orchestration
├── Shared PostgreSQL
├── Shared Redis
└── Volume mounts for data
```

### Production (Future)
```
Cloud Platform (AWS/GCP)
├── Kubernetes cluster
├── Managed PostgreSQL (RDS/Cloud SQL)
├── Managed Redis (ElastiCache/Memorystore)
├── CDN for static assets
├── Load balancer
└── Auto-scaling groups
```

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend Services** |
| AI Detection | Python | 3.12+ | Core detection logic |
| API Gateway | Python/FastAPI | 0.104+ | Request routing |
| Competition | PHP/Laravel | 8.2+/10+ | Business logic |
| **Frontend** |
| UI Framework | Vue.js/React | 3+/18+ | User interface |
| **Infrastructure** |
| Database | PostgreSQL | 15+ | Data persistence |
| Cache | Redis | 7+ | Caching & queues |
| Container | Docker | Latest | Containerization |
| Orchestration | Docker Compose | Latest | Multi-container |
| **AI/ML Libraries** |
| Computer Vision | OpenCV | 4.8+ | Image processing |
| Forensics | PyWavelets | 1.5+ | PRNU extraction |
| RAW Processing | rawpy | 0.19+ | RAW file handling |

## Design Patterns

### Microservices Pattern
- Independent services
- Single responsibility
- Technology diversity
- Independent deployment

### API Gateway Pattern
- Single entry point
- Request routing
- Protocol translation
- Response aggregation

### Repository Pattern
- Data access abstraction
- Testability
- Separation of concerns

### Factory Pattern
- Service instantiation
- Configuration management
- Dependency injection

## Performance Optimization

### Caching Strategy

**Redis Cache**:
```python
# Cache metadata analysis results
cache_key = f"metadata:{file_hash}"
if cached := redis.get(cache_key):
    return cached

result = analyze_metadata(file)
redis.setex(cache_key, 3600, result)  # 1 hour TTL
```

### Database Optimization

**Indexes**:
- submission_id (primary)
- user_id (foreign key)
- created_at (time-series queries)
- verdict (filtering)

**Query Optimization**:
- Use SELECT specific fields
- Pagination for large results
- Prepared statements
- Connection pooling

### File Processing

**Temporary Storage**:
- Process files in `/tmp` or memory
- Auto-cleanup after analysis
- Stream large files
- Compress before storage

## Monitoring & Logging

### Logging Strategy

**Levels**:
- ERROR: Critical failures
- WARNING: Suspicious activity
- INFO: Normal operations
- DEBUG: Detailed diagnostics

**Structured Logging**:
```python
logger.info(
    "Analysis complete",
    extra={
        "submission_id": id,
        "verdict": verdict,
        "processing_time_ms": duration
    }
)
```

### Metrics (Future)

**Key Metrics**:
- Request rate (req/sec)
- Response time (ms)
- Error rate (%)
- Queue depth
- Cache hit rate

**Tools**:
- Prometheus (metrics)
- Grafana (visualization)
- ELK Stack (log aggregation)

## Disaster Recovery

### Backup Strategy

**Database**:
- Daily full backups
- Transaction log backups
- Point-in-time recovery

**Files**:
- Replicated storage
- Geographic redundancy
- Versioning enabled

### High Availability

**Future Implementation**:
- Multi-region deployment
- Automatic failover
- Health checks
- Circuit breakers

## Future Enhancements

1. **Machine Learning Pipeline**
   - Model training infrastructure
   - Feature extraction
   - Model versioning
   - A/B testing

2. **Real-Time Processing**
   - WebSocket connections
   - Live progress updates
   - Streaming analysis

3. **Batch Processing**
   - Bulk submission handling
   - Scheduled jobs
   - Report generation

4. **Advanced Analytics**
   - Detection accuracy metrics
   - False positive analysis
   - Performance dashboards
   - Trend analysis

---

**Version**: 1.0.0
**Last Updated**: November 6, 2025
**Author**: Rasan Dilikshana
