# 🚀 دليل تركيب ArenaStream Backend على Ubuntu Server

## 📋 المتطلبات الأساسية

قبل البدء، تأكد من توفر:
- Ubuntu Server 20.04 أو أحدث
- وصول Root أو sudo
- اتصال بالإنترنت
- معرفة أساسية بـ Linux Terminal

---

## 🔧 الخطوة 1: تحديث النظام

```bash
# تحديث النظام
sudo apt update
sudo apt upgrade -y

# تثبيت الأدوات الأساسية
sudo apt install -y build-essential curl wget git
```

---

## 🗄️ الخطوة 2: تثبيت PostgreSQL

```bash
# تثبيت PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# تشغيل PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# إنشاء قاعدة البيانات والمستخدم
sudo -u postgres psql << EOF
CREATE DATABASE arenastream;
CREATE USER arenastream WITH PASSWORD 'YourSecurePassword123!';
ALTER ROLE arenastream SET client_encoding TO 'utf8';
ALTER ROLE arenastream SET default_transaction_isolation TO 'read committed';
ALTER ROLE arenastream SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE arenastream TO arenastream;
\q
EOF

# التحقق من التثبيت
sudo systemctl status postgresql
```

---

## 💾 الخطوة 3: تثبيت Redis

```bash
# تثبيت Redis
sudo apt install -y redis-server

# تعديل إعدادات Redis
sudo nano /etc/redis/redis.conf

# اضغط Ctrl+W وابحث عن "supervised" وغيرها إلى:
# supervised systemd

# إعادة تشغيل Redis
sudo systemctl restart redis
sudo systemctl enable redis

# التحقق من التثبيت
redis-cli ping
# يجب أن تظهر: PONG
```

---

## 🐍 الخطوة 4: تثبيت Python و Python Virtual Environment

```bash
# تثبيت Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# تثبيت pip
sudo apt install -y python3-pip

# تثبيت مكتبات النظام المطلوبة
sudo apt install -y \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    ffmpeg \
    nginx
```

---

## 📦 الخطوة 5: إنشاء Directory للمشروع

```bash
# إنشاء مجلد للمشروع
sudo mkdir -p /var/www/arena-stream-backend
sudo chown -R $USER:$USER /var/www/arena-stream-backend

# الانتقال للمجلد
cd /var/www/arena-stream-backend

# استنساخ المشروع من Git
git clone https://github.com/your-username/arena_stream.git arena_stream_api
# أو نسخ الملفات يدوياً إذا لم يكن المشروع على Git
```

---

## 🔐 الخطوة 6: إنشاء Python Virtual Environment

```bash
# الانتقال لمجلد المشروع
cd /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend

# إنشاء Virtual Environment
python3.11 -m venv venv

# تفعيل Virtual Environment
source venv/bin/activate

# ترقية pip
pip install --upgrade pip

# تثبيت المتطلبات
pip install -r requirements.txt
```

---

## ⚙️ الخطوة 7: تكوين المشروع

```bash
# إنشاء ملف .env
nano .env
```

أضف المحتوى التالي:

```env
# Django Settings
SECRET_KEY='your-super-secret-key-here-generate-new-one'
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database
DB_NAME=arenastream
DB_USER=arenastream
DB_PASS=YourSecurePassword123!
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://your-domain.com,https://your-domain.com
CORS_ALLOW_CREDENTIALS=True

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stream Controller
STREAMER_URL=http://localhost:5000
HMAC_SECRET=your-hmac-secret-key

# Security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

احفظ الملف: `Ctrl+O` ثم `Enter` ثم `Ctrl+X`

---

## 🗃️ الخطوة 8: تشغيل Migrations

```bash
# التأكد من تفعيل Virtual Environment
source venv/bin/activate

# تشغيل Migrations
python manage.py migrate

# إنشاء Superuser
python manage.py createsuperuser

# جمع Static Files (للـ Django Admin)
python manage.py collectstatic --noinput
```

---

## 🔧 الخطوة 9: تكوين Gunicorn

```bash
# إنشاء ملف Gunicorn Service
sudo nano /etc/systemd/system/arena-stream-backend.service
```

أضف المحتوى التالي:

```ini
[Unit]
Description=ArenaStream Backend Gunicorn daemon
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend
Environment="PATH=/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/venv/bin"
ExecStart=/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/arena_core.sock \
    arena_core.wsgi:application \
    --timeout 120 \
    --access-logfile /var/www/arena-stream-backend/arena_stream_api/logs/access.log \
    --error-logfile /var/www/arena-stream-backend/arena_stream_api/logs/error.log \
    --log-level info

[Install]
WantedBy=multi-user.target
```

```bash
# إعادة تحميل systemd
sudo systemctl daemon-reload

# بدء الخدمة
sudo systemctl start arena-stream-backend

# تفعيل الخدمة عند إعادة التشغيل
sudo systemctl enable arena-stream-backend

