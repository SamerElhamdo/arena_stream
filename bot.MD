# 🎯 ArenaStream - نظرة عامة على المشروع

## 📋 الوصف
**ArenaStream** هو نظام SaaS احترافي لبث الفعاليات الرياضية المباشرة، يتكون من ثلاثة مكونات رئيسية:

1. **🖥️ Admin Dashboard** - واجهة إدارة للتحكم في المستخدمين والقنوات والفعاليات
2. **⚙️ Backend API** - REST API مبني بـ Django يدير كل العمليات والبيانات
3. **📱 Mobile App** - تطبيق موبايل للمستخدمين النهائيين

---

## 🏗️ البنية المعمارية (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    ArenaStream Platform                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │        Load Balancer / CDN (Nginx)       │
        └─────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        ┌─────────────────┐      ┌─────────────────┐
        │  Admin Frontend │      │   Mobile App    │
        │  (React + TS)   │      │  (React Native) │
        └─────────────────┘      └─────────────────┘
                 │                         │
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │    Django REST API      │
                 │  (Python + DRF + JWT)   │
                 └─────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        ┌─────────────────┐      ┌─────────────────┐
        │   PostgreSQL    │      │      Redis      │
        │   (Main DB)     │      │  (Sessions)     │
        └─────────────────┘      └─────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   FFmpeg Streamer       │
                 │   (Flask + FFmpeg)      │
                 │   HLS Generator         │
                 └─────────────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │    HLS Storage (Nginx)  │
                 │  /var/www/hls/          │
                 └─────────────────────────┘
```

---

## 📂 هيكل المشروع

```
arena_stream/
│
├── arena-stream-admin-frontend/    # ✅ React Admin Dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── lib/
│   │   └── hooks/
│   ├── package.json
│   ├── vite.config.ts
│   └── bot.MD                      # 📄 Frontend Documentation
│
├── arena-stream-api-backend/       # ❌ Django REST API (لم يُنشأ بعد)
│   └── bot.MD                      # 📄 Backend Documentation
│
├── arena-stream-mobile/            # ⏳ React Native Mobile App (قيد الإنشاء)
│   ├── App.tsx
│   ├── package.json
│   └── bot.MD                      # 📄 Mobile App Documentation
│
└── bot.MD                          # 📄 هذا الملف (نظرة عامة)
```

---

## 🎯 المكونات الثلاثة

### 1. 🖥️ Admin Dashboard (Frontend)
**الحالة:** 🟢 **70% مُنجز**

**التقنيات:**
- React 18 + TypeScript
- Vite (Build Tool)
- shadcn/ui (UI Components)
- Tailwind CSS
- React Router
- React Query

**الصفحات:**
- ✅ Login
- ✅ Dashboard Home
- ✅ Users & Subscriptions
- ✅ Channels Management
- ✅ Events & Scheduling
- ✅ Live Monitor
- ✅ Analytics
- ✅ Logs
- ✅ Settings

**الملف:** `arena-stream-admin-frontend/bot.MD`

---

### 2. ⚙️ Backend API
**الحالة:** 🔴 **لم يبدأ (0%)**

**التقنيات:**
- Django 5
- Django REST Framework
- PostgreSQL
- Redis
- SimpleJWT (Authentication)
- drf-spectacular (API Docs)
- Gunicorn

**المميزات:**
- ❌ JWT Authentication
- ❌ User & Subscription Management
- ❌ Channel & Event CRUD
- ❌ Device Limit Control (via Redis)
- ❌ Signed HLS URLs (HMAC)
- ❌ FFmpeg Controller Integration
- ❌ Admin Endpoints
- ❌ API Documentation (Swagger/OpenAPI)

**الملف:** `arena-stream-api-backend/bot.MD`

---

### 3. 📱 Mobile App
**الحالة:** 🟡 **10% مُنجز (قيد الإنشاء)**

**التقنيات:**
- React Native (Expo 54)
- TypeScript
- React Navigation
- TanStack Query
- react-native-video (HLS Player)
- AsyncStorage (JWT Storage)

**الشاشات:**
- ⏳ Splash Screen
- ⏳ Login Screen
- ❌ Register Screen
- ❌ Home Screen
- ❌ Channels Screen
- ❌ Events Screen
- ❌ Video Player Screen
- ❌ Favorites Screen
- ❌ Profile Screen
- ❌ Device Management

**الملف:** `arena-stream-mobile/bot.MD`

---

## 🔗 كيف تعمل الأجزاء معاً؟

### سيناريو: مستخدم يشاهد مباراة

```
1️⃣ User → فتح Mobile App
2️⃣ App → POST /auth/login/ (Django API)
3️⃣ API → Returns JWT token
4️⃣ App → Saves token in AsyncStorage

