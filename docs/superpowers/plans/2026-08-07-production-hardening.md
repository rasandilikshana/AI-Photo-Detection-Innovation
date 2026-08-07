# AVAR Production Hardening Implementation Plan

## STATUS: COMPLETE — all 8 tasks executed and deployed, plus 2 unplanned fixes

| Task | Outcome | Commit |
|---|---|---|
| 1 Memory containment | `MemoryHigh=1400M` / `MemoryMax=1650M`, single worker. Peak 1358→1174 MB, swap 156→0 MB, available ~700→1195 MB | server-only |
| 2 Mandatory RAW | `raw_file` required; verified in the live OpenAPI schema | `e17ac9d` |
| 3 Generator list | Fooocus, InvokeAI, AUTOMATIC1111, A1111, sd-webui + a guard test for legitimate tools | `e17ac9d` |
| 4 Hive retune | reject 0.7→0.90, review band 0.4→0.50 | `e17ac9d` |
| 5 Authenticity Score | 0–100, six weighted signals, five bands, critical-signal capping | `76a6b89` |
| 6 PRNU by PCE | correct statistic, threshold 60, "not evaluable" when no reference. Reference pipeline deferred with evidence | `62e01f7` |
| 7 Compression history | **kill switch fired** — measured non-discriminating, excluded, 10 points reassigned | `691cc13` |
| 8 Backfill | 39 records re-analysed; 0 stale; 0 score/verdict contradictions | `8e1ad7f` + script |
| 9 Judge evidence UI *(added)* | score, bands, per-signal evidence, geometry, crop overlay on the RAW | `8e1ad7f` |

**Two defects found during execution, both by verification rather than by review:**

- The backfill **dry run** caught that submissions 33 and 36 — legitimate Photoshop edits with re-attached EXIF — would be written as `REJECTED/AI_GENERATED`. Metadata hygiene was being conflated with decisive provenance. Fixed in `3d39382`; they now score 89–90 AUTHENTIC. This also closed deferred item 4.
- Auditing the backfilled rows caught submission 27 storing `REJECTED` beside a score of **84/100 (approve band)**, because a Hive REJECT only costs 5 points. Fixed in `b1efcf1` by capping the score on any layer REJECT.

Both are the same class: **a verdict decided outside the score creates two sources of truth that can disagree on the judge's screen.** Three instances were closed in total (the linkage guard, the hygiene counts, the layer-REJECT path).

**Final production state:** 172 tests locally / 169 + 3 skipped on the server. 39 submissions scored, bimodal with no overlap — 26 APPROVED at 89–100, 13 REJECTED at 0–24.

---

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every verification claim the platform makes true, measured, and defensible — and stop a single submission from being able to OOM the production box.

**Architecture:** Replace the current sequential-override verdict (where the last layer to speak sets `confidence_score`) with a weighted Authenticity Score of 0–100 over seven signals, banded into defined actions. Fix the two signals that are currently claimed but non-functional (PRNU correlation, mandatory RAW), then add the one high-value pixel forensic that is both citable and implementable (double-JPEG history). Separately, contain the memory profile that already caused one global OOM.

**Tech Stack:** Python 3.12, FastAPI, uvicorn (systemd), OpenCV 4.8, rawpy/libraw, PyWavelets, exiftool, PostgreSQL, Vue 3. Tests: pytest + pytest-asyncio via the service-local venv.

## Global Constraints

- Run tests with the service venv: `cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/ -p no:cacheprovider --no-header -q`
- Production host has **1967 MB RAM and ~700 MB free**. One submission already peaks at 1358 MB. No task may increase peak memory without measuring it.
- **False rejections are worse than false passes.** A rejected photographer loses their competition entry; a forgery that slips one layer still faces the others. Every new check must abstain rather than guess when it lacks the knowledge to be sure.
- Never claim a threshold you cannot cite or have not measured. Thresholds in code carry a comment stating their origin: a measurement, or a paper.
- No new Python dependencies except where a task explicitly installs one; the server venv must be updated in the same task.
- Deploy sequence for every task that changes the detection service: push to `origin/main` → on server `cd /var/www/avar && git fetch origin && git checkout -B main origin/main` → `./venv/bin/python -c 'import app.main'` → `systemctl restart avar-detection.service` → `curl -s 127.0.0.1:8001/health`.
- Real fixture files live at `/home/rasan/Downloads/test/` on the dev machine and `/var/www/avar/src/backend/competition-service/uploads/` on the server. Tests that need them must `pytest.skip` when absent.
- When verifying against the real synthetic files, **copy them to neutral filenames first**. The originals contain the word `synthetic`, which matches `AI_SIGNATURES` and produces a pass for the wrong reason.

---

## Build Order Rationale

Tasks are ordered so that each one is independently deployable and the risky ones come after the safety net exists.

| Order | Task | Why here |
|---|---|---|
| 1 | Memory containment | Pure config. Prevents a global OOM taking postgres down while we do everything else. No code risk. |
| 2 | Mandatory RAW | One line. The entire thesis depends on it, and every later signal assumes a RAW is present. |
| 3 | Generator name list | One line, zero risk, closes a named gap from the review. |
| 4 | Hive threshold retune | Config-level. Must land before the score aggregates Hive's output. |
| 5 | **Authenticity Score** | The structural change. Everything after this plugs into it rather than overriding verdicts. |
| 6 | PRNU correlation (PCE) | Converts the weakest uncitable threshold into the most citable one. Needs the score to exist so it can be weighted rather than gating. |
| 7 | Double-JPEG history | The one high-value pixel forensic worth building. Additive signal into the score. |
| 8 | Stale record backfill | Only meaningful once the pipeline is final. |

**Explicitly out of scope**, recorded so nobody adds them later without a decision: frequency-grid / checkerboard prominence (GAN-era signal, weak against modern diffusion — the source document concedes diffusion scores in the same range as real photos); specular/Fresnel s-score (no verifiable published thresholds); SynthID (no public detection API for arbitrary images); lighting, geometry, anatomy, object-repetition and semantic consistency (research-grade, brittle, high effort); training an in-house CNN (Hive already does this better). C2PA verification is deferred, not rejected — it can only raise confidence since most genuine photos carry no manifest.

---

## File Structure

**Created:**
- `src/backend/ai-detection-service/app/services/authenticity_score.py` — the weighted aggregator. Owns the signal weights, the band definitions, and the mapping from band to action. Pure function of layer results; no I/O.
- `src/backend/ai-detection-service/app/services/compression_history.py` — double-JPEG / DQ analysis. Reads a JPEG, returns a single score plus evidence.
- `src/backend/ai-detection-service/tests/test_authenticity_score.py`
- `src/backend/ai-detection-service/tests/test_compression_history.py`
- `src/backend/ai-detection-service/scripts/backfill_verdicts.py` — re-analyses stored submissions against the current pipeline.
- `/etc/systemd/system/avar-detection.service.d/memory.conf` — systemd drop-in (server only, not in git).

**Modified:**
- `app/main.py` — orchestration: stop overriding `confidence_score` per layer; call the aggregator once at the end.
- `app/services/layer2_fingerprint.py` — replace residual-energy PRNU with reference correlation; delete dead `ela_threshold`.
- `app/services/layer3_api.py` — Hive decision thresholds.
- `src/backend/competition-service/app/routes/submissions.py` — RAW becomes mandatory.
- `src/backend/competition-service/app/services/prnu_extractor.py` — add PCE to `compare_patterns` if absent.
- `app/services/layer1_metadata.py` — generator name list.

---

## Task 1: Contain the memory profile

Measured facts this task responds to: one submission drives the service from 546 MB to 1149 MB, leaving 107 MB system-available; cgroup peak 1358 MB of 1967 MB total; `MemoryMax` and `MemoryHigh` are both `infinity`; `--workers 2` with no concurrency guard; one global OOM occurred 2026-08-07 06:51 with `constraint=CONSTRAINT_NONE`, meaning the kernel could have chosen postgres instead of the analyser.

**Files:**
- Create (server only): `/etc/systemd/system/avar-detection.service.d/memory.conf`
- Modify (server only): worker count in the unit's `ExecStart`

**Interfaces:**
- Consumes: nothing
- Produces: no code interface. Later tasks may assume a single worker, so any per-process cache is process-global.

