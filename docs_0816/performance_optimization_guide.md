# 性能优化指南

## 1. 数据库查询优化

### 添加数据库索引
```python
# common/models.py
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
```

### 使用select_related
```python
# 在视图中使用
def get_queryset(self):
    return super().get_queryset().select_related('tenant', 'user')
```

### 数据库连接池
```python
# settings.py
DATABASES = {
    'default': {
        # ... 其他配置
        'CONN_MAX_AGE': 600,  # 10分钟连接池
    }
}
```

## 2. 日志配置优化

### 使用轮转日志
```python
# settings.py
'handlers': {
    'file': {
        'class': 'logging.handlers.RotatingFileHandler',
        'maxBytes': 10 * 1024 * 1024,  # 10MB
        'backupCount': 5,  # 保留5个备份文件
    },
}
```

## 3. 缓存配置

### 添加Redis缓存
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 4. 静态文件优化

### 添加WhiteNoise
```python
# settings.py
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... 其他中间件
]
```

## 5. 批量操作优化

### 使用bulk_create
```python
# 批量创建
articles = [Article(**data) for data in articles_data]
Article.objects.bulk_create(articles, batch_size=100)
```

## 性能优化检查清单

- [ ] 数据库索引已优化
- [ ] 使用select_related和prefetch_related
- [ ] 数据库连接池已配置
- [ ] 日志轮转已配置
- [ ] Redis缓存已配置
- [ ] 静态文件已压缩
- [ ] 批量操作已优化
