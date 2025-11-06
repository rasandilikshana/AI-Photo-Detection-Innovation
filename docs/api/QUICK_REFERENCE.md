# A.V.A.R. API Quick Reference

Quick reference guide for common API operations.

## 🚀 Quick Start

### 1. Start Services
```bash
docker compose up -d
```

### 2. Check Health
```bash
curl http://localhost:8001/health  # AI Detection
curl http://localhost:8080/health  # Competition
curl http://localhost:8000/health  # Gateway
```

---

## 🔐 Authentication Flow

### Step 1: Register
```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "photographer",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

### Step 2: Login
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# Save the access_token from response
export TOKEN="your_access_token_here"
```

### Step 3: Use Token
```bash
curl http://localhost:8080/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🖼️ AI Detection

### Analyze Single Image
```bash
curl -X POST http://localhost:8001/api/v1/analyze \
  -F "file=@/path/to/image.jpg"
```

### Verify RAW-JPG Linkage
```bash
curl -X POST http://localhost:8001/api/v1/verify-linkage \
  -F "raw_file=@/path/to/image.CR2" \
  -F "jpg_file=@/path/to/image.jpg"
```

### Batch Analysis
```bash
curl -X POST http://localhost:8001/api/v1/analyze/batch \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

---

## 🏆 Competition Management

### Create Competition (Organizer)
```bash
curl -X POST http://localhost:8080/api/v1/competitions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Wildlife Photography 2025",
    "description": "Capture wildlife beauty",
    "submission_start": "2025-02-01T00:00:00Z",
    "submission_end": "2025-03-31T23:59:59Z",
    "max_submissions_per_user": 5,
    "require_raw_files": true,
    "entry_fee": 25.00,
    "prize_amount": 5000.00
  }'
```

### List Competitions
```bash
# All competitions
curl http://localhost:8080/api/v1/competitions

# Filter by status
curl "http://localhost:8080/api/v1/competitions?status=open"

# With pagination
curl "http://localhost:8080/api/v1/competitions?skip=0&limit=10"
```

### Get Competition Details
```bash
# By ID
curl http://localhost:8080/api/v1/competitions/1

# By slug
curl http://localhost:8080/api/v1/competitions/slug/wildlife-photography-2025
```

---

## 📸 Submit to Competition

### Create Submission
```bash
curl -X POST http://localhost:8080/api/v1/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -F "competition_id=1" \
  -F "title=Golden Hour Eagle" \
  -F "description=A majestic eagle at sunset" \
  -F "image_file=@/path/to/image.jpg" \
  -F "raw_file=@/path/to/image.CR2" \
  -F "camera_model=Canon EOS R5" \
  -F "lens_model=RF 100-500mm"
```

### List My Submissions
```bash
curl http://localhost:8080/api/v1/submissions/my \
  -H "Authorization: Bearer $TOKEN"
```

### Get Submission Details
```bash
curl http://localhost:8080/api/v1/submissions/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🌐 Using API Gateway

All services can be accessed through the gateway:

### AI Detection via Gateway
```bash
# Instead of: http://localhost:8001/api/v1/analyze
curl -X POST http://localhost:8000/ai/analyze \
  -F "file=@image.jpg"
```

### Competition via Gateway
```bash
# Instead of: http://localhost:8080/api/v1/auth/login
curl -X POST http://localhost:8000/competition/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass"}'
```

---

## 🔄 Common Workflows

### Workflow 1: Register and Submit to Competition

```bash
# 1. Register
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "pass123", "full_name": "User"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}' \
  | jq -r '.access_token')

# 3. View competitions
curl http://localhost:8080/api/v1/competitions?status=open

# 4. Submit entry
curl -X POST http://localhost:8080/api/v1/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -F "competition_id=1" \
  -F "title=My Entry" \
  -F "image_file=@photo.jpg"
```

### Workflow 2: Verify Image Authenticity

```bash
# 1. Check for AI generation
curl -X POST http://localhost:8001/api/v1/analyze \
  -F "file=@photo.jpg"

# 2. Verify RAW linkage
curl -X POST http://localhost:8001/api/v1/verify-linkage \
  -F "raw_file=@photo.CR2" \
  -F "jpg_file=@photo.jpg"

# 3. Check metadata
curl -X POST http://localhost:8001/api/v1/metadata \
  -F "file=@photo.jpg"
```

---

## 📊 Response Examples

### Success Response
```json
{
  "id": 1,
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Authentication required",
  "status_code": 401
}
```

### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🛠️ Debugging

### Check Service Status
```bash
docker compose ps
```

### View Logs
```bash
docker compose logs -f ai-detection-service
docker compose logs -f competition-service
docker compose logs -f api-gateway
```

### Test Connectivity
```bash
# AI Detection
curl -v http://localhost:8001/health

# Competition
curl -v http://localhost:8080/health

# Gateway
curl -v http://localhost:8000/health
```

---

## 📱 Testing with Postman

1. Import collections from `docs/api/*.postman_collection.json`
2. Set environment variables:
   - `base_url`: Service URL
   - `access_token`: Your JWT token (auto-set by Login request)
3. Run requests in order within folders

---

## 🔗 Useful Links

- **Interactive API Docs (Swagger):**
  - AI Detection: http://localhost:8001/docs
  - Competition: http://localhost:8080/docs
  - Gateway: http://localhost:8000/docs

- **Alternative Docs (ReDoc):**
  - AI Detection: http://localhost:8001/redoc
  - Competition: http://localhost:8080/redoc
  - Gateway: http://localhost:8000/redoc

- **Full Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

## ⚡ Tips

1. **Save your token:** After login, save the `access_token` as an environment variable
2. **Use jq:** Parse JSON responses: `curl ... | jq`
3. **Check health first:** Always verify services are running
4. **File uploads:** Use `-F` for multipart form data, not `-d`
5. **Gateway vs Direct:** Use gateway in production, direct URLs for debugging

---

**Last Updated:** 2025-11-06
