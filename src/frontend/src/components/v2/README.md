# V2.0 Feature Components

Vue 3 components for NPAS Competition Service v2.0 innovations: Camera Reputation, Judge Consensus Analysis, and Credential Sharing Detection.

## Overview

This directory contains 7 reusable Vue components that integrate with the v2.0 backend APIs:

1. **CameraReputationBadge** - Compact trust score display
2. **CameraReputationCard** - Detailed PRNU fingerprint analysis
3. **ConsensusIndicator** - Compact consensus status display
4. **ConsensusAnalysisCard** - Detailed ICC and score agreement
5. **JudgeProfileBadge** - Judge bias and consistency display
6. **CredentialSharingAlert** - Security risk warnings
7. **BiasReportDashboard** - Competition-wide bias analytics

## Installation

Components are already integrated into the project. Import them using:

```typescript
import {
  CameraReputationBadge,
  CameraReputationCard,
  ConsensusIndicator,
  ConsensusAnalysisCard,
  JudgeProfileBadge,
  CredentialSharingAlert,
  BiasReportDashboard
} from '@/components/v2'
```

## Store

Use the v2 analytics store for API calls:

```typescript
import { useV2AnalyticsStore } from '@/stores/v2Analytics'

const v2Store = useV2AnalyticsStore()

// Extract camera fingerprint
await v2Store.extractCameraFingerprint(submissionId)

// Get consensus analysis
const consensus = await v2Store.getConsensusAnalysis(submissionId)

// Check credential sharing
const detection = await v2Store.analyzeCredentialSharing(judgeId, competitionId)
```

## Component Usage

### 1. CameraReputationBadge

Compact badge showing camera trust level and boost.

**Props:**
- `trustScore` (number, 0-1): Camera trust score
- `boost` (number): Confidence boost applied (-0.1 to +0.15)
- `cameraMake` (string): Camera manufacturer
- `cameraModel` (string): Camera model
- `verified` (boolean): PRNU verification status
- `size` ('sm' | 'md' | 'lg'): Badge size

**Example:**
```vue
<template>
  <CameraReputationBadge
    :trust-score="0.92"
    :boost="0.15"
    camera-make="Canon"
    camera-model="EOS R5"
    :verified="true"
    size="md"
  />
</template>
```

**Output:**
- Badge color: Green (high trust), Blue (medium), Yellow (low), Red (suspicious)
- Trust percentage: "92%"
- Boost indicator: "+15%" (green if positive, red if negative)

---

### 2. CameraReputationCard

Detailed card with PRNU energy, fraud detection, and trust breakdown.

**Props:**
- `submissionId` (number, required): Submission ID
- `cameraMake` (string): Camera manufacturer
- `cameraModel` (string): Camera model
- `trustScore` (number): Trust score (0-1)
- `boost` (number): Confidence boost
- `prnuEnergy` (number): PRNU energy value
- `verified` (boolean): Verification status
- `fraudCheck` (object): Fraud detection results
  - `fraud_likelihood` (number)
  - `fraud_verdict` (string)
  - `indicators` (string[])
  - `recommendation` (string)

**Example:**
```vue
<template>
  <CameraReputationCard
    :submission-id="123"
    camera-make="Canon"
    camera-model="EOS R5"
    :trust-score="0.87"
    :boost="0.15"
    :prnu-energy="0.0234"
    :verified="true"
    :fraud-check="fraudData"
  />
</template>

<script setup>
const fraudData = {
  fraud_likelihood: 0.15,
  fraud_verdict: 'low_fraud_risk',
  indicators: [],
  recommendation: 'approve'
}
</script>
```

**Features:**
- Expandable details (click "Show Details")
- PRNU energy visualization
- Trust score breakdown
- Fraud indicators (if detected)
- Boost explanation

---

### 3. ConsensusIndicator

Compact indicator showing judge consensus status.

**Props:**
- `icc` (number, 0-1): Intraclass Correlation Coefficient
- `verdict` (string): Consensus verdict
  - 'strong_consensus'
  - 'moderate_consensus'
  - 'weak_consensus'
  - 'poor_consensus'
