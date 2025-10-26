# Redis Troubleshooting Guide - حل مشكلة Redis

## 🔍 تشخيص المشكلة

### الخطأ 1: `sudo: unable to resolve host`
هذا تحذير بسيط عن اسم المضيف ويمكن تجاهله مؤقتاً.

### الخطأ 2: `Job for redis-server.service failed`
هذا الخطأ الأساسي - Redis لا يعمل.

## 🛠️ الحل السريع

### الخطوة 1: فحص حالة Redis

```bash
# فحص حالة الخدمة
sudo systemctl status redis-server

# عرض الـ Logs
sudo journalctl -xeu redis-server.service

# فحص الإعدادات
sudo cat /etc/redis/redis.conf | grep -E "bind|port|dir"
```

### الخطوة 2: إصلاح مشكلة Hostname (اختياري)

```bash
# إضافة اسم المضيف إلى /etc/hosts
echo "127.0.0.1 localhost $(hostname)" | sudo tee -a /etc/hosts

# أو إزالة التحذير
echo "your-server-name" | sudo tee /etc/hostname
sudo hostnamectl set-hostname your-server-name
```

### الخطوة 3: إزالة وتثبيت Redis من جديد

```bash
# إيقاف Redis
sudo systemctl stop redis-server

# إزالة Redis
sudo apt remove --purge redis-server -y
sudo apt autoremove -y

# تنظيف الملفات القديمة
sudo rm -rf /var/lib/redis
sudo rm -rf /etc/redis

# تثبيت Redis من جديد
sudo apt update
sudo apt install -y redis-server

# فحص حالة الملفات
ls -la /etc/redis/
cat /etc/redis/redis.conf | head -20
```

### الخطوة 4: تعديل إعدادات Redis

```bash
# فتح ملف الإعدادات
sudo nano /etc/redis/redis.conf
```

ابحث عن هذه السطور وغيرها:

```
# من:
# bind 127.0.0.1 ::1

# إلى:
bind 127.0.0.1
```

قم بتعطيل هذه السطور:

```
# من:
# supervised no

# إلى:
supervised systemd
```

### الخطوة 5: فحص وإصلاح Permissions

```bash
# فحص ملكية المجلدات
ls -la /var/lib/redis/
ls -la /var/log/redis/

# إصلاح الصلاحيات إذا لزم الأمر
sudo chown -R redis:redis /var/lib/redis
sudo chown -R redis:redis /var/log/redis
sudo chmod 755 /var/lib/redis
```

### الخطوة 6: إنشاء مجلد الـ Data إذا لم يكن موجود

```bash
# إنشاء المجلدات المطلوبة
sudo mkdir -p /var/lib/redis
sudo mkdir -p /var/log/redis

# تعديل الملكية
sudo chown redis:redis /var/lib/redis
sudo chown redis:redis /var/log/redis

# تعديل الصلاحيات
sudo chmod 755 /var/lib/redis
sudo chmod 755 /var/log/redis
```

### الخطوة 7: بدء وإعادة بدء Redis

```bash
# بدء الخدمة
sudo systemctl start redis-server

# التحقق من الحالة
sudo systemctl status redis-server

# تفعيل الخدمة عند إعادة التشغيل
sudo systemctl enable redis-server

# اختبار الاتصال
redis-cli ping
# يجب أن يظهر: PONG
```

## 🔧 الحل البديل (Manual Start)

إذا استمرت المشكلة، يمكنك تشغيل Redis يدوياً:

```bash
# إيقاف الخدمة
sudo systemctl stop redis-server

# تشغيل Redis يدوياً
sudo -u redis redis-server /etc/redis/redis.conf

# في terminal آخر، اختبر الاتصال
redis-cli ping

# إذا نجح، استخدم Ctrl+C لإيقاف العملية اليدوية
```

## 📝 إعدادات ملف redis.conf الافتراضية

```bash
# إنشاء ملف إعدادات بسيط
sudo nano /etc/redis/redis.conf
```

أضف هذا المحتوى:

```
bind 127.0.0.1
port 6379
protected-mode yes
dir /var/lib/redis
logfile /var/log/redis/redis-server.log
supervised systemd
```

## 🧪 اختبار شامل

بعد إصلاح المشكلة، قم بهذه الاختبارات:

```bash
# 1. فحص حالة الخدمة
sudo systemctl status redis-server

# 2. اختبار الاتصال
redis-cli ping
# يجب أن يظهر: PONG

# 3. تعيين واسترجاع قيمة
redis-cli set test "Hello Redis"
redis-cli get test
# يجب أن يظهر: Hello Redis

# 4. عرض معلومات الخادم
redis-cli info

# 5. مراقبة الـ Commands في الوقت الفعلي
redis-cli monitor
```

## 🚨 إذا فشل كل شيء

### الحل الأخير: تثبيت من المصدر

```bash
# تحميل وتثبيت من المصدر
cd /tmp
wget https://download.redis.io/redis-stable.tar.gz
tar xzf redis-stable.tar.gz
cd redis-stable
make
sudo make install

# تشغيل Redis
redis-server

# في terminal آخر
redis-cli ping
```

## 📊 أوامر إضافية مفيدة

```bash
# عرض جميع مفاتيح Redis
redis-cli KEYS *

# حذف جميع البيانات
redis-cli FLUSHALL

# إيقاف Redis بشكل آمن
redis-cli SHUTDOWN

# فحص استخدام الذاكرة
redis-cli INFO memory
```

## ✅ التحقق النهائي

بعد إصلاح المشكلة، تأكد من:

```bash
# Redis يعمل
sudo systemctl status redis-server

# يمكن الاتصال
redis-cli ping
# النتيجة: PONG

# يعمل بعد إعادة التشغيل
sudo reboot
# ثم بعد إعادة التشغيل:
redis-cli ping
```
