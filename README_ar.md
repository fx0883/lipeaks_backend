# 🚀 LiPeaks Backend - نظام خلفي لمنصة SaaS متعددة المستأجرين للمؤسسات

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 مقدمة المشروع

LiPeaks Backend هو نظام خلفي لمنصة SaaS متعددة المستأجرين للمؤسسات مبني على Django 5.2. يعتمد تصميم معماري متقدم متعدد المستأجرين لتوفير بيئات تطبيقية معزولة تماماً للمنظمات أو العملاء المختلفين (المستأجرين).

## ✨ الميزات الأساسية

- 🔐 **الهندسة المعمارية متعددة المستأجرين** - عزل البيانات الكامل، يدعم التوسع غير المحدود للمستأجرين
- 👥 **إدارة صلاحيات المستخدمين** - نظام صلاحيات RBAC مع تحكم دقيق
- 📝 **نظام إدارة المحتوى** - إدارة المقالات والوسائط والقوالب
- 💼 **إدارة علاقات العملاء** - معلومات العملاء والتصنيف والتتبع
- 📋 **نظام إدارة الطلبات** - العمليات التجارية وإدارة التكاليف
- ⏰ **نظام تسجيل الحضور** - إدارة المهام والتحليل الإحصائي
- 🍽️ **إدارة القوائم** - قوائم ديناميكية مع تحكم في الصلاحيات
- 📊 **تحليل الرسوم البيانية** - تصور البيانات وتوليد التقارير

## 🏗️ الهندسة المعمارية التقنية

- **إطار العمل الخلفي**: Django 5.2 + Django REST Framework
- **قاعدة البيانات**: MySQL 8.0+ (مشغل PyMySQL)
- **المصادقة**: JWT + نظام صلاحيات RBAC
- **توثيق API**: OpenAPI 3.0 + Swagger UI
- **النشر**: Docker + Nginx + Gunicorn

## 🚀 البداية السريعة

### المتطلبات
- Python 3.9+
- MySQL 8.0+
- Redis 6.0+ (اختياري)

### النشر بنقرة واحدة باستخدام Docker
```bash
# استنساخ المشروع
git clone https://github.com/fx0883/lipeaks_backend.git
cd lipeaks_backend

# بدء الخدمات
docker-compose up -d

# تهيئة قاعدة البيانات
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### النشر في بيئة Python
```bash
# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# تثبيت التبعيات
pip install -r requirements.txt

# تكوين متغيرات البيئة
cp .env.sample .env
# تحرير ملف .env

# ترحيل قاعدة البيانات
python manage.py migrate
python manage.py createsuperuser

# بدء الخدمة
python manage.py runserver
```

## 📚 توثيق API

- **Swagger UI**: `/api/v1/docs/`
- **ReDoc**: `/api/v1/redoc/`
- **OpenAPI Schema**: `/api/v1/schema/`

## 🔧 التكوين

### متغيرات البيئة
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=lipeaks_db
DB_USER=lipeaks_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

### تكوين قاعدة البيانات
```sql
CREATE DATABASE lipeaks_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lipeaks_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON lipeaks_db.* TO 'lipeaks_user'@'localhost';
```

## 🛠️ دليل التطوير

### هيكل المشروع
```
lipeaks_backend/
├── core/           # التكوين الأساسي
├── users/          # إدارة المستخدمين
├── tenants/        # إدارة المستأجرين
├── rbac/           # إدارة الصلاحيات
├── cms/            # إدارة المحتوى
├── customers/      # إدارة العملاء
├── orders/         # إدارة الطلبات
├── check_system/   # نظام تسجيل الحضور
├── menus/          # إدارة القوائم
├── charts/         # تحليل الرسوم البيانية
└── common/         # الوظائف المشتركة
```

### بيئة التطوير
```bash
# تثبيت تبعيات التطوير
pip install -r requirements-dev.txt

# تنسيق الكود
black .
isort .

# تشغيل الاختبارات
python manage.py test
```

## 🚀 دليل النشر

### نشر بيئة الإنتاج
```bash
# استخدام Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000

# استخدام Docker
docker-compose -f docker-compose.prod.yml up -d
```

### تكوين Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 ميزات الأمان

- آلية مصادقة JWT
- عزل بيانات المستأجرين
- تحكم في الصلاحيات RBAC
- حماية من CSRF
- حماية من XSS
- حماية من حقن SQL

## 📈 المراقبة والعمليات

### إدارة السجلات
- تسجيل السجلات المنظمة
- تدوير السجلات والاحتفاظ بها
- مراقبة الأخطاء والتقارير

### تحسين الأداء
- تحسين استعلامات قاعدة البيانات
- دعم ذاكرة التخزين المؤقت Redis
- تحسين الملفات الثابتة

## ❓ الأسئلة الشائعة

**س: كيف أضيف وحدات أعمال جديدة؟**
ج: ورث من BaseModel للحصول تلقائياً على وظيفة عزل المستأجرين

**س: كيف أحسن أداء قاعدة البيانات؟**
ج: استخدم TenantManager وقم بإعداد الفهارس المناسبة

**س: كيف أكون بيئة الإنتاج؟**
ج: اضبط DEBUG=False، كون قاعدة بيانات الإنتاج، فعّل HTTPS

## 🤝 المساهمة

1. انسخ المشروع
2. أنشئ فرع ميزة
3. اكتب تغييراتك
4. أنشئ طلب سحب

## 📄 الترخيص

هذا المشروع مرخص تحت [رخصة MIT](LICENSE)

## 📞 اتصل بنا

- **البريد الإلكتروني**: contact@lipeaks.com
- **تقرير المشاكل**: [GitHub Issues](https://github.com/fx0883/lipeaks_backend/issues)
- **النقاش التقني**: مجموعة QQ/مجموعة WeChat

---

<div align="center">

**إذا ساعدك هذا المشروع، يرجى إعطاؤنا ⭐ نجمة!**

صنع بـ ❤️ بواسطة [فريق LiPeaks](https://github.com/fx0883)

</div>
