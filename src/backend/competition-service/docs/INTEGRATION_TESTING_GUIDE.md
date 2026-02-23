# V2.0 Integration Testing Guide

## Overview

This guide provides step-by-step instructions for testing v2.0 innovations with actual database and images.

**Prerequisites**:
- Database migrations applied (`alembic upgrade head`)
- Backend service running
- Test images available (JPG files with EXIF metadata)
- API authentication tokens

---

## 🎬 Test Environment Setup

### 1. Database Migration

```bash
cd src/backend/competition-service

# Check current migration status
alembic current

# Apply v2.0 migrations
alembic upgrade head

# Verify new tables exist
psql -U postgres -d competition_db -c "
SELECT table_name
FROM information_schema.tables
WHERE table_name IN (
    'camera_fingerprints',
    'camera_profiles',
    'judge_scoring_profiles',
    'judge_consensus_analyses',
    'credential_sharing_detections'
);
"
```

**Expected Output**: 5 tables listed

---

### 2. Install Dependencies

```bash
# Ensure all required packages installed
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
pip install PyWavelets>=1.4.1
pip install scipy>=1.11.0

# Verify imports
python3 -c "
import cv2
import numpy
import pywt
import scipy
print('✅ All dependencies installed')
"
```

---

### 3. Prepare Test Data

**Test Images** (create `tests/test_images/` directory):
```bash
mkdir -p tests/test_images
```

Required test images:
1. **same_camera_1.jpg** - Photo from Camera A
2. **same_camera_2.jpg** - Different photo from Camera A (should match)
3. **different_camera.jpg** - Photo from Camera B (should not match)
4. **ai_generated.jpg** - AI-generated image (low PRNU energy)
5. **manipulated.jpg** - Photo with fake EXIF (fraud detection)

**Test Users** (create test accounts):
- Admin user (for all endpoints)
- Judge user 1 (for scoring tests)
- Judge user 2 (for consensus tests)
- Judge user 3 (for consensus tests)
- Regular user (for submission tests)

---

## 🧪 Test Scenarios

### Scenario 1: PRNU Extraction & Storage

**Objective**: Verify PRNU fingerprint extraction and storage

#### Step 1.1: Create Test Submission
```bash
# API: POST /api/v1/submissions
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "title=Test Submission 1" \
  -F "description=Camera A - Photo 1" \
  -F "jpg_file=@tests/test_images/same_camera_1.jpg" \
  -F "competition_id=1"
```

**Expected Response**:
```json
{
  "id": 101,
  "status": "pending",
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  ...
}
```

**Save submission_id**: 101

---

#### Step 1.2: Extract PRNU Fingerprint
```bash
# API: POST /api/v1/cameras/fingerprints/{submission_id}
curl -X POST http://localhost:8000/api/v1/cameras/fingerprints/101 \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Expected Response**:
```json
{
  "id": 1,
  "submission_id": 101,
  "user_id": 5,
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "prnu_energy": 0.0234,
  "prnu_hash": "a3f2b91c...",
  "similarity_to_profile": null,
  "trust_boost_applied": 0.0,
  "verified": true,
  "created_at": "2026-02-24T10:30:00Z"
}
```

**Validation**:
- [ ] `prnu_energy` > 0.01 (indicates valid fingerprint)
- [ ] `prnu_hash` is 64-character SHA256
- [ ] `verified: true`
- [ ] Processing time: 2-4 seconds

---

#### Step 1.3: Verify Database Storage
```sql
-- Check fingerprint stored
SELECT
    id,
    submission_id,
    camera_make,
    camera_model,
    prnu_energy,
    LENGTH(prnu_signature) as signature_size,
    verified
FROM camera_fingerprints
WHERE submission_id = 101;
```

**Expected**:
- `signature_size` ≈ 262,144 bytes (256KB)
- `verified = true`
- `prnu_energy` > 0.01

---

### Scenario 2: Camera Trust Profile

**Objective**: Verify trust scoring with multiple submissions from same camera

#### Step 2.1: Submit Second Photo from Same Camera
```bash
# Create submission with same_camera_2.jpg
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "title=Test Submission 2" \
  -F "description=Camera A - Photo 2" \
  -F "jpg_file=@tests/test_images/same_camera_2.jpg" \
  -F "competition_id=1"