- [ ] **Step 1: Record the current baseline for comparison**

```bash
ssh root@165.245.178.225 "systemctl show avar-detection -p MemoryPeak -p MemoryMax -p MemoryHigh --value; systemctl cat avar-detection | grep -oE '\-\-workers [0-9]+'"
```

Write the three values into the task notes. Expected today: peak ≈ 1425010688, both limits `infinity`, `--workers 2`.

- [ ] **Step 2: Create the systemd drop-in**

`MemoryMax` is set above the measured 1358 MB legitimate peak so real work is never killed, but below total RAM so a runaway is contained to this service — which already has `Restart=always` — instead of becoming a global OOM that can select postgres.

```ini
# /etc/systemd/system/avar-detection.service.d/memory.conf
# Measured 2026-08-07: one submission peaks at 1358MB of 1967MB total RAM.
# MemoryHigh throttles via reclaim before the hard cap; MemoryMax contains a
# runaway to this service rather than letting the kernel pick a system-wide victim
# (a global OOM on 2026-08-07 06:51 could have chosen postgres).
[Service]
MemoryHigh=1400M
MemoryMax=1650M
```

- [ ] **Step 3: Reduce to one worker**

Two workers on a 2 vCPU / 2 GB host double the worst-case memory for no throughput gain — analysis is CPU-bound and a single submission already saturates one core for ~4 s. One worker makes concurrent analysis impossible, which is the actual OOM trigger.

```bash
ssh root@165.245.178.225 "sed -i 's/--workers 2/--workers 1/' /etc/systemd/system/avar-detection.service && systemctl daemon-reload && systemctl restart avar-detection.service && sleep 6 && systemctl is-active avar-detection.service && systemctl show avar-detection -p MemoryMax -p MemoryHigh --value"
```

Expected: `active`, then `1730150400` and `1468006400`.

- [ ] **Step 4: Verify a real submission still completes under the cap**

```bash
ssh root@165.245.178.225 "cd /var/www/avar/src/backend/competition-service/uploads && curl -s -m 200 -X POST http://127.0.0.1:8001/api/v1/analyze -F 'jpg_file=@1_6_original-photoshop-edit-Twisted Crowns-2511305-Monocrom.jpg' -F 'raw_file=@1_6_Twisted Crowns-2511305-Mono.CR2' -o /dev/null -w 'HTTP %{http_code} in %{time_total}s\n'; systemctl show avar-detection -p MemoryPeak --value"
```

Expected: HTTP 200, and MemoryPeak below 1730150400. If the request fails with a 5xx or the service restarted, `MemoryMax` is too low — raise to 1800M and re-run.

- [ ] **Step 5: Record the change in the deployment memory file**

Append the drop-in path, both values, and the worker change to `/home/rasan/.claude/projects/-media-rasan-windows-drive-NPAS-NPAS---Third-Year-Rasan-Research-3/memory/production-deployment.md`, because this configuration lives only on the server and is not in git.

---

## Task 2: Make the RAW file mandatory

The platform's central claim is that a submission is a photograph *plus its RAW*. Today `raw_file` is `Optional` and only enforced when a per-competition `require_raw_files` flag is set, so a JPEG-only submission can be accepted and every RAW-dependent signal silently scores neutral.

**Files:**
- Modify: `src/backend/competition-service/app/routes/submissions.py:284` (signature), `:339` (validation)
- Test: `src/backend/competition-service/tests/test_submissions_raw_required.py` (create)

**Interfaces:**
- Consumes: nothing
- Produces: guarantees `raw_path` is non-None for every submission reaching `run_ai_analysis`, so Task 5's scorer may treat a missing RAW as a hard failure rather than a neutral.

- [ ] **Step 1: Write the failing test**

```python
# src/backend/competition-service/tests/test_submissions_raw_required.py
"""A submission without a RAW file must be rejected at upload.

The platform verifies that a photograph is derived from its RAW. Accepting a
JPEG-only entry means every RAW-dependent signal scores neutral and the
submission is judged on metadata alone — which is exactly the weak position the
architecture exists to avoid.
"""
import io

import pytest
from httpx import AsyncClient


def _jpeg_bytes():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (90, 120, 90)).save(buf, "JPEG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_submission_without_raw_is_rejected(client: AsyncClient, auth_headers, competition_id):
    response = await client.post(
        "/api/v1/submissions/",
        headers=auth_headers,
        data={"title": "No RAW", "competition_id": str(competition_id)},
        files={"jpg_file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")},
    )

    assert response.status_code == 422, response.text
    assert "raw" in response.text.lower()
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
cd src/backend/competition-service && ./venv/bin/python -m pytest tests/test_submissions_raw_required.py -v --no-cov
```

Expected: FAIL — the submission is accepted with 200/201 because `raw_file` is optional.

If the shared `client`/`auth_headers`/`competition_id` fixtures do not exist in `tests/conftest.py`, read the existing `tests/test_main.py` to find the established fixture names and use those instead. Do not invent new fixtures.

- [ ] **Step 3: Make the parameter required**

```python
# submissions.py — change the signature at line ~284
    raw_file: UploadFile = File(..., description="RAW image file (required — the platform verifies the JPEG is derived from it)"),
```

- [ ] **Step 4: Remove the now-dead conditional and keep the format check**

```python
# submissions.py — replace the block at line ~339
    # RAW is mandatory: every downstream signal (provenance, geometric linkage,
    # PRNU correlation) is defined against it. The per-competition
    # require_raw_files flag is retained on the model for historical rows but is
    # no longer consulted for new submissions.
    ALLOWED_RAW_EXTENSIONS = ['cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'orf', 'rw2', 'pef', 'srw', 'raw']
    if not validate_file_extension(raw_file.filename, ALLOWED_RAW_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid RAW file format. Supported formats: {', '.join([ext.upper() for ext in ALLOWED_RAW_EXTENSIONS])}",
        )
```

Then delete the `if competition.require_raw_files and not raw_file:` block and change every later `if raw_file:` guard in this function to unconditional code, since `raw_file` can no longer be None.

- [ ] **Step 5: Run the test to confirm it passes, then the whole service suite**

```bash
cd src/backend/competition-service && ./venv/bin/python -m pytest tests/test_submissions_raw_required.py -v --no-cov && ./venv/bin/python -m pytest tests/ --no-cov -q
```

Expected: the new test passes. Other tests that post a submission without a RAW will now fail — fix each by adding a RAW file to the request, not by relaxing the requirement.

- [ ] **Step 6: Update the frontend upload form to require it**

In `src/frontend/src/views/Submit.vue`, mark the RAW input `required` and update the helper text to state that a RAW file is mandatory. Find the existing JPG input and mirror its validation pattern.

- [ ] **Step 7: Commit**

```bash
git add src/backend/competition-service/app/routes/submissions.py src/backend/competition-service/tests/test_submissions_raw_required.py src/frontend/src/views/Submit.vue
git commit -m "feat: require a RAW file for every submission

The platform verifies that a submitted photograph is geometrically derived from
its RAW. Accepting a JPEG-only entry meant provenance, linkage and PRNU all
scored neutral and the submission was judged on metadata alone."
```

---

## Task 3: Complete the generator signature list

Four generators named in the reference material are absent from `AI_SIGNATURES`.

**Files:**
- Modify: `app/services/layer1_metadata.py` (the `AI_SIGNATURES` list)
- Test: `app/../tests/test_forensics.py` (extend the existing signature test)

**Interfaces:**
- Consumes: nothing
- Produces: nothing new

- [ ] **Step 1: Extend the existing test**

```python
# tests/test_forensics.py — add below test_ai_signatures_detect_gemini_and_google
def test_ai_signatures_detect_local_generation_tooling(analyzer):
    """Locally-run generators write their own tool names into metadata. These were
    missing from the list while cloud generators were covered."""
    for value in ["Fooocus", "InvokeAI v4.2", "AUTOMATIC1111 webui", "A1111", "Fooocus-MRE"]:
        detected, flags = analyzer._detect_ai_signatures({"Software": value})
        assert detected is True, f"should detect: {value}"
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_forensics.py::test_ai_signatures_detect_local_generation_tooling -v -p no:cacheprovider
```

