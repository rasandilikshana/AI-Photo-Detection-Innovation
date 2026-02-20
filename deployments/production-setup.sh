#!/bin/bash
# AVAR Production Server Setup Script - Security Hardened
# Version: 2.0
# Last Updated: 2026-02-21

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "AVAR Production Server Setup (Secure)"
echo "=========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# Configuration - CHANGE THESE BEFORE RUNNING
DOMAIN="${DOMAIN:-avar.studio}"  # Your domain
APP_USER="avar"
APP_GROUP="avar"
APP_DIR="/var/www/avar"
ENABLE_SSL="${ENABLE_SSL:-true}"  # Enable SSL with Let's Encrypt

# Generate secure random secrets if not provided
generate_secret() {
    openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 64
}

DB_PASSWORD="${DB_PASSWORD:-$(generate_secret)}"
JWT_SECRET="${JWT_SECRET:-$(generate_secret)}"
REDIS_PASSWORD="${REDIS_PASSWORD:-$(generate_secret)}"

# ============================================
# Step 1: System Updates & Security Hardening
# ============================================
log_info "[1/10] Installing system dependencies and hardening..."

apt update && apt upgrade -y
apt install -y \
    git curl wget build-essential software-properties-common \
    nginx certbot python3-certbot-nginx \
    ufw fail2ban \
    postgresql postgresql-contrib \
    redis-server \
    libraw-dev libimage-exiftool-perl libjpeg-dev libpng-dev zlib1g-dev \
    acl logrotate

# Install Python 3.12
add-apt-repository ppa:deadsnakes/ppa -y
apt install -y python3.12 python3.12-venv python3.12-dev

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# ============================================
# Step 2: Create Application User (Non-Root)
# ============================================
log_info "[2/10] Creating application user..."

if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -d "$APP_DIR" -s /bin/bash "$APP_USER"
    log_info "Created user: $APP_USER"
else
    log_warn "User $APP_USER already exists"
fi

# ============================================
# Step 3: Firewall Configuration
# ============================================
log_info "[3/10] Configuring firewall..."

ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
log_info "Firewall enabled - SSH, HTTP, HTTPS allowed"

# ============================================
# Step 4: Fail2Ban Configuration
# ============================================
log_info "[4/10] Configuring Fail2Ban..."

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# ============================================
# Step 5: PostgreSQL Setup (Secure)
# ============================================
log_info "[5/10] Setting up PostgreSQL..."

# Configure PostgreSQL for password auth only
sudo -u postgres psql -c "CREATE USER $APP_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || log_warn "User may already exist"
sudo -u postgres psql -c "CREATE DATABASE avar_db OWNER $APP_USER;" 2>/dev/null || log_warn "Database may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE avar_db TO $APP_USER;"
sudo -u postgres psql -c "ALTER USER $APP_USER WITH PASSWORD '$DB_PASSWORD';"

# Harden PostgreSQL
PG_HBA=$(sudo -u postgres psql -t -c "SHOW hba_file;" | xargs)
if ! grep -q "local.*avar_db.*md5" "$PG_HBA"; then
    echo "local   avar_db     $APP_USER                               md5" >> "$PG_HBA"
    systemctl restart postgresql
fi

# ============================================
# Step 6: Redis Setup (Secure)
# ============================================
log_info "[6/10] Configuring Redis..."

# Secure Redis configuration
cat > /etc/redis/redis-avar.conf << EOF
bind 127.0.0.1
port 6379
requirepass $REDIS_PASSWORD
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
dir /var/lib/redis
EOF

systemctl restart redis-server

# ============================================
# Step 7: Application Setup
# ============================================
log_info "[7/10] Setting up application..."

# Set ownership
chown -R $APP_USER:$APP_GROUP "$APP_DIR"

# Competition Service
log_info "Setting up Competition Service..."
cd "$APP_DIR/src/backend/competition-service"
sudo -u $APP_USER python3.12 -m venv venv
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

cat > "$APP_DIR/src/backend/competition-service/.env" << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://$APP_USER:$DB_PASSWORD@localhost:5432/avar_db