# التحقق من الحالة
sudo systemctl status arena-stream-backend
```

---

## 🌐 الخطوة 10: تكوين Nginx

```bash
# إنشاء ملف Nginx Configuration
sudo nano /etc/nginx/sites-available/arena-stream-backend
```

أضف المحتوى التالي:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS (Uncomment after SSL setup)
    # return 301 https://$server_name$request_uri;

    # For HTTP only (Before SSL setup)
    location / {
        proxy_pass http://unix:/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/arena_core.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static/ {
        alias /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/media/;
    }

    # Increase file upload size
    client_max_body_size 100M;
}

# HTTPS Configuration (After SSL setup)
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com www.your-domain.com;
#
#     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
#
#     location / {
#         proxy_pass http://unix:/var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/arena_core.sock;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#         proxy_redirect off;
#     }
#
#     location /static/ {
#         alias /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/staticfiles/;
#     }
#
#     location /media/ {
#         alias /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend/media/;
#     }
#
#     client_max_body_size 100M;
# }
```

```bash
# تفعيل الموقع
sudo ln -s /etc/nginx/sites-available/arena-stream-backend /etc/nginx/sites-enabled/

# اختبار إعدادات Nginx
sudo nginx -t

# إعادة تشغيل Nginx
sudo systemctl restart nginx

# التحقق من الحالة
sudo systemctl status nginx
```

---

## 🔒 الخطوة 11: إعداد SSL Certificate (اختياري)

```bash
# تثبيت Certbot
sudo apt install -y certbot python3-certbot-nginx

# الحصول على SSL Certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# إعداد التجديد التلقائي
sudo certbot renew --dry-run
```

---

## 🛠️ الخطوة 12: تثبيت FFmpeg لإعادة البث

```bash
# FFmpeg تم تثبيته مسبقاً، تحقق من التثبيت
ffmpeg -version

# إذا لم يكن مثبتاً:
# sudo apt install -y ffmpeg
```

---

## 📊 الخطوة 13: مراقبة الخدمات

```bash
# التحقق من حالة جميع الخدمات
sudo systemctl status arena-stream-backend
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# عرض الـ Logs
sudo journalctl -u arena-stream-backend -f
sudo tail -f /var/log/nginx/error.log

# مراقبة استخدام الموارد
htop
```

---

## 🔧 الخطوة 14: إعداد Firewall

```bash
# تثبيت UFW
sudo apt install -y ufw

# إعداد القواعد
sudo ufw default deny incoming
sudo ufw default allow outgoing

# السماح بـ SSH (مهم!)
sudo ufw allow ssh
sudo ufw allow 22/tcp

# السماح بـ HTTP و HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# تفعيل Firewall
sudo ufw enable

# عرض الحالة
sudo ufw status
```

---

## ✅ الخطوة 15: التحقق من التركيب

```bash
# اختبار API
curl http://your-server-ip/api/schema/

# اختبار Authentication
curl -X POST http://your-server-ip/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}'

# اختبار Database
sudo -u postgres psql -d arenastream -c "\dt"

# اختبار Redis
redis-cli ping
```

---

## 🔄 أوامر الصيانة الشائعة

```bash
# إعادة تشغيل Backend
sudo systemctl restart arena-stream-backend

# إعادة تشغيل Nginx
sudo systemctl restart nginx

# إعادة تشغيل PostgreSQL
sudo systemctl restart postgresql

# إعادة تشغيل Redis
sudo systemctl restart redis

# عرض Logs
sudo tail -f /var/www/arena-stream-backend/arena_stream_api/logs/error.log

# تشغيل Migrations جديدة
cd /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend
source venv/bin/activate
python manage.py migrate

# تجميع Static Files
python manage.py collectstatic --noinput

# إنشاء Database Backup
sudo -u postgres pg_dump arenastream > backup_$(date +%Y%m%d).sql

# استعادة Database Backup
sudo -u postgres psql arenastream < backup_20231201.sql
```

---

## 🚨 استكشاف الأخطاء

### الخطأ: Cannot connect to PostgreSQL
```bash
# التحقق من حالة PostgreSQL
sudo systemctl status postgresql

# إعادة تشغيل PostgreSQL
sudo systemctl restart postgresql

# التحقق من الـ Connection
sudo -u postgres psql -d arenastream
```

### الخطأ: Cannot connect to Redis
```bash
# التحقق من حالة Redis
sudo systemctl status redis

# إعادة تشغيل Redis
sudo systemctl restart redis

# اختبار Connection
redis-cli ping
```

### الخطأ: 502 Bad Gateway
```bash
# التحقق من حالة Gunicorn
sudo systemctl status arena-stream-backend

# التحقق من الـ Logs
sudo journalctl -u arena-stream-backend -n 50

# التحقق من Permissions
sudo chown -R www-data:www-data /var/www/arena-stream-backend
sudo chmod -R 755 /var/www/arena-stream-backend
```

---

## 📝 ملاحظات مهمة

1. **الأمان**: استخدم كلمات مرور قوية ومفتاح سري آمن
2. **Backups**: رتب نسخ احتياطية منتظمة لقاعدة البيانات
3. **Monitoring**: راقب الموارد والملفات بانتظام
4. **Updates**: حافظ على تحديث النظام والحزم
5. **Logs**: راجع السجلات لاستكشاف المشاكل

---

## 📞 الدعم

للأسئلة أو المشاكل:
- راجع Documentation في المشروع
- تحقق من Logs في `/var/log/`
- راجع Django Admin على `/admin/`

---

**آخر تحديث:** ديسمبر 2024
**الإصدار:** 1.0.0