Expected: FAIL on "Fooocus".

- [ ] **Step 3: Add the names**

```python
# layer1_metadata.py — append inside AI_SIGNATURES
        "fooocus",
        "invokeai",
        "invoke ai",
        "automatic1111",
        "a1111",
        "sd webui",
        "stable-diffusion-webui",
```

- [ ] **Step 4: Run the full suite**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/ -p no:cacheprovider --no-header -q
```

Expected: all pass.

- [ ] **Step 5: Commit and deploy**

```bash
git add src/backend/ai-detection-service/app/services/layer1_metadata.py src/backend/ai-detection-service/tests/test_forensics.py
git commit -m "feat: detect locally-run generator tooling in metadata"
```

Then run the standard deploy sequence from Global Constraints.

---

## Task 4: Retune the Hive AI decision thresholds

Current thresholds reject at `ai_generated_score > 0.7` and quarantine above `0.4`. For a competition where a false rejection costs a photographer their entry, auto-rejection should demand higher precision, and the uncertain band should be wider and routed to a human.

**Files:**
- Modify: `app/services/layer3_api.py:145-156`
- Test: `tests/test_layer3_thresholds.py` (create)

**Interfaces:**
- Consumes: nothing
- Produces: `_verify_hive_ai` returns `verdict` in `{REJECT, QUARANTINE, AUTHENTIC}` and `ai_score` as a float in 0..1. Task 5 consumes `ai_score` directly rather than the verdict.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_layer3_thresholds.py
"""Hive AI decision bands.

A false rejection costs a photographer their competition entry, so auto-rejection
requires high precision. Anything short of that goes to a human rather than being
decided automatically.
"""
import pytest

from app.services.layer3_api import ThirdPartyAPIVerifier


@pytest.fixture
def verifier():
    return ThirdPartyAPIVerifier()


@pytest.mark.parametrize("score,expected", [
    (0.99, "REJECT"),
    (0.90, "REJECT"),
    (0.89, "QUARANTINE"),
    (0.50, "QUARANTINE"),
    (0.49, "AUTHENTIC"),
    (0.01, "AUTHENTIC"),
])
def test_hive_score_bands(verifier, score, expected):
    assert verifier.classify_hive_score(score)[0] == expected


def test_authentic_confidence_is_the_complement_of_the_ai_score(verifier):
    verdict, confidence = verifier.classify_hive_score(0.02)
    assert verdict == "AUTHENTIC"
    assert confidence == pytest.approx(0.98)
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_layer3_thresholds.py -v -p no:cacheprovider
```

Expected: FAIL — `classify_hive_score` does not exist.

- [ ] **Step 3: Extract the banding into a testable method**

```python
# layer3_api.py — add as a method on ThirdPartyAPIVerifier
    # Auto-rejection demands high precision because a false rejection costs a
    # photographer their competition entry; Hive's own guidance for high-volume
    # moderation is a 0.9 positive-class threshold. Everything between 0.5 and 0.9
    # is genuinely uncertain and goes to a judge rather than being decided here.
    HIVE_REJECT_AT = 0.90
    HIVE_QUARANTINE_AT = 0.50

    def classify_hive_score(self, ai_generated_score: float) -> tuple[str, float]:
        """Map Hive's ai_generated probability to a verdict and confidence."""
        if ai_generated_score >= self.HIVE_REJECT_AT:
            return "REJECT", ai_generated_score
        if ai_generated_score >= self.HIVE_QUARANTINE_AT:
            return "QUARANTINE", ai_generated_score
        return "AUTHENTIC", 1.0 - ai_generated_score
```

- [ ] **Step 4: Use it in `_verify_hive_ai`**

Replace the inline `if ai_generated_score > 0.7: ... elif > 0.4: ... else: ...` block with:

```python
                verdict, confidence = self.classify_hive_score(ai_generated_score)
                flags = [
                    f"Hive AI detected AI-generated content (score={ai_generated_score:.2f})" if verdict == "REJECT"
                    else f"Hive AI uncertain (score={ai_generated_score:.2f}) - manual review required" if verdict == "QUARANTINE"
                    else f"Hive AI verified authentic (AI score={ai_generated_score:.2f})"
                ]
```

- [ ] **Step 5: Run the tests and commit**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/ -p no:cacheprovider --no-header -q
git add src/backend/ai-detection-service/app/services/layer3_api.py src/backend/ai-detection-service/tests/test_layer3_thresholds.py
git commit -m "fix: raise Hive auto-reject threshold to 0.90 and widen the review band"
```

---

## Task 5: Authenticity Score (0–100) with review bands

This is the structural change. Today each layer overwrites `confidence_score`, so the final number reflects whichever layer spoke last rather than the weight of evidence — and a strong signal can be erased by a weak one. Replace it with a single weighted aggregation over seven signals, banded into defined actions.

Weights reflect *measured* discriminative power on this platform's own data, not a generic table. Geometric linkage is weighted second-highest because it is the only signal with a measured two-orders-of-magnitude separation (463–883 inliers on genuine pairs versus 4–5 on substitutions).

**Files:**
- Create: `app/services/authenticity_score.py`
- Create: `tests/test_authenticity_score.py`
- Modify: `app/main.py` (stop per-layer overrides; aggregate once at the end)

**Interfaces:**
- Consumes: `layer1_result`, `layer2_result`, `layer3_result`, `raw_jpg_linkage` dicts as returned today
- Produces:
  - `AuthenticityScorer.score(layer1, layer2, layer3, linkage) -> dict` with keys `score: int` (0–100), `band: str`, `verdict: str`, `action: str`, `signals: list[dict]`, `missing: list[str]`
  - `verdict` is one of `AUTHENTIC`, `QUARANTINE`, `REJECT` so the existing `verdict_map` in `submissions.py:205` keeps working unchanged
  - each entry of `signals` is `{"name": str, "weight": int, "score": float, "contribution": float, "evidence": str}`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_authenticity_score.py
"""Weighted Authenticity Score.

Replaces sequential verdict override, where the last layer to speak set the final
confidence and a strong signal could be erased by a weak one. Weights are set from
measured discriminative power on this platform's own data: geometric linkage
separates genuine from substituted pairs by two orders of magnitude (463-883
inliers versus 4-5), so it carries more weight than pixel statistics whose
thresholds were tuned empirically.

A signal that could not be evaluated must be EXCLUDED and the remaining weights
renormalised — never scored as zero. Scoring an unavailable signal as zero
punishes the photographer for our inability to measure, which is the single
easiest way to reject a genuine entry.
"""
import pytest

from app.services.authenticity_score import AuthenticityScorer


@pytest.fixture
def scorer():
    return AuthenticityScorer()


def _l1(verdict="PASS", confidence=1.0, forensic=0, source="RAW"):
    return {"verdict": verdict, "confidence": confidence, "forensic_indicators": forensic,
            "metadata_source": source, "camera_fields_found": 8}


def _l2(prnu=1.0, ela=1.0, fft=1.0):
    return {"verdict": "PASS", "prnu_score": prnu, "ela_score": ela, "fft_score": fft}


def _linkage(verdict="PASS", inliers=500, crop_like=True, ratio=0.93):
    return {"verdict": verdict, "confidence": ratio,
            "geometry": {"inliers": inliers, "crop_like": crop_like, "inlier_ratio": ratio,
                         "low_texture": False}}


def test_weights_sum_to_one_hundred(scorer):
    assert sum(w for _, w in scorer.WEIGHTS.items()) == 100


def test_bands_are_ordered_and_cover_zero_to_one_hundred(scorer):
    lows = [low for low, _, _, _ in scorer.BANDS]
    assert lows == sorted(lows, reverse=True)
    assert scorer.BANDS[-1][0] == 0
    assert scorer.BANDS[0][1] == 100


def test_a_fully_clean_submission_scores_at_the_top(scorer):
    result = scorer.score(_l1(), _l2(), None, _linkage())
    assert result["score"] >= 90
    assert result["verdict"] == "AUTHENTIC"


def test_substituted_jpeg_scores_in_the_reject_band(scorer):
    """Linkage rejects, provenance flags the metadata: the evidence agrees."""
    result = scorer.score(
        _l1(verdict="SUSPICIOUS", confidence=0.4, forensic=3),
        _l2(prnu=0.5),
        {"verdict": "REJECT", "ai_score": 0.95},
        _linkage(verdict="REJECT", inliers=4, crop_like=False, ratio=0.2),
    )
    assert result["score"] <= 24
    assert result["verdict"] == "REJECT"


def test_legitimate_heavy_edit_stays_approvable(scorer):
    """A mono crop: linkage confirms it geometrically, pixel stats look unusual
    because the file was edited. It must not fall out of the approve bands."""
    result = scorer.score(_l1(), _l2(prnu=0.5, ela=1.0, fft=1.0), None,
                          _linkage(inliers=462, ratio=0.93))
    assert result["score"] >= 75, result


def test_an_unavailable_signal_is_excluded_not_scored_zero(scorer):
    """Layer 3 not run must not cost the submission its weight."""
    with_l3 = scorer.score(_l1(), _l2(), {"verdict": "AUTHENTIC", "ai_score": 0.01}, _linkage())
    without_l3 = scorer.score(_l1(), _l2(), None, _linkage())

    assert "third_party" in without_l3["missing"]
    assert without_l3["score"] == pytest.approx(with_l3["score"], abs=2)


def test_missing_raw_is_a_hard_failure_not_a_missing_signal(scorer):
    """RAW is mandatory as of Task 2. Its absence is evidence, not an inability
    to measure, so it scores zero rather than being excluded."""
    result = scorer.score(_l1(source="JPG"), _l2(), None, None)
    assert result["score"] <= 49
    assert "raw_provenance" not in result["missing"]


def test_ai_signature_forces_rejection_regardless_of_score(scorer):
    """A file that names its own generator is not a weighing exercise."""
    result = scorer.score(
        {"verdict": "REJECT", "confidence": 1.0, "ai_signatures_found": 2},
        _l2(), None, _linkage(),
    )
    assert result["verdict"] == "REJECT"
    assert result["score"] == 0


def test_every_signal_reports_its_evidence(scorer):
    result = scorer.score(_l1(), _l2(), None, _linkage())
    assert len(result["signals"]) >= 5
    for signal in result["signals"]:
        assert signal["evidence"], f"{signal['name']} must explain its score to a judge"
        assert 0.0 <= signal["score"] <= 1.0


def test_result_is_json_serialisable(scorer):
    import json
    json.dumps(scorer.score(_l1(), _l2(), None, _linkage()))
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_authenticity_score.py -v -p no:cacheprovider
```

