# V2.0.0 Production Deployment Instructions

## Quick Start

You're already SSH'd into the production server. Follow these steps:

### Option 1: Automated Deployment (Recommended)

From your local machine:
```bash
./deploy-v2.0.0.sh
```

This will automatically:
1. Backup database and files
2. Pull v2.0.0 code
3. Install dependencies
4. Run migrations
5. Build and deploy frontend
6. Restart services
7. Run health checks

### Option 2: Manual Deployment (Step-by-Step)

You're currently logged in as: `root@165.245.178.225`

#### Step 1: Create Backup

```bash
# Create backup directory
mkdir -p /root/backups/pre-v2-$(date +%Y%m%d-%H%M%S)

# Backup database
cd /root
pg_dump -U avar_user avar_db > backups/pre-v2-$(date +%Y%m%d-%H%M%S)/database_backup.sql

# Backup application
tar -czf backups/pre-v2-$(date +%Y%m%d-%H%M%S)/app_backup.tar.gz avar/

echo "✅ Backup complete"
```

#### Step 2: Pull Latest Code

```bash
cd /root/avar

# Fetch all tags
git fetch --all --tags

# Checkout v2.0.0
git checkout v2.0.0

# Verify version
git describe --tags

echo "✅ Code updated to v2.0.0"
```

#### Step 3: Install V2.0 Dependencies

```bash
cd /root/avar/src/backend/competition-service

# Install new Python packages
pip install opencv-python numpy PyWavelets scipy

# Verify installations
python3 -c "import cv2; import pywt; import scipy; print('✅ All dependencies installed')"
```

#### Step 4: Stop Services

```bash
cd /root/avar

# Stop all services
docker-compose down

# Verify stopped
docker ps
```

#### Step 5: Run Database Migrations

```bash
cd /root/avar/src/backend/competition-service

# Check current migration
alembic current

# Run migrations
alembic upgrade head

# Verify new tables
psql -U avar_user -d avar_db << 'EOF'
SELECT table_name
FROM information_schema.tables
WHERE table_name IN (
  'camera_fingerprints',
  'camera_profiles',
  'judge_scoring_profiles',
  'judge_consensus_analyses',
  'credential_sharing_detections'
);
EOF

echo "✅ Migrations complete - you should see 5 tables listed"
```

Expected output:
```
          table_name
------------------------------
 camera_fingerprints
 camera_profiles
 judge_scoring_profiles
 judge_consensus_analyses
 credential_sharing_detections
(5 rows)
```

#### Step 6: Build Frontend

```bash
cd /root/avar/src/frontend

# Install dependencies
pnpm install

# Build with production API URL
VITE_API_URL=https://avar.studio/api/v1 pnpm build

# Deploy to nginx
sudo cp -r dist/* /var/www/avar.studio/
sudo chown -R www-data:www-data /var/www/avar.studio/

echo "✅ Frontend deployed"
```

#### Step 7: Start Services

```bash
cd /root/avar

# Start all services
docker-compose up -d

# Wait for services to start
sleep 10

# Check status
docker-compose ps

# View logs
docker-compose logs -f competition-service
```

#### Step 8: Verify Deployment

```bash
# Health check
curl http://localhost:8080/health

# Check if new endpoints are available
curl http://localhost:8080/docs | grep -i "camera"
curl http://localhost:8080/docs | grep -i "judges-analytics"

# Run validation script
cd /root/avar/src/backend/competition-service
python tests/validate_v2_setup.py
```

Expected validation output:
```
✅ PASS   Dependencies
✅ PASS   Service Files
✅ PASS   Route Files
✅ PASS   Model Files
...
```

#### Step 9: Test Frontend

Open browser to: https://avar.studio

Test:
- [ ] Can login as admin (admin@avar.com / Admin@123!)
- [ ] Navigate to a submission - should see camera reputation badge (if camera data available)
- [ ] Navigate to Judge Dashboard - should see consensus indicators
- [ ] Navigate to Admin Panel - should see "Bias Report" and "Security" tabs
- [ ] Submit a new photo - PRNU extraction should trigger

#### Step 10: Monitor

