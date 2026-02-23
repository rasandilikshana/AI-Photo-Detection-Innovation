-- Migration: 001_add_v2_innovations_up.sql
-- Adds Camera Reputation and Judge Analytics tables for v2.0
-- Created: 2026-02-23

BEGIN;

-- ============================================================================
-- Camera Reputation System Tables
-- ============================================================================

-- Table: camera_fingerprints
-- Stores PRNU (Photo Response Non-Uniformity) fingerprints for camera identification
CREATE TABLE IF NOT EXISTS camera_fingerprints (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_make VARCHAR(100) NOT NULL,
    camera_model VARCHAR(100) NOT NULL,
    prnu_signature BYTEA NOT NULL,
    prnu_energy FLOAT NOT NULL,
    prnu_hash VARCHAR(64) NOT NULL UNIQUE,
    similarity_to_profile FLOAT,
    trust_boost_applied FLOAT DEFAULT 0.0,
    capture_context JSONB,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_camera_fingerprints_submission ON camera_fingerprints(submission_id);
CREATE INDEX IF NOT EXISTS idx_camera_fingerprints_user ON camera_fingerprints(user_id);
CREATE INDEX IF NOT EXISTS idx_camera_fingerprints_camera ON camera_fingerprints(camera_make, camera_model);
CREATE INDEX IF NOT EXISTS idx_camera_fingerprints_hash ON camera_fingerprints(prnu_hash);

-- Table: camera_trust_profiles
-- Aggregated trust profiles for each camera make/model
CREATE TABLE IF NOT EXISTS camera_trust_profiles (
    id SERIAL PRIMARY KEY,
    camera_make VARCHAR(100) NOT NULL,
    camera_model VARCHAR(100) NOT NULL,
    total_submissions INTEGER DEFAULT 0,
    authentic_count INTEGER DEFAULT 0,
    suspicious_count INTEGER DEFAULT 0,
    ai_generated_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    avg_trust_score FLOAT DEFAULT 0.5,
    prnu_pattern_stability FLOAT DEFAULT 0.0,
    avg_prnu_energy FLOAT,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(camera_make, camera_model)
);

CREATE INDEX IF NOT EXISTS idx_camera_trust_profiles_camera ON camera_trust_profiles(camera_make, camera_model);
CREATE INDEX IF NOT EXISTS idx_camera_trust_profiles_trust_score ON camera_trust_profiles(avg_trust_score);

-- Table: prnu_comparisons
-- Records pairwise PRNU pattern comparisons
CREATE TABLE IF NOT EXISTS prnu_comparisons (
    id SERIAL PRIMARY KEY,
    fingerprint1_id INTEGER NOT NULL REFERENCES camera_fingerprints(id) ON DELETE CASCADE,
    fingerprint2_id INTEGER NOT NULL REFERENCES camera_fingerprints(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    distance_metric VARCHAR(50),
    correlation_coefficient FLOAT,
    same_camera BOOLEAN NOT NULL,
    same_user BOOLEAN NOT NULL,
    comparison_details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prnu_comparisons_fp1 ON prnu_comparisons(fingerprint1_id);
CREATE INDEX IF NOT EXISTS idx_prnu_comparisons_fp2 ON prnu_comparisons(fingerprint2_id);
CREATE INDEX IF NOT EXISTS idx_prnu_comparisons_similarity ON prnu_comparisons(similarity_score);

-- ============================================================================
-- Judge Analytics System Tables
-- ============================================================================

-- Table: judge_scoring_profiles
-- Statistical profiles of judge scoring behavior
CREATE TABLE IF NOT EXISTS judge_scoring_profiles (
    id SERIAL PRIMARY KEY,
    judge_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    submission_count INTEGER DEFAULT 0,
    avg_score_given FLOAT,
    score_std_dev FLOAT,
    score_range_min FLOAT,
    score_range_max FLOAT,
    bias_score FLOAT,
    consistency_score FLOAT,
    score_distribution JSONB,
    outlier_count INTEGER DEFAULT 0,
    extreme_scores_ratio FLOAT,
    avg_scoring_time_seconds FLOAT,
    scoring_time_variance FLOAT,
    last_analyzed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(judge_id, competition_id)
);

CREATE INDEX IF NOT EXISTS idx_judge_scoring_profiles_judge ON judge_scoring_profiles(judge_id);
CREATE INDEX IF NOT EXISTS idx_judge_scoring_profiles_competition ON judge_scoring_profiles(competition_id);
CREATE INDEX IF NOT EXISTS idx_judge_scoring_profiles_bias ON judge_scoring_profiles(bias_score);

-- Table: judge_consensus_analysis
-- Consensus analysis for multi-judge submissions
CREATE TABLE IF NOT EXISTS judge_consensus_analysis (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    judge_count INTEGER NOT NULL,
    scores_received JSONB NOT NULL,
    score_mean FLOAT,
    score_std_dev FLOAT,
    score_range FLOAT,
    icc_value FLOAT,
    score_agreement_ratio FLOAT,
    coefficient_of_variation FLOAT,
    outlier_judges INTEGER[],
    outlier_scores JSONB,
    consensus_verdict VARCHAR(50),
    confidence_level FLOAT,
    flagged_for_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(competition_id, submission_id)
);

CREATE INDEX IF NOT EXISTS idx_judge_consensus_competition ON judge_consensus_analysis(competition_id);
CREATE INDEX IF NOT EXISTS idx_judge_consensus_submission ON judge_consensus_analysis(submission_id);
CREATE INDEX IF NOT EXISTS idx_judge_consensus_flagged ON judge_consensus_analysis(flagged_for_review);

-- Table: credential_sharing_detection
-- Monitors judge activity for credential sharing
CREATE TABLE IF NOT EXISTS credential_sharing_detection (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    judge_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    unique_ip_count INTEGER,
    unique_session_count INTEGER,
    unique_user_agent_count INTEGER,
    ip_addresses TEXT[],
    session_ids TEXT[],
    time_gap_anomalies JSONB,
    geographic_inconsistencies JSONB,
    risk_score FLOAT,
    risk_level VARCHAR(50),
    risk_factors TEXT[],
    alert_triggered BOOLEAN DEFAULT FALSE,
    investigation_status VARCHAR(50) DEFAULT 'pending',
    investigation_notes TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credential_sharing_competition ON credential_sharing_detection(competition_id);
CREATE INDEX IF NOT EXISTS idx_credential_sharing_judge ON credential_sharing_detection(judge_id);
CREATE INDEX IF NOT EXISTS idx_credential_sharing_risk ON credential_sharing_detection(risk_score);
CREATE INDEX IF NOT EXISTS idx_credential_sharing_status ON credential_sharing_detection(investigation_status);

-- ============================================================================
-- Modify Existing Tables
-- ============================================================================

-- Add camera reputation columns to submissions table
ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS prnu_fingerprint_id INTEGER REFERENCES camera_fingerprints(id),
ADD COLUMN IF NOT EXISTS prnu_extracted_energy FLOAT,
ADD COLUMN IF NOT EXISTS camera_trust_score FLOAT DEFAULT 0.5;

COMMIT;