- `judgeCount` (number): Number of judges
- `outlierCount` (number): Number of outlier judges
- `flaggedForReview` (boolean): Manual review flag
- `size` ('sm' | 'md' | 'lg'): Indicator size

**Example:**
```vue
<template>
  <ConsensusIndicator
    :icc="0.75"
    verdict="strong_consensus"
    :judge-count="3"
    :outlier-count="0"
    :flagged-for-review="false"
  />
</template>
```

**Output:**
- Badge: "Strong Consensus" (green checkmark)
- ICC value: "ICC: 0.75"
- Judge count: "3 judges"

---

### 4. ConsensusAnalysisCard

Detailed card with ICC, score statistics, and outlier detection.

**Props:**
- `submissionId` (number, required): Submission ID
- `judgeCount` (number): Total judges
- `scoreMean` (number): Average score
- `scoreStd` (number): Standard deviation
- `iccValue` (number): ICC score (0-1)
- `consensusVerdict` (string): Verdict
- `outlierJudges` (number[]): Outlier judge IDs
- `outlierScores` (number[]): Outlier scores
- `flaggedForReview` (boolean): Manual review flag
- `confidenceLevel` (number): Confidence in verdict
- `judgeScores` (array): Individual judge scores
  - `judge_id` (number)
  - `score` (number)
  - `is_outlier` (boolean)

**Example:**
```vue
<template>
  <ConsensusAnalysisCard
    :submission-id="104"
    :judge-count="3"
    :score-mean="6.5"
    :score-std="2.87"
    :icc-value="0.35"
    consensus-verdict="poor_consensus"
    :outlier-judges="[12]"
    :flagged-for-review="true"
    :confidence-level="0.45"
    :judge-scores="scores"
  />
</template>

<script setup>
const scores = [
  { judge_id: 10, score: 8.5, is_outlier: false },
  { judge_id: 11, score: 8.0, is_outlier: false },
  { judge_id: 12, score: 3.0, is_outlier: true }
]
</script>
```

**Features:**
- ICC visualization with progress bar
- Score statistics (mean, std dev, range)
- Individual judge scores
- Outlier explanation
- Poor consensus alert (if ICC < 0.4)

---

### 5. JudgeProfileBadge

Badge showing judge bias category and consistency.

**Props:**
- `biasScore` (number): Z-score bias (-3 to +3)
- `biasCategory` (string): 'harsh' | 'neutral' | 'lenient'
- `consistencyScore` (number, 0-1): Scoring consistency
- `submissionCount` (number): Submissions scored
- `size` ('sm' | 'md' | 'lg'): Badge size
- `showDetails` (boolean): Show detailed metrics

**Example:**
```vue
<template>
  <JudgeProfileBadge
    :bias-score="-2.5"
    bias-category="harsh"
    :consistency-score="0.92"
    :submission-count="15"
    show-details
  />
</template>
```

**Output:**
- Badge: "Significant" (red, trending down icon)
- Bias score: "-2.5"
- Consistency: "92% (Excellent)"
- Warning if |bias_score| > 2.0

---

### 6. CredentialSharingAlert

Alert for suspicious judge activity patterns.

**Props:**
- `riskScore` (number, 0-1, required): Overall risk score
- `riskLevel` (string, required): 'high' | 'medium' | 'low'
- `riskFactors` (string[]): List of detected issues
- `uniqueIpCount` (number): Unique IP addresses
- `uniqueSessionCount` (number): Unique sessions
- `uniqueUserAgentCount` (number): Unique user agents
- `timeGapAnomalies` (array): Impossible time gaps
- `geoAnomalies` (array): Geographic inconsistencies
- `investigationStatus` (string): Investigation status
- `compact` (boolean): Compact view

**Example:**
```vue
<template>
  <CredentialSharingAlert
    :risk-score="0.72"
    risk-level="high"
    :risk-factors="[
      'Multiple IP addresses detected (4)',
      'Multiple user agents (4)',
      '3 impossible time gaps detected'
    ]"
    :unique-ip-count="4"
    :unique-session-count="4"
    :unique-user-agent-count="4"
    :time-gap-anomalies="anomalies"
    investigation-status="pending"
  />
</template>
```

