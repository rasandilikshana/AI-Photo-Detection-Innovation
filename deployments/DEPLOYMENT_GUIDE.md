# AVAR Production Deployment Guide

This guide covers deploying AVAR to a production server with security hardening.

## Live Deployment

**Production URL**: https://avar.studio
**Fallback (IP)**: http://165.245.178.225
**Server**: DigitalOcean Droplet (Singapore)
**Last Deployed**: February 21, 2026

### Quick Access
- **Frontend**: https://avar.studio
- **API Health**: https://avar.studio/api/v1/competitions
- **AI Detection**: https://avar.studio/detect/health

### Test Accounts (Production)
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@avar.com | Admin@123! |
| Judge | judge@avar.com | Judge@123! |
| Organizer | organizer@avar.com | Organizer@123! |

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Manual Deployment](#manual-deployment)
4. [Docker Deployment](#docker-deployment)
5. [SSL/HTTPS Setup](#sslhttps-setup)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements
- **OS**: Ubuntu 22.04 LTS or later
- **CPU**: 2+ cores (4+ recommended for AI analysis)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 50GB+ SSD
- **Network**: Static IP or domain name

### Software Requirements
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Nginx

---

## Quick Start

### Step 1: Transfer Files to Server

From your local machine:
```bash
rsync -avz --progress \
  -e "ssh -i ~/.ssh/id_ed25519_digitalocean" \
  "/media/rasan/windows-drive/NPAS/NPAS - Third Year/Rasan Research 3/" \
  root@165.245.178.225:/var/www/avar/
```

### Step 2: Run Setup Script

SSH into your server and run:
```bash
ssh -i ~/.ssh/id_ed25519_digitalocean root@165.245.178.225

# Make the script executable and run it
chmod +x /var/www/avar/deployments/production-setup.sh
/var/www/avar/deployments/production-setup.sh
```

### Step 3: Save Your Credentials

The script generates secure credentials and saves them to `/root/avar-credentials.txt`. **Copy these immediately and delete the file**.

---

## Manual Deployment

### 1. System Setup

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y git curl wget nginx postgresql redis-server ufw fail2ban

# Install Python 3.12
add-apt-repository ppa:deadsnakes/ppa -y
apt install -y python3.12 python3.12-venv python3.12-dev

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Image processing libraries
apt install -y libraw-dev libimage-exiftool-perl libjpeg-dev libpng-dev
```

### 2. Create Application User

```bash
# Create dedicated user (not root!)
useradd -r -m -d /var/www/avar -s /bin/bash avar
```

### 3. Database Setup

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32)

# Create PostgreSQL user and database
sudo -u postgres psql << EOF
CREATE USER avar WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE avar_db OWNER avar;
GRANT ALL PRIVILEGES ON DATABASE avar_db TO avar;
EOF
```

### 4. Configure Environment Variables

Copy the template and fill in values:
```bash
cp /var/www/avar/deployments/.env.production.template \
   /var/www/avar/src/backend/competition-service/.env

# Edit the file
nano /var/www/avar/src/backend/competition-service/.env
```

**Important**: Generate secure values for:
- `DB_PASSWORD`
- `JWT_SECRET_KEY`
- `REDIS_PASSWORD`

Use: `openssl rand -base64 64` for secure random strings.

### 5. Backend Services Setup

```bash
# Competition Service
cd /var/www/avar/src/backend/competition-service
sudo -u avar python3.12 -m venv venv
sudo -u avar bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u avar bash -c "source venv/bin/activate && alembic upgrade head"

# AI Detection Service
cd /var/www/avar/src/backend/ai-detection-service
sudo -u avar python3.12 -m venv venv
sudo -u avar bash -c "source venv/bin/activate && pip install -r requirements.txt"
```

### 6. Frontend Build

```bash
cd /var/www/avar/src/frontend

# Set API URL
echo "VITE_API_BASE_URL=http://YOUR_DOMAIN/api/v1" > .env.production

npm install
npm run build
```

### 7. Systemd Services

Create service files as shown in `production-setup.sh`, then:
```bash
systemctl daemon-reload
systemctl enable avar-competition avar-detection
systemctl start avar-competition avar-detection
```

### 8. Nginx Configuration

```bash
cp /var/www/avar/deployments/nginx-ssl.conf /etc/nginx/sites-available/avar
# Edit YOUR_DOMAIN in the file
ln -sf /etc/nginx/sites-available/avar /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

---

## Docker Deployment

For simpler deployment, use the existing Docker Compose setup:

### 1. Configure Environment

```bash
cd /var/www/avar
cp .env.example .env
# Edit .env with production values
```

### 2. Deploy with Docker Compose

```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps
docker compose logs -f
```

### 3. Run Migrations

```bash
docker compose exec competition-service alembic upgrade head
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
certbot renew --dry-run
```

### Manual SSL Configuration

1. Copy `deployments/nginx-ssl.conf` to `/etc/nginx/sites-available/avar`
2. Replace `YOUR_DOMAIN` with your actual domain
3. Place certificates in `/etc/letsencrypt/live/YOUR_DOMAIN/`
4. Restart Nginx: `systemctl restart nginx`

---

## Security Hardening

### Firewall (UFW)

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw enable
```

### Fail2Ban

Already configured in the setup script. Check status:
```bash
fail2ban-client status
fail2ban-client status sshd
```

### Security Checklist

- [ ] Changed all default passwords
- [ ] JWT secret is cryptographically random (64+ characters)
- [ ] Database password is strong
- [ ] Redis password is set
- [ ] Services run as non-root user
- [ ] Firewall enabled (only SSH, HTTP, HTTPS)
- [ ] Fail2Ban active
- [ ] SSL/HTTPS enabled
- [ ] File permissions are restrictive (600 for .env files)
- [ ] `/root/avar-credentials.txt` deleted after copying

---

## Monitoring & Maintenance

### View Logs

```bash
# Service logs
journalctl -u avar-competition -f
journalctl -u avar-detection -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*-main.log
```

### Service Management

```bash
# Restart services
systemctl restart avar-competition avar-detection

# Check status
systemctl status avar-competition
systemctl status avar-detection

# Reload after config changes
systemctl reload nginx
```

### Database Backup

```bash
# Manual backup
sudo -u postgres pg_dump avar_db > /var/backups/avar_db_$(date +%Y%m%d).sql

# Automated daily backup (add to crontab)
0 3 * * * sudo -u postgres pg_dump avar_db | gzip > /var/backups/avar_db_$(date +\%Y\%m\%d).sql.gz
```

### Updates

```bash
# Pull latest code
cd /var/www/avar
git pull origin main

# Update dependencies
cd src/backend/competition-service
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate

# Rebuild frontend
cd ../../../src/frontend
npm install
npm run build

# Restart services
systemctl restart avar-competition avar-detection
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
journalctl -u avar-competition -n 100 --no-pager

# Test manually
cd /var/www/avar/src/backend/competition-service
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
sudo -u avar psql -h localhost -d avar_db

# Check pg_hba.conf for auth method
sudo -u postgres cat $(sudo -u postgres psql -t -c "SHOW hba_file;")
```

### Nginx 502 Bad Gateway

```bash
# Check if backend services are running
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8001/health

# Check Nginx error log
tail -50 /var/log/nginx/error.log
```

### Permission Denied Errors

```bash
# Fix ownership
chown -R avar:avar /var/www/avar

# Fix upload directory permissions
chmod 750 /var/www/avar/src/backend/competition-service/uploads
chmod 750 /var/www/avar/src/backend/ai-detection-service/uploads
```

### Redis Connection Issues

```bash
# Check Redis status
systemctl status redis-server

# Test connection
redis-cli -a YOUR_REDIS_PASSWORD ping
```

---

## Default Test Accounts

After running seed scripts:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@avar.com | Admin@123! |
| Judge | judge@avar.com | Judge@123! |
| Organizer | organizer@avar.com | Organizer@123! |

**IMPORTANT**: Change these passwords immediately in production!

---

## Support

For issues or questions:
- Check logs first: `journalctl -u avar-competition -f`
- Review this guide's troubleshooting section
- Check GitHub issues: https://github.com/rasandilikshana/AI-Photo-Detection-Innovation/issues
