# CI/CD集成指南 - 租户隔离功能

## 概述

本文档描述如何将租户隔离功能测试集成到CI/CD流程中。

## GitHub Actions配置

### 完整工作流配置

创建文件: `.github/workflows/tenant_isolation_tests.yml`

```yaml
name: Tenant Isolation Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov
    
    - name: Wait for MySQL
      run: |
        for i in {1..30}; do
          if mysqladmin ping -h 127.0.0.1 -u root -proot --silent; then
            echo "MySQL is up"
            break
          fi
          echo "Waiting for MySQL..."
          sleep 1
        done
    
    - name: Run migrations
      env:
        DATABASE_URL: mysql://root:root@127.0.0.1:3306/test_db
      run: |
        python manage.py migrate
    
    - name: Run tenant isolation tests
      env:
        DATABASE_URL: mysql://root:root@127.0.0.1:3306/test_db
      run: |
        pytest tests/test_tenant_isolation.py -v --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: tenant_isolation
        name: codecov-tenant-isolation
    
    - name: Run database validation
      env:
        DATABASE_URL: mysql://root:root@127.0.0.1:3306/test_db
      run: |
        python temp1122/test_remaining_modules.py
        python temp1122/test_cross_tenant_access.py
    
    - name: Performance benchmark
      env:
        DATABASE_URL: mysql://root:root@127.0.0.1:3306/test_db
      run: |
        python temp1122/test_query_performance.py
```

## GitLab CI配置

### 完整Pipeline配置

创建文件: `.gitlab-ci.yml`

```yaml
stages:
  - test
  - security
  - performance

variables:
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: test_db
  MYSQL_HOST: mysql

services:
  - mysql:8.0

before_script:
  - pip install -r requirements.txt
  - pip install pytest pytest-django pytest-cov

test:tenant_isolation:
  stage: test
  script:
    - python manage.py migrate
    - pytest tests/test_tenant_isolation.py -v --cov=. --cov-report=html --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 1 week

test:database_validation:
  stage: test
  script:
    - python manage.py migrate
    - python temp1122/test_remaining_modules.py
    - python temp1122/test_cross_tenant_access.py

security:cross_tenant_access:
  stage: security
  script:
    - python manage.py migrate
    - python temp1122/test_cross_tenant_access.py
  allow_failure: false

performance:query_benchmarks:
  stage: performance
  script:
    - python manage.py migrate
    - python temp1122/test_query_performance.py
  artifacts:
    paths:
      - performance_results.txt
    expire_in: 1 week
```

## Jenkins Pipeline配置

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        DATABASE_URL = 'mysql://root:root@mysql:3306/test_db'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-django pytest-cov'
            }
        }
        
        stage('Database Migration') {
            steps {
                sh 'python manage.py migrate'
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh 'pytest tests/test_tenant_isolation.py -v --junitxml=test-results.xml'
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }
        
        stage('Database Validation') {
            steps {
                sh 'python temp1122/test_remaining_modules.py'
                sh 'python temp1122/test_cross_tenant_access.py'
            }
        }
        
        stage('Security Tests') {
            steps {
                sh 'python temp1122/test_cross_tenant_access.py'
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh 'python temp1122/test_query_performance.py'
            }
        }
    }
    
    post {
        success {
            echo 'All tenant isolation tests passed!'
        }
        failure {
            echo 'Tenant isolation tests failed!'
            mail to: 'dev-team@example.com',
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "Tenant isolation tests failed. Please check ${env.BUILD_URL}"
        }
    }
}
```

## 本地测试脚本

### run_all_tests.sh

```bash
#!/bin/bash
# 本地运行所有租户隔离测试

set -e  # 遇到错误立即退出

echo "======================================================================"
echo "租户隔离功能完整测试套件"
echo "======================================================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试计数
PASSED=0
FAILED=0

run_test() {
    TEST_NAME=$1
    TEST_COMMAND=$2
    
    echo ""
    echo "运行: $TEST_NAME"
    echo "----------------------------------------------------------------------"
    
    if eval "$TEST_COMMAND"; then
        echo -e "${GREEN}✅ $TEST_NAME 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $TEST_NAME 失败${NC}"
        ((FAILED++))
    fi
}

# 1. 数据库迁移
echo ""
echo "步骤1: 数据库迁移"
python manage.py migrate

# 2. 单元测试
run_test "单元测试" "pytest tests/test_tenant_isolation.py -v"

# 3. 数据库验证
run_test "数据库验证" "python manage.py shell < temp1122/test_remaining_modules.py"

# 4. 跨租户访问测试
run_test "跨租户访问测试" "python manage.py shell < temp1122/test_cross_tenant_access.py"

# 5. 性能测试
run_test "性能测试" "python manage.py shell < temp1122/test_query_performance.py"

# 总结
echo ""
echo "======================================================================"
echo "测试总结"
echo "======================================================================"
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo "总计: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "\n${RED}❌ 有测试失败！${NC}"
    exit 1
fi
```

## 测试覆盖率配置

### pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --cov=applications
    --cov=orders
    --cov=customers
    --cov=feedbacks
    --cov=interactions
    --cov=check_system
    --cov=cms
    --cov=licenses
    --cov=points
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    tenant_isolation: 租户隔离相关测试
    security: 安全性测试
    performance: 性能测试
```

### .coveragerc

