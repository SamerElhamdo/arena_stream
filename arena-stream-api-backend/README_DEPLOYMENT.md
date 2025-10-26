# 🚀 ArenaStream - دليل التثبيت على Ubuntu Server

## 📋 نظرة عامة

هذا الدليل خطوة بخطوة لتثبيت ArenaStream Backend على خادم Ubuntu.

## ⚡ التثبيت السريع

إذا كنت تريد تثبيتاً سريعاً تلقائياً:

```bash
# على السيرفر
cd /root
wget https://raw.githubusercontent.com/your-repo/arena_stream/main/arena-stream-api-backend/install.sh
chmod +x install.sh
sudo ./install.sh
```

⚠️ **ملاحظة**: السكريبت التلقائي لا يزال قيد التطوير، يُنصح بالتثبيت اليدوي حسب الدليل أدناه.

## 📖 التثبيت اليدوي

### الأسلوب الأول: التثبيت اليدوي الكامل

اتبع الدليل المفصل في: [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)

### الأسلوب الثاني: Docker (موصى به)

```bash
# الانتقال لمجلد المشروع
cd arena-stream-api-backend

# بناء الصورة
docker-compose build

# تشغيل الخدمات
docker-compose up -d

# التحقق من الحالة
docker-compose ps
```

## 🛠️ المتطلبات الأساسية

- Ubuntu 20.04 أو أحدث
- PostgreSQL 13+
- Redis 6+
- Python 3.11+
- FFmpeg
- Nginx
- 2GB RAM (حد أدنى)
- 20GB Storage (حد أدنى)

## 📝 خطوات التثبيت الأساسية

### 1. إعداد قاعدة البيانات

```bash
sudo -u postgres createuser arenastream
sudo -u postgres createdb arenastream
sudo -u postgres psql arenastream -c "ALTER USER arenastream WITH PASSWORD 'YourPassword';"
```

### 2. إعداد Redis

```bash
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping
```

### 3. إعداد Django

```bash
cd arena-stream-api-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 4. إعداد Gunicorn

```bash
sudo nano /etc/systemd/system/arena-stream-backend.service
# راجع DEPLOYMENT_GUIDE.md للحصول على محتوى الملف

sudo systemctl daemon-reload
sudo systemctl enable arena-stream-backend
sudo systemctl start arena-stream-backend
```

### 5. إعداد Nginx

```bash
sudo nano /etc/nginx/sites-available/arena-stream-backend
# راجع DEPLOYMENT_GUIDE.md للحصول على محتوى الملف

sudo ln -s /etc/nginx/sites-available/arena-stream-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 ملفات الإعدادات

### .env Example

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

DB_NAME=arenastream
DB_USER=arenastream
DB_PASS=your-password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0
```

### Gunicorn Service

راجع DEPLOYMENT_GUIDE.md للحصول على محتوى `/etc/systemd/system/arena-stream-backend.service`

### Nginx Config

راجع DEPLOYMENT_GUIDE.md للحصول على محتوى `/etc/nginx/sites-available/arena-stream-backend`

## 🧪 الاختبار

```bash
# اختبار API
curl http://localhost/api/schema/

# اختبار Authentication
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'
```

## 🔄 الصيانة

### إعادة التشغيل

```bash
sudo systemctl restart arena-stream-backend
sudo systemctl restart nginx
```

### عرض Logs

```bash
# Gunicorn logs
sudo journalctl -u arena-stream-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### تحديث الكود

```bash
cd /var/www/arena-stream-backend/arena_stream_api/arena-stream-api-backend
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart arena-stream-backend
```

### Backup Database

```bash
sudo -u postgres pg_dump arenastream > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
sudo -u postgres psql arenastream < backup_20231201.sql
```

## 🚨 استكشاف الأخطاء

### 502 Bad Gateway

```bash
# تحقق من Gunicorn
sudo systemctl status arena-stream-backend

# تحقق من Logs
sudo journalctl -u arena-stream-backend -n 50
```

### Database Connection Error

```bash
# تحقق من PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -d arenastream
```

### Redis Connection Error

```bash
# تحقق من Redis
sudo systemctl status redis
redis-cli ping
```

## 📚 الوثائق الإضافية

- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - دليل مفصل خطوة بخطوة
- [README.md](../README.md) - نظرة عامة على المشروع
- [requirements.txt](requirements.txt) - قائمة الحزم المطلوبة

## 🤝 الدعم

للأسئلة أو المشاكل، يرجى فتح Issue في Repository.

---

**آخر تحديث**: ديسمبر 2024
**الإصدار**: 1.0.0
