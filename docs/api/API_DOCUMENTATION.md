# A.V.A.R. API Documentation

Complete API documentation for the A.V.A.R. (Aura Verification and Authentication for RAW files) backend services.

## Table of Contents

- [Overview](#overview)
- [Base URLs](#base-urls)
- [Authentication](#authentication)
- [API Services](#api-services)
  - [AI Detection Service](#ai-detection-service)
  - [Competition Service](#competition-service)
  - [API Gateway](#api-gateway)
- [Postman Collections](#postman-collections)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

The A.V.A.R. platform consists of three main backend services:

1. **AI Detection Service** - Multi-layer AI detection and RAW-JPG verification
2. **Competition Service** - Competition management, user authentication, and submissions
3. **API Gateway** - Unified access point with routing and rate limiting

---

## Base URLs

| Environment | AI Detection | Competition | Gateway |
|-------------|-------------|-------------|---------|
| **Local** | `http://localhost:8001` | `http://localhost:8080` | `http://localhost:8000` |
| **Docker** | `http://localhost:8001` | `http://localhost:8080` | `http://localhost:8000` |
| **Production** | TBD | TBD | TBD |

---

## Authentication

### JWT Authentication

The Competition Service uses JWT (JSON Web Tokens) for authentication.

**Token Types:**
- **Access Token**: Short-lived (30 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

**Authentication Flow:**

```
1. Register/Login → Receive tokens
2. Include Access Token in headers: Authorization: Bearer <token>
3. Token expires → Use Refresh Token to get new Access Token
```

**Example:**

```bash
# 1. Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}

# 2. Use Access Token
curl http://localhost:8080/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGc..."
```

---

## API Services

### AI Detection Service

**Base URL:** `http://localhost:8001`

#### Endpoints

##### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-detection-service",
  "timestamp": "2025-11-06T18:00:00.000000"
}
```

---

##### Analyze Single Image
```http
POST /api/v1/analyze
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file, required): Image file (JPG/PNG)

**Response:**
```json
{
  "file_id": "abc123",
  "filename": "image.jpg",
  "ai_probability": 0.15,
  "is_likely_ai": false,
  "analysis": {
    "prnu_score": 0.85,
    "ela_score": 0.12,
    "fft_score": 0.10,
    "metadata_authentic": true
  },
  "timestamp": "2025-11-06T18:00:00Z"
}
```

---

##### Batch Analysis
```http
POST /api/v1/analyze/batch
Content-Type: multipart/form-data
```

**Parameters:**
- `files` (file[], required): Multiple image files (up to 10)

**Response:**
```json
{
  "results": [
    {
      "filename": "image1.jpg",
      "ai_probability": 0.15,
      "is_likely_ai": false
    },
    {
      "filename": "image2.jpg",
      "ai_probability": 0.85,
      "is_likely_ai": true
    }
  ],
  "total_analyzed": 2
}
```

---

##### Verify RAW-JPG Linkage
```http
POST /api/v1/verify-linkage
Content-Type: multipart/form-data
```

**Parameters:**
- `raw_file` (file, required): RAW image file (CR2, NEF, ARW, DNG, etc.)
- `jpg_file` (file, required): JPG image file

**Response:**
```json
{
  "linked": true,
  "confidence": 0.95,
  "analysis": {
    "metadata_match": true,
    "prnu_correlation": 0.92,
    "timestamp_match": true,
    "exif_consistency": true
  },
  "message": "RAW and JPG files are linked with high confidence"
}
```

---

##### PRNU Analysis
```http
POST /api/v1/prnu
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file, required): Image file

**Response:**
```json
{
  "prnu_fingerprint": "base64_encoded_data",
  "sensor_score": 0.87,
  "authenticity_score": 0.92
}
```

---

##### ELA Analysis
```http
POST /api/v1/ela
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file, required): Image file

**Response:**
```json
{
  "ela_image": "base64_encoded_data",
  "manipulation_score": 0.12,
  "suspicious_regions": []
}
```

---

##### Metadata Analysis
```http
POST /api/v1/metadata
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file, required): Image file

**Response:**
```json
{
  "camera": "Canon EOS R5",
  "lens": "RF 24-105mm F4L",
  "iso": 400,
  "shutter_speed": "1/250",
  "aperture": "f/4.0",
  "focal_length": "50mm",
  "date_taken": "2025-01-15T14:30:00",
  "gps": null,
  "software": null
}
```

---

### Competition Service

**Base URL:** `http://localhost:8080`

#### Authentication Endpoints

##### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "photographer",
  "password": "SecurePass123!",
  "full_name": "John Photographer"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "photographer",
  "full_name": "John Photographer",
  "role": "participant",
  "is_active": true,
  "created_at": "2025-11-06T18:00:00Z"
}
```

---

##### Login
```http
POST /api/v1/auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "photographer",
    "role": "participant"
  }
}
```

---

##### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### User Endpoints

##### Get Current User
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "photographer",
  "full_name": "John Photographer",
  "role": "participant",
  "is_active": true,
  "created_at": "2025-11-06T18:00:00Z"
}
```

---

##### List Users
```http
GET /api/v1/users?skip=0&limit=50
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 50)

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "username": "photographer1",
    "role": "participant"
  },
  {
    "id": 2,
    "email": "user2@example.com",
    "username": "photographer2",
    "role": "organizer"
  }
]
```

---

#### Competition Endpoints

##### Create Competition
```http
POST /api/v1/competitions
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Roles Required:** Organizer, Admin

**Request Body:**
```json
{
  "title": "Wildlife Photography Challenge 2025",
  "description": "Capture the beauty of wildlife in their natural habitat",
  "rules": "1. Original work only\n2. No AI-generated images\n3. RAW files required",
  "submission_start": "2025-02-01T00:00:00Z",
  "submission_end": "2025-03-31T23:59:59Z",
  "max_submissions_per_user": 5,
  "require_raw_files": true,
  "allow_ai_generated": false,
  "entry_fee": 25.00,
  "prize_description": "1st: $5000, 2nd: $2500, 3rd: $1000",
  "prize_amount": 8500.00
}
```

**Response (201):**
```json
{
  "id": 1,
  "slug": "wildlife-photography-challenge-2025",
  "title": "Wildlife Photography Challenge 2025",
  "status": "draft",
  "organizer_id": 1,
  "created_at": "2025-11-06T18:00:00Z"
}
```

---

##### List Competitions
```http
GET /api/v1/competitions?status=open&skip=0&limit=20
```

**Query Parameters:**
- `status` (string, optional): Filter by status (draft, open, closed, judging, completed)
- `skip` (integer, optional): Pagination offset
- `limit` (integer, optional): Results per page

**Response (200):**
```json
[
  {
    "id": 1,
    "slug": "wildlife-photography-challenge-2025",
    "title": "Wildlife Photography Challenge 2025",
    "status": "open",
    "submission_start": "2025-02-01T00:00:00Z",
    "submission_end": "2025-03-31T23:59:59Z",
    "entry_fee": 25.00,
    "prize_amount": 8500.00
  }
]
```

---

##### Get Competition by ID
```http
GET /api/v1/competitions/{competition_id}
```

**Response (200):**
```json
{
  "id": 1,
  "slug": "wildlife-photography-challenge-2025",
  "title": "Wildlife Photography Challenge 2025",
  "description": "Capture the beauty of wildlife...",
  "rules": "1. Original work only...",
  "status": "open",
  "submission_start": "2025-02-01T00:00:00Z",
  "submission_end": "2025-03-31T23:59:59Z",
  "max_submissions_per_user": 5,
  "require_raw_files": true,
  "entry_fee": 25.00,
  "prize_amount": 8500.00,
  "total_submissions": 42,
  "organizer": {
    "id": 1,
    "username": "competition_organizer"
  }
}
```

---

##### Update Competition
```http
PATCH /api/v1/competitions/{competition_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Roles Required:** Organizer (own competitions), Admin

**Request Body (partial update):**
```json
{
  "status": "open",
  "description": "Updated description"
}
```

**Response (200):** Updated competition object

---

##### Delete Competition
```http
DELETE /api/v1/competitions/{competition_id}
Authorization: Bearer <access_token>
```

**Roles Required:** Organizer (own competitions), Admin

**Response (200):**
```json
{
  "message": "Competition deleted successfully"
}
```

---

#### Submission Endpoints

##### Create Submission
```http
POST /api/v1/submissions
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Parameters:**
- `competition_id` (integer, required)
- `title` (string, required)
- `description` (string, optional)
- `image_file` (file, required): Main image (JPG/PNG)
- `raw_file` (file, optional): RAW file if competition requires
- `camera_model` (string, optional)
- `lens_model` (string, optional)
- `capture_date` (datetime, optional)

**Response (201):**
```json
{
  "id": 1,
  "competition_id": 1,
  "user_id": 1,
  "title": "Golden Hour Eagle",
  "status": "pending",
  "ai_detection_score": 0.15,
  "is_ai_detected": false,
  "submitted_at": "2025-11-06T18:00:00Z"
}
```

---

##### List Submissions
```http
GET /api/v1/submissions?competition_id=1&skip=0&limit=20
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `competition_id` (integer, optional): Filter by competition
- `status` (string, optional): Filter by status
- `skip`, `limit`: Pagination

**Response (200):** Array of submission objects

---

##### Get My Submissions
```http
GET /api/v1/submissions/my
Authorization: Bearer <access_token>
```

**Response (200):** Array of current user's submissions

---

##### Update Submission
```http
PATCH /api/v1/submissions/{submission_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response (200):** Updated submission object

---

##### Delete Submission
```http
DELETE /api/v1/submissions/{submission_id}
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Submission deleted successfully"
}
```

---

### API Gateway

**Base URL:** `http://localhost:8000`

The API Gateway provides a unified interface to all backend services with:
- Request routing
- Rate limiting
- Load balancing
- Health monitoring

#### Route Mapping

| Gateway Route | Target Service | Target Endpoint |
|--------------|----------------|-----------------|
| `/health` | Gateway | Health check (all services) |
| `/ai/*` | AI Detection | `/api/v1/*` |
| `/competition/*` | Competition | `/api/v1/*` |

**Example:**
```bash
# Direct to AI Detection Service
curl http://localhost:8001/api/v1/analyze

# Via Gateway (equivalent)
curl http://localhost:8000/ai/analyze
```

---

## Postman Collections

Import these collections into Postman for easy API testing:

1. **[AI Detection Service Collection](./AVAR-AI-Detection-Service.postman_collection.json)**
   - All AI detection endpoints
   - Image analysis workflows
   - RAW-JPG verification

2. **[Competition Service Collection](./AVAR-Competition-Service.postman_collection.json)**
   - Authentication flow
   - Competition management
   - Submission workflows
   - Automatic token management

3. **[API Gateway Collection](./AVAR-API-Gateway.postman_collection.json)**
   - Unified access to all services
   - Gateway-routed requests

### Importing Collections

1. Open Postman
2. Click "Import" button
3. Select the JSON file
4. Collections will be imported with pre-configured requests

### Environment Variables

Set these variables in Postman:

```
base_url: http://localhost:8001  (AI Detection)
base_url: http://localhost:8080  (Competition)
base_url: http://localhost:8000  (Gateway)
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message description",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

**API Gateway Rate Limits:**
- **Per IP:** 100 requests/minute
- **Per User (authenticated):** 200 requests/minute
- **File Upload:** 10 MB max file size
- **Batch Upload:** Max 10 files per request

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699281600
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

### AI Detection Service
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

### Competition Service
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

### API Gateway
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Support

For issues or questions:
- **GitHub Issues:** [github.com/rasanentechlabs/avar/issues](https://github.com)
- **Email:** support@avar.com
- **Documentation:** [Full docs](../../README.md)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-06
