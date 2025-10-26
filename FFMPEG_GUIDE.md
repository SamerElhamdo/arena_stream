# 📺 دليل FFmpeg - استقبال وإعادة البث

## 📋 نظرة عامة

نستخدم **FFmpeg** لاستقبال البث من مصادر M3U/HLS وإعادة إرساله إلى منصات RTMP مثل Telegram و Twitter و YouTube.

## 🎯 كيفية عمل النظام

```
[مصدر M3U/HLS]  →  [FFmpeg]  →  [RTMP Server]  →  [منصات البث]
   (Input)                        (Process)         (Output)
```

## 🔧 مكونات النظام

### 1. ملف restream_service.py

هذا الملف يحتوي على 3 دوال رئيسية:

#### أ. `start_restream()`
دالة لبدء إعادة البث باستخدام FFmpeg

```python
ffmpeg_cmd = [
    'ffmpeg',
    '-i', source_url,          # مصدر البث (M3U/HLS)
    '-c:v', 'copy',            # نسخ كودك الفيديو بدون إعادة تشفير
    '-c:a', 'copy',            # نسخ كودك الصوت بدون إعادة تشفير
    '-f', 'flv',               # تنسيق الإخراج (FLV للـ RTMP)
    '-stream_loop', '-1',      # تكرار البث عند انتهائه
    '-reconnect', '1',         # إعادة الاتصال التلقائية
    '-reconnect_at_eof', '1',  # إعادة الاتصال عند نهاية الملف
    '-reconnect_streamed', '1',
    '-reconnect_delay_max', '2',
    full_rtmp                  # عنوان RTMP الوجهة
]
```

#### ب. `stop_restream()`
دالة لإيقاف عملية FFmpeg

#### ج. `check_restream_status()`
دالة للتحقق من حالة عملية FFmpeg

## 📊 سير العمل (Workflow)

### 1. المستخدم يبدأ إعادة البث

```
المستخدم يدخل في Admin Panel:
- رابط M3U Source: https://example.com/playlist.m3u8
- Target: Telegram RTMP
```

### 2. Backend يستدعي FFmpeg

```python
result = start_restream(
    source_url="https://example.com/playlist.m3u8",
    rtmp_url="rtmp://dc1.contribute.live-video.net/app/",
    stream_key="live_xxxxx"
)
```

### 3. FFmpeg يبدأ عملية البث

```bash
ffmpeg -i https://example.com/playlist.m3u8 \
    -c:v copy -c:a copy -f flv \
    -stream_loop -1 -reconnect 1 \
    rtmp://dc1.contribute.live-video.net/app/live_xxxxx
```

### 4. يتم حفظ العملية في قاعدة البيانات

```python
session = ReStreamSession.objects.create(
    channel=channel,
    target=target,
    source_url=source_url,
    rtmp_url=rtmp_url,
    status='Running',
    process_id=process_id  # Process ID من FFmpeg
)
```

## 🎛️ إعدادات FFmpeg المستخدمة

### إعدادات المدخلات (Input)
- `-i`: مصدر البث (M3U/HLS URL)
- يدعم جميع الصيغ: HLS, MPEG-TS, RTSP, HTTP

### إعدادات التشفير (Encoding)
- `-c:v copy`: نسخ كودك الفيديو كما هو (توفير مواصفات)
- `-c:a copy`: نسخ كودك الصوت كما هو
- البديل: يمكن إعادة التشفير لضغط أو تحسين:
  ```
  -c:v libx264          # H.264 encoding
  -preset fast           # سرعة التشفير
  -crf 23                # جودة الفيديو
  -c:a aac               # AAC audio encoding
  -b:a 128k              # بت معدل الصوت
  ```

### إعدادات الإخراج (Output)
- `-f flv`: تنسيق FLV للـ RTMP
- يدعم أيضاً: RTMP, SRT, WebRTC

### إعدادات إعادة الاتصال
- `-reconnect 1`: تفعيل إعادة الاتصال التلقائية
- `-reconnect_at_eof 1`: إعادة الاتصال عند نهاية الملف
- `-reconnect_streamed 1`: إعادة الاتصال للبث المباشر
- `-reconnect_delay_max 2`: أقصى تأخير (ثواني)

### إعدادات التكرار (Looping)
- `-stream_loop -1`: تكرار لا نهائي

## 🔄 السيناريوهات المدعومة

### السيناريو 1: بث مباشر HLS → RTMP

```bash
ffmpeg -i https://server.com/live.m3u8 \
    -c copy -f flv \
    rtmp://live.twitch.tv/app/live_xxxxx
```

### السيناريو 2: ملفات M3U → RTMP

```bash
ffmpeg -i https://example.com/playlist.m3u8 \
    -c copy -f flv \
    -stream_loop -1 \
    rtmp://server.com/live/streamkey
```