Expected: all fail with `ModuleNotFoundError: app.services.authenticity_score`.

- [ ] **Step 3: Implement the scorer**

```python
# app/services/authenticity_score.py
"""Weighted Authenticity Score.

Replaces sequential verdict override. Previously each layer overwrote
confidence_score, so the final number reflected whichever layer spoke last rather
than the weight of evidence — a measured, decisive signal could be erased by a
tuned, weak one.

Weights come from measured discriminative power on this platform's own data, not
from a generic table:

  raw_provenance   30  container/writer/sensor-geometry checks; caught the only
                       known successful forgery against this platform
  geometric_linkage 25  the only signal with a measured two-orders-of-magnitude
                       separation: 463-883 RANSAC inliers on genuine pairs vs 4-5
                       on substituted ones
  metadata          15  transplant forensics; caught the earlier Gemini attack
  prnu              10  sensor-reference correlation (Task 6)
  compression        10  double-JPEG history (Task 7)
  frequency          5  crude global FFT ratio, empirically tuned thresholds
  third_party        5  Hive AI; strong but external and not always consulted

A signal that could not be EVALUATED is excluded and the remaining weights are
renormalised. It is never scored zero: doing so punishes the photographer for our
inability to measure, which is the easiest way to reject a genuine entry. A signal
that was evaluated and failed scores zero and keeps its weight.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AuthenticityScorer:

    WEIGHTS = {
        "raw_provenance": 30,
        "geometric_linkage": 25,
        "metadata": 15,
        "prnu": 10,
        "compression": 10,
        "frequency": 5,
        "third_party": 5,
    }

    # (low, high, verdict, action) — highest band first, low bound inclusive.
    BANDS = [
        (90, 100, "AUTHENTIC", "Auto-approve: provenance and forensics agree"),
        (75, 89, "AUTHENTIC", "Approve, flagged for judge visibility"),
        (50, 74, "QUARANTINE", "Judge review required"),
        (25, 49, "QUARANTINE", "High suspicion - request originals or burst frames"),
        (0, 24, "REJECT", "Auto-reject"),
    ]

    def score(self, layer1: Optional[Dict], layer2: Optional[Dict],
              layer3: Optional[Dict], linkage: Optional[Dict]) -> Dict:
        layer1 = layer1 or {}

        # A file naming its own generator is not a weighing exercise.
        if layer1.get("ai_signatures_found", 0) > 0:
            return self._result(0, [], ["Generator signature present in metadata"], forced="REJECT")

        signals: List[Dict] = []
        missing: List[str] = []

        for name, evaluate in (
            ("raw_provenance", lambda: self._raw_provenance(layer1)),
            ("geometric_linkage", lambda: self._linkage(linkage)),
            ("metadata", lambda: self._metadata(layer1)),
            ("prnu", lambda: self._from_layer2(layer2, "prnu_score", "PRNU")),
            ("compression", lambda: self._compression(layer2)),
            ("frequency", lambda: self._from_layer2(layer2, "fft_score", "Frequency")),
            ("third_party", lambda: self._third_party(layer3)),
        ):
            try:
                outcome = evaluate()
            except Exception as e:
                logger.warning(f"Authenticity signal {name} failed: {str(e)}")
                outcome = None

            if outcome is None:
                missing.append(name)
                continue

            value, evidence = outcome
            weight = self.WEIGHTS[name]
            signals.append({
                "name": name, "weight": weight, "score": round(float(value), 3),
                "contribution": round(weight * float(value), 2), "evidence": evidence,
            })

        available = sum(s["weight"] for s in signals)
        if available == 0:
            return self._result(0, signals, missing)

        raw_total = sum(s["contribution"] for s in signals)
        score = int(round(raw_total / available * 100))
        return self._result(score, signals, missing)

    def _result(self, score: int, signals: List[Dict], missing: List[str],
                forced: Optional[str] = None) -> Dict:
        score = max(0, min(100, score))
        band = next((b for b in self.BANDS if b[0] <= score <= b[1]), self.BANDS[-1])
        return {
            "score": score,
            "band": f"{band[0]}-{band[1]}",
            "verdict": forced or band[2],
            "action": band[3],
            "signals": signals,
            "missing": missing,
        }

    # -- individual signals: return (0..1, evidence) or None if unevaluable --

    def _raw_provenance(self, layer1: Dict):
        if layer1.get("metadata_source") != "RAW":
            # RAW is mandatory, so its absence is evidence rather than a gap.
            return 0.0, "No usable RAW metadata — camera fields came from the JPEG"
        indicators = layer1.get("forensic_indicators", 0)
        if indicators == 0:
            return 1.0, "RAW passes writer, container and sensor-geometry checks"
        return max(0.0, 1.0 - 0.34 * indicators), f"{indicators} provenance/transplant indicator(s)"

    def _linkage(self, linkage: Optional[Dict]):
        if not linkage or linkage.get("verdict") == "ERROR":
            return None
        geometry = linkage.get("geometry")
        if linkage["verdict"] == "PASS" and not geometry:
            return 1.0, "Whole-frame match: the JPEG is the RAW unedited"
        if linkage["verdict"] == "PASS":
            return 1.0, (f"Geometrically confirmed: {geometry['inliers']} matching sensor features, "
                         f"{linkage.get('crop_fraction', 1.0):.0%} crop")
        if geometry and geometry.get("low_texture"):
            return None  # genuinely undecidable, do not penalise
        if linkage["verdict"] == "SUSPICIOUS":
            return 0.35, f"Linkage inconclusive ({(geometry or {}).get('inliers', 0)} features)"
        return 0.0, f"No crop of the RAW matches this JPEG ({(geometry or {}).get('inliers', 0)} features)"

    def _metadata(self, layer1: Dict):
        if not layer1:
            return None
        fields = layer1.get("camera_fields_found", 0)
        return min(1.0, fields / 8.0), f"{fields}/8 camera fields present and self-consistent"

    def _from_layer2(self, layer2: Optional[Dict], key: str, label: str):
        if not layer2 or layer2.get(key) is None:
            return None
        value = float(layer2[key])
        return value, f"{label} score {value:.2f}"

    def _compression(self, layer2: Optional[Dict]):
        # Populated by Task 7. Absent until then, so this signal is excluded and
        # the other weights renormalise — no behaviour change before Task 7 lands.
        if not layer2 or layer2.get("compression_score") is None:
            return None
        value = float(layer2["compression_score"])
        return value, layer2.get("compression_evidence", f"Compression history score {value:.2f}")

    def _third_party(self, layer3: Optional[Dict]):
        if not layer3 or layer3.get("ai_score") is None:
            return None
        ai_score = float(layer3["ai_score"])
        return 1.0 - ai_score, f"Hive AI generated-probability {ai_score:.2f}"
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_authenticity_score.py -v -p no:cacheprovider
```

