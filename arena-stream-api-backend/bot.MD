# 🎯 ArenaStream - Backend API (Django REST)

## 📋 نظرة عامة
Backend API احترافي لنظام البث الرياضي **ArenaStream** مبني بـ Django + DRF + Redis + PostgreSQL

---

## 🛠️ التقنيات المطلوبة

```json
{
  "framework": "Django 5 + Django REST Framework",
  "database": "PostgreSQL",
  "cache": "Redis",
  "authentication": "SimpleJWT",
  "docs": "drf-spectacular (OpenAPI/Swagger)",
  "cors": "django-cors-headers",
  "server": "Gunicorn + Nginx",
  "streaming": "FFmpeg Controller Integration"
}
```

---

## 🏗️ إعداد المشروع

### اسم المشروع
- **Project:** `arena_core`
- **Main App:** `stream_api`

### متغيرات البيئة (.env)

```bash
# Django
DJANGO_SECRET=change-me-to-secure-random-string
DEBUG=False
ALLOWED_HOSTS=api.arenastream.com,localhost

# Database
DB_NAME=arenastream
DB_USER=arenastream
DB_PASS=your-secure-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Streaming Service
STREAMER_URL=http://streamer:8080

# Security
HMAC_SECRET=supersecretkey-change-me
JWT_ACCESS_TTL=3600
JWT_REFRESH_TTL=86400

# CORS
CORS_ALLOWED_ORIGINS=https://viewer.arenastream.com,https://admin.arenastream.com

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@arenastream.com
EMAIL_HOST_PASSWORD=your-email-password
```

---

## 📊 نماذج البيانات (Models)

### 1. CustomUser
```python
- email (unique, primary identifier)
- password (hashed)
- first_name
- last_name
- date_joined
- is_active
- is_staff
- is_superuser
```

### 2. Subscription
```python
- user (FK to CustomUser)
- plan_type (choices: Free, Monthly, Yearly, Lifetime)
- max_devices (integer, default=1)
- price (decimal)
- starts_at (datetime)
- expires_at (datetime, nullable)
- is_active (boolean, auto-computed)
- created_at
- updated_at
```

### 3. Channel
```python
- name (string)
- slug (unique, auto-generated)
- description (text)
- source_url (private HLS/TS link)
- thumbnail (image, optional)
- is_live (boolean)
- viewers_count (integer, cached from Redis)
- category (FK to Category)
- created_at
- updated_at
```

### 4. Category
```python
- name (Football, Basketball, Tennis, etc.)
- slug (unique)
- icon (optional)
```

### 5. Event
```python
- title (Barcelona vs Real Madrid)
- description (text)
- channel (FK to Channel)
- start_time (datetime)
- end_time (datetime, optional)
- status (choices: Upcoming, Live, Ended)
- thumbnail (image)
- created_at
- updated_at
```

### 6. ActiveSession (Redis-based)
```python
Key: session:{user_id}:{session_id}
Value: {
  "user_id": int,
  "channel_id": int,
  "ip": string,
  "user_agent": string,
  "device_type": string,
  "started_at": timestamp,
  "last_seen": timestamp
}
TTL: 5 minutes (auto-refresh on activity)
```

### 7. DeviceLimit (optional model)
```python
- user (FK)
- device_identifier (unique hash)
- device_name
- last_used_at
- is_blocked
```

---

## 🔐 نظام المصادقة (Authentication)

### JWT Token Flow
```
1. POST /auth/register/ → Create user
2. POST /auth/login/ → Returns access + refresh tokens
3. Use access token in header: Authorization: Bearer <token>
4. POST /auth/refresh/ → Get new access token
5. POST /auth/logout/ → Invalidate token + clear Redis sessions
```

### Permissions
- `IsAuthenticated`: للمستخدمين المسجلين
- `IsAdminUser`: للإداريين فقط
- `HasActiveSubscription`: للمستخدمين بإشتراك نشط

---

## 🧠 المنطق الأساسي (Business Logic)

### 1. التحكم في عدد الأجهزة (Device Limit)

**عند طلب بث:**
```python
def enforce_device_limit(user, ip, user_agent):
    # 1. احصل على الاشتراك
    subscription = user.subscription
    
    # 2. احصل على الجلسات النشطة من Redis
    active_sessions = redis.keys(f"session:{user.id}:*")
    
    # 3. تحقق من الحد
    if len(active_sessions) >= subscription.max_devices:
        # خيار A: رفض الطلب
        raise PermissionDenied("Device limit exceeded")
        
        # خيار B: إنهاء الأقدم (configurable)
        # terminate_oldest_session(user)
    
    # 4. أنشئ جلسة جديدة
    session_id = uuid.uuid4()
    redis.setex(
        f"session:{user.id}:{session_id}",
        300,  # 5 minutes TTL
        json.dumps({...})
    )
```