### السيناريو 3: مع إعادة التشفير (لتحسين الجودة)

```bash
ffmpeg -i https://example.com/playlist.m3u8 \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 128k \
    -f flv \
    rtmp://server.com/live/streamkey
```

## 🛠️ صيانة ومراقبة FFmpeg

### عرض العمليات النشطة

```bash
# عرض جميع عمليات FFmpeg
ps aux | grep ffmpeg

# عرض عمليات محددة
pgrep -f "ffmpeg.*rtmp"
```

### مراقبة استخدام الموارد

```bash
# عرض استخدام CPU والذاكرة
top -p $(pgrep -d',' ffmpeg)

# مراقبة في الوقت الفعلي
htop -p $(pgrep -d',' ffmpeg)
```

### إيقاف عملية معينة

```bash
# إيقاف عملية بـ PID
kill -15 <PID>

# إيقاف قسري
kill -9 <PID>

# إيقاف جميع عمليات FFmpeg
pkill ffmpeg
```

### عرض الـ Logs

```bash
# Logs من Django
sudo journalctl -u arena-stream-backend -f

# Logs من /var/log/
sudo tail -f /var/log/arena-stream-restream.log
```

## 📈 تحسين الأداء

### 1. إعدادات FFmpeg المحسّنة

```python
ffmpeg_cmd = [
    'ffmpeg',
    '-i', source_url,
    
    # Video settings
    '-c:v', 'libx264',
    '-preset', 'veryfast',    # توازن بين السرعة والجودة
    '-tune', 'zerolatency',   # تقليل التأخير
    '-crf', '23',             # جودة الفيديو (18-28)
    
    # Audio settings
    '-c:a', 'aac',
    '-b:a', '128k',           # بت معدل الصوت
    
    # Buffer settings
    '-maxrate', '3000k',      # أقصى معدل بت
    '-bufsize', '6000k',      # حجم الـ Buffer
    
    # Output
    '-f', 'flv',
    '-rtmp_live', 'live',     # وضع البث المباشر
    full_rtmp
]
```

### 2. إدارة الموارد

```bash
# تحديد عدد الـ Workers
# في gunicorn.service
--workers 3  # للنوات المتعددة

# تحديد استخدام الذاكرة
ulimit -v 2097152  # 2GB لكل عملية
```

## 🚨 استكشاف الأخطاء

### الخطأ: FFmpeg not found

```bash
# تثبيت FFmpeg
sudo apt install -y ffmpeg

# التحقق من التثبيت
ffmpeg -version
```

### الخطأ: Connection timeout

```python
# إضافة timeouts في FFmpeg
'-rw_timeout', '5000000',      # 5 seconds read timeout
'-stimeout', '5000000',        # socket timeout
```

### الخطأ: Codec not supported

```python
# إعادة التشفير إذا الكودك غير مدعوم
'-c:v', 'libx264',            # بدلاً من copy
'-c:a', 'aac',                # بدلاً من copy
```

### الخطأ: Process died

```python
# إضافة auto-restart في Django
def monitor_restream_sessions():
    """مراقبة الجلسات وإعادة تشغيل الميتة"""
    sessions = ReStreamSession.objects.filter(status='Running')
    for session in sessions:
        if session.process_id and not check_restream_status(session.process_id):
            # إعادة التشغيل
            start_restream(session.source_url, session.rtmp_url)
```

## 📊 إحصائيات ومراقبة

### إضافة مراقبة الأداء

```python
# في restream_service.py
import psutil

def get_ffmpeg_stats(process_id):
    """الحصول على إحصائيات عملية FFmpeg"""
    try:
        process = psutil.Process(int(process_id))
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'status': process.status(),
            'create_time': process.create_time(),
        }
    except:
        return None
```

## 🔐 الأمان

### تثبيت FFmpeg بشكل آمن

```bash
# استخدام FFmpeg من official sources
sudo add-apt-repository ppa:jonathonf/ffmpeg-4
sudo apt update
sudo apt install -y ffmpeg
```

### حماية العمليات

```python
# في start_restream()
process = subprocess.Popen(
    ffmpeg_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    preexec_fn=os.setsid,     # إنشاء process group جديد
    user='www-data'           # تشغيل بصلاحيات محدودة
)
```

## 📝 ملخص

✅ **نعم، نحن نستخدم FFmpeg** لـ:
1. استقبال البث من مصادر M3U/HLS
2. إعادة إرسال البث إلى RTMP servers
3. معالجة وإعادة التشفير (اختياري)
4. إدارة الاتصالات وإعادة الاتصال التلقائي

🎯 **المميزات**:
- دعم جميع صيغ الفيديو والصوت
- إعادة اتصال تلقائية
- تكرار البث
- إدارة العمليات
- معالجة الأخطاء

📚 **لمزيد من المعلومات**: راجع [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
