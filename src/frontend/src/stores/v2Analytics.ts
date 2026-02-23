import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

// Types
export interface CameraFingerprint {
  id: number
  submission_id: number
  user_id: number
  camera_make: string
  camera_model: string
  prnu_energy: number
  prnu_hash: string
  similarity_to_profile?: number
  trust_boost_applied: number
  verified: boolean
  created_at: string
}

export interface CameraTrustProfile {
  camera_make: string
  camera_model: string
  total_submissions: number
  authentic_count: number
  suspicious_count: number
  trust_score: number
  avg_prnu_energy: number
  consistency_score: number
}

export interface FraudCheck {
  submission_id: number
  fraud_likelihood: number
  fraud_verdict: string
  indicators: string[]
  recommendation: string
  explanation: string
}

export interface JudgeScoringProfile {
  id: number
  judge_id: number
  competition_id: number
  submission_count: number
  avg_score_given: number
  bias_score: number
  bias_category: string
  consistency_score: number
}

export interface ConsensusAnalysis {
  id: number
  competition_id: number
  submission_id: number
  judge_count: number
  score_mean?: number
  score_std?: number
  icc_value?: number
  consensus_verdict?: string
  consensus_quality: string
  outlier_judges?: number[]
  outlier_scores?: number[]
  flagged_for_review: boolean
  confidence_level?: number
  created_at: string
}

export interface CredentialSharingDetection {
  id: number
  judge_id: number
  competition_id: number
  unique_ip_count: number
  unique_session_count: number
  unique_user_agent_count: number
  risk_score: number
  risk_level: string
  risk_factors?: string[]
  time_gap_anomalies?: any[]
  geographic_inconsistencies?: any[]
  alert_triggered: boolean
  investigation_status: string
  investigation_notes?: string
}