# Security - DO NOT COMMIT THIS FILE
SECRET_KEY=$JWT_SECRET
JWT_SECRET_KEY=$JWT_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service Configuration
AI_DETECTION_SERVICE_URL=http://localhost:8001
UPLOAD_DIR=$APP_DIR/src/backend/competition-service/uploads

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
EOF

chmod 600 "$APP_DIR/src/backend/competition-service/.env"
chown $APP_USER:$APP_GROUP "$APP_DIR/src/backend/competition-service/.env"

# Create uploads directory
mkdir -p "$APP_DIR/src/backend/competition-service/uploads"
chown $APP_USER:$APP_GROUP "$APP_DIR/src/backend/competition-service/uploads"
chmod 750 "$APP_DIR/src/backend/competition-service/uploads"

# Run database migrations
sudo -u $APP_USER bash -c "cd $APP_DIR/src/backend/competition-service && source venv/bin/activate && python -m alembic upgrade head"

# Seed default users (optional)
sudo -u $APP_USER bash -c "cd $APP_DIR/src/backend/competition-service && source venv/bin/activate && python -m scripts.seed_users" || log_warn "Seed script may have failed or users already exist"

# AI Detection Service
log_info "Setting up AI Detection Service..."
cd "$APP_DIR/src/backend/ai-detection-service"
sudo -u $APP_USER python3.12 -m venv venv
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

cat > "$APP_DIR/src/backend/ai-detection-service/.env" << EOF
# Third-party APIs (configure these with your actual keys)
SIGHTENGINE_USER=
SIGHTENGINE_SECRET=
HIVE_AI_API_KEY=
OPTIC_API_KEY=

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/1
EOF

chmod 600 "$APP_DIR/src/backend/ai-detection-service/.env"
chown $APP_USER:$APP_GROUP "$APP_DIR/src/backend/ai-detection-service/.env"

# Create uploads directory for AI service
mkdir -p "$APP_DIR/src/backend/ai-detection-service/uploads"
chown $APP_USER:$APP_GROUP "$APP_DIR/src/backend/ai-detection-service/uploads"
chmod 750 "$APP_DIR/src/backend/ai-detection-service/uploads"

# ============================================
# Step 8: Frontend Build
# ============================================
log_info "[8/10] Building Frontend..."

cd "$APP_DIR/src/frontend"
npm install

cat > .env.production << EOF
VITE_API_BASE_URL=https://$DOMAIN/api/v1
EOF

npm run build

# Set proper ownership
chown -R $APP_USER:$APP_GROUP "$APP_DIR/src/frontend/dist"

# ============================================
# Step 9: Systemd Services (Non-Root)
# ============================================
log_info "[9/10] Creating systemd services..."

cat > /etc/systemd/system/avar-competition.service << EOF
[Unit]
Description=AVAR Competition Service
After=network.target postgresql.service redis.service
Requires=postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR/src/backend/competition-service
Environment=PATH=$APP_DIR/src/backend/competition-service/venv/bin:/usr/bin
EnvironmentFile=$APP_DIR/src/backend/competition-service/.env
ExecStart=$APP_DIR/src/backend/competition-service/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$APP_DIR/src/backend/competition-service/uploads
ProtectHome=yes

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/avar-detection.service << EOF
[Unit]
Description=AVAR AI Detection Service
After=network.target redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR/src/backend/ai-detection-service
Environment=PATH=$APP_DIR/src/backend/ai-detection-service/venv/bin:/usr/bin
EnvironmentFile=$APP_DIR/src/backend/ai-detection-service/.env
ExecStart=$APP_DIR/src/backend/ai-detection-service/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$APP_DIR/src/backend/ai-detection-service/uploads
ProtectHome=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable avar-competition avar-detection
systemctl start avar-competition avar-detection

# ============================================
# Step 10: Nginx Configuration (With Security)
# ============================================
log_info "[10/10] Configuring Nginx..."

