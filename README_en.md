# 🚀 LiPeaks Backend - Enterprise Multi-Tenant SaaS Platform Backend System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 Project Introduction

LiPeaks Backend is an enterprise-grade multi-tenant SaaS platform backend system built on Django 5.2. It adopts advanced multi-tenant architecture design to provide completely isolated application environments for different organizations or clients (tenants).

## ✨ Core Features

- 🔐 **Multi-Tenant Architecture** - Complete data isolation, supports unlimited tenant expansion
- 👥 **User Permission Management** - RBAC permission system with fine-grained control
- 📝 **Content Management System** - Article, media, and template management
- 💼 **Customer Relationship Management** - Customer information, classification, and tracking
- 📋 **Order Management System** - Business processes and cost management
- ⏰ **Check-in System** - Task management and statistical analysis
- 🍽️ **Menu Management** - Dynamic menus with permission control
- 📊 **Chart Analysis** - Data visualization and report generation

## 🏗️ Technical Architecture

- **Backend Framework**: Django 5.2 + Django REST Framework
- **Database**: MySQL 8.0+ (PyMySQL driver)
- **Authentication**: JWT + RBAC permission system
- **API Documentation**: OpenAPI 3.0 + Swagger UI
- **Deployment**: Docker + Nginx + Gunicorn

## 🚀 Quick Start

### Requirements
- Python 3.9+
- MySQL 8.0+
- Redis 6.0+ (optional)

### Docker One-Click Deployment
```bash
# Clone project
git clone https://github.com/fx0883/lipeaks_backend.git
cd lipeaks_backend

# Start services
docker-compose up -d

# Initialize database
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Python Environment Deployment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.sample .env
# Edit .env file

# Database migration
python manage.py migrate
python manage.py createsuperuser

# Start service
python manage.py runserver
```

## 📚 API Documentation

- **Swagger UI**: `/api/v1/docs/`
- **ReDoc**: `/api/v1/redoc/`
- **OpenAPI Schema**: `/api/v1/schema/`

## 🔧 Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=lipeaks_db
DB_USER=lipeaks_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

### Database Configuration
```sql
CREATE DATABASE lipeaks_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lipeaks_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON lipeaks_db.* TO 'lipeaks_user'@'localhost';
```

## 🛠️ Development Guide

### Project Structure
```
lipeaks_backend/
├── core/           # Core configuration
├── users/          # User management
├── tenants/        # Tenant management
├── rbac/           # Permission management
├── cms/            # Content management
├── customers/      # Customer management
├── orders/         # Order management
├── check_system/   # Check-in system
├── menus/          # Menu management
├── charts/         # Chart analysis
└── common/         # Common functionality
```

### Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Code formatting
black .
isort .

# Run tests
python manage.py test
```

## 🚀 Deployment Guide

### Production Environment Deployment
```bash
# Using Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000

# Using Docker
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx Configuration
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

## 🔒 Security Features

- JWT authentication mechanism
- Tenant data isolation
- RBAC permission control
- CSRF protection
- XSS protection
- SQL injection protection

## 📈 Monitoring and Operations

### Log Management
- Structured log recording
- Log rotation and retention
- Error monitoring and reporting

### Performance Optimization
- Database query optimization
- Redis cache support
- Static file optimization

## ❓ FAQ

**Q: How to add new business modules?**
A: Inherit from BaseModel to automatically get tenant isolation functionality

**Q: How to optimize database performance?**
A: Use TenantManager and set up proper indexes

**Q: How to configure production environment?**
A: Set DEBUG=False, configure production database, enable HTTPS

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Create a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE)

## 📞 Contact Us

- **Email**: contact@lipeaks.com
- **Issue Feedback**: [GitHub Issues](https://github.com/fx0883/lipeaks_backend/issues)
- **Technical Discussion**: QQ Group/WeChat Group

---

<div align="center">

**If this project helps you, please give us a ⭐ Star!**

Made with ❤️ by [LiPeaks Team](https://github.com/fx0883)

</div>