```bash
# Watch logs
docker-compose logs -f

# Check for V2.0 specific logs
docker logs avar-competition-service | grep -E "PRNU|consensus|credential"

# Check database growth
psql -U avar_user -d avar_db << 'EOF'
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE '%camera%' OR tablename LIKE '%judge%' OR tablename LIKE '%credential%'
ORDER BY tablename;
EOF
```

---

## Rollback Procedure

If something goes wrong:

```bash
cd /root/avar

# Stop services
docker-compose down

# Checkout previous version
git checkout v1.4.0

# Restore database (if migrations failed)
psql -U avar_user -d avar_db < /root/backups/pre-v2-YYYYMMDD-HHMMSS/database_backup.sql

# Start services
docker-compose up -d

echo "✅ Rolled back to v1.4.0"
```

---

## Post-Deployment Checklist

- [ ] Services running: `docker-compose ps`
- [ ] Health check passing: `curl http://localhost:8080/health`
- [ ] Frontend accessible: https://avar.studio
- [ ] Admin login working
- [ ] New API endpoints available: https://avar.studio/api/v1/docs
- [ ] Database migrations applied: 5 new tables exist
- [ ] Logs clean (no errors): `docker-compose logs --tail=50`
- [ ] SSL certificate valid: https://avar.studio
- [ ] Nginx reload: `sudo systemctl status nginx`

---

## Troubleshooting

### Issue: Services won't start

```bash
# Check Docker logs
docker-compose logs competition-service

# Check disk space
df -h

# Check memory
free -h

# Restart Docker
sudo systemctl restart docker
docker-compose up -d
```

### Issue: Migrations fail

```bash
# Check database connection
psql -U avar_user -d avar_db -c "SELECT version();"

# Manually run migrations
cd /root/avar/src/backend/competition-service
alembic upgrade head --verbose

# Check migration history
alembic history
alembic current
```

### Issue: Frontend not updating

```bash
# Clear nginx cache
sudo rm -rf /var/www/avar.studio/*

# Rebuild and deploy frontend
cd /root/avar/src/frontend
VITE_API_URL=https://avar.studio/api/v1 pnpm build
sudo cp -r dist/* /var/www/avar.studio/
sudo chown -R www-data:www-data /var/www/avar.studio/

# Restart nginx
sudo systemctl restart nginx
```

### Issue: PRNU extraction failing

```bash
# Check Python packages
docker exec avar-competition-service python -c "import cv2, pywt, scipy; print('OK')"

# If missing, install inside container
docker exec avar-competition-service pip install opencv-python PyWavelets scipy

# Restart service
docker-compose restart competition-service
```

---

## Important Notes

### Performance Expectations

- **PRNU Extraction**: 2-4 seconds per image
  - First submission may take longer (loading libraries)
  - Subsequent submissions will be faster

- **Database Growth**: ~256KB per fingerprint
  - 1000 submissions = ~250MB
  - Monitor disk usage regularly

- **Memory Usage**: +50MB per PRNU extraction
  - System should have 2GB+ RAM available
  - Current system: 2GB (42% usage before deployment)

### Monitoring

```bash
# Watch system resources
htop

# Monitor Docker stats
docker stats

# Check specific service
docker stats avar-competition-service

# Database size
psql -U avar_user -d avar_db -c "
SELECT pg_size_pretty(pg_database_size('avar_db'));"
```

### Maintenance

Schedule regular maintenance:

```bash
# Weekly: Vacuum database
psql -U avar_user -d avar_db -c "VACUUM ANALYZE;"

# Monthly: Clean old Docker images
docker system prune -a

# Monthly: Review and archive old logs
journalctl --vacuum-time=30d
```

---

## Support

- **Documentation**: See `/root/avar/docs/DEPLOYMENT_V2.md`
- **Logs**: `docker-compose logs -f`
- **GitHub**: https://github.com/rasandilikshana/AI-Photo-Detection-Innovation
- **Contact**: rasandilikshana@gmail.com

---

**Version**: 2.0.0
**Deployed**: 2026-02-24
**Server**: 165.245.178.225 (Singapore)
**Status**: Production Ready
