# A.V.A.R. Innovation Enhancement Implementation Plan
**Camera Reputation System + Judge Consensus Analysis**

**Version:** 2.0 (Innovation Enhancement)
**Date:** February 21, 2026
**Author:** Rasan Dilikshana
**Project:** A.V.A.R. - AI-Powered Authenticity Verification And Rating

---

## Executive Summary

This implementation plan details the integration of **two major innovations** into the existing A.V.A.R. platform:

1. **Camera Reputation System** - Builds trust profiles for photographers by storing and comparing PRNU sensor fingerprints across submissions
2. **Judge Consensus Analysis** - Detects biased judges and credential sharing through statistical analysis

### Innovation Value Proposition

**Current A.V.A.R. (v1.4.0):**
- ✅ World-first RAW-JPG triple verification
- ✅ Multi-layer forensic detection (PRNU+ELA+FFT)
- ✅ Complete audit trail system

**Enhanced A.V.A.R. (v2.0):**
- ✅✅ **Camera Reputation System** - Unique, defensible, creates network effects
- ✅✅ **Judge Bias Detection** - Unique, extends audit trail innovation
- ✅ All existing features preserved and enhanced

### Expected Outcomes

| Metric | Current | Target (v2.0) | Improvement |
|--------|---------|---------------|-------------|
| Accuracy | 96.7% | 98.5%+ | +1.8% |
| First-time submission confidence | 0.70 | 0.70 | Baseline |
| Repeat submission confidence | 0.70 | 0.85+ | +21% boost |
| Judge fairness score | Not measured | 0.80+ | New metric |
| Credential sharing detection | Manual | Automated | 100% |
| Innovation uniqueness | 8/10 | 10/10 | Market-leading |

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Innovation Architecture](#2-innovation-architecture)
3. [Implementation Roadmap](#3-implementation-roadmap)
4. [Technical Specifications](#4-technical-specifications)
5. [Database Schema](#5-database-schema)
6. [API Design](#6-api-design)
7. [Frontend Integration](#7-frontend-integration)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment Plan](#9-deployment-plan)
10. [Success Metrics](#10-success-metrics)

---

## 1. Current State Analysis

### 1.1 Existing Architecture

**Backend Services:**
- **AI Detection Service** (FastAPI + Python 3.12)
  - Layer 1: Metadata forensics (50-150ms)
  - Layer 2: PRNU + ELA + FFT (2-4s)
  - Layer 3: External API placeholder (1-10s)

- **Competition Service** (FastAPI + Python 3.12)
  - User authentication (JWT)
  - Competition management
  - Submission handling
  - Judge scoring
  - Audit logging

**Frontend:**
- Vue 3 + TypeScript
- 8 views implemented
- Real-time status polling
- Mobile-responsive

**Database:**
- PostgreSQL 15 (async SQLAlchemy)
- 7 core tables
- Complete audit trail infrastructure

### 1.2 Integration Points Identified

**For Camera Reputation:**
- ✅ PRNU extraction already implemented in `layer2_fingerprint.py`
- ✅ Camera metadata extraction in place (make, model)
- ✅ Submission workflow supports async processing
- ⚠️ **Missing**: PRNU storage, comparison logic, trust scoring

**For Judge Consensus:**
- ✅ Score audit logs capture IP, session, user-agent
- ✅ Score data model includes all components
- ✅ Submission-judge relationships established
- ⚠️ **Missing**: Statistical analysis, bias detection, consensus calculation

### 1.3 Dependencies Already Available

**Python Libraries (AI Detection Service):**
```
✅ numpy>=1.24.3          # Array operations
✅ scipy>=1.11.4          # Statistical analysis
✅ Pillow>=10.0.0         # Image processing
✅ opencv-python>=4.8.0   # Computer vision
✅ pywavelets>=1.4.1      # Wavelet transforms (for PRNU)
```

**Python Libraries (Competition Service):**
```
✅ sqlalchemy>=2.0.20     # Async ORM
✅ fastapi>=0.103.1       # API framework
✅ pydantic>=2.3.0        # Data validation
```

### 1.4 Dependencies to Add

**New Requirements:**
```python
# competition-service/requirements.txt additions:
scikit-learn>=1.3.0     # Outlier detection, clustering
pandas>=2.0.0           # Statistical aggregation
geoip2>=4.7.0          # IP geolocation (optional)
```

---

## 2. Innovation Architecture

### 2.1 Camera Reputation System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         SUBMISSION UPLOAD & VERIFICATION                 │
│  (Existing: JPG + RAW → AI Analysis → Verdict)          │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Layer 2: PRNU Extraction     │
        │  (Enhanced to return pattern) │
        └───────────────────────────────┘
                        ↓
        ┌───────────────────────────────────────────┐
        │  NEW: Camera Reputation Manager           │
        │  --------------------------------          │
        │  1. Store PRNU fingerprint in DB          │
        │  2. Check against user's camera history   │
        │  3. Calculate similarity score            │
        │  4. Apply trust boost/penalty             │
        │  5. Update camera profile statistics      │
        └───────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Enhanced Verdict             │
        │  + Camera Trust Score         │
        │  + Reputation Boost Applied   │
        └───────────────────────────────┘
```

### 2.2 Judge Consensus Analysis Architecture

```
┌─────────────────────────────────────────────────────────┐
│            JUDGE SCORING WORKFLOW                        │
│  (Existing: Score Input → Validation → Save)            │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Score Audit Log              │
        │  (Existing: IP, UA, Session)  │
        └───────────────────────────────┘
                        ↓
        ┌───────────────────────────────────────────┐
        │  NEW: Judge Consensus Analyzer            │
        │  --------------------------------          │
        │  1. Calculate score agreement (ICC)       │
        │  2. Identify outlier judges (Z-score)     │
        │  3. Detect bias patterns                  │
        │  4. Update judge profile                  │
        │  5. Flag for review if needed             │
        └───────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  NEW: Credential Sharing      │
        │  Detector (Async)             │
        │  --------------------------------          │
        │  - Analyze IP patterns        │
        │  - Check session anomalies    │
        │  - Geographic consistency     │
        │  - Time gap analysis          │
        └───────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Enhanced Scoring Report      │
        │  + Consensus Verdict          │
        │  + Judge Bias Indicators      │
        │  + Fairness Metrics           │
        └───────────────────────────────┘
```

### 2.3 Data Flow Diagrams

#### Camera Reputation Flow

```
User Submission
      ↓
[Extract PRNU Pattern]
      ↓
   Is New User?
   ↙         ↘
  YES         NO
   ↓           ↓
[Store as    [Compare with
 Baseline]     Historical]
   ↓           ↓
[Trust=0.5]  Match > 0.85?
              ↙         ↘
            YES          NO
             ↓            ↓
         [Trust+15%]  [Trust-10%]
             ↓            ↓
           [Apply to Final Verdict]
```

#### Judge Consensus Flow

```
Judge Submits Score
      ↓
[Store Score + Audit Log]
      ↓
   All Judges Scored?
   ↙         ↘
  NO          YES
   ↓           ↓
[Wait]     [Calculate ICC]
             ↓
         [Identify Outliers]
             ↓
         Z-score > 2.0?
         ↙         ↘
       YES          NO
        ↓            ↓
   [Flag Judge]  [Update Profile]
        ↓            ↓
   [Admin Alert] [Consensus Verdict]
```

---

## 3. Implementation Roadmap

### Phase 1: Foundation (Week 1) - Camera Reputation Database

**Goal:** Create database schema and models for camera reputation

**Tasks:**

1. **Database Migration** (Day 1-2)
   - Create `camera_fingerprints` table
   - Create `camera_trust_profiles` table
   - Create `prnu_comparisons` table
   - Add foreign keys and indexes
   - Test migration rollback

2. **SQLAlchemy Models** (Day 2-3)
   - Define `CameraFingerprint` model
   - Define `CameraTrustProfile` model
   - Define `PRNUComparison` model
   - Add relationships to `Submission` model
   - Unit tests for models

3. **Pydantic Schemas** (Day 3)
   - `CameraFingerprintResponse`
   - `CameraTrustProfileResponse`
   - `PRNUComparisonResponse`
   - Validation rules

**Deliverables:**
- [ ] Database migration scripts
- [ ] SQLAlchemy models with relationships
- [ ] Pydantic schemas with validation
- [ ] Unit tests (80%+ coverage)

**Acceptance Criteria:**
- All tables created successfully
- Foreign keys enforced
- Indexes on `camera_make`, `camera_model`, `submission_id`
- Models can be imported without errors
- All tests pass

---

### Phase 2: PRNU Enhancement (Week 1-2) - Camera Fingerprint Extraction

**Goal:** Enhance PRNU extraction to return full pattern for storage

**Tasks:**

1. **Enhance `layer2_fingerprint.py`** (Day 4-5)
   ```python
   # Current signature:
   def extract_prnu_fingerprint(image_path: str) -> tuple:
       return score, flags, energy

   # New signature:
   def extract_prnu_fingerprint(image_path: str) -> dict:
       return {
           "score": float,
           "flags": dict,
           "energy": float,
           "pattern": np.ndarray,      # NEW: Full PRNU pattern
           "pattern_hash": str,        # NEW: SHA256 hash
           "pattern_bytes": bytes      # NEW: Serialized pattern
       }
   ```

2. **Add PRNU Comparison Function** (Day 5-6)
   ```python
   def compare_prnu_patterns(prnu1: np.ndarray, prnu2: np.ndarray) -> dict:
       """
       Compare two PRNU patterns using multiple metrics
       Returns: similarity_score (0-1), distance, correlation
       """
       # Normalized cross-correlation
       # Euclidean distance
       # Structural similarity (SSIM)
       # Peak signal-to-noise ratio (PSNR)
   ```

3. **Add Pattern Normalization** (Day 6)
   ```python
   def normalize_prnu_for_comparison(prnu: np.ndarray,
                                      iso: int,
                                      aperture: float) -> np.ndarray:
       """
       Normalize PRNU to account for camera settings
       Reduces false negatives from different ISO/aperture
       """
   ```

4. **Unit Tests** (Day 7)
   - Test PRNU extraction consistency
   - Test pattern comparison accuracy
   - Test normalization effectiveness
   - Test with various camera models

**Deliverables:**
- [ ] Enhanced PRNU extraction returning full pattern
- [ ] PRNU comparison function with multiple metrics
- [ ] Pattern normalization for different settings
- [ ] Comprehensive unit tests

**Acceptance Criteria:**
- PRNU patterns consistently extracted (95%+ success rate)
- Comparison accuracy: Same camera > 0.85 similarity
- Comparison accuracy: Different cameras < 0.50 similarity
- Performance: <500ms additional overhead

---

### Phase 3: Camera Reputation Service (Week 2) - Core Logic

**Goal:** Implement camera reputation management service

**Location:** `/src/backend/competition-service/app/services/camera_reputation.py`

**Tasks:**

1. **Create Service Class** (Day 8-9)
   ```python
   class CameraReputationManager:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def store_fingerprint(
           self,
           submission_id: int,
           prnu_data: dict,
           camera_make: str,
           camera_model: str
       ) -> CameraFingerprint:
           """Store PRNU fingerprint after verification"""
           pass

       async def get_or_create_camera_profile(
           self,
           camera_make: str,
           camera_model: str
       ) -> CameraTrustProfile:
           """Get existing or create new camera profile"""
           pass

       async def calculate_trust_score(
           self,
           current_prnu: np.ndarray,
           camera_make: str,
           camera_model: str,
           user_id: int
       ) -> dict:
           """
           Compare with historical fingerprints
           Return: trust_score, similarity, boost, message
           """
           pass

       async def update_profile_stats(
           self,
           camera_make: str,
           camera_model: str,
           verdict: str
       ):
           """Update camera profile statistics"""
           pass
   ```

2. **Implement Trust Scoring Algorithm** (Day 9-10)
   ```python
   def calculate_trust_boost(similarity: float) -> float:
       """
       Similarity thresholds:
       > 0.85: +15% trust boost (strong match)
       0.70-0.85: +5% boost (moderate match)
       0.50-0.70: 0% (neutral)
       < 0.50: -10% penalty (suspicious)
       """
       if similarity > 0.85:
           return 0.15
       elif similarity > 0.70:
           return 0.05
       elif similarity > 0.50:
           return 0.0
       else:
           return -0.10
   ```

3. **Add Fraud Detection** (Day 10)
   ```python
   async def detect_camera_fraud(
       self,
       submission_id: int,
       current_prnu: np.ndarray,
       claimed_camera_make: str,
       claimed_camera_model: str
   ) -> dict:
       """
       Detect if submitted image doesn't match claimed camera
       Check against:
       - User's previous submissions
       - Global camera profile
       - Known camera PRNU ranges
       """
       pass
   ```

4. **Integration Tests** (Day 11)
   - Test fingerprint storage workflow
   - Test trust score calculation
   - Test profile update logic
   - Test fraud detection

**Deliverables:**
- [ ] Complete `CameraReputationManager` service
- [ ] Trust scoring algorithm implemented
- [ ] Fraud detection logic
- [ ] Integration tests (80%+ coverage)

**Acceptance Criteria:**
- Service can store and retrieve fingerprints
- Trust scores calculated correctly
- Profile statistics update properly
- Fraud detection flags mismatches
- All tests pass

---

### Phase 4: Camera Reputation API (Week 2-3) - Endpoints

**Goal:** Expose camera reputation features via REST API

**Location:** `/src/backend/competition-service/app/routes/cameras.py`

**Tasks:**

1. **Create API Router** (Day 12)
   ```python
   from fastapi import APIRouter, Depends
   from app.services.camera_reputation import CameraReputationManager

   router = APIRouter(prefix="/cameras", tags=["cameras"])
   ```

2. **Implement Endpoints** (Day 12-13)

   **POST** `/cameras/fingerprints/{submission_id}`
   ```python
   @router.post("/fingerprints/{submission_id}")
   async def store_camera_fingerprint(
       submission_id: int,
       prnu_data: dict,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Store PRNU fingerprint for verified submission
       Returns: fingerprint_id, trust_score, boost_applied
       """
   ```

   **GET** `/cameras/trust-profile/{camera_make}/{camera_model}`
   ```python
   @router.get("/trust-profile/{camera_make}/{camera_model}")
   async def get_camera_trust_profile(
       camera_make: str,
       camera_model: str,
       db: AsyncSession = Depends(get_db)
   ):
       """
       Returns camera reputation summary:
       - Total submissions
       - Authentic/suspicious/rejected counts
       - Average trust score
       - PRNU pattern stability
       """
   ```

   **GET** `/cameras/user-cameras/{user_id}`
   ```python
   @router.get("/user-cameras/{user_id}")
   async def get_user_camera_history(
       user_id: int,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Returns user's camera history:
       - List of registered cameras (make, model)
       - Submission count per camera
       - Trust scores
       - Last used dates
       """
   ```

   **GET** `/cameras/comparison/{fingerprint_id1}/{fingerprint_id2}`
   ```python
   @router.get("/comparison/{fingerprint_id1}/{fingerprint_id2}")
   async def compare_fingerprints(
       fingerprint_id1: int,
       fingerprint_id2: int,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Direct PRNU pattern comparison
       Returns: similarity_score, distance_metrics, verdict
       """
   ```

   **GET** `/cameras/fraud-check/{submission_id}`
   ```python
   @router.get("/fraud-check/{submission_id}")
   async def check_camera_fraud(
       submission_id: int,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Check if submission's PRNU matches claimed camera
       Returns: fraud_likelihood, explanation, evidence
       Admin/Judge only
       """
   ```

3. **Register Router** (Day 13)
   ```python
   # In main.py:
   from app.routes import cameras
   app.include_router(cameras.router, prefix="/api/v1")
   ```

4. **API Tests** (Day 13-14)
   - Test endpoint authentication
   - Test response schemas
   - Test error handling
   - Test rate limiting

**Deliverables:**
- [ ] Complete camera reputation API routes
- [ ] OpenAPI documentation auto-generated
- [ ] API integration tests
- [ ] Postman collection for testing

**Acceptance Criteria:**
- All endpoints return correct status codes
- Response schemas validate properly
- Authentication enforced
- Error messages clear and helpful
- API documentation complete

---

### Phase 5: Judge Consensus Database (Week 3) - Foundation

**Goal:** Create database schema for judge consensus analysis

**Tasks:**

1. **Database Migration** (Day 15)
   - Create `judge_scoring_profiles` table
   - Create `judge_consensus_analysis` table
   - Create `credential_sharing_detection` table
   - Add indexes for performance
   - Test migration

2. **SQLAlchemy Models** (Day 15-16)
   - Define `JudgeScoringProfile` model
   - Define `JudgeConsensusAnalysis` model
   - Define `CredentialSharingDetection` model
   - Add relationships
   - Unit tests

3. **Pydantic Schemas** (Day 16)
   - `JudgeProfileResponse`
   - `ConsensusAnalysisResponse`
   - `CredentialSharingAlertResponse`

**Deliverables:**
- [ ] Database migration scripts
- [ ] SQLAlchemy models
- [ ] Pydantic schemas
- [ ] Unit tests

**Acceptance Criteria:**
- Tables created with proper constraints
- Indexes on `judge_id`, `competition_id`, `ip_address`
- Models import without errors
- All tests pass

---

### Phase 6: Judge Consensus Service (Week 3-4) - Core Logic

**Goal:** Implement statistical analysis for judge consensus

**Location:** `/src/backend/competition-service/app/services/judge_consensus.py`

**Tasks:**

1. **Create Service Class** (Day 17-18)
   ```python
   from sklearn.ensemble import IsolationForest
   import numpy as np
   import pandas as pd

   class JudgeConsensusAnalyzer:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def analyze_submission_scores(
           self,
           submission_id: int
       ) -> dict:
           """
           Calculate score agreement for submission
           Returns: ICC, outlier_judges, consensus_verdict
           """
           pass

       async def build_judge_profile(
           self,
           judge_id: int,
           competition_id: int
       ) -> JudgeScoringProfile:
           """
           Aggregate judge's scoring patterns
           Calculate: bias, consistency, variance
           """
           pass

       async def detect_biased_judges(
           self,
           competition_id: int
       ) -> list:
           """
           Identify judges with significant bias
           Z-score > 2.0 from competition mean
           """
           pass

       async def detect_credential_sharing(
           self,
           competition_id: int
       ) -> list:
           """
           Analyze audit logs for sharing patterns
           Check: IP diversity, session timing, geo-location
           """
           pass
   ```

2. **Implement Statistical Methods** (Day 18-19)

   **Intraclass Correlation Coefficient (ICC)**
   ```python
   def calculate_icc(scores_matrix: np.ndarray) -> float:
       """
       Measures agreement among judges
       ICC(2,1) for absolute agreement
       Range: 0-1 (higher = better agreement)
       """
       # Implementation using scipy.stats
   ```

   **Judge Bias Detection (Z-Score)**
   ```python
   def calculate_judge_bias(
       judge_scores: list,
       competition_mean: float,
       competition_std: float
   ) -> dict:
       """
       Z-score = (judge_mean - competition_mean) / std
       Z > 2.0: Significantly lenient
       Z < -2.0: Significantly harsh
       """
   ```

   **Score Consistency (Coefficient of Variation)**
   ```python
   def calculate_consistency(judge_scores: list) -> float:
       """
       CV = std_dev / mean
       Lower CV = more consistent scoring
       """
   ```

   **Outlier Detection (Isolation Forest)**
   ```python
   def detect_score_outliers(
       all_scores: list,
       threshold: float = 0.1
   ) -> list:
       """
       Use Isolation Forest to detect anomalous scores
       Returns: list of outlier indices
       """
       clf = IsolationForest(contamination=threshold)
       clf.fit(all_scores)
       return clf.predict(all_scores)
   ```

3. **Implement Credential Sharing Detection** (Day 19-20)
   ```python
   async def analyze_ip_patterns(
       self,
       audit_logs: list
   ) -> dict:
       """
       Detect suspicious IP patterns:
       - Too many unique IPs for one judge
       - Geographically impossible location changes
       - IP sharing across judges
       """
       pass

   async def analyze_session_timing(
       self,
       audit_logs: list
   ) -> dict:
       """
       Detect suspicious timing:
       - Multiple sessions active simultaneously
       - Time gaps too short (physically impossible)
       - Identical scoring patterns
       """
       pass
   ```

4. **Integration Tests** (Day 20-21)
   - Test ICC calculation
   - Test bias detection
   - Test consistency scoring
   - Test credential sharing detection

**Deliverables:**
- [ ] Complete `JudgeConsensusAnalyzer` service
- [ ] Statistical methods implemented
- [ ] Credential sharing detector
- [ ] Integration tests (80%+ coverage)

**Acceptance Criteria:**
- ICC calculated correctly
- Bias detection flags outliers (Z > 2.0)
- Consistency scores accurate
- Credential sharing patterns detected
- All tests pass

---

### Phase 7: Judge Consensus API (Week 4) - Endpoints

**Goal:** Expose judge consensus features via REST API

**Location:** `/src/backend/competition-service/app/routes/judges.py`

**Tasks:**

1. **Create API Router** (Day 22)
   ```python
   from fastapi import APIRouter, Depends
   from app.services.judge_consensus import JudgeConsensusAnalyzer

   router = APIRouter(prefix="/judges", tags=["judges"])
   ```

2. **Implement Endpoints** (Day 22-23)

   **GET** `/judges/profile/{judge_id}`
   ```python
   @router.get("/profile/{judge_id}")
   async def get_judge_profile(
       judge_id: int,
       competition_id: Optional[int] = None,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Returns judge's scoring profile:
       - Bias score (-1 to +1)
       - Consistency score (0-1)
       - Submission count
       - Comparison to other judges
       """
   ```

   **GET** `/judges/competition/{competition_id}/consensus`
   ```python
   @router.get("/competition/{competition_id}/consensus")
   async def get_competition_consensus(
       competition_id: int,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Full consensus analysis for competition:
       - Score agreement (ICC)
       - Biased judges list
       - Consensus verdicts per submission
       - Fairness metrics
       """
   ```

   **GET** `/submissions/{submission_id}/consensus`
   ```python
   @router.get("/submissions/{submission_id}/consensus")
   async def get_submission_consensus(
       submission_id: int,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Consensus for specific submission:
       - Score agreement ratio
       - Outlier judges
       - Consensus verdict
       - Statistical confidence
       """
   ```

   **GET** `/admin/credential-sharing/{competition_id}`
   ```python
   @router.get("/admin/credential-sharing/{competition_id}")
   async def detect_credential_sharing(
       competition_id: int,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Credential sharing detection report (Admin only):
       - Judges with suspicious IP patterns
       - Session anomalies
       - Geographic inconsistencies
       - Risk scores
       """
   ```

   **POST** `/admin/judge-review/{judge_id}`
   ```python
   @router.post("/admin/judge-review/{judge_id}")
   async def create_judge_review(
       judge_id: int,
       review_data: JudgeReviewCreate,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """
       Flag judge for investigation (Admin only):
       - Review notes
       - Action taken (warning, suspension, etc.)
       - Investigation status
       """
   ```

3. **Register Router** (Day 23)
   ```python
   # In main.py:
   from app.routes import judges
   app.include_router(judges.router, prefix="/api/v1")
   ```

4. **API Tests** (Day 23-24)
   - Test endpoint authorization (admin-only)
   - Test response schemas
   - Test statistical accuracy
   - Test error handling

**Deliverables:**
- [ ] Complete judge consensus API routes
- [ ] OpenAPI documentation
- [ ] API integration tests
- [ ] Admin permission enforcement

**Acceptance Criteria:**
- All endpoints secured properly
- Statistical calculations accurate
- Admin-only endpoints enforced
- Response schemas validate
- API documentation complete

---

### Phase 8: Integration with Existing Workflows (Week 5)

**Goal:** Integrate camera reputation and judge consensus into existing submission/scoring flows

**Tasks:**

1. **Enhance Submission Verification Workflow** (Day 25-26)

   **Location:** `/src/backend/competition-service/app/routes/submissions.py`

   ```python
   # After AI analysis completes:
   async def process_verification_result(
       submission_id: int,
       ai_result: dict,
       db: AsyncSession
   ):
       # Existing: Update submission with AI verdict
       submission = await db.get(Submission, submission_id)
       submission.verification_verdict = ai_result["verdict"]
       submission.verification_confidence = ai_result["confidence"]

       # NEW: Store PRNU fingerprint
       if "prnu_data" in ai_result:
           camera_rep = CameraReputationManager(db)
           fingerprint = await camera_rep.store_fingerprint(
               submission_id=submission_id,
               prnu_data=ai_result["prnu_data"],
               camera_make=submission.camera_make,
               camera_model=submission.camera_model
           )

           # NEW: Calculate trust boost
           trust_result = await camera_rep.calculate_trust_score(
               current_prnu=ai_result["prnu_data"]["pattern"],
               camera_make=submission.camera_make,
               camera_model=submission.camera_model,
               user_id=submission.user_id
           )

           # NEW: Apply trust boost to confidence
           submission.camera_trust_score = trust_result["trust_score"]
           submission.verification_confidence += trust_result["boost"]
           submission.verification_confidence = min(1.0, submission.verification_confidence)

       await db.commit()
   ```

2. **Enhance Judge Scoring Workflow** (Day 26-27)

   **Location:** `/src/backend/competition-service/app/routes/scores.py`

   ```python
   # After score is saved:
   @router.post("/{submission_id}")
   async def create_score(
       submission_id: int,
       score_data: ScoreCreate,
       request: Request,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_user),
   ):
       # Existing: Create score + audit log
       new_score = Score(...)
       db.add(new_score)

       audit_log = ScoreAuditLog(...)
       db.add(audit_log)

       await db.commit()

       # NEW: Trigger consensus analysis (async background task)
       from app.services.judge_consensus import JudgeConsensusAnalyzer
       consensus = JudgeConsensusAnalyzer(db)

       # Check if all assigned judges have scored
       submission = await db.get(Submission, submission_id)
       competition_id = submission.competition_id

       judge_count = await db.scalar(
           select(func.count(JudgeAssignment.id))
           .where(
               JudgeAssignment.competition_id == competition_id,
               JudgeAssignment.is_active == True
           )
       )

       score_count = await db.scalar(
           select(func.count(Score.id))
           .where(Score.submission_id == submission_id)
       )

       if score_count == judge_count:
           # All judges scored - run consensus analysis
           consensus_result = await consensus.analyze_submission_scores(submission_id)

           # Store consensus analysis
           consensus_record = JudgeConsensusAnalysis(
               competition_id=competition_id,
               submission_id=submission_id,
               judge_count=judge_count,
               score_agreement_ratio=consensus_result["icc"],
               outlier_judges=consensus_result["outliers"],
               consensus_verdict=consensus_result["verdict"],
               confidence_level=consensus_result["confidence"]
           )
           db.add(consensus_record)
           await db.commit()

       # NEW: Update judge profile (async)
       await consensus.build_judge_profile(current_user.id, competition_id)

       return new_score
   ```

3. **Add Background Jobs** (Day 27)

   **Location:** `/src/backend/competition-service/app/tasks/`

   ```python
   # tasks/camera_reputation.py
   async def update_camera_profiles_daily():
       """
       Daily job: Update camera profile statistics
       Recalculate trust scores based on new submissions
       """
       pass

   # tasks/judge_analysis.py
   async def analyze_judge_patterns_hourly():
       """
       Hourly job: Check for credential sharing patterns
       Flag suspicious activity for admin review
       """
       pass

   async def generate_consensus_reports():
       """
       End of competition: Generate full consensus report
       Calculate final fairness metrics
       """
       pass
   ```

4. **Integration Tests** (Day 28)
   - Test full submission workflow with camera reputation
   - Test full scoring workflow with consensus analysis
   - Test background job execution
   - Test error handling and rollback

**Deliverables:**
- [ ] Enhanced submission verification workflow
- [ ] Enhanced judge scoring workflow
- [ ] Background job definitions
- [ ] End-to-end integration tests

**Acceptance Criteria:**
- Camera reputation integrated seamlessly
- Judge consensus calculated automatically
- Background jobs execute successfully
- No performance degradation
- All tests pass

---

### Phase 9: Frontend Integration (Week 5-6)

**Goal:** Display camera reputation and judge consensus in UI

**Tasks:**

1. **Submission Details View** (Day 29-30)

   **Location:** `/src/frontend/src/views/MySubmissions.vue`

   Add camera reputation display:
   ```vue
   <template>
     <div class="camera-reputation-card">
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

       <div v-if="submission.reputation_boost > 0" class="boost-indicator">
         <Alert>
           <AlertTitle>Trust Boost Applied</AlertTitle>
           <AlertDescription>
             +{{ (submission.reputation_boost * 100).toFixed(0) }}% confidence boost
             from verified camera history
           </AlertDescription>
         </Alert>
       </div>
     </div>
   </template>
   ```

2. **Judge Dashboard Enhancements** (Day 30-31)

   **Location:** `/src/frontend/src/views/JudgeDashboard.vue`

   Add judge profile card:
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
             <div class="bias-meter">
               <meter
                 :value="judgeProfile.bias_score + 1"
                 min="0"
                 max="2"
                 low="0.5"
                 high="1.5"
                 optimum="1.0"
               ></meter>
               <span>{{ judgeProfile.bias_score.toFixed(2) }}</span>
             </div>
             <p class="text-xs text-muted">
               {{ getBiasLabel(judgeProfile.bias_score) }}
             </p>
           </div>

           <div class="stat">
             <label>Consistency</label>
             <progress :value="judgeProfile.consistency_score" max="1.0"></progress>
             <span>{{ (judgeProfile.consistency_score * 100).toFixed(0) }}%</span>
           </div>

           <div class="stat">
             <label>Submissions Scored</label>
             <span class="text-2xl">{{ judgeProfile.submission_count }}</span>
           </div>
         </div>
       </CardContent>
     </Card>
   </template>

   <script setup lang="ts">
   function getBiasLabel(bias: number): string {
     if (bias > 0.3) return "You tend to score higher than average"
     if (bias < -0.3) return "You tend to score lower than average"
     return "Your scores are well-calibrated"
   }
   </script>
   ```

3. **Score Submission View** (Day 31-32)

   **Location:** `/src/frontend/src/views/ScoreSubmission.vue`

   Add consensus indicators:
   ```vue
   <template>
     <div class="consensus-panel">
       <h4>Other Judges' Scores</h4>
       <div v-if="consensusData.icc > 0" class="agreement-indicator">
         <Badge :variant="getAgreementVariant(consensusData.icc)">
           Agreement: {{ getAgreementLabel(consensusData.icc) }}
         </Badge>
         <p class="text-sm">
           ICC: {{ consensusData.icc.toFixed(2) }}
         </p>
       </div>

       <div class="score-distribution">
         <canvas ref="scoreChart"></canvas>
       </div>

       <Alert v-if="consensusData.outliers.includes(currentUser.id)" variant="warning">
         <AlertTitle>Your score differs significantly</AlertTitle>
         <AlertDescription>
           Consider reviewing your rating - other judges scored differently
         </AlertDescription>
       </Alert>
     </div>
   </template>

   <script setup lang="ts">
   import { Chart } from 'chart.js'

   function getAgreementLabel(icc: number): string {
     if (icc > 0.9) return "Excellent"
     if (icc > 0.75) return "Good"
     if (icc > 0.5) return "Fair"
     return "Poor"
   }
   </script>
   ```

4. **Admin Dashboard** (Day 32-33)

   **Location:** `/src/frontend/src/views/AdminPanel.vue`

   Add monitoring sections:
   ```vue
   <template>
     <div class="admin-dashboard">
       <!-- Camera Reputation Monitoring -->
       <Card>
         <CardHeader>
           <CardTitle>Camera Trust Monitoring</CardTitle>
         </CardHeader>
         <CardContent>
           <div class="camera-stats">
             <div class="stat-card">
               <h4>Total Registered Cameras</h4>
               <span class="stat-value">{{ cameraStats.total_cameras }}</span>
             </div>
             <div class="stat-card">
               <h4>High Trust Cameras (>0.8)</h4>
               <span class="stat-value">{{ cameraStats.high_trust_count }}</span>
             </div>
             <div class="stat-card">
               <h4>Flagged for Fraud</h4>
               <span class="stat-value text-red-600">
                 {{ cameraStats.fraud_flags }}
               </span>
             </div>
           </div>

           <DataTable :data="suspiciousCameras" :columns="cameraColumns" />
         </CardContent>
       </Card>

       <!-- Judge Consensus Monitoring -->
       <Card>
         <CardHeader>
           <CardTitle>Judge Performance Monitoring</CardTitle>
         </CardHeader>
         <CardContent>
           <div class="judge-stats">
             <div class="stat-card">
               <h4>Average Agreement (ICC)</h4>
               <span class="stat-value">{{ judgeStats.avg_icc.toFixed(2) }}</span>
             </div>
             <div class="stat-card">
               <h4>Biased Judges Detected</h4>
               <span class="stat-value text-yellow-600">
                 {{ judgeStats.biased_count }}
               </span>
             </div>
             <div class="stat-card">
               <h4>Credential Sharing Alerts</h4>
               <span class="stat-value text-red-600">
                 {{ judgeStats.sharing_alerts }}
               </span>
             </div>
           </div>

           <DataTable :data="flaggedJudges" :columns="judgeColumns" />
         </CardContent>
       </Card>
     </div>
   </template>
   ```

5. **API Client Updates** (Day 33)

   **Location:** `/src/frontend/src/api/`

   ```typescript
   // api/cameras.ts
   export const camerasApi = {
     async getCameraTrustProfile(make: string, model: string) {
       return client.get(`/cameras/trust-profile/${make}/${model}`)
     },

     async getUserCameraHistory(userId: number) {
       return client.get(`/cameras/user-cameras/${userId}`)
     },

     async checkCameraFraud(submissionId: number) {
       return client.get(`/cameras/fraud-check/${submissionId}`)
     }
   }

   // api/judges.ts
   export const judgesApi = {
     async getJudgeProfile(judgeId: number, competitionId?: number) {
       const params = competitionId ? `?competition_id=${competitionId}` : ''
       return client.get(`/judges/profile/${judgeId}${params}`)
     },

     async getCompetitionConsensus(competitionId: number) {
       return client.get(`/judges/competition/${competitionId}/consensus`)
     },

     async getSubmissionConsensus(submissionId: number) {
       return client.get(`/submissions/${submissionId}/consensus`)
     },

     async detectCredentialSharing(competitionId: number) {
       return client.get(`/admin/credential-sharing/${competitionId}`)
     }
   }
   ```

**Deliverables:**
- [ ] Enhanced submission details view
- [ ] Judge profile dashboard
- [ ] Consensus indicators in scoring
- [ ] Admin monitoring dashboard
- [ ] API client methods

**Acceptance Criteria:**
- Camera trust scores displayed correctly
- Judge profiles show accurate statistics
- Consensus indicators functional
- Admin dashboard shows real-time data
- UI responsive and accessible

---

### Phase 10: Testing & Quality Assurance (Week 6)

**Goal:** Comprehensive testing of all new features

**Tasks:**

1. **Unit Tests** (Day 34)
   - Camera reputation service tests
   - Judge consensus service tests
   - Statistical method tests
   - API endpoint tests

2. **Integration Tests** (Day 35)
   - Full submission workflow with camera reputation
   - Full scoring workflow with consensus
   - Background job execution
   - Database transaction integrity

3. **E2E Tests** (Day 36)
   - User submits photo → camera reputation displayed
   - Judge scores submission → consensus calculated
   - Admin views monitoring dashboard
   - Fraud detection alerts triggered

4. **Performance Testing** (Day 37)
   - PRNU comparison performance (<500ms)
   - Statistical analysis performance (<200ms)
   - Database query optimization
   - API response time benchmarks

5. **Security Testing** (Day 38)
   - API authorization enforcement
   - SQL injection prevention
   - XSS prevention
   - Rate limiting effectiveness

6. **User Acceptance Testing** (Day 39)
   - Test with real judges
   - Gather feedback on UI/UX
   - Validate statistical accuracy
   - Check for edge cases

7. **Bug Fixes & Polish** (Day 40-42)
   - Fix identified issues
   - Improve error messages
   - Enhance user feedback
   - Documentation updates

**Deliverables:**
- [ ] Comprehensive test suite (90%+ coverage)
- [ ] Performance benchmarks documented
- [ ] Security audit passed
- [ ] UAT feedback incorporated
- [ ] All critical bugs fixed

**Acceptance Criteria:**
- All tests pass
- Code coverage >90%
- Performance targets met
- No critical security vulnerabilities
- Positive UAT feedback

---

## 4. Technical Specifications

### 4.1 Camera Reputation Algorithms

#### PRNU Pattern Extraction
```python
def extract_prnu_pattern(image: np.ndarray) -> np.ndarray:
    """
    Extract Photo Response Non-Uniformity pattern

    Steps:
    1. Convert to grayscale
    2. Apply DWT (db8 wavelet, level 4)
    3. Soft threshold high-frequency coefficients
    4. Reconstruct denoised image
    5. PRNU = Original - Denoised
    6. Normalize to [-1, 1] range

    Returns: PRNU pattern (H x W numpy array)
    """
```

#### PRNU Comparison Metrics
```python
def compare_prnu_patterns(prnu1: np.ndarray, prnu2: np.ndarray) -> dict:
    """
    Multiple comparison metrics for robustness

    Metrics:
    1. Normalized Cross-Correlation (NCC)
       - Measures linear similarity
       - Range: [-1, 1], higher = more similar

    2. Peak Signal-to-Noise Ratio (PSNR)
       - Measures reconstruction quality
       - Higher PSNR = more similar

    3. Structural Similarity Index (SSIM)
       - Perceptual similarity
       - Range: [0, 1], higher = more similar

    4. Euclidean Distance
       - L2 norm of difference
       - Lower distance = more similar

    Returns: {
        "ncc": float,
        "psnr": float,
        "ssim": float,
        "euclidean_distance": float,
        "overall_similarity": float  # Weighted average
    }
    """
```

#### Trust Score Calculation
```python
def calculate_trust_score(
    similarity_metrics: dict,
    camera_history: dict,
    submission_verdict: str
) -> float:
    """
    Calculate camera trust score based on:
    - PRNU similarity to historical patterns
    - Camera submission history (count, success rate)
    - Submission verdict consistency

    Formula:
    trust_score = (
        similarity_weight * overall_similarity +
        history_weight * (authentic_count / total_count) +
        consistency_weight * verdict_consistency
    )

    Weights: similarity=0.5, history=0.3, consistency=0.2

    Returns: Trust score [0.0, 1.0]
    """
```

### 4.2 Judge Consensus Algorithms

#### Intraclass Correlation Coefficient (ICC)
```python
def calculate_icc_2_1(scores_matrix: np.ndarray) -> float:
    """
    ICC(2,1) - Two-way random effects, absolute agreement

    Formula:
    ICC = (MS_rows - MS_error) / (MS_rows + (k-1)*MS_error + k*(MS_cols - MS_error)/n)

    Where:
    - MS_rows: Mean square between submissions
    - MS_cols: Mean square between judges
    - MS_error: Mean square error
    - k: Number of judges
    - n: Number of submissions

    Interpretation:
    - < 0.5: Poor agreement
    - 0.5-0.75: Fair agreement
    - 0.75-0.9: Good agreement
    - > 0.9: Excellent agreement

    Returns: ICC value [0, 1]
    """
```

#### Judge Bias Detection (Z-Score)
```python
def detect_judge_bias(
    judge_scores: list,
    competition_mean: float,
    competition_std: float
) -> dict:
    """
    Calculate Z-score for judge's average score

    Formula:
    z_score = (judge_mean - competition_mean) / competition_std

    Interpretation:
    - |z| < 1.5: Normal range
    - 1.5 < |z| < 2.0: Slight bias, monitor
    - 2.0 < |z| < 3.0: Significant bias, flag
    - |z| > 3.0: Extreme bias, investigate

    Returns: {
        "z_score": float,
        "judge_mean": float,
        "deviation": float,
        "bias_category": str,  # harsh/normal/lenient
        "severity": str  # low/medium/high
    }
    """
```

#### Credential Sharing Risk Score
```python
def calculate_sharing_risk(
    ip_count: int,
    session_count: int,
    time_gaps: list,
    geo_distances: list
) -> dict:
    """
    Calculate risk score for credential sharing

    Risk factors:
    1. IP diversity (many IPs = higher risk)
    2. Session overlap (simultaneous = higher risk)
    3. Impossible time gaps (< 1 hour between distant locations)
    4. Geographic inconsistencies (>1000km in < 1 hour)

    Formula:
    risk_score = (
        0.4 * ip_diversity_score +
        0.3 * session_overlap_score +
        0.2 * time_gap_score +
        0.1 * geo_consistency_score
    )

    Returns: {
        "risk_score": float [0, 1],
        "risk_level": str,  # low/medium/high
        "factors": list,
        "recommendation": str
    }
    """
```

---

## 5. Database Schema

### 5.1 Camera Reputation Tables

#### `camera_fingerprints`
```sql
CREATE TABLE camera_fingerprints (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_make VARCHAR(100) NOT NULL,
    camera_model VARCHAR(100) NOT NULL,
    prnu_signature BYTEA NOT NULL,  -- Binary PRNU pattern (compressed)
    prnu_energy FLOAT NOT NULL,
    prnu_hash VARCHAR(64) NOT NULL,  -- SHA256 hash
    similarity_to_profile FLOAT,
    trust_boost_applied FLOAT DEFAULT 0.0,
    capture_context JSONB,  -- {iso, aperture, shutter, etc.}
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_camera_fingerprints_submission ON camera_fingerprints(submission_id);
CREATE INDEX idx_camera_fingerprints_user ON camera_fingerprints(user_id);
CREATE INDEX idx_camera_fingerprints_camera ON camera_fingerprints(camera_make, camera_model);
CREATE INDEX idx_camera_fingerprints_hash ON camera_fingerprints(prnu_hash);
```

#### `camera_trust_profiles`
```sql
CREATE TABLE camera_trust_profiles (
    id SERIAL PRIMARY KEY,
    camera_make VARCHAR(100) NOT NULL,
    camera_model VARCHAR(100) NOT NULL,
    total_submissions INTEGER DEFAULT 0,
    authentic_count INTEGER DEFAULT 0,
    suspicious_count INTEGER DEFAULT 0,
    ai_generated_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    avg_trust_score FLOAT DEFAULT 0.5,
    prnu_pattern_stability FLOAT DEFAULT 0.0,  -- Std dev of similarities
    avg_prnu_energy FLOAT,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(camera_make, camera_model)
);

CREATE INDEX idx_camera_trust_profiles_camera ON camera_trust_profiles(camera_make, camera_model);
CREATE INDEX idx_camera_trust_profiles_trust_score ON camera_trust_profiles(avg_trust_score);
```

#### `prnu_comparisons`
```sql
CREATE TABLE prnu_comparisons (
    id SERIAL PRIMARY KEY,
    fingerprint1_id INTEGER NOT NULL REFERENCES camera_fingerprints(id) ON DELETE CASCADE,
    fingerprint2_id INTEGER NOT NULL REFERENCES camera_fingerprints(id) ON DELETE CASCADE,
    ncc_score FLOAT NOT NULL,  -- Normalized Cross-Correlation
    psnr_score FLOAT NOT NULL,  -- Peak Signal-to-Noise Ratio
    ssim_score FLOAT NOT NULL,  -- Structural Similarity Index
    euclidean_distance FLOAT NOT NULL,
    overall_similarity FLOAT NOT NULL,  -- Weighted average
    comparison_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fingerprint1_id, fingerprint2_id)
);

CREATE INDEX idx_prnu_comparisons_fp1 ON prnu_comparisons(fingerprint1_id);
CREATE INDEX idx_prnu_comparisons_fp2 ON prnu_comparisons(fingerprint2_id);
CREATE INDEX idx_prnu_comparisons_similarity ON prnu_comparisons(overall_similarity);
```

### 5.2 Judge Consensus Tables

#### `judge_scoring_profiles`
```sql
CREATE TABLE judge_scoring_profiles (
    id SERIAL PRIMARY KEY,
    judge_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competition_id INTEGER REFERENCES competitions(id) ON DELETE CASCADE,
    submission_count INTEGER DEFAULT 0,
    avg_composition_score FLOAT,
    avg_technical_score FLOAT,
    avg_creativity_score FLOAT,
    avg_overall_score FLOAT,
    score_std_dev FLOAT,  -- Consistency metric
    z_score FLOAT,  -- Bias metric
    bias_category VARCHAR(50),  -- harsh/normal/lenient
    consistency_score FLOAT,  -- Coefficient of variation
    comment_length_avg FLOAT,
    outlier_count INTEGER DEFAULT 0,  -- How many times flagged as outlier
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(judge_id, competition_id)
);

CREATE INDEX idx_judge_scoring_profiles_judge ON judge_scoring_profiles(judge_id);
CREATE INDEX idx_judge_scoring_profiles_competition ON judge_scoring_profiles(competition_id);
CREATE INDEX idx_judge_scoring_profiles_z_score ON judge_scoring_profiles(z_score);
```

#### `judge_consensus_analysis`
```sql
CREATE TABLE judge_consensus_analysis (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    judge_count INTEGER NOT NULL,
    icc_score FLOAT,  -- Intraclass Correlation Coefficient
    score_agreement_ratio FLOAT,  -- 0-1
    outlier_judge_ids INTEGER[],  -- Array of judge IDs
    consensus_verdict VARCHAR(50),  -- AUTHENTIC/SUSPICIOUS/NEEDS_REVIEW
    consensus_confidence FLOAT,
    flagged_for_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(competition_id, submission_id)
);

CREATE INDEX idx_judge_consensus_competition ON judge_consensus_analysis(competition_id);
CREATE INDEX idx_judge_consensus_submission ON judge_consensus_analysis(submission_id);
CREATE INDEX idx_judge_consensus_flagged ON judge_consensus_analysis(flagged_for_review);
```

#### `credential_sharing_detection`
```sql
CREATE TABLE credential_sharing_detection (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    judge_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    unique_ip_count INTEGER,
    unique_session_count INTEGER,
    unique_user_agent_count INTEGER,
    ip_addresses TEXT[],  -- Array of IPs
    session_ids TEXT[],
    time_gap_anomalies JSONB,  -- [{from, to, gap_seconds, expected_min}]
    geographic_inconsistencies JSONB,  -- [{ip1, ip2, distance_km, time_seconds}]
    risk_score FLOAT,  -- 0-1
    risk_level VARCHAR(50),  -- low/medium/high
    risk_factors TEXT[],
    alert_triggered BOOLEAN DEFAULT FALSE,
    investigation_status VARCHAR(50) DEFAULT 'pending',  -- pending/reviewing/resolved
    investigation_notes TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_credential_sharing_competition ON credential_sharing_detection(competition_id);
CREATE INDEX idx_credential_sharing_judge ON credential_sharing_detection(judge_id);
CREATE INDEX idx_credential_sharing_risk ON credential_sharing_detection(risk_score);
CREATE INDEX idx_credential_sharing_status ON credential_sharing_detection(investigation_status);
```

### 5.3 Database Migration Scripts

**Migration Up:**
```sql
-- Migration: 001_add_camera_reputation_tables.sql

BEGIN;

-- Create camera_fingerprints table
CREATE TABLE camera_fingerprints (
    -- (schema from above)
);

-- Create indexes
CREATE INDEX idx_camera_fingerprints_submission ON camera_fingerprints(submission_id);
-- (other indexes)

-- Create camera_trust_profiles table
CREATE TABLE camera_trust_profiles (
    -- (schema from above)
);

-- Modify submissions table
ALTER TABLE submissions
ADD COLUMN prnu_fingerprint_id INTEGER REFERENCES camera_fingerprints(id),
ADD COLUMN prnu_extracted_energy FLOAT,
ADD COLUMN camera_trust_score FLOAT DEFAULT 0.5;

COMMIT;
```

**Migration Down:**
```sql
-- Rollback: 001_add_camera_reputation_tables.sql

BEGIN;

ALTER TABLE submissions
DROP COLUMN IF EXISTS prnu_fingerprint_id,
DROP COLUMN IF EXISTS prnu_extracted_energy,
DROP COLUMN IF EXISTS camera_trust_score;

DROP TABLE IF EXISTS prnu_comparisons CASCADE;
DROP TABLE IF EXISTS camera_trust_profiles CASCADE;
DROP TABLE IF EXISTS camera_fingerprints CASCADE;

COMMIT;
```

---

## 6. API Design

### 6.1 Camera Reputation Endpoints

**Base URL:** `https://avar.studio/api/v1/cameras`

#### POST /fingerprints/{submission_id}
Store PRNU fingerprint for verified submission

**Request:**
```json
{
  "prnu_signature": "base64_encoded_binary_data",
  "prnu_energy": 0.00023,
  "prnu_hash": "sha256_hash_string",
  "capture_context": {
    "iso": 400,
    "aperture": 2.8,
    "shutter_speed": "1/125",
    "focal_length": 85
  }
}
```

**Response 201:**
```json
{
  "fingerprint_id": 123,
  "camera_make": "Canon",
  "camera_model": "EOS R6",
  "trust_score": 0.75,
  "trust_boost_applied": 0.15,
  "message": "Matches your registered Canon EOS R6 (used 5 times)"
}
```

#### GET /trust-profile/{camera_make}/{camera_model}
Get camera reputation summary

**Response 200:**
```json
{
  "camera_make": "Canon",
  "camera_model": "EOS R6",
  "total_submissions": 150,
  "authentic_count": 140,
  "suspicious_count": 8,
  "ai_generated_count": 2,
  "avg_trust_score": 0.82,
  "prnu_pattern_stability": 0.91,
  "avg_prnu_energy": 0.00025,
  "last_updated": "2026-02-20T10:30:00Z"
}
```

#### GET /user-cameras/{user_id}
Get user's camera history

**Response 200:**
```json
{
  "user_id": 42,
  "cameras": [
    {
      "camera_make": "Canon",
      "camera_model": "EOS R6",
      "submission_count": 12,
      "authentic_count": 11,
      "suspicious_count": 1,
      "avg_trust_score": 0.85,
      "first_used": "2025-11-15T08:00:00Z",
      "last_used": "2026-02-19T14:30:00Z"
    },
    {
      "camera_make": "Sony",
      "camera_model": "A7 IV",
      "submission_count": 3,
      "authentic_count": 3,
      "suspicious_count": 0,
      "avg_trust_score": 0.70,
      "first_used": "2026-01-10T12:00:00Z",
      "last_used": "2026-01-25T09:15:00Z"
    }
  ]
}
```

### 6.2 Judge Consensus Endpoints

**Base URL:** `https://avar.studio/api/v1/judges`

#### GET /profile/{judge_id}
Get judge's scoring profile

**Query Parameters:**
- `competition_id` (optional): Filter by competition

**Response 200:**
```json
{
  "judge_id": 15,
  "competition_id": 8,
  "submission_count": 45,
  "avg_composition_score": 7.2,
  "avg_technical_score": 6.8,
  "avg_creativity_score": 7.5,
  "avg_overall_score": 7.15,
  "score_std_dev": 1.2,
  "z_score": -0.35,
  "bias_category": "normal",
  "consistency_score": 0.83,
  "comment_length_avg": 125,
  "outlier_count": 2,
  "performance_summary": "Well-calibrated judge with consistent scoring patterns"
}
```

#### GET /competition/{competition_id}/consensus
Full consensus analysis for competition

**Response 200:**
```json
{
  "competition_id": 8,
  "judge_count": 5,
  "total_submissions": 120,
  "scored_submissions": 115,
  "avg_icc_score": 0.78,
  "icc_interpretation": "Good agreement",
  "biased_judges": [
    {
      "judge_id": 22,
      "z_score": 2.3,
      "bias_category": "lenient",
      "deviation": 1.5,
      "flagged": true
    }
  ],
  "consensus_verdicts": {
    "authentic": 98,
    "suspicious": 15,
    "needs_review": 2
  },
  "fairness_score": 0.82,
  "recommendations": [
    "Review judge #22 for leniency bias",
    "Consider additional calibration for judges"
  ]
}
```

#### GET /submissions/{submission_id}/consensus
Consensus for specific submission

**Response 200:**
```json
{
  "submission_id": 456,
  "judge_count": 5,
  "scores_received": 5,
  "icc_score": 0.85,
  "score_agreement_ratio": 0.92,
  "outlier_judges": [18],
  "consensus_verdict": "AUTHENTIC",
  "consensus_confidence": 0.88,
  "score_distribution": {
    "composition": {"mean": 8.2, "std": 0.8},
    "technical": {"mean": 7.6, "std": 1.1},
    "creativity": {"mean": 8.0, "std": 0.9}
  },
  "explanation": "Strong agreement among judges. Judge #18 scored significantly lower."
}
```

#### GET /admin/credential-sharing/{competition_id}
Credential sharing detection (Admin only)

**Response 200:**
```json
{
  "competition_id": 8,
  "alerts": [
    {
      "judge_id": 33,
      "judge_email": "judge@example.com",
      "unique_ip_count": 12,
      "unique_session_count": 15,
      "risk_score": 0.75,
      "risk_level": "high",
      "risk_factors": [
        "Scored from 12 different IPs in 3 days",
        "Geographic inconsistency: USA → India in 2 hours",
        "Simultaneous sessions detected"
      ],
      "investigation_status": "pending",
      "created_at": "2026-02-20T08:00:00Z"
    }
  ],
  "summary": {
    "total_judges": 5,
    "judges_flagged": 1,
    "high_risk_count": 1,
    "medium_risk_count": 0,
    "low_risk_count": 0
  }
}
```

---

## 7. Frontend Integration

### 7.1 Component Structure

```
src/frontend/src/
├── components/
│   ├── camera/
│   │   ├── CameraTrustMeter.vue
│   │   ├── CameraHistoryCard.vue
│   │   └── FingerprintVerificationBadge.vue
│   ├── judge/
│   │   ├── JudgeProfileCard.vue
│   │   ├── ConsensusIndicator.vue
│   │   ├── ScoreDistributionChart.vue
│   │   └── BiasCalibrationTip.vue
│   └── admin/
│       ├── CameraMonitoringPanel.vue
│       ├── JudgePerformanceTable.vue
│       └── CredentialSharingAlerts.vue
├── views/
│   ├── MySubmissions.vue (enhanced)
│   ├── JudgeDashboard.vue (enhanced)
│   ├── ScoreSubmission.vue (enhanced)
│   └── AdminPanel.vue (enhanced)
└── api/
    ├── cameras.ts (new)
    └── judges.ts (new)
```

### 7.2 State Management

**Pinia Store: `cameraStore.ts`**
```typescript
import { defineStore } from 'pinia'
import { camerasApi } from '@/api/cameras'

export const useCameraStore = defineStore('camera', {
  state: () => ({
    userCameras: [],
    cameraProfiles: new Map(),
    trustScores: new Map(),
    loading: false,
    error: null
  }),

  actions: {
    async fetchUserCameras(userId: number) {
      this.loading = true
      try {
        const response = await camerasApi.getUserCameraHistory(userId)
        this.userCameras = response.data.cameras
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async fetchCameraTrustProfile(make: string, model: string) {
      const key = `${make}-${model}`
      if (this.cameraProfiles.has(key)) {
        return this.cameraProfiles.get(key)
      }

      const response = await camerasApi.getCameraTrustProfile(make, model)
      this.cameraProfiles.set(key, response.data)
      return response.data
    }
  }
})
```

**Pinia Store: `judgeStore.ts`**
```typescript
import { defineStore } from 'pinia'
import { judgesApi } from '@/api/judges'

export const useJudgeStore = defineStore('judge', {
  state: () => ({
    judgeProfile: null,
    consensusData: new Map(),
    competitionConsensus: null,
    loading: false,
    error: null
  }),

  actions: {
    async fetchJudgeProfile(judgeId: number, competitionId?: number) {
      this.loading = true
      try {
        const response = await judgesApi.getJudgeProfile(judgeId, competitionId)
        this.judgeProfile = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async fetchSubmissionConsensus(submissionId: number) {
      const response = await judgesApi.getSubmissionConsensus(submissionId)
      this.consensusData.set(submissionId, response.data)
      return response.data
    },

    async fetchCompetitionConsensus(competitionId: number) {
      const response = await judgesApi.getCompetitionConsensus(competitionId)
      this.competitionConsensus = response.data
      return response.data
    }
  }
})
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Camera Reputation Tests:**
```python
# tests/unit/test_camera_reputation.py

import pytest
from app.services.camera_reputation import CameraReputationManager
from app.models.camera import CameraFingerprint, CameraTrustProfile

@pytest.mark.asyncio
async def test_store_fingerprint(db_session):
    """Test storing PRNU fingerprint"""
    manager = CameraReputationManager(db_session)

    prnu_data = {
        "pattern": np.random.rand(100, 100),
        "energy": 0.00023,
        "hash": "test_hash_123"
    }

    fingerprint = await manager.store_fingerprint(
        submission_id=1,
        prnu_data=prnu_data,
        camera_make="Canon",
        camera_model="EOS R6"
    )

    assert fingerprint.id is not None
    assert fingerprint.prnu_energy == 0.00023
    assert fingerprint.camera_make == "Canon"

@pytest.mark.asyncio
async def test_calculate_trust_score_new_camera(db_session):
    """Test trust score for first submission from camera"""
    manager = CameraReputationManager(db_session)

    prnu = np.random.rand(100, 100)
    result = await manager.calculate_trust_score(
        current_prnu=prnu,
        camera_make="Canon",
        camera_model="EOS R6",
        user_id=1
    )

    assert result["trust_score"] == 0.5  # Baseline
    assert result["boost"] == 0.0
    assert "new_camera" in result["message"]

@pytest.mark.asyncio
async def test_calculate_trust_score_existing_camera(db_session):
    """Test trust boost for verified camera"""
    manager = CameraReputationManager(db_session)

    # First submission
    prnu1 = np.random.rand(100, 100)
    await manager.store_fingerprint(
        submission_id=1,
        prnu_data={"pattern": prnu1, "energy": 0.0002, "hash": "hash1"},
        camera_make="Canon",
        camera_model="EOS R6"
    )

    # Second submission with similar PRNU
    prnu2 = prnu1 + np.random.rand(100, 100) * 0.01  # 1% noise
    result = await manager.calculate_trust_score(
        current_prnu=prnu2,
        camera_make="Canon",
        camera_model="EOS R6",
        user_id=1
    )

    assert result["trust_score"] > 0.5
    assert result["boost"] > 0
    assert result["similarity"] > 0.85
```

**Judge Consensus Tests:**
```python
# tests/unit/test_judge_consensus.py

import pytest
from app.services.judge_consensus import JudgeConsensusAnalyzer

@pytest.mark.asyncio
async def test_calculate_icc(db_session):
    """Test ICC calculation"""
    analyzer = JudgeConsensusAnalyzer(db_session)

    # Seed scores: 5 judges, 3 submissions
    scores = np.array([
        [7, 8, 7, 8, 7],  # Submission 1
        [6, 7, 6, 7, 6],  # Submission 2
        [9, 9, 8, 9, 9],  # Submission 3
    ])

    icc = analyzer.calculate_icc_2_1(scores)

    assert 0 <= icc <= 1
    assert icc > 0.75  # Good agreement expected

@pytest.mark.asyncio
async def test_detect_biased_judge(db_session):
    """Test judge bias detection"""
    analyzer = JudgeConsensusAnalyzer(db_session)

    judge_scores = [9, 9, 8, 9, 9, 8, 9]  # Consistently high
    competition_mean = 7.0
    competition_std = 1.0

    bias_result = analyzer.calculate_judge_bias(
        judge_scores,
        competition_mean,
        competition_std
    )

    assert bias_result["z_score"] > 2.0
    assert bias_result["bias_category"] == "lenient"
    assert bias_result["severity"] == "high"

@pytest.mark.asyncio
async def test_detect_credential_sharing(db_session):
    """Test credential sharing detection"""
    analyzer = JudgeConsensusAnalyzer(db_session)

    # Create audit logs with suspicious IP patterns
    audit_logs = [
        {"ip_address": "1.1.1.1", "timestamp": "2026-02-20T08:00:00Z"},
        {"ip_address": "2.2.2.2", "timestamp": "2026-02-20T09:00:00Z"},
        {"ip_address": "3.3.3.3", "timestamp": "2026-02-20T10:00:00Z"},
        {"ip_address": "4.4.4.4", "timestamp": "2026-02-20T11:00:00Z"},
        {"ip_address": "5.5.5.5", "timestamp": "2026-02-20T12:00:00Z"},
    ]

    risk_result = await analyzer.calculate_sharing_risk(
        ip_count=5,
        session_count=5,
        time_gaps=[],
        geo_distances=[]
    )

    assert risk_result["risk_score"] > 0.5
    assert risk_result["risk_level"] in ["medium", "high"]
```

### 8.2 Integration Tests

**Full Workflow Tests:**
```python
# tests/integration/test_camera_reputation_workflow.py

@pytest.mark.asyncio
async def test_submission_with_camera_reputation(client, db_session):
    """Test full submission workflow with camera reputation"""

    # Step 1: User uploads photo
    with open("test_data/canon_r6_photo.jpg", "rb") as f:
        response = await client.post(
            "/api/v1/submissions/",
            files={"jpg_file": f},
            data={"title": "Test Photo", "competition_id": 1}
        )

    assert response.status_code == 201
    submission_id = response.json()["id"]

    # Step 2: Wait for AI analysis (polling)
    for _ in range(10):
        response = await client.get(f"/api/v1/submissions/{submission_id}")
        if response.json()["status"] != "analyzing":
            break
        await asyncio.sleep(1)

    submission = response.json()

    # Step 3: Verify camera reputation was calculated
    assert "camera_trust_score" in submission
    assert "prnu_fingerprint_id" in submission

    # Step 4: Check camera profile was created
    response = await client.get(
        f"/api/v1/cameras/trust-profile/Canon/EOS R6"
    )
    assert response.status_code == 200
    profile = response.json()
    assert profile["total_submissions"] >= 1
```

### 8.3 Performance Benchmarks

**Target Performance:**
- PRNU extraction: <500ms
- PRNU comparison: <200ms
- Trust score calculation: <100ms
- ICC calculation: <150ms
- Bias detection: <50ms

**Benchmark Tests:**
```python
# tests/performance/test_camera_reputation_performance.py

import time
import pytest

def test_prnu_extraction_performance():
    """PRNU extraction should complete in <500ms"""
    image = load_test_image()

    start = time.time()
    prnu = extract_prnu_fingerprint(image)
    duration = time.time() - start

    assert duration < 0.5, f"PRNU extraction took {duration}s (target: <0.5s)"

def test_prnu_comparison_performance():
    """PRNU comparison should complete in <200ms"""
    prnu1 = np.random.rand(1000, 1000)
    prnu2 = np.random.rand(1000, 1000)

    start = time.time()
    result = compare_prnu_patterns(prnu1, prnu2)
    duration = time.time() - start

    assert duration < 0.2, f"PRNU comparison took {duration}s (target: <0.2s)"
```

---

## 9. Deployment Plan

### 9.1 Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Code coverage >90%
- [ ] Security audit completed
- [ ] Database migrations tested (up and down)
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] API documentation generated
- [ ] Rollback plan documented

### 9.2 Deployment Steps

**Step 1: Database Migration (Day 1)**
```bash
# Backup production database
pg_dump -U avar_user avar_production > backup_pre_v2.sql

# Run migrations
alembic upgrade head

# Verify tables created
psql -U avar_user -d avar_production -c "\dt camera_*"
psql -U avar_user -d avar_production -c "\dt judge_*"
```

**Step 2: Backend Deployment (Day 1-2)**
```bash
# Pull latest code
git pull origin main

# Install new dependencies
cd src/backend/competition-service
pip install -r requirements.txt

# Restart services
docker-compose restart competition-service
docker-compose restart ai-detection-service

# Health check
curl https://avar.studio/api/v1/health
```

**Step 3: Frontend Deployment (Day 2)**
```bash
# Build frontend with new features
cd src/frontend
npm install
npm run build

# Deploy to production
rsync -avz dist/ production:/var/www/avar-frontend/
```

**Step 4: Verification (Day 2)**
```bash
# Test camera reputation API
curl https://avar.studio/api/v1/cameras/trust-profile/Canon/EOS%20R6

# Test judge consensus API
curl https://avar.studio/api/v1/judges/profile/1

# Submit test photo and verify workflow
```

### 9.3 Rollback Plan

If issues occur:

```bash
# Rollback database
psql -U avar_user avar_production < backup_pre_v2.sql
alembic downgrade -1

# Revert code
git revert HEAD
docker-compose restart
```

### 9.4 Monitoring

**Key Metrics to Monitor:**
- PRNU extraction latency (target: <500ms)
- Trust score calculation latency (target: <200ms)
- Database query performance (camera fingerprint lookups)
- API error rates
- User engagement (camera reputation views, judge profile views)

**Alerts:**
- PRNU extraction failures >5% in 1 hour
- Database queries >1s
- API error rate >1% in 5 minutes

---

## 10. Success Metrics

### 10.1 Technical Metrics

| Metric | Current (v1.4) | Target (v2.0) | Measurement |
|--------|----------------|---------------|-------------|
| AI Detection Accuracy | 96.7% | 98.5%+ | Test on 1,000 images |
| First-time Confidence | 0.70 avg | 0.70 avg | No change expected |
| Repeat Submission Confidence | 0.70 avg | 0.85+ avg | 21% improvement |
| PRNU Comparison Accuracy | N/A | >90% | Same camera >0.85 similarity |
| Judge Agreement (ICC) | Not measured | 0.75+ | Good agreement |
| Credential Sharing Detection | Manual | 95%+ | Automated detection |
| API Response Time | 3-8s | 4-9s | +1s acceptable |

### 10.2 User Experience Metrics

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| User Trust (Survey) | Not measured | 8/10 | Post-submission survey |
| Judge Satisfaction | Not measured | 8/10 | Post-competition survey |
| Admin Time Savings | 0% | 50%+ | Time tracking |
| False Positive Rate | 3.3% | <2% | Test dataset |
| User Retention | Not measured | Track | Month-over-month |

### 10.3 Innovation Metrics

| Metric | Target | Purpose |
|--------|--------|---------|
| Camera Profiles Created | 100+ in Month 1 | Adoption tracking |
| Trust Boosts Applied | 30%+ of submissions | Feature usage |
| Judge Bias Alerts | <10% of judges | Quality assurance |
| Credential Sharing Detected | 0-2 per competition | Fraud prevention |
| Research Citations | Track | Academic impact |

### 10.4 Business Metrics

| Metric | Target | Impact |
|--------|--------|--------|
| Competitions Using A.V.A.R. | 10+ in Q1 2026 | Market adoption |
| User Growth | 500+ users in Q1 | Platform growth |
| Innovation Score (Self-rated) | 9/10 | Uniqueness |
| Competitive Advantage | "No competitor has this" | Market positioning |

---

## 11. Risk Assessment & Mitigation

### 11.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PRNU storage bloat | Medium | Medium | Compress patterns, archive old data |
| Statistical false positives | Low | High | Multiple metrics, human review option |
| Performance degradation | Low | High | Caching, indexing, async processing |
| Database migration failure | Low | Critical | Extensive testing, rollback plan |

### 11.2 User Experience Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users don't understand trust scores | High | Medium | Clear UI explanations, tooltips |
| Judges frustrated by bias alerts | Medium | Medium | Calibration tips, positive framing |
| Privacy concerns (fingerprinting) | Low | High | Transparency, opt-in, data retention policy |

---

## 12. Timeline Summary

**Total Duration:** 6 weeks (42 days)

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Foundation + PRNU Enhancement | Database schema, enhanced PRNU extraction |
| 2 | Camera Reputation Service + API | Complete camera reputation system |
| 3 | Judge Consensus Database + Service | Statistical analysis implementation |
| 4 | Judge Consensus API | Complete judge analysis endpoints |
| 5 | Integration + Frontend | Workflow integration, UI updates |
| 6 | Testing + Deployment | Comprehensive testing, production deployment |

---

## 13. Resources Required

### 13.1 Development Resources
- 1 Full-stack Developer (you): 6 weeks full-time
- Optional: 1 QA Tester: Part-time for Week 6

### 13.2 Infrastructure
- PostgreSQL storage: +10GB for PRNU patterns
- Compute: No additional (existing VPS sufficient)
- Dependencies: $0 (all open-source)

### 13.3 Budget
- Development time: 240 hours @ $50/hr = $12,000 (opportunity cost)
- Infrastructure: $26/month (no change)
- Testing data: $0 (use existing datasets)
- **Total:** $12,000 + ongoing $26/month

---

## 14. Conclusion

This implementation plan provides a comprehensive roadmap for integrating **Camera Reputation System** and **Judge Consensus Analysis** into A.V.A.R., elevating it from a strong platform (v1.4) to a **market-leading innovation** (v2.0).

### Key Takeaways

1. **Strategic Value:**
   - Both innovations are **uniquely yours** (not just API integrations)
   - Create **network effects** (users build trust over time)
   - **Defensible** (require your infrastructure and historical data)

2. **Technical Feasibility:**
   - Builds on existing PRNU implementation
   - Leverages existing audit trail infrastructure
   - No major architectural changes required
   - Performance targets achievable

3. **Market Positioning:**
   - No competitor has all three: RAW verification + AI detection + Trust systems
   - Moves from "good tool" to "industry standard"
   - Creates barriers to entry for competitors

### Next Steps

1. **Review and approve** this implementation plan
2. **Set up development environment** for Phase 1
3. **Begin database migrations** (Week 1, Day 1)
4. **Iterative development** following roadmap
5. **Weekly progress reviews** to track milestones

---

**Document Version:** 1.0
**Last Updated:** February 21, 2026
**Status:** Ready for Implementation

---

**Prepared by:** Rasan Dilikshana
**Project:** A.V.A.R. v2.0 Innovation Enhancement
**Contact:** [GitHub](https://github.com/rasandilikshana/AI-Photo-Detection-Innovation)
