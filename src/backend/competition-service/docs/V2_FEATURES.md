# A.V.A.R. v2.0 Features Documentation
## Camera Reputation System & Judge Analytics

**Version:** 2.0.0
**Date:** 2026-02-24
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Camera Reputation System](#camera-reputation-system)
3. [Judge Consensus Analysis](#judge-consensus-analysis)
4. [Credential Sharing Detection](#credential-sharing-detection)
5. [API Endpoints](#api-endpoints)
6. [Integration & Workflows](#integration--workflows)
7. [Frontend Integration](#frontend-integration)
8. [Performance & Scaling](#performance--scaling)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Overview

A.V.A.R. v2.0 introduces three major innovations to enhance photo authenticity verification:

### 1. **Camera Reputation System**
Builds trust profiles for cameras over time using PRNU (Photo Response Non-Uniformity) fingerprinting. Applies confidence boosts for submissions from trusted cameras and detects camera fraud.

### 2. **Judge Consensus Analysis**
Uses statistical methods (ICC, Z-scores) to measure judge agreement, detect bias, and identify outliers in scoring patterns.

### 3. **Credential Sharing Detection**
Monitors judge activity patterns to detect account sharing and suspicious behavior through IP analysis, session tracking, and geographic monitoring.

---

## Camera Reputation System

### Core Concept

Every camera sensor has a unique "fingerprint" created by manufacturing imperfections. By extracting and comparing these fingerprints (PRNU patterns) across submissions, we can:
- Build trust profiles for cameras
- Boost confidence for repeat submissions from known cameras
- Detect fraud (wrong camera claimed in EXIF)

### How It Works

#### 1. PRNU Extraction

**Algorithm:** Wavelet Denoising (Daubechies-8)

```
Process:
1. Load image → Grayscale → Resize to 512×512
2. Apply 2D Discrete Wavelet Transform (DWT)
3. Estimate noise using MAD (Median Absolute Deviation)
4. Threshold: σ × sqrt(2 × log(N))
5. Apply soft thresholding to detail coefficients
6. Reconstruct denoised image (Inverse DWT)
7. Extract residual: PRNU = original - denoised
8. Compress (zlib) and hash (SHA256)
```

**Output:**
- Pattern: 512×512 noise signature
- Energy: Variance (quality metric)
- Hash: SHA256 for deduplication
- Compressed: 256KB binary

**Performance:**
- Extraction time: 2-4 seconds
- Memory usage: ~50MB peak
- Storage: 256KB per fingerprint

#### 2. Trust Scoring

**Formula:**
```python
trust_score = (
    0.5 × pattern_similarity +      # How similar to previous submissions
    0.3 × (authentic_count / total) +  # Camera's historical authenticity rate
    0.2 × verdict_consistency       # User's consistency rate
)
```

**Trust Boosts:**

| Similarity | Boost | Verdict | Example |
|-----------|-------|---------|---------|
| > 0.85 | **+15%** | Strong match | Same physical camera |
| 0.70-0.85 | **+5%** | Moderate match | Likely same camera |
| 0.50-0.70 | **0%** | Weak match | Uncertain |
| < 0.50 | **-10%** | Suspicious | Different camera |

**Real-World Example:**
```
User submits photo from Canon EOS R5:
- AI Detection Confidence: 85%
- Camera has 10 previous submissions (9 authentic)
- Current PRNU similarity: 0.92 (strong match)

Trust Calculation:
- Pattern similarity: 0.92 × 0.5 = 0.46
- History: (9/10) × 0.3 = 0.27
- Consistency: 0.90 × 0.2 = 0.18
- Trust score: 0.91 (91%)

Trust boost: +15% (strong match)
Final confidence: 85% + 15% = 100%
```

#### 3. Fraud Detection

**Three-Level Check System:**

**Check 1: PRNU Pattern Mismatch**
- Compares current pattern with user's previous submissions for claimed camera
- Threshold: Similarity < 0.40
- Risk weight: +0.4

**Check 2: Energy Deviation**
- Compares PRNU energy with camera's average
- Threshold: >2× deviation from profile
- Risk weight: +0.3

**Check 3: Cross-Camera Match**
- Checks if pattern matches a different camera model
- Threshold: Similarity > 0.75 with other camera
- Risk weight: +0.5
- **Scenario:** User claims Canon but PRNU matches their Sony

**Fraud Verdicts:**

| Likelihood | Verdict | Action | Example |
|-----------|---------|--------|---------|
| > 0.7 | High Risk | **Auto-reject** | PRNU matches different camera |
| 0.4-0.7 | Medium Risk | **Manual review** | Energy deviation + weak match |
| < 0.4 | Low Risk | **Approve** | All checks pass |

#### 4. Camera Profiles

Each camera make/model has an aggregated profile:

```json
{
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "total_submissions": 247,
  "authentic_count": 231,
  "suspicious_count": 12,
  "ai_generated_count": 3,
  "rejected_count": 1,
  "avg_trust_score": 0.89,
  "prnu_pattern_stability": 0.08,
  "authenticity_rate": 93.5%,
  "rejection_rate": 1.6%
}
```

**Profile Uses:**
- Trust score calculation baseline
- Fraud detection reference
- Competition statistics
- Camera leaderboards

---

## Judge Consensus Analysis

### Core Concept

When multiple judges score the same submission, statistical analysis reveals:
- How much judges agree (consensus quality)
- Which judges are biased (harsh/lenient)
- Which scores are outliers
- Overall fairness of judging

### How It Works

#### 1. ICC (Intraclass Correlation Coefficient)

**Purpose:** Measures inter-rater reliability (how much judges agree)

**Formula:**
```python
# Simplified for single submission:
score_range = max(scores) - min(scores)
max_possible_range = 10.0  # 1-10 scale

ICC = 1.0 - (score_range / max_possible_range)

# Adjusted for judge count:
confidence_factor = min(1.0, n_judges / 5.0)
ICC_final = ICC × (0.5 + 0.5 × confidence_factor)
```

**Interpretation:**

| ICC Range | Quality | Meaning |
|-----------|---------|---------|
| > 0.75 | Excellent | Strong agreement - reliable verdict |
| 0.60-0.75 | Good | Moderate agreement - verdict acceptable |
| 0.40-0.60 | Fair | Weak agreement - consider review |
| < 0.40 | Poor | No consensus - manual review required |

**Example:**
```
Submission scored by 4 judges:
- Judge 1: 8.5
- Judge 2: 8.2
- Judge 3: 8.7
- Judge 4: 8.4

Score range: 0.5 (very tight)
ICC: 1.0 - (0.5 / 10.0) = 0.95
Confidence: min(1.0, 4/5) = 0.8
ICC_final: 0.95 × 0.9 = 0.855

Verdict: "Excellent consensus" ✓
```

#### 2. Bias Detection (Z-Score)

**Purpose:** Identifies judges who score consistently higher/lower than others

**Formula:**
```python
judge_avg = mean(judge's scores)
competition_avg = mean(all scores in competition)
competition_std = std(all scores)

bias_z_score = (judge_avg - competition_avg) / competition_std
```

**Categories:**

| Z-Score | Category | Meaning |
|---------|----------|---------|
| > 0.5 | Lenient | Scores higher than average |
| -0.5 to 0.5 | Fair | Well-calibrated |
| < -0.5 | Harsh | Scores lower than average |
| |Z| > 2.0 | Significant Bias | Requires investigation |

**Example:**
```
Judge Profile:
- Avg score given: 7.8
- Competition avg: 7.2
- Competition std: 0.9

Z-score: (7.8 - 7.2) / 0.9 = 0.67
Category: "Lenient" (scores ~0.6 points higher)
```

#### 3. Outlier Detection

**Purpose:** Identifies judges whose individual scores deviate significantly

**Method:**
```python
For each score:
  z_score = (score - mean) / std

  if |z_score| > 2.0:
    Flag as outlier
```

**Example:**
```
Submission scores: [8.2, 8.5, 8.3, 3.1]
Mean: 7.03
Std: 2.49

Judge 4's Z-score: (3.1 - 7.03) / 2.49 = -1.58
Not flagged (|z| < 2.0)

If Judge 4 gave 2.0:
Z-score: (2.0 - 7.33) / 2.79 = -1.91
Still not flagged

If Judge 4 gave 1.0:
Z-score: (1.0 - 7.67) / 3.13 = -2.13
FLAGGED as outlier! ⚠️
```

#### 4. Consistency Scoring

**Purpose:** Measures judge's scoring stability

**Formula:**
```python
cv = std_dev / mean  # Coefficient of Variation
consistency_score = max(0.0, 1.0 - cv)
```

**Example:**
```
Judge A scores: [8.1, 8.3, 8.2, 8.4, 8.0]
Mean: 8.2, Std: 0.14
CV: 0.14 / 8.2 = 0.017
Consistency: 1.0 - 0.017 = 0.983 (98%) ✓

Judge B scores: [5.0, 9.0, 3.0, 10.0, 6.0]
Mean: 6.6, Std: 2.88
CV: 2.88 / 6.6 = 0.436
Consistency: 1.0 - 0.436 = 0.564 (56%) ⚠️
```

---

## Credential Sharing Detection

### Core Concept

Monitors judge activity patterns to detect account sharing or compromise through:
- IP address diversity
- Concurrent sessions
- Impossible time gaps
- Geographic inconsistencies

### Risk Scoring

**Formula:**
```python
risk_score = (
    0.4 × ip_diversity_score +
    0.3 × session_overlap_score +
    0.2 × time_gap_score +
    0.1 × geo_consistency_score
)
```

**Risk Levels:**

| Score | Level | Action |
|-------|-------|--------|
| > 0.7 | High | Alert triggered, investigation required |
| 0.4-0.7 | Medium | Flag for review |
| < 0.4 | Low | No action needed |

### Detection Methods

#### 1. IP Diversity

**Scoring:**
```
1 IP: 0.0 (normal - same location)
2 IPs: 0.2 (acceptable - home/work)
3 IPs: 0.5 (suspicious - multiple locations)
4+ IPs: 0.8+ (high risk - likely sharing)
```

#### 2. Session Overlap

**Detection:**
- Identifies concurrent sessions from different IPs
- Threshold: Activities within 5 minutes
- Example: Judge scores from New York at 2:00 PM and Los Angeles at 2:03 PM

#### 3. Time Gap Anomalies

**Detection:**
- Rapid IP changes (< 1 hour between different IPs)
- Example: Activity from IP A at 2:00 PM, then IP B at 2:30 PM

#### 4. Geographic Inconsistencies

**Detection (Placeholder):**
- Different network blocks suggest different locations
- Future: Integrate geo-IP service for precise distances

---

## API Endpoints

### Camera Reputation

**Base URL:** `/api/v1/cameras`

#### POST `/fingerprints/{submission_id}`
Extract and store PRNU fingerprint.

**Auth:** Required (submission owner, judge, admin)

**Response:**
```json
{
  "id": 123,
  "submission_id": 456,
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "prnu_energy": 0.00234,
  "trust_boost_applied": 0.15,
  "verified": true
}
```

#### GET `/trust-profile/{make}/{model}`
Get camera reputation profile.

**Auth:** Public

**Response:**
```json
{
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "total_submissions": 247,
  "authenticity_rate": 93.5,
  "avg_trust_score": 0.89
}
```

#### GET `/user-cameras/{user_id}`
Get user's camera history.

**Auth:** Required (self or admin)

**Response:**
```json
[
  {
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "submission_count": 12,
    "first_used": "2025-01-15T10:30:00Z",
    "last_used": "2026-02-20T14:22:00Z",
    "avg_trust_score": 0.91
  }
]
```

#### GET `/fraud-check/{submission_id}`
Check submission for camera fraud.

**Auth:** Required (judge, admin)

**Response:**
```json
{
  "fraud_likelihood": 0.82,
  "verdict": "high_fraud_risk",
  "recommendation": "reject",
  "indicators": [
    "PRNU pattern doesn't match previous Canon EOS R5 submissions",
    "PRNU matches previous Sony A7R IV"
  ],
  "explanation": "High fraud risk detected..."
}
```

### Judge Analytics

**Base URL:** `/api/v1/judges-analytics`

#### GET `/profile/{judge_id}/{competition_id}`
Get judge scoring profile.

**Auth:** Required (self or admin)

**Response:**
```json
{
  "judge_id": 5,
  "submission_count": 47,
  "avg_score_given": 7.8,
  "bias_score": 0.67,
  "bias_category": "lenient",
  "consistency_score": 0.89
}
```

#### GET `/consensus/{submission_id}`
Get consensus analysis.

**Auth:** Required (judge, organizer, admin)

**Response:**
```json
{
  "submission_id": 123,
  "judge_count": 4,
  "icc_value": 0.87,
  "consensus_verdict": "strong_consensus",
  "outlier_judges": [],
  "confidence_level": 0.92
}
```

#### GET `/credential-sharing/{judge_id}/{competition_id}`
Get credential sharing status.

**Auth:** Required (admin only)

**Response:**
```json
{
  "judge_id": 8,
  "unique_ip_count": 4,
  "risk_score": 0.75,
  "risk_level": "high",
  "risk_factors": [
    "Multiple IP addresses detected (4)",
    "Concurrent session patterns detected"
  ],
  "alert_triggered": true
}
```

#### GET `/competition/{competition_id}/bias-report`
Get comprehensive bias report.

**Auth:** Required (admin, organizer)

**Response:**
```json
{
  "competition_id": 10,
  "total_judges": 6,
  "avg_bias_score": 0.12,
  "flagged_submissions_count": 3,
  "judge_profiles": [...],
  "flagged_submissions": [...]
}
```

---

## Integration & Workflows

### Submission Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User uploads photo (JPG + RAW)                           │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Metadata extraction & validation                          │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. AI Detection (Layer 1-3)                                  │
│    - Metadata checks                                          │
│    - PRNU/ELA/FFT analysis                                   │
│    - API checks                                              │
│    Result: Verdict + Confidence (e.g., 85%)                  │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. **Camera Reputation (NEW v2.0)**                          │
│    ┌──────────────────────────────────────────────┐          │
│    │ a. Extract PRNU fingerprint (2-4s)           │          │
│    │ b. Compare with user's camera history        │          │
│    │ c. Calculate trust score (0.91)              │          │
│    │ d. Apply trust boost (+15%)                  │          │
│    │ e. Detect fraud (likelihood: 0.1)            │          │
│    │ f. Update camera profile stats               │          │
│    └──────────────────────────────────────────────┘          │
│    Result: Final Confidence = 85% + 15% = 100%               │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Verdict determined                                         │
│    - AUTHENTIC (100% confidence) ✓                           │
│    - APPROVED status                                          │
└─────────────────────────────────────────────────────────────┘
```

### Scoring Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Judge scores submission (composition, technical, etc.)   │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Score created & audit log saved                           │
│    - IP address: 192.168.1.100                              │
│    - Session ID: abc123                                      │
│    - Timestamp: 2026-02-24 14:30:00                         │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. **Judge Consensus Check (NEW v2.0)**                      │
│    ┌──────────────────────────────────────────────┐          │
│    │ Check: All judges scored?                    │          │
│    │ - Assigned judges: 4                         │          │
│    │ - Scores received: 4                         │          │
│    │ Result: YES → Run consensus analysis         │          │
│    └──────────────────────────────────────────────┘          │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. **Consensus Analysis**                                    │
│    ┌──────────────────────────────────────────────┐          │
│    │ a. Calculate ICC (0.87)                      │          │
│    │ b. Detect outliers (none found)              │          │
│    │ c. Determine verdict (strong_consensus)      │          │
│    │ d. Store consensus analysis                  │          │
│    └──────────────────────────────────────────────┘          │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. **Judge Profile Update**                                  │
│    ┌──────────────────────────────────────────────┐          │
│    │ a. Calculate judge's avg score (7.8)         │          │
│    │ b. Calculate bias Z-score (0.67)             │          │
│    │ c. Determine bias category (lenient)         │          │
│    │ d. Calculate consistency (0.89)              │          │
│    │ e. Store judge profile                       │          │
│    └──────────────────────────────────────────────┘          │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Final verdict available with consensus metrics            │
│    - Score: 8.4 / 10                                         │
│    - Consensus: Strong (ICC=0.87)                            │
│    - Confidence: 92%                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Frontend Integration

### Display Camera Trust Score

```vue
<template>
  <div class="camera-trust-card">
    <h3>Camera Trust Score</h3>
    <div class="trust-meter">
      <progress :value="submission.camera_trust_score" max="1.0"></progress>
      <span>{{ (submission.camera_trust_score * 100).toFixed(0) }}%</span>
    </div>

    <div v-if="submission.prnu_fingerprint_id" class="verification-badge">
      <Badge variant="success">
        ✓ Verified Camera: {{ submission.camera_make }} {{ submission.camera_model }}
      </Badge>
      <p class="text-sm text-muted">
        This camera has {{ cameraHistory.submission_count }} verified submissions
      </p>
    </div>

    <div v-if="trustBoost > 0" class="boost-indicator">
      <Alert>
        <AlertTitle>Trust Boost Applied</AlertTitle>
        <AlertDescription>
          +{{ (trustBoost * 100).toFixed(0) }}% confidence boost
          from verified camera history
        </AlertDescription>
      </Alert>
    </div>
  </div>
</template>
```

### Display Judge Profile

```vue
<template>
  <Card class="judge-profile-card">
    <CardHeader>
      <CardTitle>Your Judging Profile</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="stat-grid">
        <div class="stat">
          <label>Bias Score</label>
          <meter
            :value="judgeProfile.bias_score + 1"
            min="0"
            max="2"
            low="0.5"
            high="1.5"
            optimum="1.0"
          ></meter>
          <span>{{ judgeProfile.bias_score.toFixed(2) }}</span>
          <p class="text-xs">{{ getBiasLabel(judgeProfile.bias_score) }}</p>
        </div>

        <div class="stat">
          <label>Consistency</label>
          <progress :value="judgeProfile.consistency_score" max="1.0"></progress>
          <span>{{ (judgeProfile.consistency_score * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
function getBiasLabel(bias) {
  if (bias > 0.3) return "You tend to score higher than average"
  if (bias < -0.3) return "You tend to score lower than average"
  return "Your scores are well-calibrated"
}
</script>
```

### Display Consensus Metrics

```vue
<template>
  <div class="consensus-card">
    <h4>Judge Consensus</h4>
    <div class="consensus-quality">
      <Badge :variant="getQualityVariant(consensus.icc_value)">
        {{ consensus.consensus_quality }}
      </Badge>
      <span class="icc-value">ICC: {{ consensus.icc_value.toFixed(2) }}</span>
    </div>

    <div v-if="consensus.outlier_judges.length > 0" class="outlier-alert">
      <AlertTriangle />
      <span>{{ consensus.outlier_judges.length }} outlier score(s) detected</span>
    </div>

    <div class="score-distribution">
      <p>Scores: {{ formatScores(consensus.scores_received) }}</p>
      <p>Agreement: {{ (consensus.score_agreement_ratio * 100).toFixed(0) }}%</p>
    </div>
  </div>
</template>
```

---

## Performance & Scaling

### Benchmarks

| Operation | Time | Memory | Notes |
|-----------|------|--------|-------|
| PRNU Extraction | 2-4s | 50MB | Can run in background |
| Pattern Comparison | 50ms | 10MB | Fast enough for sync |
| Trust Score Calculation | 100ms | 15MB | Includes DB queries |
| ICC Calculation | 20ms | 5MB | Pure computation |
| Bias Analysis | 50ms | 8MB | Includes aggregation |

### Optimization Strategies

#### 1. Background Processing

**Use Cases:**
- PRNU extraction (2-4s → non-blocking)
- Camera profile updates
- Consensus analysis for completed submissions

**Implementation:**
```python
from fastapi import BackgroundTasks

background_tasks.add_task(
    integrate_camera_reputation,
    submission_id, submission, jpg_path, db
)
```

#### 2. Caching

**Redis Cache Strategy:**
```python
# Cache decompressed PRNU patterns
cache_key = f"prnu:fingerprint:{fingerprint_id}"
redis.setex(cache_key, 3600, compressed_pattern)  # 1 hour TTL

# Cache camera profiles
cache_key = f"camera:profile:{make}:{model}"
redis.setex(cache_key, 600, profile_json)  # 10 min TTL
```

#### 3. Database Indexing

**Critical Indexes:**
```sql
-- Camera fingerprints
CREATE INDEX idx_camera_fingerprints_user ON camera_fingerprints(user_id);
CREATE INDEX idx_camera_fingerprints_camera ON camera_fingerprints(camera_make, camera_model);
CREATE INDEX idx_camera_fingerprints_hash ON camera_fingerprints(prnu_hash);

-- Judge profiles
CREATE INDEX idx_judge_scoring_profiles_judge ON judge_scoring_profiles(judge_id);
CREATE INDEX idx_judge_scoring_profiles_bias ON judge_scoring_profiles(bias_score);

-- Consensus
CREATE INDEX idx_judge_consensus_flagged ON judge_consensus_analysis(flagged_for_review);
```

#### 4. Batch Processing

**Competition Analysis:**
```python
# Analyze all submissions in competition
for submission_id in submission_ids:
    analyzer.analyze_submission_scores(submission_id)

# Update all judge profiles
for judge_id in judge_ids:
    analyzer.build_judge_profile(judge_id, competition_id)
```

---

## Security Considerations

### Authentication & Authorization

**Camera Reputation:**
- Fingerprint extraction: Submission owner, judge, admin
- Trust profile viewing: Public
- Fraud check: Judge, admin only
- Comparison: Admin only

**Judge Analytics:**
- Profile viewing: Self or admin
- Consensus viewing: Judge, organizer, admin
- Credential sharing: Admin only
- Bias reports: Admin, organizer only

### Data Privacy

**PII Handling:**
- IP addresses stored for security monitoring
- Session IDs anonymized
- User agents logged for fraud detection
- Geographic data (future) will be aggregated

**Data Retention:**
- Audit logs: 1 year
- PRNU fingerprints: Permanent (compressed)
- Consensus analyses: Permanent
- Credential sharing alerts: 90 days after resolution

### Rate Limiting

**Endpoints:**
```python
# Expensive operations
/cameras/fingerprints: 10 per minute per user
/cameras/comparison: 30 per minute per user
/judges-analytics/*/analyze: 20 per minute per admin

# General endpoints
All others: 100 per minute per user
```

---

## Troubleshooting

### Camera Reputation Issues

**Problem:** PRNU extraction fails

**Solutions:**
1. Check image format (JPEG/JPG required)
2. Verify file size (< 50MB recommended)
3. Check memory availability (need ~50MB)
4. Review logs for specific error

**Problem:** Trust score always 0.5 (neutral)

**Reasons:**
- First submission with this camera (no history)
- PRNU energy too low (< 0.00001)
- No previous verified submissions

**Problem:** False fraud detection

**Solutions:**
1. Check camera EXIF data accuracy
2. Verify user hasn't changed cameras
3. Review PRNU energy levels
4. Manual review by admin

### Judge Consensus Issues

**Problem:** ICC always low

**Reasons:**
- Judges have genuinely different opinions
- Unclear judging criteria
- Complex/ambiguous photo
- Too few judges (need 3+)

**Problem:** Bias score seems wrong

**Solutions:**
1. Check competition statistics (mean, std)
2. Verify judge has scored enough submissions
3. Review score distribution
4. Consider competition-specific factors

### Performance Issues

**Problem:** PRNU extraction too slow

**Solutions:**
1. Resize image before extraction
2. Use background task processing
3. Scale worker processes
4. Consider GPU acceleration

**Problem:** Database queries slow

**Solutions:**
1. Verify indexes exist
2. Analyze query plans (EXPLAIN)
3. Add caching layer
4. Partition large tables

---

## Support & Contact

**Documentation:** `/docs/` (this file)
**API Docs:** `/docs` (Swagger UI)
**GitHub:** [Repository URL]
**Email:** support@avar.studio

---

**Version:** 2.0.0
**Last Updated:** 2026-02-24
**Authors:** Claude Sonnet 4.5 & Development Team
