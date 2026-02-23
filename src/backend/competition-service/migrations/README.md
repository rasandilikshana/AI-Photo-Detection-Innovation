# Database Migrations

This directory contains database migration scripts for the AVAR Competition Service.

## Migration Naming Convention

```
{version_number}_{description}_{up|down}.sql
```

Example:
- `001_add_v2_innovations_up.sql` - Applies the migration
- `001_add_v2_innovations_down.sql` - Rolls back the migration

## Available Migrations

### 001_add_v2_innovations (v2.0 Features)

**Status:** Ready to apply

**Description:** Adds Camera Reputation System and Judge Analytics tables

**Tables Added:**
- `camera_fingerprints` - PRNU fingerprint storage
- `camera_trust_profiles` - Aggregated camera reputation
- `prnu_comparisons` - Pattern comparison history
- `judge_scoring_profiles` - Judge bias detection
- `judge_consensus_analysis` - Multi-judge consensus metrics
- `credential_sharing_detection` - Security monitoring

**Columns Modified:**
- `submissions.prnu_fingerprint_id` - Link to camera fingerprint
- `submissions.prnu_extracted_energy` - PRNU energy metric
- `submissions.camera_trust_score` - Camera trust score (0.0-1.0)

## How to Apply Migrations

### Method 1: Using psql (Manual)

```bash
# Apply migration
psql -U postgres -d avar_competition -f migrations/001_add_v2_innovations_up.sql

# Rollback migration
psql -U postgres -d avar_competition -f migrations/001_add_v2_innovations_down.sql
```

### Method 2: Using Python (Programmatic)

The application uses SQLAlchemy's `Base.metadata.create_all()` which automatically creates tables based on model definitions. When you start the application with the new models imported, tables will be created automatically.

```python
# In database.py, tables are created via:
from app.models import (
    CameraFingerprint,
    CameraTrustProfile,
    PRNUComparison,
    JudgeScoringProfile,
    JudgeConsensusAnalysis,
    CredentialSharingDetection,
)

await init_db()  # Creates all tables
```

### Method 3: Docker Compose (Automatic)

If using Docker Compose, migrations can be run as part of container startup:

```yaml
# In docker-compose.yml
services:
  competition-service:
    command: >
      sh -c "python -m app.migrate && uvicorn app.main:app --host 0.0.0.0"
```

## Migration Best Practices

1. **Always test in development first**
2. **Backup production database before applying**
3. **Use transactions (BEGIN/COMMIT) to allow rollback on error**
4. **Create both "up" and "down" scripts**
5. **Document breaking changes**
6. **Version control all migration scripts**

## Rollback Instructions

If you need to rollback the v2.0 innovations:

```bash
# 1. Backup current data
pg_dump -U postgres avar_competition > backup_before_rollback.sql

# 2. Run rollback script
psql -U postgres -d avar_competition -f migrations/001_add_v2_innovations_down.sql

# 3. Verify rollback
psql -U postgres -d avar_competition -c "\dt"
```

## Troubleshooting

### Error: "relation already exists"

Tables may already exist. Check existing tables:

```sql
\dt camera_*
\dt judge_*
```

Either drop existing tables or skip migration.

### Error: "column does not exist"

SQLAlchemy models may be out of sync with database. Ensure:
1. Models are imported in `database.py`
2. All relationships are properly defined
3. Foreign key tables exist first

### Performance Issues

After applying migrations, update statistics:

```sql
ANALYZE camera_fingerprints;
ANALYZE camera_trust_profiles;
ANALYZE judge_scoring_profiles;
VACUUM ANALYZE;
```

## Next Steps

After applying migrations:

1. Verify tables created: `\dt` in psql
2. Check indexes: `\di` in psql
3. Test model imports: `python -c "from app.models import CameraFingerprint; print('OK')"`
4. Run integration tests
5. Update API documentation
