# Camera Reputation Services

Business logic services for camera reputation system and PRNU fingerprint analysis.

## Services

### PRNUExtractor

Extracts PRNU (Photo Response Non-Uniformity) fingerprints from images using wavelet denoising.

**Key Methods:**
- `extract_prnu_fingerprint(image_path)` - Extract PRNU pattern from image
- `compare_patterns(pattern1, pattern2)` - Compare two PRNU patterns
- `compress_pattern(pattern)` - Compress for storage
- `decompress_pattern(data, shape)` - Decompress from storage
- `estimate_quality(pattern)` - Assess fingerprint quality

**Algorithm:**
1. Load and preprocess image (grayscale, resize to 512x512)
2. Apply 2D Discrete Wavelet Transform (DWT) using Daubechies-8 wavelet
3. Estimate noise using Median Absolute Deviation (MAD)
4. Apply soft thresholding to denoise
5. Reconstruct denoised image via Inverse DWT
6. Extract residual: PRNU = original - denoised
7. Compress using zlib (int16 quantization)
8. Generate SHA256 hash for deduplication

**Output:**
```python
{
    "pattern": np.ndarray,           # 512x512 noise pattern
    "energy": float,                 # Variance (quality metric)
    "hash": str,                     # SHA256 for deduplication
    "signature": bytes,              # Compressed binary (zlib)
    "valid": bool,                   # Energy > threshold
    "metadata": dict                 # Extraction details
}
```

**Comparison Metrics:**
- Correlation coefficient (primary)
- Normalized cross-correlation (NCC)
- Euclidean distance
- **Similarity score**: 0.0-1.0 (weighted combination)

**Thresholds:**
- > 0.85: Strong match (same camera)
- 0.70-0.85: Moderate match
- 0.50-0.70: Weak match
- < 0.50: Different cameras

### CameraReputationManager

Manages camera trust profiles and fraud detection based on fingerprint history.

**Key Methods:**
- `store_fingerprint(submission_id, prnu_data, ...)` - Store fingerprint in DB
- `calculate_trust_score(prnu, camera, user)` - Calculate trust boost
- `detect_camera_fraud(...)` - Detect EXIF manipulation
- `update_profile_stats(camera, verdict)` - Update reputation

**Trust Score Formula:**
```
trust_score = (
    0.5 * overall_similarity +
    0.3 * (authentic_count / total_count) +
    0.2 * verdict_consistency
)
```

**Trust Boost Thresholds:**
- Similarity > 0.85: **+15%** confidence boost (strong match)
- Similarity 0.70-0.85: **+5%** confidence boost (moderate match)
- Similarity 0.50-0.70: **0%** (neutral)
- Similarity < 0.50: **-10%** penalty (suspicious)

**Fraud Detection Checks:**
1. **PRNU Mismatch**: Current pattern doesn't match user's previous submissions
2. **Energy Deviation**: PRNU energy differs significantly from camera profile
3. **Cross-Camera Match**: Pattern matches different camera (EXIF manipulation)

**Fraud Verdict:**
- `high_fraud_risk`: Likelihood > 0.7 → Recommend rejection
- `moderate_fraud_risk`: Likelihood 0.4-0.7 → Manual review
- `low_fraud_risk`: Likelihood < 0.4 → Approve

## Usage Example

```python
from app.services import PRNUExtractor, CameraReputationManager
from app.database import get_db

# Extract PRNU fingerprint
extractor = PRNUExtractor()
prnu_result = await extractor.extract_prnu_fingerprint(
    image_path="/path/to/photo.jpg",
    camera_make="Canon",
    camera_model="EOS R5"
)

# Check if valid
if not prnu_result["valid"]:
    print("PRNU energy too low - possible AI-generated image")

# Store in database and calculate trust score
async with get_db() as db:
    manager = CameraReputationManager(db)

    # Store fingerprint
    fingerprint = await manager.store_fingerprint(
        submission_id=123,
        prnu_data=prnu_result,
        camera_make="Canon",
        camera_model="EOS R5",
        user_id=456,
        capture_context={"iso": 400, "aperture": "f/2.8"}
    )

    # Calculate trust score
    trust_result = await manager.calculate_trust_score(
        current_prnu=prnu_result["pattern"],
        camera_make="Canon",
        camera_model="EOS R5",
        user_id=456
    )

    print(f"Trust Score: {trust_result['trust_score']:.1%}")
    print(f"Boost: {trust_result['boost']:+.1%}")
    print(f"Message: {trust_result['message']}")

    # Detect fraud
    fraud_result = await manager.detect_camera_fraud(
        submission_id=123,
        current_prnu=prnu_result["pattern"],
        claimed_camera_make="Canon",
        claimed_camera_model="EOS R5",
        user_id=456
    )

    if fraud_result["fraud_likelihood"] > 0.7:
        print("⚠️ HIGH FRAUD RISK DETECTED")
        print(f"Indicators: {fraud_result['indicators']}")

    # Update camera profile
    await manager.update_profile_stats(
        camera_make="Canon",
        camera_model="EOS R5",
        verdict="authentic",
        prnu_energy=prnu_result["energy"]
    )

    await db.commit()
```