5️⃣ User → تصفح الفعاليات
6️⃣ App → GET /events/live/ (Django API)
7️⃣ API → Returns list of live events

8️⃣ User → يضغط على "Watch"
9️⃣ App → GET /stream/{channel_id}/play/ (Django API)
🔟 API → Checks:
   - Is user authenticated? ✅
   - Has active subscription? ✅
   - Device limit not exceeded? ✅

1️⃣1️⃣ API → POST http://streamer:8080/spawn
   Body: {"slug": "channel5", "source": "http://..."}

1️⃣2️⃣ FFmpeg Streamer → Starts transcoding
   Creates: /var/www/hls/channel5/index.m3u8

1️⃣3️⃣ API → Generates signed HLS URL
   https://stream.arenastream.com/hls/channel5/index.m3u8?expires=...&sig=...

1️⃣4️⃣ API → Returns HLS URL to App

1️⃣5️⃣ App → Loads URL in Video Player (react-native-video)

1️⃣6️⃣ User → يشاهد المباراة 🎉

1️⃣7️⃣ App → Sends heartbeat every 30s (POST /stream/heartbeat/)
   To keep session alive in Redis
```

---

## 📊 حالة الإنجاز الإجمالية

| المكون | الحالة | النسبة | المهام المتبقية |
|--------|--------|---------|------------------|
| **Admin Frontend** | 🟢 جاهز للتطوير | **70%** | ربط API، اختبارات |
| **Backend API** | 🔴 لم يبدأ | **0%** | إنشاء كامل المشروع |
| **Mobile App** | 🟡 قيد الإنشاء | **10%** | جميع الشاشات + Video Player |
| **إجمالي المشروع** | 🟡 | **27%** | - |

---

## 📋 خارطة الطريق (Roadmap)

### المرحلة 1: Backend Setup (أسبوع 1-2)
- [ ] إنشاء Django project
- [ ] إعداد PostgreSQL + Redis
- [ ] إنشاء Models (User, Subscription, Channel, Event)
- [ ] تنفيذ JWT Authentication
- [ ] إنشاء الـ API Endpoints الأساسية
- [ ] تنفيذ Device Limit Logic
- [ ] تكامل FFmpeg Controller

### المرحلة 2: Mobile App Core (أسبوع 3-4)
- [ ] إعداد Expo + Navigation
- [ ] تنفيذ Login/Register
- [ ] إنشاء Home Screen
- [ ] تنفيذ Video Player
- [ ] ربط API Endpoints
- [ ] اختبار HLS Playback

### المرحلة 3: Admin Dashboard Integration (أسبوع 5)
- [ ] ربط Frontend بـ API
- [ ] استبدال Mock Data
- [ ] تنفيذ JWT Auth
- [ ] اختبار جميع الصفحات

### المرحلة 4: Advanced Features (أسبوع 6-7)
- [ ] Push Notifications (Mobile)
- [ ] WebSocket للبيانات الفورية (Admin)
- [ ] تحسين الأداء
- [ ] إضافة Caching
- [ ] تحسين Video Quality Selection

### المرحلة 5: Testing & Deployment (أسبوع 8)
- [ ] Unit Tests (Backend)
- [ ] Integration Tests
- [ ] UI Tests (Mobile)
- [ ] إعداد Docker Compose
- [ ] إعداد CI/CD
- [ ] النشر على Production

---

## 🚀 كيفية البدء

### المتطلبات الأساسية
```bash
# للـ Backend
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

# للـ Frontend
- Node.js 18+
- npm or yarn

# للـ Mobile
- Node.js 18+
- Expo CLI
- iOS Simulator / Android Emulator
```

### تشغيل المشروع

#### 1. Backend (بعد إنشائه)
```bash
cd arena-stream-api-backend
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### 2. Admin Frontend
```bash
cd arena-stream-admin-frontend
npm install
npm run dev
# يفتح على http://localhost:5173
```

