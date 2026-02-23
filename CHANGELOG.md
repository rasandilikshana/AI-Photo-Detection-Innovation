# Changelog

All notable changes to the A.V.A.R. (Aura Verification and Authentication for RAW files) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-24

### Added - Camera Reputation System
- **PRNU Fingerprint Extraction**: DWT-based sensor pattern extraction using Daubechies-8 wavelet
  - Processing time: 2-4 seconds per 512×512 image
  - Storage: ~256KB per fingerprint (compressed from ~1MB raw)
  - Energy estimation for quality assessment
  - SHA256 hashing for deduplication
- **Trust Scoring Algorithm**: Weighted formula (0.5×similarity + 0.3×history + 0.2×consistency)
  - Confidence boost thresholds: +15% (strong), +5% (moderate), 0% (neutral), -10% (suspicious)
  - Camera profile aggregation (trust score, consistency, submission count)
  - Historical authentication tracking
- **Fraud Detection**: 3-level checks for EXIF manipulation
  - PRNU mismatch detection (pattern doesn't match user's previous submissions)
  - Energy deviation detection (PRNU energy differs from camera profile)
  - Cross-camera matching (pattern matches different camera model)
  - Fraud likelihood scoring: High (>70%), Moderate (40-70%), Low (<40%)
- **8 REST API Endpoints** for camera reputation management
- **2 Vue Components**: CameraReputationBadge.vue, CameraReputationCard.vue

### Added - Judge Consensus Analysis
- **ICC Calculation**: Intraclass Correlation Coefficient for inter-rater reliability
- **Bias Detection**: Z-score analysis for identifying harsh/lenient judges (|Z| > 2.0)
- **Outlier Identification**: Automatic flagging of judges who score significantly differently
- **Judge Profiles**: Comprehensive bias and consistency metrics
- **Auto-flagging**: Poor consensus submissions (ICC < 0.4) marked for manual review
- **9 REST API Endpoints** for judge analytics
- **3 Vue Components**: ConsensusIndicator.vue, ConsensusAnalysisCard.vue, JudgeProfileBadge.vue

### Added - Credential Sharing Detection
- **4-Factor Risk Scoring**: IP diversity (40%), session overlap (30%), time gaps (20%), geo (10%)
- **Activity Monitoring**: Complete audit trail with IP, session, user agent tracking
- **Risk Levels**: High (>70%), Medium (40-70%), Low (<40%)
- **Investigation Workflow**: Admin panel for alert management
- **1 Vue Component**: CredentialSharingAlert.vue

### Added - Bias Report Dashboard
- **BiasReportDashboard.vue**: Full-page competition analytics
  - Competition health overview
  - Bias distribution visualization
  - Individual judge profiles
  - Flagged submissions list

### Added - Database Schema (5 New Tables)
- camera_fingerprints, camera_profiles
- judge_scoring_profiles, judge_consensus_analyses
- credential_sharing_detections

### Added - Documentation (6 Files, 3,763 Lines)
- V2_FEATURES.md, V2_IMPLEMENTATION_SUMMARY.md
- CODE_REVIEW_CHECKLIST.md, INTEGRATION_TESTING_GUIDE.md
- Component README.md, V2_FULLSTACK_COMPLETE.md

### Changed - Workflow Integration
- Automatic PRNU extraction in submission verification
- Automatic consensus analysis after all judges score
- Trust boost applied to AI detection confidence

### Changed - Dependencies
- Added opencv-python ≥4.8.0, PyWavelets ≥1.4.1, scipy ≥1.11.0

### Performance
- PRNU Extraction: 2-4s/image, ~50MB memory
- Pattern Comparison: 50-100ms, ~10MB memory
- Consensus Analysis: 100-300ms, <5MB memory

## [1.4.0] - 2026-02-21
### Added
- Judge manual review workflow with approve/reject functionality
- Feedback mechanism for manual review decisions

### Changed
- Judge Dashboard UX enhancements
- MySubmissions page shows judge review feedback

## [1.3.0] - 2025-12-15
### Added
- Score audit logs with IP, session ID, user agent tracking
- Foundation for credential sharing detection

## [1.2.0] - 2025-12-01
### Added
- Judge dashboard enhancements (clickable cards, image lightbox, pagination)
- Score submission history

## [1.1.0] - 2025-11-15
### Added
- Admin panel, Organizer panel
- Role-based access control

## [1.0.0] - 2025-11-01
### Added - Initial Release
- AI Detection Service (3 layers + RAW-JPG linkage)
- Competition Service (auth, competitions, submissions, scoring)
- Frontend Application (Vue 3 + TypeScript)
- API Gateway
- Docker deployment
- 80%+ test coverage