```

**Save submission_id**: 102

```bash
# Extract fingerprint
curl -X POST http://localhost:8000/api/v1/cameras/fingerprints/102 \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Expected Response**:
```json
{
  "id": 2,
  "submission_id": 102,
  "similarity_to_profile": 0.87,
  "trust_boost_applied": 0.15,
  "verified": true,
  ...
}
```

**Validation**:
- [ ] `similarity_to_profile` > 0.85 (strong match)
- [ ] `trust_boost_applied` = 0.15 (+15% boost)

---

#### Step 2.2: Check Camera Profile
```bash
# API: GET /api/v1/cameras/trust-profile/{make}/{model}
curl -X GET "http://localhost:8000/api/v1/cameras/trust-profile/Canon/EOS%20R5" \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Expected Response**:
```json
{
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "total_submissions": 2,
  "authentic_count": 2,
  "suspicious_count": 0,
  "trust_score": 0.92,
  "avg_prnu_energy": 0.0231,
  "consistency_score": 0.95,
  ...
}
```

**Validation**:
- [ ] `total_submissions` = 2
- [ ] `trust_score` > 0.8 (high trust)
- [ ] `consistency_score` high (similar energies)

---

### Scenario 3: Fraud Detection

**Objective**: Detect camera EXIF manipulation

#### Step 3.1: Submit Photo with Fake EXIF
```bash
# Create submission with manipulated.jpg
# (EXIF claims Canon EOS R5, but PRNU matches different camera)
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "title=Fraudulent Submission" \
  -F "description=Fake EXIF test" \
  -F "jpg_file=@tests/test_images/manipulated.jpg" \
  -F "competition_id=1"
```

**Save submission_id**: 103

```bash
# Extract fingerprint
curl -X POST http://localhost:8000/api/v1/cameras/fingerprints/103 \
  -H "Authorization: Bearer $USER_TOKEN"
```

---

#### Step 3.2: Check Fraud Detection
```bash
# API: GET /api/v1/cameras/fraud-check/{submission_id}
curl -X GET http://localhost:8000/api/v1/cameras/fraud-check/103 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response**:
```json
{
  "submission_id": 103,
  "fraud_likelihood": 0.85,
  "fraud_verdict": "high_fraud_risk",
  "indicators": [
    "PRNU mismatch with user's previous submissions",
    "Pattern similarity to different camera model",
    "Energy deviation from camera profile"
  ],
  "recommendation": "reject",
  "explanation": "PRNU pattern does not match claimed camera..."
}
```

**Validation**:
- [ ] `fraud_likelihood` > 0.7
- [ ] `fraud_verdict` = "high_fraud_risk"
- [ ] Indicators list non-empty
- [ ] Recommendation = "reject"

---

#### Step 3.3: Verify Submission Rejected
```bash
# Check submission status
curl -X GET http://localhost:8000/api/v1/submissions/103 \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Expected**:
```json
{
  "id": 103,
  "status": "rejected",
  "rejection_reason": "Camera fraud detected: PRNU pattern mismatch",
  ...
}
```

---

### Scenario 4: Judge Consensus Analysis

**Objective**: Test consensus calculation with multiple judges

#### Step 4.1: Create Approved Submission
```bash
# Create submission for judging
curl -X POST http://localhost:8000/api/v1/submissions \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "title=Consensus Test Submission" \
  -F "jpg_file=@tests/test_images/same_camera_1.jpg" \
  -F "competition_id=1"
```

**Save submission_id**: 104

**Manually approve** submission to make it available for judging.

---

#### Step 4.2: Assign Judges
```sql
-- Assign 3 judges to submission
INSERT INTO submission_assignments (submission_id, judge_id, competition_id)
VALUES
    (104, 10, 1),  -- Judge 1
    (104, 11, 1),  -- Judge 2
    (104, 12, 1);  -- Judge 3
```

---

#### Step 4.3: Submit Scores (Judge 1)
```bash
# Judge 1 scores: 8.5/10
curl -X POST http://localhost:8000/api/v1/scores \
  -H "Authorization: Bearer $JUDGE1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": 104,
    "creativity_score": 8,
    "technical_score": 9,
    "composition_score": 8,
    "comments": "Excellent work"
  }'