Expected: all pass. If `test_legitimate_heavy_edit_stays_approvable` fails, do NOT lower the assertion — check whether `prnu=0.5` plus the excluded compression signal is dragging the total, and reconsider whether PRNU deserves 10 points before Task 6 makes it real.

- [ ] **Step 5: Wire it into `main.py`**

In `analyze_submission`, keep every layer's own verdict logic for escalation decisions (Layer 1 REJECT still short-circuits, linkage still forces Layer 3), but stop assigning `confidence_score` per layer. After Layer 3 completes and before the final guard, add:

```python
        # Single weighted aggregation replaces per-layer confidence override.
        authenticity = scorer.score(layer1_result, layer2_result, layer3_result, raw_jpg_linkage)

        # The band decides, except that an explicit REJECT from any layer stands:
        # a layer that positively identified fraud is not outvoted by averages.
        if verdict != "REJECT":
            verdict = authenticity["verdict"]
        confidence_score = authenticity["score"] / 100.0
        flags.append(f"Authenticity score {authenticity['score']}/100 ({authenticity['action']})")
```

Add `authenticity` to the `AnalysisResult` model as a `dict` field and include it in the returned object. Instantiate `scorer = AuthenticityScorer()` alongside the other analyzers at module level.

- [ ] **Step 6: Verify against all real files, before and after**

```bash
cd /tmp && rm -rf ahard && mkdir ahard && cd ahard \
  && cp "/home/rasan/Downloads/test/1_5_AVAR_high_realism_synthetic_Canon_R5_test.dng" a.dng \
  && cp "/home/rasan/Downloads/test/1_5_AVAR_high_realism_synthetic_Canon_R5_test.jpg.jpeg" a.jpg \
  && cp "/home/rasan/Downloads/test/Twisted Crowns-2511305-Mono.CR2" b.cr2 \
  && cp "/home/rasan/Downloads/test/Twisted Crowns-2511305-Mono.JPG" b.jpg \
  && cp "/home/rasan/Downloads/test/original-photoshop-edit-Twisted Crowns-2511305-Monocrom.jpg" c.jpg \
  && cp "/home/rasan/Downloads/test/Emerald Edge-2511305-Colour.CR2" d.cr2 \
  && cp "/home/rasan/Downloads/test/Emerald Dialogue.jpg" d.jpg
```

Then run each pair through the local service and record the score. Required outcomes:

| pair | required |
|---|---|
| a.jpg + a.dng (synthetic) | score ≤ 24, verdict REJECT |
| b.jpg + b.cr2 (genuine unedited) | score ≥ 90, AUTHENTIC |
| c.jpg + b.cr2 (genuine mono crop) | score ≥ 75, AUTHENTIC |
| d.jpg + d.cr2 (genuine edit) | score ≥ 75, AUTHENTIC |
| d.jpg + b.cr2 (wrong RAW) | score ≤ 49 |

If a genuine pair lands below its band, the weights are wrong — adjust weights and re-run, do not relax the requirement.

- [ ] **Step 7: Commit and deploy**

```bash
git add src/backend/ai-detection-service/app/services/authenticity_score.py src/backend/ai-detection-service/tests/test_authenticity_score.py src/backend/ai-detection-service/app/main.py
git commit -m "feat: weighted Authenticity Score (0-100) with review bands

Replaces sequential verdict override, where the last layer to speak set the final
confidence and a measured signal could be erased by a tuned one. Weights reflect
measured discriminative power on this platform's own data. Unevaluable signals are
excluded and remaining weights renormalised rather than scored zero."
```

Then run the standard deploy sequence and re-verify the five pairs against the live endpoint.

---

## Task 6: Make PRNU real — reference correlation with PCE

`layer2_fingerprint._analyze_prnu` measures `var(image - denoised)` and calls it PRNU. That is high-frequency residual energy, not a sensor fingerprint, and it cannot discriminate: the genuine Canon JPEG scored 2.26e-05 ("weak", 0.5), the synthetic AI image scored 1.39e-05 (also 0.5), and a Photoshop-edited real photo scored 2.53e-04 ("valid", 1.0) — the edited file beating the genuine camera file by 11x.

Real PRNU compares a residual against a reference pattern from that specific camera body. The decision statistic in the literature is **PCE (Peak-to-Correlation Energy)**, not raw correlation, with a threshold around **60** for a false-accept rate near 1e-5 (Goljan, Fridrich & Filler, *Large scale test of sensor fingerprint camera identification*, SPIE 2009). `prnu_extractor.py` and `camera_reputation.py` already store per-body references; Layer 2 never calls them.

**Files:**
- Modify: `src/backend/competition-service/app/services/prnu_extractor.py` (add PCE to `compare_patterns`)
- Modify: `app/services/layer2_fingerprint.py` (`_analyze_prnu`, and delete the unused `ela_threshold`)
- Test: `tests/test_prnu_correlation.py` (create)

**Interfaces:**
- Consumes: `RawProvenanceAnalyzer` is unrelated here. Uses `PRNUExtractor.compare_patterns(p1, p2) -> Dict`.
- Produces: `layer2_result["prnu_score"]` in 0..1 as before, plus `prnu_pce: float` and `prnu_reference_available: bool`. Task 5's `_from_layer2` already reads `prnu_score`; no scorer change needed.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prnu_correlation.py
"""PRNU as sensor-reference correlation rather than residual energy.

The previous implementation measured var(image - denoised) and could not tell a
genuine Canon JPEG (2.26e-05) from a synthetic AI image (1.39e-05), while scoring
a Photoshop-edited real photo (2.53e-04) higher than either.

PCE is the decision statistic used in the literature; threshold 60 corresponds to
a false-accept rate near 1e-5 (Goljan, Fridrich & Filler, SPIE 2009).
"""
import numpy as np
import pytest

from app.services.layer2_fingerprint import DigitalFingerprintAnalyzer


@pytest.fixture
def analyzer():
    return DigitalFingerprintAnalyzer()


def test_pce_threshold_matches_the_published_value(analyzer):
    assert analyzer.pce_threshold == 60.0


def test_identical_patterns_produce_a_high_pce(analyzer):
    rng = np.random.default_rng(0)
    pattern = rng.standard_normal((256, 256)).astype(np.float32)

    pce = analyzer._peak_to_correlation_energy(pattern, pattern.copy())

    assert pce > analyzer.pce_threshold, f"a pattern must match itself, got PCE={pce}"


def test_unrelated_patterns_produce_a_low_pce(analyzer):
    rng = np.random.default_rng(1)
    a = rng.standard_normal((256, 256)).astype(np.float32)
    b = rng.standard_normal((256, 256)).astype(np.float32)

    assert analyzer._peak_to_correlation_energy(a, b) < analyzer.pce_threshold


def test_no_reference_yields_an_inconclusive_score_not_a_failure(analyzer):
    """A photographer's first submission has no accumulated reference. That is an
    absence of information, not evidence against them."""
    result = analyzer._score_prnu(pce=None, reference_available=False)

    assert result["score"] == 0.5
    assert result["reference_available"] is False
    assert "no reference" in result["flags"][0].lower()