```ini
[run]
source = .
omit = 
    */migrations/*
    */tests/*
    */venv/*
    manage.py
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
precision = 2
```

## 质量门禁

### SonarQube配置

```properties
# sonar-project.properties
sonar.projectKey=lipeaks_backend
sonar.projectName=Lipeaks Backend
sonar.projectVersion=1.0

sonar.sources=.
sonar.exclusions=**/migrations/**,**/tests/**,**/venv/**

sonar.python.coverage.reportPaths=coverage.xml
sonar.python.version=3.11

# 质量门禁
sonar.qualitygate.wait=true
sonar.qualitygate.timeout=300

# 租户隔离特定规则
sonar.issue.ignore.multicriteria=e1,e2

# 忽略某些特定警告
sonar.issue.ignore.multicriteria.e1.ruleKey=python:S1192
sonar.issue.ignore.multicriteria.e1.resourceKey=**/common/viewsets.py

sonar.issue.ignore.multicriteria.e2.ruleKey=python:S3776
sonar.issue.ignore.multicriteria.e2.resourceKey=**/test_*.py
```

## Pre-commit钩子

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']
  
  - repo: local
    hooks:
      - id: tenant-isolation-quick-test
        name: Tenant Isolation Quick Test
        entry: pytest tests/test_tenant_isolation.py::TenantIsolationTestCase::test_application_tenant_isolation -v
        language: system
        pass_filenames: false
        always_run: true
```

## Docker测试环境

### docker-compose.test.yml

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: test_db
    ports:
      - "3307:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  test:
    build: .
    command: >
      bash -c "
        python manage.py migrate &&
        pytest tests/test_tenant_isolation.py -v &&
        python temp1122/test_remaining_modules.py &&
        python temp1122/test_cross_tenant_access.py
      "
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: mysql://root:root@db:3306/test_db
    volumes:
      - .:/app
```

## 监控和告警

### 性能监控

```python
# monitoring/tenant_isolation_metrics.py
from prometheus_client import Counter, Histogram

# 租户隔离相关指标
tenant_query_duration = Histogram(
    'tenant_query_duration_seconds',
    'Time spent in tenant-filtered queries',
    ['model', 'operation']
)

cross_tenant_access_attempts = Counter(
    'cross_tenant_access_attempts_total',
    'Number of cross-tenant access attempts',
    ['model', 'result']
)

tenant_data_leaks = Counter(
    'tenant_data_leaks_total',
    'Number of detected tenant data leaks',
    ['model']
)
```

### 告警规则

```yaml
# alerting/tenant_isolation_alerts.yml
groups:
  - name: tenant_isolation
    interval: 30s
    rules:
      - alert: CrossTenantAccessAttempt
        expr: rate(cross_tenant_access_attempts_total{result="blocked"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of cross-tenant access attempts"
          description: "{{ $value }} cross-tenant access attempts per second"
      
      - alert: TenantDataLeak
        expr: increase(tenant_data_leaks_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CRITICAL: Tenant data leak detected"
          description: "Potential tenant data leak in {{ $labels.model }}"
      
      - alert: SlowTenantQuery
        expr: tenant_query_duration_seconds{quantile="0.95"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow tenant queries detected"
          description: "95th percentile query time is {{ $value }}s"
```

## 部署检查清单

### 部署前检查

```bash
#!/bin/bash
# deployment_checks.sh

echo "部署前租户隔离检查..."

CHECKS_PASSED=0
CHECKS_FAILED=0

# 1. 单元测试
if pytest tests/test_tenant_isolation.py; then
    echo "✅ 单元测试通过"
    ((CHECKS_PASSED++))
else
    echo "❌ 单元测试失败"
    ((CHECKS_FAILED++))
fi

# 2. 数据库完整性
if python temp1122/test_remaining_modules.py | grep -q "所有.*模块测试通过"; then
    echo "✅ 数据库完整性检查通过"
    ((CHECKS_PASSED++))
else
    echo "❌ 数据库完整性检查失败"
    ((CHECKS_FAILED++))
fi

# 3. 安全测试
if python temp1122/test_cross_tenant_access.py | grep -q "所有跨租户访问测试通过"; then
    echo "✅ 安全测试通过"
    ((CHECKS_PASSED++))
else
    echo "❌ 安全测试失败"
    ((CHECKS_FAILED++))
fi

# 4. 性能测试
if python temp1122/test_query_performance.py | grep -q "整体性能: 优秀\|整体性能: 良好"; then
    echo "✅ 性能测试通过"
    ((CHECKS_PASSED++))
else
    echo "❌ 性能测试失败"
    ((CHECKS_FAILED++))
fi

echo ""
echo "检查结果: $CHECKS_PASSED 通过, $CHECKS_FAILED 失败"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "✅ 所有检查通过，可以部署"
    exit 0
else
    echo "❌ 有检查失败，不建议部署"
    exit 1
fi
```

## 持续监控

### 日志监控

```python
# 在settings.py中配置日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'tenant_isolation': {
            '()': 'common.logging.TenantIsolationFilter',
        },
    },
    'handlers': {
        'tenant_isolation': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/tenant_isolation.log',
            'filters': ['tenant_isolation'],
        },
    },
    'loggers': {
        'common.viewsets': {
            'handlers': ['tenant_isolation'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-22
**维护者**: DevOps团队