#### 3. Mobile App
```bash
cd arena-stream-mobile
npm install
npm start
# اختر: i (iOS) or a (Android) or w (Web)
```

---

## 🔒 الأمان (Security)

### التدابير الأمنية المطبقة/المخططة

| التدبير | الحالة | الوصف |
|---------|--------|-------|
| JWT Authentication | ⏳ | توكنات قصيرة المدى + Refresh |
| HTTPS Enforcement | ⏳ | إجباري على Production |
| CORS Whitelisting | ⏳ | نطاقات محددة فقط |
| Signed HLS URLs | ⏳ | روابط موقّعة بـ HMAC |
| Device Limit | ⏳ | Redis-based sessions |
| Rate Limiting | ⏳ | DRF Throttling |
| SQL Injection Prevention | ✅ | Django ORM |
| XSS Prevention | ✅ | React auto-escaping |
| Password Hashing | ✅ | Django bcrypt |

---

## 📊 تقديرات الأداء

### المستهدف
- **Concurrent Users:** 10,000+
- **Concurrent Streams:** 1,000+
- **API Response Time:** < 200ms
- **Video Startup Time:** < 3 seconds
- **Database Queries:** < 50ms
- **Redis Latency:** < 10ms

---

## 📝 ملاحظات مهمة

### للـ Backend Developer
1. راجع `arena-stream-api-backend/bot.MD` بالتفصيل
2. استخدم البرومبت الموجود لإنشاء المشروع
3. لا تنسَ إعداد `.env` قبل التشغيل
4. اختبر Device Limit logic جيداً

### للـ Frontend Developer
1. Admin Dashboard جاهز تقريباً
2. ركّز على ربط API الحقيقي
3. استبدل Mock Data تدريجياً
4. احرص على معالجة الأخطاء

### للـ Mobile Developer
1. راجع `arena-stream-mobile/bot.MD`
2. Video Player هو أهم مكون
3. اختبر على كلا المنصتين (iOS + Android)
4. احرص على دعم HLS بشكل صحيح

---

## 🤝 المساهمة

### Git Workflow
```bash
# للبدء
git checkout -b feature/your-feature-name

# بعد الانتهاء
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name

# افتح Pull Request
```

### Commit Message Convention
```
feat: أضف ميزة جديدة
fix: إصلاح خطأ
docs: تحديث documentation
style: تعديلات تنسيق الكود
refactor: إعادة هيكلة الكود
test: إضافة اختبارات
chore: مهام صيانة
```

---

## 📚 الموارد والروابط

### Documentation
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [React Native](https://reactnavigation.org/)
- [Expo Docs](https://docs.expo.dev/)
- [shadcn/ui](https://ui.shadcn.com/)

### Tools
- [Postman](https://www.postman.com/) - API Testing
- [Swagger UI](https://swagger.io/) - API Documentation
- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Redux DevTools](https://github.com/reduxjs/redux-devtools)

---

## 📞 الدعم

للأسئلة أو المشاكل، راجع:
1. ملفات `bot.MD` في كل مجلد
2. الـ README في كل مشروع فرعي
3. افتح Issue على GitHub

---

## 📄 الترخيص

هذا المشروع ملكية خاصة وغير متاح للاستخدام العام بدون إذن.

---

**آخر تحديث:** أكتوبر 2025
**الإصدار:** 0.1.0
**الحالة:** 🟡 قيد التطوير النشط

---

## ✅ الخلاصة

### ما تم إنجازه
- ✅ Admin Frontend (70%)
- ✅ Project Structure
- ✅ Documentation الكامل

### ما يجب العمل عليه الآن
1. **أولوية عالية جداً:** بناء Backend API (Django)
2. **أولوية عالية:** إكمال Mobile App الأساسية
3. **أولوية متوسطة:** ربط Admin Frontend بـ API
4. **أولوية منخفضة:** ميزات متقدمة + تحسينات

---

**🎯 الهدف القادم:** إنشاء Django Backend بالكامل باستخدام البرومبت الموجود في `arena-stream-api-backend/bot.MD`