def test_pce_above_threshold_scores_full_marks(analyzer):
    assert analyzer._score_prnu(pce=140.0, reference_available=True)["score"] == 1.0


def test_pce_far_below_threshold_scores_zero(analyzer):
    result = analyzer._score_prnu(pce=3.0, reference_available=True)
    assert result["score"] == 0.0
    assert "does not match" in " ".join(result["flags"]).lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_prnu_correlation.py -v -p no:cacheprovider
```

Expected: FAIL — `pce_threshold`, `_peak_to_correlation_energy` and `_score_prnu` do not exist.

- [ ] **Step 3: Implement PCE and the scoring bands**

```python
# layer2_fingerprint.py — in __init__, replace the prnu/ela threshold block
        # PCE (Peak-to-Correlation Energy) is the decision statistic for sensor
        # fingerprint matching; 60 corresponds to a false-accept rate near 1e-5
        # (Goljan, Fridrich & Filler, "Large scale test of sensor fingerprint camera
        # identification", SPIE Media Forensics 2009). Replaces a residual-energy
        # threshold that could not distinguish a genuine camera JPEG from an AI image.
        self.pce_threshold = 60.0
        self.pce_floor = 10.0  # below this, actively inconsistent rather than merely weak
        self.fft_threshold = 0.15  # empirically tuned, not calibrated

    def _peak_to_correlation_energy(self, residual: np.ndarray, reference: np.ndarray) -> float:
        """PCE: squared correlation peak over the energy of the correlation surface
        excluding a small neighbourhood of the peak."""
        a = (residual - residual.mean()).astype(np.float32)
        b = (reference - reference.mean()).astype(np.float32)
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]))

        correlation = cv2.filter2D(a, -1, b, borderType=cv2.BORDER_WRAP)
        peak_index = int(np.argmax(np.abs(correlation)))
        peak = float(correlation.flat[peak_index]) ** 2

        surface = correlation.copy().ravel()
        half = 5
        rows, cols = correlation.shape
        py, px = divmod(peak_index, cols)
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                y, x = (py + dy) % rows, (px + dx) % cols
                surface[y * cols + x] = 0.0

        energy = float(np.sum(surface.astype(np.float64) ** 2)) / max(1, surface.size - (2 * half + 1) ** 2)
        if energy <= 0 or not np.isfinite(energy):
            return 0.0
        return float(peak / energy)

    def _score_prnu(self, pce: Optional[float], reference_available: bool) -> Dict:
        """Map a PCE value to a 0..1 signal score."""
        if not reference_available or pce is None:
            return {
                "score": 0.5,
                "flags": ["PRNU inconclusive: no reference fingerprint for this camera body yet "
                          "(first submission from this camera)"],
                "pce": None,
                "reference_available": False,
            }
        if pce >= self.pce_threshold:
            return {"score": 1.0,
                    "flags": [f"PRNU matches this camera body (PCE={pce:.1f}, threshold {self.pce_threshold:.0f})"],
                    "pce": pce, "reference_available": True}
        if pce >= self.pce_floor:
            return {"score": 0.5,
                    "flags": [f"PRNU weakly consistent (PCE={pce:.1f}, below threshold {self.pce_threshold:.0f})"],
                    "pce": pce, "reference_available": True}
        return {"score": 0.0,
                "flags": [f"PRNU does not match this camera body (PCE={pce:.1f})"],
                "pce": pce, "reference_available": True}
```

Delete `self.prnu_threshold` and `self.ela_threshold` (the latter was never read — `_analyze_ela` hardcodes 50.0 and 30.0).

- [ ] **Step 4: Run the new tests**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_prnu_correlation.py -v -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Fetch the reference and wire it into `_analyze_prnu`**

The detection service has no database access; the reference must be supplied by the caller. Add an optional parameter to the public entry point:

```python
    async def analyze(self, jpg_path: str, raw_path: Optional[str] = None,
                      reference_pattern: Optional[np.ndarray] = None) -> Dict:
```

Inside `_analyze_prnu`, keep the existing wavelet residual extraction (it produces the residual correctly), then replace the energy-threshold block with:

```python
            if reference_pattern is None:
                outcome = self._score_prnu(None, reference_available=False)
            else:
                pce = self._peak_to_correlation_energy(prnu, reference_pattern)
                outcome = self._score_prnu(pce, reference_available=True)

            return {
                "score": outcome["score"],
                "flags": outcome["flags"],
                "energy": float(prnu_energy),  # retained as descriptive evidence only
                "pce": outcome["pce"],
                "reference_available": outcome["reference_available"],
            }
```

Then in `main.py`, accept an optional `reference_pattern` in the request (base64 int16, matching `prnu_extractor._compress_pattern`) and pass it through. In `submissions.py`, look up the user's most recent `CameraFingerprint` for this make/model via `_get_user_camera_fingerprints`, decompress it with `PRNUExtractor.decompress_pattern`, and include it in the multipart request.

- [ ] **Step 6: Verify the discrimination that previously failed**

Run the synthetic pair and the genuine pair through the local pipeline twice: once with no reference (both should score 0.5 — honest) and once with the genuine Canon reference supplied (the genuine JPEG should exceed PCE 60; the synthetic should not). Record both PCE values in the commit message. If the genuine file does not exceed 60, the reference is being built from too few images — note the count and raise it rather than lowering the threshold.

- [ ] **Step 7: Commit and deploy**

```bash
git add src/backend/ai-detection-service/app/services/layer2_fingerprint.py src/backend/ai-detection-service/tests/test_prnu_correlation.py src/backend/ai-detection-service/app/main.py src/backend/competition-service/app/routes/submissions.py
git commit -m "fix: PRNU by sensor-reference correlation (PCE) instead of residual energy"
```

---

## Task 7: Double-JPEG compression history

The highest-value pixel forensic available, and citable: a JPEG that has been decompressed and re-saved carries periodic double peaks and missing values in its DCT coefficient histograms (Lukáš & Fridrich 2003; Popescu & Farid 2004), and the likelihood-ratio framework for localising it uses a posterior ratio with threshold τ = 1.0 (Bianchi & Piva, *Image Forgery Localization via Block-Grained Analysis of JPEG Artifacts*, IEEE TIFS 2012).

For this platform the useful question is narrower than tamper localisation: **has this JPEG been through a camera or editor compression pipeline at all, or was it written once, fresh, by a generator?**

**Files:**
- Create: `app/services/compression_history.py`
- Create: `tests/test_compression_history.py`
- Modify: `app/services/layer2_fingerprint.py` (call it, expose `compression_score` and `compression_evidence`)

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: `CompressionHistoryAnalyzer.analyze(jpg_path) -> {"score": float, "evidence": str, "double_compressed": Optional[bool], "quality_estimate": Optional[int], "dq_strength": float}`. Task 5's `_compression` reads `layer2_result["compression_score"]` and `["compression_evidence"]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_compression_history.py
"""Double-JPEG compression history.

A photograph reaching a competition has been compressed at least twice: once by
the camera or the RAW converter, and again on export. An image written once by a
generator has a single-compression signature.

Detected via periodic double peaks and missing bins in DCT coefficient histograms
(Lukas & Fridrich 2003; Popescu & Farid 2004). Threshold interpretation follows
the likelihood-ratio framework of Bianchi & Piva, IEEE TIFS 2012.
"""
import io

import numpy as np
import pytest
from PIL import Image

from app.services.compression_history import CompressionHistoryAnalyzer


@pytest.fixture
def analyzer():
    return CompressionHistoryAnalyzer()


def _scene(seed=0, size=(512, 512)):
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 255, (*size, 3), dtype=np.uint8)
    import cv2
    return cv2.GaussianBlur(base, (0, 0), 2.0)


def _save(image, quality, path):
    Image.fromarray(image).save(str(path), "JPEG", quality=quality)
    return str(path)


def test_single_compression_is_detected(analyzer, tmp_path):
    """A generator's output: written once, never round-tripped."""
    path = _save(_scene(1), 95, tmp_path / "single.jpg")

    result = analyzer.analyze(path)

    assert result["double_compressed"] is False, result
    assert result["score"] < 0.5