## Integration with Existing Workflow

### Submission Verification Flow

```python
# In app/routes/submissions.py

async def verify_submission(submission_id: int, db: AsyncSession):
    submission = await db.get(Submission, submission_id)

    # 1. Extract PRNU fingerprint
    extractor = PRNUExtractor()
    prnu_result = await extractor.extract_prnu_fingerprint(
        submission.jpg_file_url,
        submission.camera_make,
        submission.camera_model
    )

    # 2. Check AI detection (existing Layer 2)
    from ai_detection_service import DigitalFingerprintAnalyzer
    ai_result = await DigitalFingerprintAnalyzer().analyze(submission.jpg_file_url)

    # 3. Calculate camera trust score
    manager = CameraReputationManager(db)
    trust_result = await manager.calculate_trust_score(
        prnu_result["pattern"],
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    # 4. Apply trust boost to AI confidence
    submission.verification_confidence = ai_result["confidence"]
    submission.verification_confidence += trust_result["boost"]
    submission.verification_confidence = min(1.0, submission.verification_confidence)

    # 5. Store fingerprint
    fingerprint = await manager.store_fingerprint(
        submission_id,
        prnu_result,
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    submission.prnu_fingerprint_id = fingerprint.id
    submission.prnu_extracted_energy = prnu_result["energy"]
    submission.camera_trust_score = trust_result["trust_score"]

    # 6. Detect fraud
    fraud_result = await manager.detect_camera_fraud(
        submission_id,
        prnu_result["pattern"],
        submission.camera_make,
        submission.camera_model,
        submission.user_id
    )

    if fraud_result["fraud_likelihood"] > 0.7:
        submission.status = "rejected"
        submission.rejection_reason = "Camera fraud detected: " + fraud_result["explanation"]

    # 7. Update camera profile
    await manager.update_profile_stats(
        submission.camera_make,
        submission.camera_model,
        submission.verification_verdict,
        prnu_result["energy"]
    )

    await db.commit()
```

## Dependencies

### Required Packages
```
opencv-python>=4.8.0      # Image processing
numpy>=1.24.0             # Numerical operations
PyWavelets>=1.4.1         # Wavelet transforms
scipy>=1.11.0             # Scientific computing
sqlalchemy[asyncio]>=2.0  # Database ORM
```

### Install
```bash
pip install opencv-python numpy PyWavelets scipy sqlalchemy[asyncio]
```

## Performance Considerations

### PRNU Extraction
- **Time:** 2-4 seconds per image (512x512)
- **Memory:** ~50MB peak per extraction
- **Storage:** 256KB per fingerprint (compressed)

### Pattern Comparison
- **Time:** 50-100ms per comparison
- **Memory:** ~10MB per comparison

### Optimization Tips
1. **Parallel Processing**: Extract fingerprints in background workers
2. **Caching**: Cache decompressed patterns for recent comparisons
3. **Batch Comparisons**: Compare against top N most recent submissions only
4. **Database Indexing**: Ensure indexes on `user_id`, `camera_make`, `camera_model`

## Testing

See `tests/test_services_v2.py` for comprehensive test suite:
- PRNU extraction accuracy
- Pattern compression/decompression
- Similarity calculation
- Trust score formulas
- Fraud detection logic

## References

1. **PRNU Theory:**
   - Lukas et al. (2006) - "Digital Camera Identification from Sensor Pattern Noise"
   - IEEE Transactions on Information Forensics and Security

2. **Wavelet Denoising:**
   - Donoho & Johnstone (1994) - "Ideal spatial adaptation by wavelet shrinkage"
   - Biometrika

3. **Camera Fingerprinting:**
   - Chen et al. (2008) - "Determining Image Origin and Integrity Using Sensor Noise"
   - IEEE Transactions on Information Forensics and Security