```

---

#### Step 4.4: Submit Scores (Judge 2)
```bash
# Judge 2 scores: 8.0/10 (similar, good consensus)
curl -X POST http://localhost:8000/api/v1/scores \
  -H "Authorization: Bearer $JUDGE2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": 104,
    "creativity_score": 8,
    "technical_score": 8,
    "composition_score": 8,
    "comments": "Very good"
  }'
```

---

#### Step 4.5: Submit Scores (Judge 3 - Outlier)
```bash
# Judge 3 scores: 3.0/10 (outlier, poor consensus)
curl -X POST http://localhost:8000/api/v1/scores \
  -H "Authorization: Bearer $JUDGE3_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": 104,
    "creativity_score": 3,
    "technical_score": 3,
    "composition_score": 3,
    "comments": "Needs improvement"
  }'
```

---

#### Step 4.6: Check Consensus Analysis
```bash
# API: GET /api/v1/judges-analytics/consensus/{submission_id}
curl -X GET http://localhost:8000/api/v1/judges-analytics/consensus/104 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response**:
```json
{
  "id": 1,
  "competition_id": 1,
  "submission_id": 104,
  "judge_count": 3,
  "score_mean": 6.5,
  "score_std": 2.87,
  "icc_value": 0.35,
  "consensus_verdict": "poor_consensus",
  "consensus_quality": "low",
  "outlier_judges": [12],
  "outlier_scores": [3.0],
  "flagged_for_review": true,
  "confidence_level": 0.45,
  ...
}
```

**Validation**:
- [ ] `judge_count` = 3
- [ ] `score_mean` ≈ 6.5
- [ ] `icc_value` < 0.4 (poor consensus)
- [ ] `consensus_verdict` = "poor_consensus"
- [ ] `outlier_judges` contains Judge 3's ID [12]
- [ ] `flagged_for_review` = true

---

#### Step 4.7: Check Judge Profile (Judge 3)
```bash
# API: GET /api/v1/judges-analytics/profile/{judge_id}/{competition_id}
curl -X GET http://localhost:8000/api/v1/judges-analytics/profile/12/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response**:
```json
{
  "id": 1,
  "judge_id": 12,
  "competition_id": 1,
  "submission_count": 1,
  "avg_score_given": 3.0,
  "bias_score": -2.5,
  "bias_category": "harsh",
  "consistency_score": 1.0,
  ...
}
```

**Validation**:
- [ ] `bias_score` < -2.0 (significantly harsh)
- [ ] `bias_category` = "harsh"

---

### Scenario 5: Credential Sharing Detection

**Objective**: Detect suspicious activity patterns

#### Step 5.1: Simulate Activity from Multiple IPs

**Note**: This requires manually inserting audit logs with different IPs.

```sql
-- Insert mock activity logs for Judge 1
INSERT INTO score_audit_log (
    submission_id, judge_id, action,
    ip_address, session_id, user_agent, created_at
)
VALUES
    (104, 10, 'score_created', '192.168.1.100', 'sess_abc', 'Mozilla/5.0', NOW() - INTERVAL '2 hours'),
    (105, 10, 'score_created', '10.0.0.50', 'sess_xyz', 'Chrome/120', NOW() - INTERVAL '1 hour 50 minutes'),
    (106, 10, 'score_created', '172.16.0.20', 'sess_def', 'Firefox/115', NOW() - INTERVAL '1 hour 45 minutes'),
    (107, 10, 'score_created', '203.0.113.10', 'sess_ghi', 'Safari/17', NOW());
```

**Pattern**: 4 different IPs, 4 different sessions, rapid IP changes

---

#### Step 5.2: Run Credential Sharing Analysis
```bash
# API: POST /api/v1/judges-analytics/credential-sharing/{judge_id}/{competition_id}/analyze
curl -X POST "http://localhost:8000/api/v1/judges-analytics/credential-sharing/10/1/analyze?time_window_days=7" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response**:
```json
{
  "id": 1,
  "judge_id": 10,
  "competition_id": 1,
  "unique_ip_count": 4,
  "unique_session_count": 4,
  "unique_user_agent_count": 4,
  "risk_score": 0.72,
  "risk_level": "high",
  "risk_factors": [
    "Multiple IP addresses detected (4)",
    "Multiple user agents (4)",
    "3 impossible time gaps detected"
  ],
  "alert_triggered": true,
  "investigation_status": "pending",
  ...
}
```