def test_double_compression_is_detected(analyzer, tmp_path):
    """A camera JPEG opened in an editor and re-exported."""
    first = _save(_scene(2), 70, tmp_path / "first.jpg")
    reopened = np.array(Image.open(first).convert("RGB"))
    second = _save(reopened, 92, tmp_path / "second.jpg")

    result = analyzer.analyze(second)

    assert result["double_compressed"] is True, result
    assert result["score"] >= 0.5


def test_quality_is_estimated(analyzer, tmp_path):
    path = _save(_scene(3), 85, tmp_path / "q85.jpg")
    assert 70 <= analyzer.analyze(path)["quality_estimate"] <= 99


def test_unreadable_file_is_inconclusive_not_a_failure(analyzer, tmp_path):
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a jpeg")

    result = analyzer.analyze(str(broken))

    assert result["score"] == 0.5
    assert result["double_compressed"] is None


def test_non_jpeg_input_is_inconclusive(analyzer, tmp_path):
    path = tmp_path / "image.png"
    Image.fromarray(_scene(4)).save(str(path), "PNG")

    assert analyzer.analyze(str(path))["score"] == 0.5


def test_result_is_json_serialisable(analyzer, tmp_path):
    import json
    json.dumps(analyzer.analyze(_save(_scene(5), 90, tmp_path / "x.jpg")))
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/test_compression_history.py -v -p no:cacheprovider
```

Expected: `ModuleNotFoundError: app.services.compression_history`.

- [ ] **Step 3: Implement the analyzer**

Extract DCT coefficient histograms per frequency using the quantisation tables read from the file, then measure double-quantisation periodicity. Use `jpeglib` if available; otherwise compute the block DCT with OpenCV and read the tables via PIL's `quantization` attribute.

```python
# app/services/compression_history.py
"""Double-JPEG compression history.

A photograph reaching a competition has been compressed at least twice: the camera
or RAW converter writes one JPEG, and the export writes another. An image written
once, fresh, by a generator has a single-compression signature.

Double quantisation leaves periodic double peaks and empty bins in the DCT
coefficient histograms (Lukas & Fridrich 2003; Popescu & Farid 2004). We measure
the strength of that periodicity rather than localising tampered blocks, because
the question here is whether the file has a camera pipeline behind it at all.
Threshold interpretation follows Bianchi & Piva, IEEE TIFS 2012.

Inconclusive results score 0.5 and are reported as such. A non-JPEG, an unreadable
file or a texture-free image is an absence of information, not evidence of forgery.
"""

