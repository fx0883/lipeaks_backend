# 代码清理指南

## 1. 临时文件清理

### 需要删除的文件

#### 1.1 空文件
- `temp_models.py` - 空文件，无任何内容

#### 1.2 开发脚本
- `bulk_create_articles.py` - 批量创建文章的开发脚本
- `update_mysql_config.py` - MySQL配置更新脚本
- `verify_timezone.py` - 时区验证脚本

#### 1.3 其他临时文件
- `timezone_setup_summary.md` - 时区设置总结
- `timezone_fix_README.md` - 时区修复说明

### 删除命令
```bash
# 删除临时文件
rm temp_models.py
rm bulk_create_articles.py
rm update_mysql_config.py
rm verify_timezone.py
rm timezone_setup_summary.md
rm timezone_fix_README.md
```

## 2. 代码重复清理

### 2.1 租户过滤逻辑重复

#### 问题
租户过滤逻辑在多个地方重复实现：
- `cms/admin_mixins.py`
- `check_system/admin_mixins.py`

#### 解决方案
创建通用的租户过滤基类：

```python
# common/admin_mixins.py
class BaseTenantFilterMixin:
    """通用租户过滤Mixin"""
    
    def changelist_view(self, request, extra_context=None):
        # 通用实现
        pass
    
    def get_queryset(self, request):
        # 通用实现
        pass

# cms/admin_mixins.py
class CMSAdminMixin(BaseTenantFilterMixin):
    change_list_template = 'admin/cms/change_list.html'

# check_system/admin_mixins.py
class CheckSystemAdminMixin(BaseTenantFilterMixin):
    change_list_template = 'admin/check_system/change_list.html'
```

## 3. 注释和文档完善

### 3.1 模型文档

#### 需要添加文档的模型
- `common/models.py` - BaseModel和APILog
- `tenants/models.py` - Tenant和TenantQuota
- `users/models.py` - User相关模型
- `cms/models.py` - CMS相关模型
- `check_system/models.py` - 打卡系统模型

#### 示例
```python
class BaseModel(models.Model):
    """
    基础模型，提供租户隔离和软删除功能
    
    所有需要租户隔离的模型都应该继承此模型。
    自动提供以下功能：
    - 租户关联
    - 创建/更新时间
    - 软删除
    - 租户过滤管理器
    """
    # ... 字段定义
```

### 3.2 视图文档

#### 需要添加文档的视图
- API视图类
- Admin视图类
- 自定义视图

#### 示例
```python
class ArticleListCreateView(generics.ListCreateAPIView):
    """
    文章列表和创建视图
    
    提供以下功能：
    - GET: 获取文章列表（支持分页和过滤）
    - POST: 创建新文章
    
    权限要求：
    - 需要认证
    - 需要租户访问权限
    """
    # ... 实现
```

## 4. 配置优化

### 4.1 环境变量管理

#### 创建环境变量验证函数
```python
# core/settings.py
def get_required_env(key, default=None):
    """获取必需的环境变量"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def get_env_with_validation(key, validator, default=None):
    """获取并验证环境变量"""
    value = os.getenv(key, default)
    if value is not None:
        try:
            return validator(value)
        except Exception as e:
            raise ValueError(f"Invalid value for environment variable {key}: {e}")
    return value
```

### 4.2 依赖管理

#### 分离开发和生产依赖
```bash
# requirements-dev.txt
-r requirements.txt
pytest==8.3.5
pytest-django==4.11.1
coverage==7.8.0
factory-boy==3.3.3
Faker==37.1.0

# requirements-prod.txt
-r requirements.txt
gunicorn==23.0.0
whitenoise==6.9.0
```

## 5. 测试文件清理

### 5.1 已删除的测试文件
- `cms/test_tenant_display.py` - 已删除
- `cms/test_tenant_filter.py` - 已删除
- `check_system/test_tenant_filter.py` - 已删除

### 5.2 保留的测试文件
- `orders/tests/test_orders.py` - 有实际测试内容
- `rbac/tests/test_rbac_api.py` - 有实际测试内容

## 6. 代码风格统一

### 6.1 导入顺序
```python
# 标准导入顺序
import os
import sys
from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
```

### 6.2 类定义顺序
```python
class MyModel(BaseModel):
    """模型文档字符串"""
    
    # 常量定义
    STATUS_CHOICES = (
        ('active', '激活'),
        ('inactive', '未激活'),
    )
    
    # 字段定义
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Meta类
    class Meta:
        verbose_name = '我的模型'
        verbose_name_plural = '我的模型'
    
    # 方法定义
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 保存逻辑
        super().save(*args, **kwargs)
```

## 7. 文件结构优化

### 7.1 建议的文件结构
```
project/
├── core/                 # 核心配置
├── common/              # 通用功能
├── tenants/             # 租户管理
├── users/               # 用户管理
├── cms/                 # CMS系统
├── check_system/        # 打卡系统
├── customers/           # 客户管理
├── orders/              # 订单管理
├── rbac/                # 权限管理
├── menus/               # 菜单管理
├── charts/              # 图表功能
├── docs_view/           # 文档查看
├── templates/           # 模板文件
├── static/              # 静态文件
├── media/               # 媒体文件
├── logs/                # 日志文件
├── docs/                # 项目文档
├── docs_0816/           # 代码缺陷文档
├── requirements.txt     # 依赖文件
├── manage.py           # Django管理脚本
└── README.md           # 项目说明
```

## 8. 清理检查清单

### 8.1 文件清理
- [ ] 删除空文件
- [ ] 删除临时脚本
- [ ] 删除过时文档
- [ ] 整理文档结构

### 8.2 代码优化
- [ ] 消除代码重复
- [ ] 完善注释文档
- [ ] 统一代码风格
- [ ] 优化导入顺序

### 8.3 配置优化
- [ ] 环境变量验证
- [ ] 依赖文件分离
- [ ] 配置文件整理
- [ ] 测试文件清理

### 8.4 文档完善
- [ ] 模型文档
- [ ] 视图文档
- [ ] API文档
- [ ] 部署文档

## 总结

通过以上清理步骤，可以显著提高代码的可读性、可维护性和一致性。建议按照优先级逐步进行清理，确保不影响现有功能。