**Features:**
- Risk score visualization (percentage)
- Activity metrics (IPs, sessions, devices)
- Risk factors list
- Recommendation based on risk level
- Investigation status badge

---

### 7. BiasReportDashboard

Full-page dashboard for competition-wide bias analysis.

**Props:**
- `competitionId` (number, required): Competition ID

**Example:**
```vue
<template>
  <BiasReportDashboard :competition-id="1" />
</template>
```

**Features:**
- Overall health metrics (judges, bias, consistency, flagged)
- Bias distribution (harsh/neutral/lenient)
- Individual judge profiles (sorted by bias)
- Flagged submissions list
- Auto-refresh functionality

**API Integration:**
Automatically fetches data from `/api/v1/judges-analytics/competition/{id}/bias-report`

---

## Integration Examples

### MySubmissions View

Add camera reputation to submission cards:

```vue
<script setup>
import { CameraReputationBadge, CameraReputationCard } from '@/components/v2'
import { useV2AnalyticsStore } from '@/stores/v2Analytics'

const v2Store = useV2AnalyticsStore()

// Load fingerprint for submission
const loadFingerprint = async (submissionId: number) => {
  try {
    const fingerprint = await v2Store.getCameraFingerprint(submissionId)
    return fingerprint
  } catch (err) {
    console.error('Failed to load fingerprint:', err)
  }
}
</script>

<template>
  <div v-for="submission in submissions" :key="submission.id">
    <!-- Existing submission card -->

    <!-- Add camera reputation -->
    <CameraReputationBadge
      v-if="submission.camera_trust_score"
      :trust-score="submission.camera_trust_score"
      :boost="submission.trust_boost"
      :camera-make="submission.camera_make"
      :camera-model="submission.camera_model"
    />
  </div>
</template>
```

### Judge Dashboard

Add consensus indicators to scored submissions:

```vue
<script setup>
import { ConsensusIndicator, ConsensusAnalysisCard } from '@/components/v2'
import { useV2AnalyticsStore } from '@/stores/v2Analytics'

const v2Store = useV2AnalyticsStore()

const loadConsensus = async (submissionId: number) => {
  try {
    const consensus = await v2Store.getConsensusAnalysis(submissionId)
    return consensus
  } catch (err) {
    // Consensus might not exist if not all judges scored yet
    return null
  }
}
</script>

<template>
  <div v-for="submission in submissions" :key="submission.id">
    <!-- Existing submission info -->

    <!-- Add consensus indicator -->
    <ConsensusIndicator
      v-if="submission.consensus"
      :icc="submission.consensus.icc_value"
      :verdict="submission.consensus.consensus_verdict"
      :judge-count="submission.consensus.judge_count"
      :outlier-count="submission.consensus.outlier_judges?.length || 0"
      :flagged-for-review="submission.consensus.flagged_for_review"
    />
  </div>
</template>
```

### Admin Panel

Add bias report and credential monitoring:

```vue
<script setup>
import { BiasReportDashboard, CredentialSharingAlert } from '@/components/v2'
import { useV2AnalyticsStore } from '@/stores/v2Analytics'

const v2Store = useV2AnalyticsStore()
const competitionId = ref(1)

const flaggedJudges = ref([])

const loadFlaggedJudges = async () => {
  flaggedJudges.value = await v2Store.listFlaggedJudges(competitionId.value)
}

onMounted(loadFlaggedJudges)
</script>

<template>
  <div class="space-y-6">
    <!-- Bias Report -->
    <BiasReportDashboard :competition-id="competitionId" />

    <!-- Credential Alerts -->
    <div v-for="detection in flaggedJudges" :key="detection.id">
      <CredentialSharingAlert
        :risk-score="detection.risk_score"
        :risk-level="detection.risk_level"
        :risk-factors="detection.risk_factors"
        :unique-ip-count="detection.unique_ip_count"
        :unique-session-count="detection.unique_session_count"
        :unique-user-agent-count="detection.unique_user_agent_count"
        :investigation-status="detection.investigation_status"
      />
    </div>
  </div>
</template>
```