### 2. إنشاء روابط موقّعة (Signed URLs)

```python
import hmac
import hashlib
import time

def generate_signed_url(channel_slug, secret, ttl=3600):
    """
    ينشئ رابط HLS موقّع بـ HMAC
    """
    expires = int(time.time()) + ttl
    path = f"/hls/{channel_slug}/index.m3u8"
    message = f"{path}?expires={expires}"
    
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"https://stream.arenastream.com{path}?expires={expires}&sig={signature}"
```

### 3. تفعيل البث التلقائي

```python
def spawn_stream(channel):
    """
    يتصل بـ FFmpeg Controller لبدء البث
    """
    response = requests.post(
        f"{settings.STREAMER_URL}/spawn",
        json={
            "slug": channel.slug,
            "source": channel.source_url
        },
        timeout=5
    )
    
    if response.status_code == 200:
        channel.is_live = True
        channel.save()
        return True
    return False
```

---

## 🛣️ نقاط النهاية (API Endpoints)

### 🔐 Authentication (`/auth/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register/` | تسجيل مستخدم جديد | ❌ |
| POST | `/auth/login/` | تسجيل دخول (JWT) | ❌ |
| POST | `/auth/logout/` | تسجيل خروج | ✅ |
| POST | `/auth/refresh/` | تحديث التوكن | ✅ |
| POST | `/auth/password-reset/` | إعادة تعيين كلمة المرور | ❌ |

---

### 👤 User (`/user/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/me/` | معلومات المستخدم الحالي | ✅ |
| PATCH | `/user/me/` | تحديث الملف الشخصي | ✅ |
| GET | `/user/subscription/` | تفاصيل الاشتراك | ✅ |
| POST | `/user/devices/` | سرد الأجهزة المسجلة | ✅ |

---

### 📺 Channels (`/channels/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/channels/` | قائمة القنوات المتاحة | ✅ |
| GET | `/channels/{id}/` | تفاصيل قناة | ✅ |
| GET | `/channels/categories/` | فئات القنوات | ✅ |
| POST | `/admin/channels/` | إضافة قناة (إداري) | 🔑 Admin |
| PATCH | `/admin/channels/{id}/` | تعديل قناة | 🔑 Admin |
| DELETE | `/admin/channels/{id}/` | حذف قناة | 🔑 Admin |

---

### ⚽ Events (`/events/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/events/` | قائمة الفعاليات | ✅ |
| GET | `/events/live/` | الفعاليات المباشرة الآن | ✅ |
| GET | `/events/upcoming/` | الفعاليات القادمة | ✅ |
| GET | `/events/{id}/` | تفاصيل فعالية | ✅ |
| POST | `/admin/events/` | إنشاء فعالية | 🔑 Admin |
| PATCH | `/admin/events/{id}/` | تعديل فعالية | 🔑 Admin |
| DELETE | `/admin/events/{id}/` | حذف فعالية | 🔑 Admin |

---

### 📡 Stream (`/stream/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/stream/{id}/play/` | الحصول على رابط HLS موقّع | ✅ |
| POST | `/stream/{id}/heartbeat/` | تحديث الجلسة (كل 30 ثانية) | ✅ |
| DELETE | `/stream/disconnect/` | إنهاء جلسة البث | ✅ |

**مثال Response لـ `/stream/{id}/play/`:**
```json
{
  "channel_id": 1,
  "channel_name": "beIN Sports 1",
  "hls_url": "https://stream.arenastream.com/hls/channel1/index.m3u8?expires=1730000000&sig=abc123...",
  "expires_in": 3600,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 🔧 Admin (`/admin/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/users/` | قائمة المستخدمين | 🔑 Admin |
| PATCH | `/admin/users/{id}/subscription/` | تعديل اشتراك | 🔑 Admin |
| POST | `/admin/users/{id}/disable/` | تعطيل مستخدم | 🔑 Admin |
| GET | `/admin/live-viewers/` | المشاهدون النشطون | 🔑 Admin |
| DELETE | `/admin/sessions/{id}/` | فصل جلسة مشاهدة | 🔑 Admin |
| GET | `/admin/analytics/` | إحصائيات شاملة | 🔑 Admin |

---

## 🔁 تكامل Stream Controller (FFmpeg)

### Flow
```
1. User → POST /stream/5/play/
2. Django → Check device limit
3. Django → POST http://streamer:8080/spawn
   Body: {"slug": "channel5", "source": "http://example.com/live.m3u8"}