**Validation**:
- [ ] `unique_ip_count` = 4
- [ ] `risk_score` > 0.7 (high risk)
- [ ] `risk_level` = "high"
- [ ] `alert_triggered` = true
- [ ] `investigation_status` = "pending"

---

#### Step 5.3: List Flagged Judges
```bash
# API: GET /api/v1/judges-analytics/credential-sharing/competition/1/flagged
curl -X GET "http://localhost:8000/api/v1/judges-analytics/credential-sharing/competition/1/flagged?min_risk_score=0.6" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "judge_id": 10,
    "risk_score": 0.72,
    "risk_level": "high",
    "investigation_status": "pending",
    ...
  }
]
```

---

#### Step 5.4: Update Investigation Status
```bash
# API: PATCH /api/v1/judges-analytics/credential-sharing/{detection_id}/investigate
curl -X PATCH http://localhost:8000/api/v1/judges-analytics/credential-sharing/1/investigate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "investigation_status": "reviewing",
    "investigation_notes": "Contacted judge - legitimate use from home/work/mobile"
  }'
```

**Expected Response**:
```json
{
  "message": "Investigation status updated to: reviewing",
  "status": "success"
}
```

---

### Scenario 6: Bias Report

**Objective**: Generate comprehensive competition bias report

#### Step 6.1: Get Competition Bias Report
```bash
# API: GET /api/v1/judges-analytics/competition/{competition_id}/bias-report
curl -X GET http://localhost:8000/api/v1/judges-analytics/competition/1/bias-report \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response**:
```json
{
  "competition_id": 1,
  "total_judges": 3,
  "avg_bias_score": -0.5,
  "bias_std_dev": 1.2,
  "avg_consistency": 0.85,
  "flagged_submissions_count": 1,
  "judge_profiles": [
    {
      "judge_id": 10,
      "submission_count": 4,
      "avg_score": 7.8,
      "bias_score": 0.2,
      "bias_category": "neutral",
      "consistency_score": 0.92
    },
    {
      "judge_id": 11,
      "submission_count": 1,
      "avg_score": 8.0,
      "bias_score": 0.5,
      "bias_category": "neutral",
      "consistency_score": 1.0
    },
    {
      "judge_id": 12,
      "submission_count": 1,
      "avg_score": 3.0,
      "bias_score": -2.5,
      "bias_category": "harsh",
      "consistency_score": 1.0
    }
  ],
  "flagged_submissions": [
    {
      "submission_id": 104,
      "icc_value": 0.35,
      "consensus_verdict": "poor_consensus",
      "outlier_judges": [12]
    }
  ]
}
```

**Validation**:
- [ ] All judges listed
- [ ] Judge 12 identified as harsh
- [ ] Submission 104 flagged

---

## 🔬 Performance Testing

### Test 1: PRNU Extraction Time
```python
# Script: tests/performance/test_prnu_speed.py
import time
from app.services import PRNUExtractor

extractor = PRNUExtractor()
images = ['test1.jpg', 'test2.jpg', 'test3.jpg']

times = []
for img in images:
    start = time.time()
    result = await extractor.extract_prnu_fingerprint(img, 'Canon', 'EOS R5')
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"{img}: {elapsed:.2f}s, energy: {result['energy']:.4f}")

print(f"Average: {sum(times)/len(times):.2f}s")
```

**Expected**: 2-4 seconds per image

---

### Test 2: Pattern Comparison Speed
```python
# Script: tests/performance/test_comparison_speed.py
import time
from app.services import PRNUExtractor

extractor = PRNUExtractor()
pattern1 = await extractor.extract_prnu_fingerprint('test1.jpg', 'Canon', 'EOS R5')
pattern2 = await extractor.extract_prnu_fingerprint('test2.jpg', 'Canon', 'EOS R5')

start = time.time()
similarity = extractor.compare_patterns(pattern1['pattern'], pattern2['pattern'])
elapsed = time.time() - start

print(f"Comparison time: {elapsed*1000:.1f}ms, similarity: {similarity:.3f}")
```

**Expected**: 50-100ms per comparison

---

### Test 3: Database Query Performance
```sql
-- Test fingerprint lookup
EXPLAIN ANALYZE
SELECT * FROM camera_fingerprints
WHERE user_id = 5 AND camera_make = 'Canon' AND camera_model = 'EOS R5'
LIMIT 50;