export const useV2AnalyticsStore = defineStore('v2Analytics', () => {
  // State
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Camera Reputation
  const cameraFingerprints = ref<Map<number, CameraFingerprint>>(new Map())
  const cameraTrustProfiles = ref<Map<string, CameraTrustProfile>>(new Map())
  const fraudChecks = ref<Map<number, FraudCheck>>(new Map())

  // Judge Analytics
  const judgeProfiles = ref<Map<string, JudgeScoringProfile>>(new Map())
  const consensusAnalyses = ref<Map<number, ConsensusAnalysis>>(new Map())
  const credentialDetections = ref<Map<string, CredentialSharingDetection>>(new Map())

  // Camera Reputation APIs
  async function extractCameraFingerprint(submissionId: number): Promise<CameraFingerprint> {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.post(`/api/v1/cameras/fingerprints/${submissionId}`)
      const fingerprint: CameraFingerprint = response.data
      cameraFingerprints.value.set(submissionId, fingerprint)
      return fingerprint
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to extract fingerprint'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getCameraFingerprint(submissionId: number): Promise<CameraFingerprint> {
    // Check cache first
    if (cameraFingerprints.value.has(submissionId)) {
      return cameraFingerprints.value.get(submissionId)!
    }

    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/cameras/fingerprint/${submissionId}`)
      const fingerprint: CameraFingerprint = response.data
      cameraFingerprints.value.set(submissionId, fingerprint)
      return fingerprint
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to get fingerprint'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getCameraTrustProfile(make: string, model: string): Promise<CameraTrustProfile> {
    const key = `${make}|${model}`

    // Check cache first
    if (cameraTrustProfiles.value.has(key)) {
      return cameraTrustProfiles.value.get(key)!
    }

    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/cameras/trust-profile/${make}/${model}`)
      const profile: CameraTrustProfile = response.data
      cameraTrustProfiles.value.set(key, profile)
      return profile
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to get camera profile'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function checkFraud(submissionId: number): Promise<FraudCheck> {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/cameras/fraud-check/${submissionId}`)
      const fraudCheck: FraudCheck = response.data
      fraudChecks.value.set(submissionId, fraudCheck)
      return fraudCheck
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to check fraud'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Judge Consensus APIs
  async function getJudgeProfile(judgeId: number, competitionId: number): Promise<JudgeScoringProfile> {
    const key = `${judgeId}|${competitionId}`

    // Check cache first
    if (judgeProfiles.value.has(key)) {
      return judgeProfiles.value.get(key)!
    }

    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/judges-analytics/profile/${judgeId}/${competitionId}`)
      const profile: JudgeScoringProfile = response.data
      judgeProfiles.value.set(key, profile)
      return profile
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to get judge profile'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function refreshJudgeProfile(judgeId: number, competitionId: number): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await axios.post(`/api/v1/judges-analytics/profile/${judgeId}/${competitionId}/refresh`)
      // Clear cache to force reload
      judgeProfiles.value.delete(`${judgeId}|${competitionId}`)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to refresh profile'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getConsensusAnalysis(submissionId: number): Promise<ConsensusAnalysis> {
    // Check cache first
    if (consensusAnalyses.value.has(submissionId)) {
      return consensusAnalyses.value.get(submissionId)!
    }

    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/judges-analytics/consensus/${submissionId}`)
      const consensus: ConsensusAnalysis = response.data
      consensusAnalyses.value.set(submissionId, consensus)
      return consensus
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to get consensus analysis'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function listCompetitionConsensus(
    competitionId: number,
    flaggedOnly: boolean = false,
    skip: number = 0,
    limit: number = 50
  ): Promise<ConsensusAnalysis[]> {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(
        `/api/v1/judges-analytics/consensus/competition/${competitionId}`,
        { params: { flagged_only: flaggedOnly, skip, limit } }
      )
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to list consensus analyses'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Credential Sharing Detection APIs
  async function analyzeCredentialSharing(
    judgeId: number,
    competitionId: number,
    timeWindowDays: number = 30
  ): Promise<CredentialSharingDetection> {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.post(
        `/api/v1/judges-analytics/credential-sharing/${judgeId}/${competitionId}/analyze`,
        null,
        { params: { time_window_days: timeWindowDays } }
      )
      const detection: CredentialSharingDetection = response.data
      credentialDetections.value.set(`${judgeId}|${competitionId}`, detection)
      return detection
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to analyze credential sharing'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getCredentialSharingStatus(
    judgeId: number,
    competitionId: number
  ): Promise<CredentialSharingDetection> {
    const key = `${judgeId}|${competitionId}`

    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(
        `/api/v1/judges-analytics/credential-sharing/${judgeId}/${competitionId}`
      )
      const detection: CredentialSharingDetection = response.data
      credentialDetections.value.set(key, detection)
      return detection
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to get credential sharing status'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function listFlaggedJudges(
    competitionId: number,
    minRiskScore: number = 0.6
  ): Promise<CredentialSharingDetection[]> {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get(
        `/api/v1/judges-analytics/credential-sharing/competition/${competitionId}/flagged`,
        { params: { min_risk_score: minRiskScore } }
      )
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to list flagged judges'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateInvestigationStatus(
    detectionId: number,
    status: string,
    notes?: string
  ): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await axios.patch(
        `/api/v1/judges-analytics/credential-sharing/${detectionId}/investigate`,
        null,
        {
          params: {
            investigation_status: status,
            investigation_notes: notes
          }
        }
      )
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update investigation status'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Clear cache functions
  function clearCameraCache() {
    cameraFingerprints.value.clear()
    cameraTrustProfiles.value.clear()
    fraudChecks.value.clear()
  }

  function clearJudgeCache() {
    judgeProfiles.value.clear()
    consensusAnalyses.value.clear()
    credentialDetections.value.clear()
  }

  function clearAllCache() {
    clearCameraCache()
    clearJudgeCache()
  }

  return {
    // State
    isLoading,
    error,
    cameraFingerprints,
    cameraTrustProfiles,
    fraudChecks,
    judgeProfiles,
    consensusAnalyses,
    credentialDetections,

    // Camera Reputation
    extractCameraFingerprint,
    getCameraFingerprint,
    getCameraTrustProfile,
    checkFraud,

    // Judge Analytics
    getJudgeProfile,
    refreshJudgeProfile,
    getConsensusAnalysis,
    listCompetitionConsensus,

    // Credential Sharing
    analyzeCredentialSharing,
    getCredentialSharingStatus,
    listFlaggedJudges,
    updateInvestigationStatus,

    // Cache management
    clearCameraCache,
    clearJudgeCache,
    clearAllCache
  }
})