4. Streamer → Creates /var/www/hls/channel5/index.m3u8
5. Django → Generate signed URL
6. Django → Return to client
7. Client → Play HLS stream
```

---

## 🔒 الأمان (Security)

### ✅ التدابير المطبقة
- CORS محدد بالنطاقات المسموح بها
- JWT مع انتهاء صلاحية قصير
- روابط HLS موقّعة تنتهي خلال ساعة
- حدود الأجهزة عبر Redis
- Rate Limiting على API endpoints
- HTTPS إلزامي
- إخفاء `source_url` في API responses

### 🔧 إعدادات Django
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

## 📦 ملفات المشروع المطلوبة

### 1. `requirements.txt`
```txt
Django==5.0.0
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
drf-spectacular==0.27.0
django-cors-headers==4.3.0
psycopg2-binary==2.9.9
redis==5.0.0
python-dotenv==1.0.0
requests==2.31.0
gunicorn==21.2.0
celery==5.3.0  # للمهام الخلفية
```

### 2. `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "arena_core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 3. `docker-compose.yml`
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: arenastream
      POSTGRES_USER: arenastream
      POSTGRES_PASSWORD: arenastream
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    
  api:
    build: .
    command: gunicorn arena_core.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

---

## 📋 قائمة المهام

### ❌ لم يبدأ (Not Started)

- [ ] إنشاء Django project (`arena_core`)
- [ ] إنشاء app (`stream_api`)
- [ ] تكوين PostgreSQL و Redis
- [ ] إنشاء CustomUser model
- [ ] إنشاء Subscription model
- [ ] إنشاء Channel model
- [ ] إنشاء Event model
- [ ] إنشاء Category model
- [ ] تنفيذ JWT authentication
- [ ] إنشاء User serializers & views
- [ ] إنشاء Channel serializers & views
- [ ] إنشاء Event serializers & views
- [ ] تنفيذ Device Limit logic
- [ ] تنفيذ Signed URL generation
- [ ] تكامل FFmpeg Controller
- [ ] إنشاء Admin endpoints
- [ ] إعداد CORS
- [ ] إعداد Rate Limiting
- [ ] كتابة Unit Tests
- [ ] إعداد Celery (للمهام الخلفية)
- [ ] إعداد Logging
- [ ] إنشاء API Documentation (drf-spectacular)
- [ ] إنشاء .env.example
- [ ] إنشاء Dockerfile
- [ ] إنشاء docker-compose.yml
- [ ] إعداد CI/CD
- [ ] إعداد Monitoring (Sentry/NewRelic)

### ⏳ قيد الإنجاز (In Progress)

- [ ] *لا شيء حالياً*

### ✅ تم الإنجاز (Completed)

- [x] تصميم Architecture
- [x] تحديد Models
- [x] تحديد API Endpoints
- [x] كتابة Documentation

---

## 🎯 الأولويات

### 🔴 عالية (High Priority)
1. إنشاء المشروع وإعداد البيئة
2. إنشاء Models الأساسية
3. تنفيذ JWT Authentication
4. إنشاء Channel & Event APIs
5. تنفيذ Device Limit Logic
6. تكامل Stream Controller

### 🟡 متوسطة (Medium Priority)
7. Admin Panel APIs
8. Rate Limiting & Security
9. Testing
10. Docker Setup

### 🟢 منخفضة (Low Priority)
11. Celery Tasks
12. Advanced Analytics
13. Email Notifications
14. CI/CD Pipeline

---

## 🚀 خطوات البدء

```bash
# 1. إنشاء Django project
django-admin startproject arena_core .

# 2. إنشاء التطبيق الرئيسي
python manage.py startapp stream_api

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. إعداد قاعدة البيانات
python manage.py makemigrations
python manage.py migrate

# 5. إنشاء superuser
python manage.py createsuperuser

# 6. تشغيل السيرفر
python manage.py runserver
```

---

## 📚 موارد مفيدة

- [Django REST Framework Docs](https://www.django-rest-framework.org/)
- [SimpleJWT Docs](https://django-rest-framework-simplejwt.readthedocs.io/)
- [drf-spectacular Docs](https://drf-spectacular.readthedocs.io/)
- [Redis Python Docs](https://redis-py.readthedocs.io/)

---

**آخر تحديث:** أكتوبر 2025
**الإصدار:** 0.0.0 (لم يبدأ)
**الحالة:** 🔴 لم يبدأ (0% مُنجز)
