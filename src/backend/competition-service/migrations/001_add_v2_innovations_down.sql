-- Rollback Migration: 001_add_v2_innovations_down.sql
-- Removes Camera Reputation and Judge Analytics tables
-- Created: 2026-02-23
-- WARNING: This will delete all camera reputation and judge analytics data!

BEGIN;

-- Remove columns from submissions table
ALTER TABLE submissions
DROP COLUMN IF EXISTS prnu_fingerprint_id,
DROP COLUMN IF EXISTS prnu_extracted_energy,
DROP COLUMN IF EXISTS camera_trust_score;

-- Drop Judge Analytics tables (reverse order due to foreign keys)
DROP TABLE IF EXISTS credential_sharing_detection CASCADE;
DROP TABLE IF EXISTS judge_consensus_analysis CASCADE;
DROP TABLE IF EXISTS judge_scoring_profiles CASCADE;

-- Drop Camera Reputation tables (reverse order due to foreign keys)
DROP TABLE IF EXISTS prnu_comparisons CASCADE;
DROP TABLE IF EXISTS camera_trust_profiles CASCADE;
DROP TABLE IF EXISTS camera_fingerprints CASCADE;

COMMIT;