---

## Styling

Components use **shadcn-vue** UI primitives and **Tailwind CSS**:

- **Badge**: Status indicators with variants (default, secondary, destructive, outline)
- **Card**: Container with header, content sections
- **Alert**: Warning/error messages with variants
- **Progress**: Visual progress bars for scores/metrics
- **Icons**: Lucide icons for visual cues

All components support dark mode automatically.

---

## Data Flow

```
User Action → Store API Call → Backend API → Database
                ↓
           Cache in Store
                ↓
        Update Component Props
                ↓
        Re-render UI
```

### Caching Strategy

- Store caches responses in Maps (keyed by ID)
- Cache checked before API call
- Clear cache with `v2Store.clearAllCache()`
- Cache cleared on logout (recommended)

---

## Error Handling

All components gracefully handle missing data:

```vue
<!-- Show badge only if data exists -->
<CameraReputationBadge
  v-if="submission.camera_trust_score"
  :trust-score="submission.camera_trust_score"
  ...
/>

<!-- Show alert only for high/medium risk -->
<CredentialSharingAlert
  v-if="detection && detection.risk_level !== 'low'"
  :risk-score="detection.risk_score"
  ...
/>
```

Store methods throw errors that can be caught:

```typescript
try {
  await v2Store.extractCameraFingerprint(submissionId)
} catch (err) {
  console.error('Fingerprint extraction failed:', err)
  // Show user-friendly error message
}
```

---

## Performance Considerations

1. **Lazy Loading**: Load v2 data on-demand, not on page load
2. **Caching**: Store caches responses to reduce API calls
3. **Conditional Rendering**: Only render components when data is available
4. **Background Processing**: PRNU extraction is async (2-4 seconds)
5. **Pagination**: Use pagination for large datasets (bias reports, consensus lists)

---

## Testing

Unit tests for components (example):

```typescript
import { mount } from '@vue/test-utils'
import { CameraReputationBadge } from '@/components/v2'

describe('CameraReputationBadge', () => {
  it('shows high trust badge for score > 0.8', () => {
    const wrapper = mount(CameraReputationBadge, {
      props: { trustScore: 0.92, boost: 0.15 }
    })
    expect(wrapper.text()).toContain('High Trust')
    expect(wrapper.text()).toContain('+15%')
  })

  it('shows suspicious badge for score < 0.4', () => {
    const wrapper = mount(CameraReputationBadge, {
      props: { trustScore: 0.25, boost: -0.10 }
    })
    expect(wrapper.text()).toContain('Suspicious')
  })
})
```

---

## API Reference

See backend documentation: `/docs/V2_FEATURES.md`

All APIs require authentication (Bearer token in header).

### Endpoints

- **POST** `/api/v1/cameras/fingerprints/{submission_id}` - Extract fingerprint
- **GET** `/api/v1/cameras/trust-profile/{make}/{model}` - Get camera profile
- **GET** `/api/v1/cameras/fraud-check/{submission_id}` - Fraud detection
- **GET** `/api/v1/judges-analytics/profile/{judge_id}/{competition_id}` - Judge profile
- **GET** `/api/v1/judges-analytics/consensus/{submission_id}` - Consensus analysis
- **POST** `/api/v1/judges-analytics/credential-sharing/.../analyze` - Run risk analysis
- **GET** `/api/v1/judges-analytics/competition/{id}/bias-report` - Bias report

---

## Troubleshooting

### Component not rendering
- Check if data props are provided
- Check browser console for errors
- Verify store API calls are successful

### API calls failing
- Check authentication token
- Verify backend is running
- Check network tab for 401/403/500 errors

### Icons not showing
- Ensure lucide-vue-next is installed
- Check import statements

### Styling broken
- Verify Tailwind CSS is configured
- Check shadcn-vue components are installed

---

## Version

**V2.0.0** - Initial release
**Date**: 2026-02-24
**Author**: NPAS Research Team

---

For backend API documentation, see:
- `/docs/V2_FEATURES.md` - Complete feature documentation
- `/docs/INTEGRATION_TESTING_GUIDE.md` - API testing guide
