# A.V.A.R. System Testing Guide

## Testing the AI Detection System with Real Images

This guide helps you test the A.V.A.R. (Aura Verification and Authentication for RAW files) system with real photographs and AI-generated images to validate detection accuracy.

---

## Quick Start

### Access the Application

**Frontend URL:** http://localhost:5174

### Services Required (All Running)
- Competition Service: Port 8000
- AI Detection Service: Port 8001
- PostgreSQL Database: Port 5432
- Frontend: Port 5174

---

## Testing Workflow

### Step 1: Create Test Accounts

Each tester needs to register an account:

1. Go to http://localhost:5174/register
2. Create accounts:
   - **Photographer accounts** (role: photographer) - for submitting images
   - **Judge account** (role: judge) - for viewing detailed AI analysis
   - **Admin account** (role: admin) - for managing competitions and judge assignments

### Step 2: Create a Test Competition (Admin)

1. Login as admin
2. Go to Admin Panel
3. Create a new competition:
   - Title: "AI Detection Test Round 1"
   - Description: "Testing AI detection accuracy"
   - Status: Set to "Open" to accept submissions

### Step 3: Assign Judges (Admin)

1. In Admin Panel, go to "Judge Assignments"
2. Select the test competition
3. Assign judge accounts to the competition

---

## Test Image Categories

### Category A: Genuine Camera Photos (Should PASS)

Submit images directly from a real camera:

| Test Case | Image Type | Expected Result |
|-----------|------------|-----------------|
| A1 | DSLR photo with full EXIF | AUTHENTIC - High confidence |
| A2 | Smartphone photo (iPhone/Android) | AUTHENTIC - High confidence |
| A3 | Mirrorless camera photo | AUTHENTIC - High confidence |
| A4 | RAW + JPG pair from same camera | PASS with strong RAW linkage |

**What to verify:**
- Layer 1 (Metadata): Camera fields detected (Make, Model, ISO, Aperture, etc.)
- Layer 2 (Fingerprint): PRNU energy > 0.0001, normal ELA pattern
- RAW Linkage (if RAW provided): pHash ≤15, SSIM ≥0.45, Histogram ≥0.40

### Category B: AI-Generated Images (Should FAIL/REJECT)

Submit images from AI tools:

| Test Case | Image Source | Expected Result |
|-----------|--------------|-----------------|
| B1 | Midjourney generated | REJECT - AI detected |
| B2 | DALL-E generated | REJECT - AI detected |
| B3 | Stable Diffusion generated | REJECT - AI detected |
| B4 | Adobe Firefly generated | REJECT - AI detected |

**What to verify:**
- Layer 1: AI signatures detected OR missing camera metadata
- Layer 2: Low PRNU energy (< 0.00001), unusual frequency patterns
- Overall: REJECT verdict with high confidence

### Category C: Manipulated/Edited Photos (Should be SUSPICIOUS)

| Test Case | Image Type | Expected Result |
|-----------|------------|-----------------|
| C1 | Heavy Photoshop edits | SUSPICIOUS or QUARANTINE |
| C2 | Composite image (real + AI elements) | SUSPICIOUS |
| C3 | Stripped EXIF metadata | SUSPICIOUS - missing camera data |

### Category D: Edge Cases

| Test Case | Image Type | Expected Result |
|-----------|------------|-----------------|
| D1 | Screenshot of a photo | REJECT or SUSPICIOUS |
| D2 | Scanned film photo | May PASS (has real texture) |
| D3 | Stock photo with metadata | Depends on original source |
| D4 | Upscaled AI image | Should still detect AI patterns |

---

## How to Submit Test Images

### As a Photographer:

1. Login to http://localhost:5174/login
2. Go to "Competitions"
3. Find the test competition
4. Click "Submit Entry"
5. Fill in:
   - **Title**: Descriptive name (e.g., "Test A1 - Canon 5D Mark IV")
   - **Description**: Note the image source for tracking
   - **JPG File**: The test image (required)
   - **RAW File**: Original RAW if available (optional but recommended for genuine photos)
6. Click "Submit"
7. Wait for AI analysis to complete (usually 5-30 seconds)

### Check Your Submission Status:

1. Go to "My Submissions"
2. View the AI verification status
3. Note: Full analysis details are visible in the Judge Dashboard

---

## Viewing Analysis Results (Judge)

### Access Judge Dashboard:

1. Login as a judge account
2. Go to http://localhost:5174/judge
3. Select the test competition
4. View all submissions with AI analysis summary

### Detailed Analysis View:

1. Click "Score Submission" on any entry
2. Expand each layer by clicking on it:

**Layer 1 - Metadata Analysis:**
- Camera fields found (out of 8)
- AI signatures detected (should be 0 for real photos)
- Camera score and consistency score

**Layer 2 - Digital Fingerprint:**
- PRNU Score (50% weight) - Sensor noise detection
- ELA Score (25% weight) - Compression artifact analysis
- FFT Score (25% weight) - Frequency domain analysis
- Technical metrics: PRNU Energy, ELA Uniformity, High-Freq Ratio

**Layer 3 - Third-Party API:**
- Only runs if Layer 2 returns SUSPICIOUS
- External API confidence score

**RAW-JPG Linkage (if RAW submitted):**
- pHash distance (≤15 = PASS)
- SSIM score (≥0.45 = PASS)
- Histogram correlation (≥0.40 = PASS)

---

## Recording Test Results

Use this template to record your findings:

```
| Test ID | Image Source | Submitted By | Expected | Actual | Layer1 | Layer2 | Notes |
|---------|--------------|--------------|----------|--------|--------|--------|-------|
| A1      | Canon 5D     | Friend1      | PASS     |        |        |        |       |
| B1      | Midjourney   | Friend2      | REJECT   |        |        |        |       |
```

---

## Interpreting Results

### Verdicts Explained:

| Verdict | Meaning | Action |
|---------|---------|--------|
| AUTHENTIC/PASS | Image passed all checks | Genuine photograph |
| SUSPICIOUS/QUARANTINE | Some checks raised concerns | Needs manual review |
| REJECT | Failed critical checks | AI-generated or forged |
| ERROR | Analysis failed | Technical issue |

### Confidence Scores:

- **90-100%**: Very high confidence in verdict
- **70-89%**: High confidence
- **50-69%**: Moderate confidence - review recommended
- **Below 50%**: Low confidence - manual verification needed

### Key Thresholds:

| Metric | Pass Threshold | Fail Threshold |
|--------|---------------|----------------|
| PRNU Energy | ≥ 0.0001 | < 0.00001 (AI) |
| ELA Uniformity | < 30 | > 50 (edited) |
| FFT High-Freq | ≥ 0.225 | < 0.15 (AI smooth) |
| pHash Distance | ≤ 15 | > 30 (different) |
| SSIM Score | ≥ 0.45 | < 0.30 (unlinked) |
| Histogram Corr | ≥ 0.40 | < 0.20 (unlinked) |

---

## Common Issues & Troubleshooting

### "Analysis stuck on pending"
- AI Detection Service may have crashed
- Check if port 8001 is responding
- Restart the AI detection service

### "RAW file not accepted"
- Supported formats: .CR2, .CR3, .NEF, .ARW, .RAF, .DNG, .ORF, .RW2
- File may be corrupted
- Try a different RAW file

### "Low camera score on genuine photo"
- Some cameras embed minimal EXIF data
- Smartphone photos may have less metadata
- This alone doesn't mean AI-generated

### "Genuine photo flagged as suspicious"
- Heavy post-processing can affect fingerprint analysis
- Very clean studio photos may have low noise
- Exported from editing software may strip data

---

## Test Completion Checklist

- [ ] Tested at least 5 genuine camera photos
- [ ] Tested at least 3 AI-generated images
- [ ] Tested RAW+JPG pair submission
- [ ] Verified Layer 1 correctly identifies camera metadata
- [ ] Verified Layer 2 detects AI patterns (low PRNU, smooth FFT)
- [ ] Verified RAW-JPG linkage works correctly
- [ ] Documented false positives (genuine marked as AI)
- [ ] Documented false negatives (AI marked as genuine)
- [ ] Calculated overall accuracy rate

---

## Collecting Feedback

After testing, please document:

1. **Accuracy Rate**: (Correct detections / Total tests) × 100%
2. **False Positive Rate**: Genuine photos incorrectly flagged
3. **False Negative Rate**: AI images incorrectly passed
4. **User Experience**: Ease of submission process
5. **Analysis Speed**: Time from submission to results
6. **UI Clarity**: Is the analysis display understandable?

---

## Contact & Support

For issues during testing:
- Check browser console for errors (F12 → Console)
- Check service logs in terminal
- Restart services if needed

**Service Restart Commands:**
```bash
# Competition Service (port 8000)
cd src/backend/competition-service
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# AI Detection Service (port 8001)
cd src/backend/ai-detection-service
source venv/bin/activate
uvicorn app.main:app --reload --port 8001

# Frontend (port 5174)
cd src/frontend
npm run dev
```

---

*Document Version: 1.0*
*A.V.A.R. Testing Guide for Research Validation*
