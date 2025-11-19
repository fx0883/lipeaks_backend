# 图片URL标准化功能修改总结

## 修改日期
2025-11-19

## 问题描述

CMS模块（Article和Category）以及Users模块（User和Member）的图片字段（`cover_image`、`cover_image_small`、`avatar`）在保存时会错误地包含domain，导致数据库中保存了完整URL（如`http://localhost:8000/media/uploads/3/xxx.jpg`）而不是相对路径。

## 解决方案

### 核心设计原则

1. **上传接口**：返回不带前缀斜杠的相对路径（如`media/uploads/3/xxx.jpg`）
2. **创建/更新接口**：自动标准化图片字段
   - 如果传入当前服务器的完整URL → 转换为相对路径
   - 如果传入外部CDN的URL → 保持不变
   - 如果传入相对路径 → 去除前缀斜杠
3. **GET接口**：为相对路径添加当前服务器domain，完整URL直接返回

## 🔄 追加修改（2025-11-19 22:36）

根据用户反馈，补充了GET接口的domain添加逻辑：

1. **cms/serializers.py - CategorySerializer.to_representation()**
   - 添加了 `cover_image` 字段的domain处理
   - 现在GET分类列表/详情时会正确返回完整URL

2. **users/serializers.py - UserSerializer.get_avatar()**
   - 修改为使用统一的 `add_domain_to_image_url` 函数
   - 保持与其他序列化器一致的处理逻辑

## 修改文件清单

### 1. 新建文件

#### `common/mixins.py`
创建`ImageFieldNormalizerMixin`，用于自动标准化图片字段。

```python
class ImageFieldNormalizerMixin:
    """自动标准化图片字段的Mixin"""
    image_fields = []
    
    def validate(self, data):
        data = super().validate(data)
        request = self.context.get('request')
        
        if request:
            for field_name in self.image_fields:
                if field_name in data and data[field_name]:
                    data[field_name] = normalize_image_path(
                        data[field_name], 
                        request
                    )
        return data
```

### 2. 修改的工具函数

#### `common/utils/image_url.py`

**新增函数**：
- `normalize_image_path(url, request)` - 将URL标准化为相对路径

**优化函数**：
- `add_domain_to_image_url(request, image_url)` - 为相对路径添加domain

**处理逻辑**：

```python
# normalize_image_path 处理逻辑
1. 空值 → 返回空值
2. 完整URL（http/https）：
   - 解析domain
   - 如果domain匹配当前服务器 → 提取相对路径（去掉前缀斜杠）
   - 如果domain不匹配 → 保持完整URL（外部CDN）
3. 相对路径 → 去除前缀斜杠

# add_domain_to_image_url 处理逻辑
1. 空值 → 返回空值
2. 完整URL → 直接返回
3. 相对路径 → 添加当前服务器domain
```

### 3. 上传接口修改

#### `common/views.py`

修改3处上传接口的返回值：

**修改点1**：FileUploadView.post() - 第670行
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}uploads/{upload_dir_name}/{unique_filename}"

# 修改后  
relative_url = f"media/uploads/{upload_dir_name}/{unique_filename}"
```

**修改点2**：ImageUploadWithThumbnailView.post() - 第886行（缩略图）
```python
# 修改前
thumbnail_url = f"{settings.MEDIA_URL}uploads/{upload_dir_name}/{thumbnail_filename}"

# 修改后
thumbnail_url = f"media/uploads/{upload_dir_name}/{thumbnail_filename}"
```

**修改点3**：ImageUploadWithThumbnailView.post() - 第903行（原图）
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}uploads/{upload_dir_name}/{unique_filename}"

# 修改后
relative_url = f"media/uploads/{upload_dir_name}/{unique_filename}"
```

### 4. CMS序列化器修改

#### `cms/serializers.py`

**导入Mixin**：
```python
from common.mixins import ImageFieldNormalizerMixin
```

**修改CategorySerializer** - 第23行：
```python
class CategorySerializer(ImageFieldNormalizerMixin, TranslatableModelSerializer):
    """分类序列化器（支持多语言）"""
    image_fields = ['cover_image']  # 需要标准化的图片字段
```

**修改ArticleCreateUpdateSerializer** - 第481行：
```python
class ArticleCreateUpdateSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
    """文章创建和更新序列化器"""
    image_fields = ['cover_image', 'cover_image_small']  # 需要标准化的图片字段
```

