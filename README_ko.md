# 🚀 LiPeaks Backend - 엔터프라이즈 멀티테넌트 SaaS 플랫폼 백엔드 시스템

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 프로젝트 소개

LiPeaks Backend는 Django 5.2를 기반으로 한 엔터프라이즈급 멀티테넌트 SaaS 플랫폼 백엔드 시스템입니다. 선진적인 멀티테넌트 아키텍처 설계를 채택하여 서로 다른 조직이나 클라이언트(테넌트)에게 완전히 격리된 애플리케이션 환경을 제공합니다.

## ✨ 핵심 기능

- 🔐 **멀티테넌트 아키텍처** - 데이터 완전 격리, 무제한 테넌트 확장 지원
- 👥 **사용자 권한 관리** - RBAC 권한 시스템, 세밀한 제어
- 📝 **콘텐츠 관리 시스템** - 기사, 미디어, 템플릿 관리
- 💼 **고객 관계 관리** - 고객 정보, 분류, 추적
- 📋 **주문 관리 시스템** - 비즈니스 프로세스, 비용 관리
- ⏰ **체크인 시스템** - 작업 관리, 통계 분석
- 🍽️ **메뉴 관리** - 동적 메뉴, 권한 제어
- 📊 **차트 분석** - 데이터 시각화, 보고서 생성

## 🏗️ 기술 아키텍처

- **백엔드 프레임워크**: Django 5.2 + Django REST Framework
- **데이터베이스**: MySQL 8.0+ (PyMySQL 드라이버)
- **인증**: JWT + RBAC 권한 시스템
- **API 문서**: OpenAPI 3.0 + Swagger UI
- **배포**: Docker + Nginx + Gunicorn

## 🚀 빠른 시작

### 요구사항
- Python 3.9+
- MySQL 8.0+
- Redis 6.0+ (선택사항)

### Docker 원클릭 배포
```bash
# 프로젝트 클론
git clone https://github.com/fx0883/lipeaks_backend.git
cd lipeaks_backend

# 서비스 시작
docker-compose up -d

# 데이터베이스 초기화
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Python 환경 배포
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.sample .env
# .env 파일 편집

# 데이터베이스 마이그레이션
python manage.py migrate
python manage.py createsuperuser

# 서비스 시작
python manage.py runserver
```

## 📚 API 문서

- **Swagger UI**: `/api/v1/docs/`
- **ReDoc**: `/api/v1/redoc/`
- **OpenAPI Schema**: `/api/v1/schema/`

## 🔧 설정

### 환경변수
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=lipeaks_db
DB_USER=lipeaks_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

### 데이터베이스 설정
```sql
CREATE DATABASE lipeaks_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lipeaks_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON lipeaks_db.* TO 'lipeaks_user'@'localhost';
```

## 🛠️ 개발 가이드

### 프로젝트 구조
```
lipeaks_backend/
├── core/           # 핵심 설정
├── users/          # 사용자 관리
├── tenants/        # 테넌트 관리
├── rbac/           # 권한 관리
├── cms/            # 콘텐츠 관리
├── customers/      # 고객 관리
├── orders/         # 주문 관리
├── check_system/   # 체크인 시스템
├── menus/          # 메뉴 관리
├── charts/         # 차트 분석
└── common/         # 공통 기능
```

### 개발 환경
```bash
# 개발 의존성 설치
pip install -r requirements-dev.txt

# 코드 포맷팅
black .
isort .

# 테스트 실행
python manage.py test
```

## 🚀 배포 가이드

### 프로덕션 환경 배포
```bash
# Gunicorn 사용
gunicorn core.wsgi:application --bind 0.0.0.0:8000

# Docker 사용
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx 설정
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

## 🔒 보안 기능

- JWT 인증 메커니즘
- 테넌트 데이터 격리
- RBAC 권한 제어
- CSRF 보호
- XSS 보호
- SQL 인젝션 보호

## 📈 모니터링 및 운영

### 로그 관리
- 구조화된 로그 기록
- 로그 로테이션 및 보존
- 오류 모니터링 및 보고

### 성능 최적화
- 데이터베이스 쿼리 최적화
- Redis 캐시 지원
- 정적 파일 최적화

## ❓ 자주 묻는 질문

**Q: 새로운 비즈니스 모듈을 추가하려면?**
A: BaseModel을 상속하면 자동으로 테넌트 격리 기능을 얻을 수 있습니다

**Q: 데이터베이스 성능을 최적화하려면?**
A: TenantManager를 사용하고 적절한 인덱스를 설정하세요

**Q: 프로덕션 환경을 설정하려면?**
A: DEBUG=False로 설정하고, 프로덕션 데이터베이스를 구성하고, HTTPS를 활성화하세요

## 🤝 기여

1. 프로젝트 포크
2. 기능 브랜치 생성
3. 변경사항 커밋
4. 풀 리퀘스트 생성

## 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다

## 📞 연락처

- **이메일**: contact@lipeaks.com
- **문제 보고**: [GitHub Issues](https://github.com/fx0883/lipeaks_backend/issues)
- **기술 토론**: QQ 그룹/WeChat 그룹

---

<div align="center">

**이 프로젝트가 도움이 되었다면 ⭐ Star를 부탁드립니다!**

[LiPeaks Team](https://github.com/fx0883)이 ❤️으로 만들었습니다

</div>