import logging
from typing import Dict, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class CompressionHistoryAnalyzer:

    # Periodicity strength above which the histogram is judged double-quantised.
    # Calibrated in Step 4 against single- and double-compressed fixtures.
    DQ_THRESHOLD = 0.28

    # Low-frequency AC coefficients carry the clearest DQ signature; DC is skipped
    # because it is dominated by scene content.
    AC_INDICES = [(0, 1), (1, 0), (1, 1), (0, 2), (2, 0), (1, 2), (2, 1), (2, 2)]

    def _inconclusive(self, reason: str) -> Dict:
        return {"score": 0.5, "evidence": f"Compression history inconclusive: {reason}",
                "double_compressed": None, "quality_estimate": None, "dq_strength": 0.0}

    def analyze(self, jpg_path: str) -> Dict:
        try:
            with Image.open(jpg_path) as img:
                if img.format != "JPEG":
                    return self._inconclusive(f"not a JPEG ({img.format})")
                tables = getattr(img, "quantization", None)
                gray = np.array(img.convert("L"), dtype=np.float32)
        except Exception as e:
            return self._inconclusive(f"unreadable ({type(e).__name__})")

        if tables:
            luma = np.array(tables[0], dtype=np.float32).reshape(8, 8) if len(tables[0]) == 64 else None
        else:
            luma = None

        quality = self._estimate_quality(luma)
        strength = self._dq_strength(gray, luma)

        if strength is None:
            return self._inconclusive("insufficient texture for histogram analysis")

        double = strength >= self.DQ_THRESHOLD
        if double:
            evidence = (f"Double-compression signature present (DQ strength {strength:.2f}, "
                        f"quality ~{quality}) — consistent with a camera or editor pipeline")
            score = 1.0
        else:
            evidence = (f"Single-compression signature (DQ strength {strength:.2f}, quality ~{quality}) — "
                        "no evidence this file passed through a camera or editor pipeline")
            score = 0.2

        return {"score": score, "evidence": evidence, "double_compressed": bool(double),
                "quality_estimate": quality, "dq_strength": round(float(strength), 4)}

    def _estimate_quality(self, luma: Optional[np.ndarray]) -> Optional[int]:
        """Approximate the IJG quality factor from the luminance table."""
        if luma is None:
            return None
        total = float(luma.sum())
        if total <= 0:
            return None
        scale = total / 64.0
        quality = 100.0 - scale * 2.0
        return int(max(1, min(100, round(quality))))

    def _dq_strength(self, gray: np.ndarray, luma: Optional[np.ndarray]) -> Optional[float]:
        """Periodicity of DCT coefficient histograms across low-frequency AC bins."""
        h, w = (gray.shape[0] // 8) * 8, (gray.shape[1] // 8) * 8
        if h < 64 or w < 64:
            return None
        blocks = gray[:h, :w].reshape(h // 8, 8, w // 8, 8).swapaxes(1, 2).reshape(-1, 8, 8)
        if blocks.shape[0] < 64:
            return None

        strengths = []
        for u, v in self.AC_INDICES:
            coeffs = np.array([cv2.dct(b - 128.0)[u, v] for b in blocks])
            if luma is not None and luma[u, v] > 0:
                coeffs = coeffs / float(luma[u, v])
            coeffs = np.round(coeffs).astype(np.int32)
            span = coeffs.max() - coeffs.min()
            if span < 6:
                continue

            hist = np.bincount(coeffs - coeffs.min(), minlength=int(span) + 1).astype(np.float64)
            if hist.sum() < 32:
                continue
            hist /= hist.sum()

            # Double quantisation makes the histogram periodic: energy concentrates at
            # a non-zero frequency of its own spectrum.
            spectrum = np.abs(np.fft.rfft(hist - hist.mean()))
            if spectrum.size < 3 or spectrum[1:].sum() <= 0:
                continue
            strengths.append(float(spectrum[1:].max() / spectrum[1:].sum()))

        return float(np.median(strengths)) if strengths else None
```

- [ ] **Step 4: Calibrate `DQ_THRESHOLD` against real files**

The 0.28 above is a starting value, not a measurement. Run this and set the threshold from the observed separation:

```bash
cd src/backend/ai-detection-service && ./venv/bin/python - <<'PY'
import sys; sys.path.insert(0,'.')
from app.services.compression_history import CompressionHistoryAnalyzer
a = CompressionHistoryAnalyzer()
for label, path in [
    ("SYNTHETIC single-write", "/home/rasan/Downloads/test/1_5_AVAR_high_realism_synthetic_Canon_R5_test.jpg.jpeg"),
    ("GENUINE camera JPEG", "/home/rasan/Downloads/test/Twisted Crowns-2511305-Mono.JPG"),
    ("GENUINE Photoshop export", "/home/rasan/Downloads/test/original-photoshop-edit-Twisted Crowns-2511305-Monocrom.jpg"),
    ("GENUINE Emerald camera", "/home/rasan/Downloads/test/Emerald Edge-2511305-Colour.JPG"),
    ("GENUINE Emerald edit", "/home/rasan/Downloads/test/Emerald Dialogue.jpg"),
]:
    r = a.analyze(path)
    print(f"  {label:28} dq={r['dq_strength']:.4f} double={r['double_compressed']} q~{r['quality_estimate']}")
PY
```

Set `DQ_THRESHOLD` midway between the highest synthetic value and the lowest genuine value, and record both numbers in the class comment. **If the ranges overlap, this signal does not discriminate on this data — set its weight to 0 in Task 5's `WEIGHTS`, document why in the commit message, and move on.** Do not ship a threshold that does not separate.

- [ ] **Step 5: Wire into Layer 2**

In `DigitalFingerprintAnalyzer.analyze`, call the analyzer and add its output to the returned dict as `compression_score` and `compression_evidence`. Do not include it in Layer 2's own `_calculate_verdict` weighting — it feeds the Authenticity Score directly.

- [ ] **Step 6: Run the full suite and verify the five real pairs again**

```bash
cd src/backend/ai-detection-service && ./venv/bin/python -m pytest tests/ -p no:cacheprovider --no-header -q
```

Then re-run the Task 5 Step 6 verification table. The required bands must still hold.

- [ ] **Step 7: Commit and deploy**

```bash
git add src/backend/ai-detection-service/app/services/compression_history.py src/backend/ai-detection-service/tests/test_compression_history.py src/backend/ai-detection-service/app/services/layer2_fingerprint.py
git commit -m "feat: double-JPEG compression history as an authenticity signal"
```

---

## Task 8: Backfill stale verdicts

Submissions 39, 40 and 45 carry verdicts computed by earlier versions of the pipeline. Submission 45 in particular still reads APPROVED / AUTHENTIC on the judge panel despite being the synthetic test case, which is misleading in a demonstration.

**Files:**
- Create: `src/backend/ai-detection-service/scripts/backfill_verdicts.py`

**Interfaces:**
- Consumes: the live `/api/v1/analyze` endpoint and the `submissions` table
- Produces: nothing consumed by other tasks

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python
"""Re-analyse stored submissions against the current pipeline.

Stored verdicts are not recomputed when the pipeline changes, so records written
by an earlier version stay on the judge panel indefinitely. This re-runs analysis
for selected submissions and updates their verdict, confidence and details.

Usage (from src/backend/ai-detection-service, on the server):
    ./venv/bin/python scripts/backfill_verdicts.py --dry-run --ids 39 40 45
    ./venv/bin/python scripts/backfill_verdicts.py --ids 39 40 45

Always run --dry-run first and read the diff. This mutates judge-visible records.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg
import httpx

DETECTION_URL = os.getenv("DETECTION_URL", "http://127.0.0.1:8001/api/v1/analyze")
VERDICT_MAP = {"AUTHENTIC": ("APPROVED", "AUTHENTIC"),
               "REJECT": ("REJECTED", "AI_GENERATED"),
               "QUARANTINE": ("PENDING", "SUSPICIOUS")}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", type=int, nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dsn", default=os.getenv("BACKFILL_DSN"))
    args = parser.parse_args()

    if not args.dsn:
        sys.exit("set BACKFILL_DSN, e.g. postgresql://user:pass@localhost/avar_db")

    conn = await asyncpg.connect(args.dsn)
    rows = await conn.fetch(
        "select id, title, jpg_file_url, raw_file_url, status::text, verification_verdict::text "
        "from submissions where id = any($1::int[]) order by id", args.ids)

    for row in rows:
        jpg, raw = row["jpg_file_url"], row["raw_file_url"]
        if not jpg or not Path(jpg).exists():
            print(f"  {row['id']}: SKIP - jpg missing at {jpg}")
            continue
        if not raw or not Path(raw).exists():
            print(f"  {row['id']}: SKIP - raw missing at {raw}")
            continue

        files = {"jpg_file": (Path(jpg).name, open(jpg, "rb"), "image/jpeg"),
                 "raw_file": (Path(raw).name, open(raw, "rb"), "application/octet-stream")}
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(DETECTION_URL, files=files)
        if response.status_code != 200:
            print(f"  {row['id']}: FAILED - HTTP {response.status_code}")
            continue

        result = response.json()
        status, verdict = VERDICT_MAP.get(result["verdict"], ("PENDING", "NEEDS_REVIEW"))
        score = (result.get("authenticity") or {}).get("score")
        print(f"  {row['id']} {row['title'][:26]:26} "
              f"{row['status']}/{row['verification_verdict']} -> {status}/{verdict} (score {score})")

        if not args.dry_run:
            await conn.execute(
                "update submissions set status=$1::submissionstatus, "
                "verification_verdict=$2::verificationverdict, verification_confidence=$3, "
                "verification_details=$4, verification_timestamp=$5 where id=$6",
                status, verdict, result.get("confidence_score", 0.0),
                json.dumps(result), result.get("timestamp", ""), row["id"])

    await conn.close()
    print("\ndry run - nothing written" if args.dry_run else "\nrecords updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

- [ ] **Step 2: Back up the affected rows before touching them**

```bash
ssh root@165.245.178.225 "sudo -u postgres pg_dump avar_db -t submissions --data-only > /root/backups/submissions-pre-backfill-\$(date +%s).sql && ls -l /root/backups/ | tail -2"
```

- [ ] **Step 3: Dry run on the server and read the diff**

```bash
ssh root@165.245.178.225 "cd /var/www/avar/src/backend/ai-detection-service && BACKFILL_DSN=\$(grep DATABASE_URL ../competition-service/.env | sed 's|.*=||; s|+asyncpg||') ./venv/bin/python scripts/backfill_verdicts.py --dry-run --ids 39 40 45"
```

Expected: 45 shows `APPROVED/AUTHENTIC -> REJECTED/AI_GENERATED`; 39 and 40 move to APPROVED if they are genuine edits.

- [ ] **Step 4: Apply, then confirm on the judge panel**

Re-run without `--dry-run`, then open `https://avar.studio/judge/score/45` and confirm it reads REJECTED with the provenance reasons listed.

- [ ] **Step 5: Commit**

```bash
git add src/backend/ai-detection-service/scripts/backfill_verdicts.py
git commit -m "feat: script to re-analyse stored submissions after pipeline changes"
```

---

## Deferred, with reasons

Recorded so these are decisions rather than oversights.

| Item | Why deferred |
|---|---|
| **C2PA verification** | Rated highest-confidence by the reference material and genuinely valuable, but most genuine photographs carry no manifest, so it can only raise confidence and never reject. Needs `c2pa-python` and a trust-list decision. Add as an eighth signal weighted 10, taken from `raw_provenance`, once the score exists. |
| **Photon-transfer noise fit on the RAW** | The strongest remaining anti-synthetic-RAW check (Foi et al. 2008). Deferred only because provenance already rejects the known attack; this closes the case where an attacker fixes aspect ratio, resolution and writer software. |
| **Judge-UI crop overlay** | `crop_rect_norm` is published and normalised; drawing it needs frontend work and a local build plus rsync deploy. High presentation value, no correctness impact. |
| **Transplant-flag downgrade (submission 36)** | Now that the RAW cross-check confirms the JPEG's metadata matches its RAW, the dimension-mismatch and exiftool-XMP indicators should become advisory. Waits for the Authenticity Score so it becomes a weight change rather than a verdict change. |
| **Burst-sequence / sibling-frame verification** | Strongest available anti-forgery measure, but it changes the submission contract and the UI. A competition-rules decision, not a code decision. |
| **Public `/detect/` endpoint** | nginx proxies it unauthenticated to port 8001, and each request consumes up to 1.3 GB. Task 1 contains the memory blast radius; restricting or authenticating the route is a separate infrastructure change. |

---

## Self-Review

**Spec coverage.** Tier A items 1–5 from the agreed plan map to Tasks 2, 5, 6, 3, 4. Tier B items 6–8 map to Task 7 (double-JPEG), the deferred table (photon transfer, C2PA). Operational findings from the production audit map to Task 1 (memory) and Task 8 (stale records), with the public-endpoint finding recorded as deferred. Tier C exclusions are recorded in Build Order Rationale.

**Type consistency.** `AuthenticityScorer.score()` returns `score`/`band`/`verdict`/`action`/`signals`/`missing` and is consumed only in `main.py`. `_compression` reads `compression_score` and `compression_evidence`, which Task 7 Step 5 produces. `_from_layer2` reads `prnu_score` and `fft_score`, both of which survive Task 6. `_third_party` reads `ai_score`, which Task 4 preserves. `classify_hive_score` returns `(str, float)`, matching its test.

**Known open question, flagged rather than hidden.** Task 5's PRNU weight of 10 is assigned before Task 6 makes PRNU functional. Between Tasks 5 and 6 that signal contributes a constant 0.5 for every submission, which shifts all scores by the same amount and does not affect ranking. Task 5 Step 4 calls this out. If it pushes a genuine pair below its band, reduce the PRNU weight to 5 and give the 5 to `geometric_linkage` until Task 6 lands.
