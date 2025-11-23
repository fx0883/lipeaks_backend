# 租户继承重构 - 快速开始指南

## 当前状态

✅ **已完成的工作**:
- 创建了`TranslatableTenantManager` (`common/managers.py`)
- 创建了`TenantApiView` (`common/views.py`)
- 重构了14个CMS models和1个Common model继承`BaseModel`
- 生成了migrations文件

⚠️ **当前问题**:
- Category模型的django-parler兼容性问题导致migrations无法执行
- 27个ViewSets等待修改

## 立即执行的解决方案

### 步骤1: 手动执行SQL（绕过Category问题）

```bash
# 1. 进入MySQL
mysql -u your_username -p your_database

# 2. 添加is_deleted字段到Category表
ALTER TABLE cms_category 
ADD COLUMN is_deleted TINYINT(1) NOT NULL DEFAULT 0;

# 3. 创建索引
CREATE INDEX cms_category_is_deleted_idx ON cms_category(is_deleted);

# 4. 退出MySQL
exit;
```

### 步骤2: 修改Migration文件

编辑 `cms/migrations/0011_remove_articlestatistics_last_updated_at_and_more.py`，找到Category相关的操作并注释掉：

```python
operations = [
    # ... 其他操作保持不变
    
    # 注释掉这一行（Category的is_deleted已通过SQL添加）
    # migrations.AddField(
    #     model_name='category',
    #     name='is_deleted',
    #     field=models.BooleanField(db_index=True, default=False, verbose_name='是否删除'),
    # ),
    
    # ... 其他操作保持不变
]
```

### 步骤3: 执行Migrations

```bash
# 执行CMS migrations
python3 manage.py migrate cms

# 执行Common migrations  
python3 manage.py migrate common

# 验证
python3 manage.py showmigrations cms common
```

### 步骤4: 验证数据库结构

```sql
-- 检查Category表结构
DESCRIBE cms_category;

-- 应该能看到is_deleted列
```

## 后续工作清单

### 优先级1: 修改ViewSets（高）

需要修改以下ViewSets继承`TenantModelViewSet`：

```python
# 修改前
class ApplicationViewSet(viewsets.ModelViewSet):
    pass

# 修改后
from common.viewsets import TenantModelViewSet

class ApplicationViewSet(TenantModelViewSet):
    pass
```

**待修改的ViewSets清单**（共27个）：

#### Applications
- [ ] `applications/views.py` - ApplicationViewSet

#### Orders
- [ ] `orders/views/order_views.py` - OrderViewSet

#### Menus
- [ ] `menus/views/menu_views.py` - MenuViewSet

#### Points
- [ ] `points/api/views.py` - TenantUserProfileViewSet
- [ ] `points/api/views.py` - TenantUserTypeTagViewSet

#### Feedbacks
- [ ] `feedbacks/views/feedback_views.py` - FeedbackViewSet
- [ ] `feedbacks/complete_system.py` - FeedbackReplyViewSet
- [ ] `feedbacks/complete_system.py` - FeedbackAttachmentViewSet
- [ ] `feedbacks/complete_system.py` - EmailTemplateViewSet

#### Check_system
- [ ] `check_system/views.py` - TaskCategoryViewSet
- [ ] `check_system/views.py` - TaskViewSet
- [ ] `check_system/views.py` - CheckRecordViewSet
- [ ] `check_system/views.py` - TaskTemplateViewSet

#### Licenses
- [ ] `licenses/views/assignment_views.py` - LicenseAssignmentViewSet
- [ ] `licenses/views/admin_views.py` - ApplicationViewSet
- [ ] `licenses/views/admin_views.py` - LicensePlanViewSet
- [ ] `licenses/views/admin_views.py` - LicenseViewSet
- [ ] `licenses/views/admin_views.py` - TenantLicenseQuotaViewSet

#### Interactions
- [ ] `interactions/views.py` - ArticleFavoriteViewSet
- [ ] `interactions/views.py` - MemberLikeViewSet
- [ ] `interactions/views.py` - MemberFollowViewSet
- [ ] `interactions/views.py` - ArticleLikeViewSet

#### Customers
- [ ] `customers/views/customer_views.py` - CustomerViewSet
- [ ] `customers/views/customer_member_views.py` - CustomerMemberRelationViewSet
- [ ] `customers/views/customer_tenant_views.py` - CustomerTenantRelationViewSet

