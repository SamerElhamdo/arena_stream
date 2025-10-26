#!/bin/bash

# ArenaStream Backend - Ubuntu Server Installation Script
# هذا السكريبت يثبت تلقائياً جميع المتطلبات والخدمات

set -e  # Stop on any error

echo "=========================================="
echo "ArenaStream Backend Installation Script"
echo "=========================================="
echo ""

# Variables
PROJECT_DIR="/var/www/arena-stream-backend"
DB_NAME="arenastream"
DB_USER="arenastream"
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 50)

echo "🔧 Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "📦 Step 2: Installing essential packages..."
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    ffmpeg \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server

echo "🗄️ Step 3: Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${DB_USER} SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\q
EOF

echo "✅ PostgreSQL configured successfully"

echo "💾 Step 4: Configuring Redis..."
# Enable Redis to be supervised by systemd
sudo sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf
sudo systemctl restart redis
sudo systemctl enable redis

echo "✅ Redis configured successfully"

echo "🐍 Step 5: Installing Python 3.11..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

echo "✅ Python installed successfully"

echo "📁 Step 6: Creating project directory..."
sudo mkdir -p ${PROJECT_DIR}
sudo chown -R $USER:$USER ${PROJECT_DIR}

echo "📋 Step 7: Copying project files..."
# Copy project files to deployment directory
# Note: Adjust this path according to your setup
echo "Please copy your project files to ${PROJECT_DIR}/arena_stream_api/"

echo "🔐 Step 8: Setting up Python virtual environment..."
cd ${PROJECT_DIR}/arena_stream_api/arena-stream-api-backend 2>/dev/null || {
    echo "⚠️  Please create the project structure first:"
    echo "   mkdir -p ${PROJECT_DIR}/arena_stream_api"
    echo "   Copy arena-stream-api-backend folder to: ${PROJECT_DIR}/arena_stream_api/"
    exit 1
}

python3.11 -m venv venv
source venv/bin/activate

echo "📦 Step 9: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Step 10: Creating .env file..."
cat > .env << EOF
# Django Settings
SECRET_KEY='${SECRET_KEY}'
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip

# Database
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=True

# Stream Controller
STREAMER_URL=http://localhost:5000
HMAC_SECRET=${SECRET_KEY}
EOF

echo "📊 Step 11: Running migrations..."
python manage.py migrate
python manage.py collectstatic --noinput

echo "👤 Step 12: Creating superuser..."
echo "You will be prompted to create a superuser account:"
python manage.py createsuperuser

echo "🔄 Step 13: Setting up Gunicorn service..."
cat > /tmp/arena-stream-backend.service << EOF
[Unit]
Description=ArenaStream Backend Gunicorn daemon
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=${PROJECT_DIR}/arena_stream_api/arena-stream-api-backend
Environment="PATH=${PROJECT_DIR}/arena_stream_api/arena-stream-api-backend/venv/bin"
ExecStart=${PROJECT_DIR}/arena_stream_api/arena-stream-api-backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:${PROJECT_DIR}/arena_stream_api/arena-stream-api-backend/arena_core.sock \
    arena_core.wsgi:application \
    --timeout 120 \
    --access-logfile ${PROJECT_DIR}/arena_stream_api/logs/access.log \
    --error-logfile ${PROJECT_DIR}/arena_stream_api/logs/error.log \
    --log-level info

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/arena-stream-backend.service /etc/systemd/system/
sudo mkdir -p ${PROJECT_DIR}/arena_stream_api/logs
sudo chown -R www-data:www-data ${PROJECT_DIR}
sudo systemctl daemon-reload
sudo systemctl enable arena-stream-backend
sudo systemctl start arena-stream-backend

echo "🌐 Step 14: Configuring Nginx..."
cat > /tmp/arena-stream-backend.nginx << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://unix:/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/arena_core.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/staticfiles/;
    }

    location /media/ {
        alias /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/media/;
    }

    client_max_body_size 100M;
}
EOF

sudo cp /tmp/arena-stream-backend.nginx /etc/nginx/sites-available/arena-stream-backend
sudo ln -sf /etc/nginx/sites-available/arena-stream-backend /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "🔒 Step 15: Configuring firewall..."
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo ""
echo "=========================================="
echo "✅ Installation completed successfully!"
echo "=========================================="
echo ""
echo "📝 Important Information:"
echo "   Database: ${DB_NAME}"
echo "   DB User: ${DB_USER}"
echo "   DB Password: ${DB_PASSWORD}"
echo "   Save these credentials!"
echo ""
echo "🔗 Access URLs:"
echo "   Backend API: http://your-server-ip/api/"
echo "   Admin Panel: http://your-server-ip/admin/"
echo "   API Docs: http://your-server-ip/api/docs/"
echo ""
echo "🔧 Useful Commands:"
echo "   sudo systemctl status arena-stream-backend"
echo "   sudo systemctl restart arena-stream-backend"
echo "   sudo tail -f ${PROJECT_DIR}/arena_stream_api/logs/error.log"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Update ALLOWED_HOSTS in .env file"
echo "   2. Update CORS settings if needed"
echo "   3. Set up SSL certificate (recommended)"
echo "   4. Configure email settings (optional)"
echo ""
echo "📚 For detailed information, see DEPLOYMENT_GUIDE.md"
echo ""