cat > /etc/nginx/sites-available/avar << EOF
# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login_limit:10m rate=5r/m;

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # File upload limit
    client_max_body_size 200M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Frontend (Vue.js SPA)
    location / {
        root $APP_DIR/src/frontend/dist;
        try_files \$uri \$uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Uploaded files (with security)
    location /uploads/ {
        alias $APP_DIR/src/backend/competition-service/uploads/;

        # Only allow specific file types
        location ~* \.(jpg|jpeg|png|gif|raw|cr2|nef|arw|dng)$ {
            expires 7d;
            add_header Cache-Control "public";
        }

        # Deny access to other file types
        location ~* \. {
            deny all;
        }
    }

    # Competition API
    location /api/ {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
    }

    # Login endpoint with stricter rate limiting
    location /api/v1/auth/login {
        limit_req zone=login_limit burst=5 nodelay;

        proxy_pass http://127.0.0.1:8000/api/v1/auth/login;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # AI Detection API
    location /detect/ {
        limit_req zone=api_limit burst=10 nodelay;

        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;  # Longer timeout for AI analysis
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ \.env$ {
        deny all;
    }
}
EOF

ln -sf /etc/nginx/sites-available/avar /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx

# ============================================
# SSL Setup with Let's Encrypt
# ============================================
if [[ "$ENABLE_SSL" == "true" ]]; then
    log_info "Setting up SSL with Let's Encrypt..."

    # Wait for DNS propagation
    log_info "Checking DNS resolution for $DOMAIN..."
    if host "$DOMAIN" > /dev/null 2>&1; then
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m admin@"$DOMAIN" --redirect

        # Auto-renewal cron
        (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet") | crontab -
        log_info "SSL certificate installed successfully!"
    else
        log_warn "DNS not yet resolved for $DOMAIN. Run certbot manually after DNS propagates:"
        log_warn "  certbot --nginx -d $DOMAIN -d www.$DOMAIN"
    fi
fi

# ============================================
# Log Rotation
# ============================================
cat > /etc/logrotate.d/avar << 'EOF'
/var/log/avar/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 avar avar
    sharedscripts
    postrotate
        systemctl reload avar-competition avar-detection 2>/dev/null || true
    endscript
}
EOF

mkdir -p /var/log/avar
chown $APP_USER:$APP_GROUP /var/log/avar

# ============================================
# Final Status Check
# ============================================
echo ""
echo "=========================================="
echo "Service Status"
echo "=========================================="
systemctl status avar-competition --no-pager -l || true
echo ""
systemctl status avar-detection --no-pager -l || true
echo ""
systemctl status nginx --no-pager -l || true
echo ""
systemctl status postgresql --no-pager -l || true

# ============================================
# Save Credentials (IMPORTANT!)
# ============================================
CREDS_FILE="/root/avar-credentials.txt"
cat > "$CREDS_FILE" << EOF
========================================
AVAR Production Credentials
Generated: $(date)
========================================

DATABASE:
  Host: localhost
  Port: 5432
  Database: avar_db
  User: $APP_USER
  Password: $DB_PASSWORD

REDIS:
  Host: localhost
  Port: 6379
  Password: $REDIS_PASSWORD

JWT:
  Secret Key: $JWT_SECRET

APPLICATION:
  URL: https://$DOMAIN

TEST ACCOUNTS:
  Admin: admin@avar.com / Admin@123!
  Judge: judge@avar.com / Judge@123!
  Organizer: organizer@avar.com / Organizer@123!

========================================
IMPORTANT: Store these credentials securely
and delete this file after noting them down!
========================================
EOF

chmod 600 "$CREDS_FILE"
log_warn "Credentials saved to $CREDS_FILE - DELETE AFTER COPYING!"

echo ""
echo "=========================================="
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "=========================================="
echo "Access your app at: https://$DOMAIN"
echo ""
echo "Credentials saved to: $CREDS_FILE"
echo ""
echo "If SSL setup failed (DNS not propagated), run manually:"
echo "  certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""
echo "View logs:"
echo "  journalctl -u avar-competition -f"
echo "  journalctl -u avar-detection -f"
echo "=========================================="