**修改模板**：
```python
# 1. 添加导入
from common.viewsets import TenantModelViewSet

# 2. 修改继承
# 修改前：
class SomeViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all()
    
    def get_queryset(self):
        # 手动租户过滤代码
        tenant = get_tenant_from_request(self.request)
        return Model.objects.filter(tenant=tenant)
    
    def perform_create(self, serializer):
        # 手动设置租户
        tenant = get_tenant_from_request(self.request)
        serializer.save(tenant=tenant)

# 修改后：
class SomeViewSet(TenantModelViewSet):
    queryset = Model.objects.all()
    # TenantModelViewSet自动处理租户过滤和设置
    # 删除手动的get_queryset和perform_create
```

### 优先级2: 测试验证（高）

#### 测试CMS API

```bash
# 测试Article列表（需要租户header）
curl -X GET "http://localhost:8000/api/cms/articles/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 测试创建Article
curl -X POST "http://localhost:8000/api/cms/articles/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "content": "测试内容",
    "status": "draft"
  }'

# 测试Category（多语言）
curl -X GET "http://localhost:8000/api/cms/categories/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 测试租户隔离

```bash
# 以租户1的身份创建数据
curl -X POST "http://localhost:8000/api/cms/articles/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN" \
  -d '{"title": "Tenant 1 Article"}'

# 以租户2的身份查询（不应该看到租户1的数据）
curl -X GET "http://localhost:8000/api/cms/articles/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN"
```

#### 测试软删除

```python
# Python测试脚本
from cms.models import Article

# 软删除
article = Article.objects.get(id=1)
article.soft_delete()

# 验证软删除
print(article.is_deleted)  # True

# 默认查询不包含已删除
articles = Article.objects.all()  # 不包含is_deleted=True的记录

# 查询所有（包括已删除）
all_articles = Article.original_objects.all()
```

### 优先级3: 文档更新（中）

- [ ] 更新API文档
- [ ] 更新开发者指南
- [ ] 添加租户隔离最佳实践

## 常见问题

### Q1: TenantModelViewSet如何工作？

**A**: `TenantModelViewSet`自动：
1. 从header (`X-Tenant-ID`) 或query参数 (`?tenant_id=1`) 获取租户ID
2. 在`get_queryset()`中自动过滤租户数据
3. 在`perform_create()`中自动设置租户ID
4. 在`perform_update()`和`perform_destroy()`中验证租户所有权

### Q2: TenantApiView如何使用？

**A**: 
```python
from common.views import TenantApiView

class MyAPIView(TenantApiView):
    def get(self, request):
        # 获取租户ID
        tenant_id = self.get_tenant_id()
        
        # 查询该租户的数据
        data = MyModel.objects.filter(tenant_id=tenant_id)
        
        return Response(...)
    
    def post(self, request):
        tenant_id = self.get_tenant_id()
        
        # 创建时设置租户
        obj = MyModel.objects.create(
            tenant_id=tenant_id,
            **request.data
        )
        
        # 或验证对象所属租户
        self.verify_tenant_access(obj)
        
        return Response(...)
```

### Q3: Category为什么特殊？

**A**: Category使用django-parler的`TranslatableModel`支持多语言，这与`BaseModel`的多重继承存在冲突。当前Category通过手动添加字段实现了相同功能。

### Q4: 如何回滚？

**A**:
```bash
# 回滚migrations
python3 manage.py migrate cms 0010  # 回滚到上一个版本
python3 manage.py migrate common 0001

# 删除已添加的列（如果需要）
ALTER TABLE cms_category DROP COLUMN is_deleted;
```

## 验证清单

完成后检查：

- [ ] Migrations执行成功
- [ ] `cms_category`表有`is_deleted`列
- [ ] CMS API正常工作
- [ ] 租户隔离功能正常
- [ ] 软删除功能正常
- [ ] 多语言功能正常（Category）
- [ ] ViewSets继承修改完成
- [ ] API测试通过

## 下一步

完成上述工作后：
1. 进行全面的集成测试
2. 更新API文档
3. 通知团队成员新的架构变更
4. 监控生产环境（如果部署）

## 需要帮助？

查看详细文档：
- `temp1122/TENANT_REFACTOR_SUMMARY.md` - 完整总结报告
- `temp1122/CATEGORY_MIGRATION_ISSUE.md` - Category问题详解
- `common/models.py` - BaseModel定义
- `common/viewsets.py` - TenantModelViewSet定义
- `common/views.py` - TenantApiView定义