-- Test consensus lookup
EXPLAIN ANALYZE
SELECT * FROM judge_consensus_analyses
WHERE competition_id = 1 AND flagged_for_review = true;

-- Test profile lookup
EXPLAIN ANALYZE
SELECT * FROM camera_profiles
WHERE camera_make = 'Canon' AND camera_model = 'EOS R5';
```

**Expected**: <50ms for indexed queries

---

## 📊 Validation Checklist

### Camera Reputation
- [ ] PRNU extraction completes in 2-4 seconds
- [ ] Fingerprints compressed to ~256KB
- [ ] Similar photos have similarity > 0.85
- [ ] Different cameras have similarity < 0.5
- [ ] Trust boost applied correctly (+15%, +5%, 0%, -10%)
- [ ] Fraud detection identifies manipulated EXIF
- [ ] Camera profiles update after each submission

### Judge Consensus
- [ ] Consensus analysis triggers after all judges score
- [ ] ICC calculated correctly (0.0-1.0 range)
- [ ] Outlier judges identified (|Z| > 2.0)
- [ ] Poor consensus flagged for review (ICC < 0.4)
- [ ] Judge profiles show bias categories
- [ ] Bias report aggregates competition data

### Credential Sharing
- [ ] Risk score calculated from 4 factors
- [ ] High risk triggers alert (score > 0.7)
- [ ] Multiple IPs detected correctly
- [ ] Rapid IP changes flagged as time gap anomalies
- [ ] Investigation workflow updates status
- [ ] Flagged judges list filtered by risk score

### Integration
- [ ] Submission workflow includes camera reputation
- [ ] Scoring workflow includes consensus analysis
- [ ] Errors don't break core functionality
- [ ] Background tasks don't block responses
- [ ] Logs provide useful debugging info

---

## 🐛 Common Issues & Solutions

### Issue 1: PRNU Extraction Fails
**Symptoms**: Error 500, "PRNU extraction failed"

**Possible Causes**:
- Missing EXIF data
- Corrupt image file
- Insufficient memory

**Solution**:
```python
# Check image validity
from PIL import Image
img = Image.open('test.jpg')
print(img.format, img.size, img.mode)

# Check EXIF
from PIL.ExifTags import TAGS
exifdata = img.getexif()
for tag_id in exifdata:
    tag = TAGS.get(tag_id, tag_id)
    print(f"{tag}: {exifdata.get(tag_id)}")
```

---

### Issue 2: Zero Variance Scores
**Symptoms**: Division by zero in ICC calculation

**Solution**: Check `judge_consensus.py:_calculate_icc()` handles edge case

```python
if score_std == 0:
    # All judges gave same score = perfect consensus
    return 1.0
```

---

### Issue 3: No Consensus Triggered
**Symptoms**: Scores submitted but consensus not calculated

**Debug**:
```sql
-- Check judge assignments
SELECT submission_id, COUNT(*) as assigned_judges
FROM submission_assignments
WHERE submission_id = 104
GROUP BY submission_id;

-- Check scores received
SELECT submission_id, COUNT(*) as scores_received
FROM scores
WHERE submission_id = 104
GROUP BY submission_id;
```

**Solution**: Ensure `assigned_judges` = `scores_received`

---

### Issue 4: Low PRNU Energy
**Symptoms**: `prnu_energy` < 0.01, `verified: false`

**Cause**: Likely AI-generated or heavily edited image

**Expected Behavior**: System correctly identifies non-authentic photo

---

## 📋 Final Checklist

### Before Production
- [ ] All test scenarios pass
- [ ] Performance benchmarks met
- [ ] Database migrations applied
- [ ] Dependencies installed
- [ ] Error handling verified
- [ ] Logs reviewed for warnings

### Production Monitoring
- [ ] Setup alerts for PRNU extraction failures (>5% failure rate)
- [ ] Monitor consensus analysis execution time
- [ ] Track credential sharing alerts
- [ ] Monitor database growth (fingerprints table)
- [ ] Setup dashboard for bias reports

---

*Generated: 2026-02-24*
*Version: 1.0*
*Feature: v2.0 Innovations Integration Testing*