### 5. Users头像上传接口修改

#### `users/views/admin_user_views.py`

**修改点1** - 第843行：
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"

# 修改后
relative_url = f"media/avatars/{unique_filename}"
```

**修改点2** - 第992行：
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"

# 修改后
relative_url = f"media/avatars/{unique_filename}"
```

#### `users/views/member_views.py`

**修改点1** - 第959行：
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"

# 修改后
relative_url = f"media/avatars/{unique_filename}"
```

**修改点2** - 第1125行：
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"

# 修改后
relative_url = f"media/avatars/{unique_filename}"
```

#### `users/views/member_admin_views.py`

**修改点** - 第621行：
```python
# 修改前
relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"

# 修改后
relative_url = f"media/avatars/{unique_filename}"
```

### 6. Users序列化器修改

#### `users/serializers.py`

**导入Mixin**：
```python
from common.mixins import ImageFieldNormalizerMixin
```

**修改UserUpdateSerializer** - 第169行：
```python
class UserUpdateSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
    """用户更新序列化器"""
    image_fields = ['avatar']  # 需要标准化的图片字段
```

**修改SubAccountCreateSerializer** - 第682行：
```python
class SubAccountCreateSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
    """子账号创建序列化器"""
    image_fields = ['avatar']  # 需要标准化的图片字段
```

## 数据兼容性

代码完全兼容现有数据库中的各种格式：
- ✅ 新格式：`media/uploads/3/xxx.jpg`
- ✅ 旧格式：`/media/uploads/3/xxx.jpg`（带前缀斜杠）
- ✅ 完整URL：`http://localhost:8000/media/uploads/3/xxx.jpg`
- ✅ 外部URL：`https://cdn.example.com/xxx.jpg`

`add_domain_to_image_url`函数会自动处理所有这些格式。

## 测试场景

### 场景1：上传图片
**操作**：调用`POST /api/v1/common/upload-file/`上传图片  
**期望结果**：返回`media/uploads/3/xxx.jpg`（不带前缀斜杠）

### 场景2：创建文章/分类（传入上传返回的URL）
**操作**：创建文章，`cover_image`字段传入`media/uploads/3/xxx.jpg`  
**期望结果**：
- 数据库保存：`media/uploads/3/xxx.jpg`
- GET返回：`http://localhost:8000/media/uploads/3/xxx.jpg`

### 场景3：更新文章/分类（传入完整URL-当前服务器）
**操作**：更新文章，`cover_image`字段传入`http://localhost:8000/media/uploads/3/xxx.jpg`  
**期望结果**：
- 数据库保存：`media/uploads/3/xxx.jpg`（自动转换）
- GET返回：`http://localhost:8000/media/uploads/3/xxx.jpg`

### 场景4：更新文章/分类（传入外部CDN URL）
**操作**：更新文章，`cover_image`字段传入`https://cdn.example.com/xxx.jpg`  
**期望结果**：
- 数据库保存：`https://cdn.example.com/xxx.jpg`（保持不变）
- GET返回：`https://cdn.example.com/xxx.jpg`

### 场景5：GET旧数据
**操作**：GET数据库中带前缀斜杠的旧数据  
**期望结果**：自动添加domain，返回`http://localhost:8000/media/uploads/3/xxx.jpg`

## 优势

1. **统一管理**：所有图片字段的标准化逻辑集中在`ImageFieldNormalizerMixin`中
2. **易于扩展**：新增模型只需继承Mixin并设置`image_fields`
3. **向后兼容**：完全兼容现有数据，无需数据迁移
4. **支持CDN**：可以保存外部CDN的完整URL
5. **代码简洁**：避免重复的标准化代码

## 影响的模型字段

- ✅ `Article.cover_image`
- ✅ `Article.cover_image_small`
- ✅ `Category.cover_image`
- ✅ `User.avatar`
- ✅ `Member.avatar`

## 注意事项

1. 所有修改均向后兼容，不会破坏现有功能
2. `add_domain_to_image_url`函数已优化，能正确处理各种格式
3. 序列化器的Mixin需要放在继承链的第一个位置
4. normalize函数依赖request对象来判断当前domain

## 下一步建议

1. 进行完整的集成测试，验证所有场景
2. 监控生产环境日志，确认没有异常
3. 考虑添加单元测试覆盖工具函数
4. 文档化前端对接规范
