# CMS租户过滤器使用指南

## 概述

CMS租户过滤器是一个为多租户CMS系统设计的直观过滤工具，允许管理员和超级管理员在不同租户之间切换查看内容。

## 功能特性

### 1. 租户选择下拉框
- 位于CMS页面顶部，搜索栏上方
- 显示所有可用的租户（超级管理员）或当前用户关联的租户
- 包含"所有租户"选项，用于查看全局数据

### 2. 实时过滤
- 选择租户后点击"应用过滤"按钮
- 页面自动刷新并显示选定租户的内容
- 保持其他搜索和过滤条件

### 3. 状态显示
- 显示当前选中的租户名称
- 在URL中保持租户ID参数
- 支持浏览器前进/后退操作

## 使用方法

### 超级管理员
1. 访问任何CMS管理页面（如分类管理、文章管理等）
2. 在页面顶部找到"选择租户"下拉框
3. 选择要查看的租户
4. 点击"应用过滤"按钮
5. 页面将显示选定租户的内容

### 普通用户
- 只能看到自己关联的租户
- 租户选择器显示为只读状态
- 自动过滤显示当前租户的内容

## 支持的页面

目前支持租户过滤的页面包括：

### CMS系统
- **分类管理** (`/admin/cms/category/`)
- **文章管理** (`/admin/cms/article/`)
- **标签管理** (`/admin/cms/tag/`)
- **评论管理** (`/admin/cms/comment/`)

### 打卡系统 (Check_System)
- **打卡类型管理** (`/admin/check_system/taskcategory/`)
- **打卡任务管理** (`/admin/check_system/task/`)
- **任务模板管理** (`/admin/check_system/tasktemplate/`)
- **打卡记录管理** (`/admin/check_system/checkrecord/`)

## 技术实现

### 架构设计
- 使用Django Admin自定义模板
- 通过Mixin类提供通用功能
- 支持URL参数传递租户ID

### 核心组件
1. **自定义模板**: 
   - CMS: `templates/admin/cms/change_list.html`
   - Check_System: `templates/admin/check_system/change_list.html`
2. **Mixin类**: 
   - CMS: `cms.admin_mixins.CMSAdminMixin`
   - Check_System: `check_system.admin_mixins.CheckSystemAdminMixin`
3. **Admin配置**: 各模型的Admin类继承对应的Mixin

### 权限控制
- 超级管理员：可以查看和切换所有租户
- 普通用户：只能查看自己关联的租户
- 租户隔离：数据完全按租户分离

## 配置说明

### 添加新页面支持
要为新的页面添加租户过滤支持：

#### CMS系统
1. 在对应的Admin类中继承`CMSAdminMixin`：
```python
@admin.register(YourModel)
class YourModelAdmin(CMSAdminMixin, admin.ModelAdmin):
    # 配置...
```

#### Check_System
1. 在对应的Admin类中继承`CheckSystemAdminMixin`：
```python
@admin.register(YourModel)
class YourModelAdmin(CheckSystemAdminMixin, admin.ModelAdmin):
    # 配置...
```

#### 通用要求
2. 确保模型有`tenant`字段

3. 在`list_filter`中包含`tenant`字段

### 自定义过滤逻辑
可以通过重写`get_queryset`方法来自定义过滤逻辑：

```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    # 自定义过滤逻辑
    return qs
```

## 故障排除

### 常见问题

1. **租户选择器不显示**
   - 检查用户权限
   - 确认Admin类继承了`CMSAdminMixin`
   - 验证模板文件路径

2. **过滤不生效**
   - 检查URL参数是否正确
   - 确认模型有`tenant`字段
   - 验证数据库中的租户数据
   - 确认Admin类继承了正确的Mixin

3. **权限错误**
   - 检查用户是否为超级管理员
   - 确认用户关联了正确的租户
   - 验证租户状态是否正常

4. **租户名称显示不全**
   - 检查浏览器控制台是否有错误信息
   - 验证租户名称在数据库中的完整性
   - 确认CSS样式没有限制文本显示
   - 使用测试脚本验证租户数据

### 调试方法

1. 检查浏览器控制台错误
2. 查看Django日志
3. 验证URL参数格式
4. 测试数据库查询
5. 运行租户名称测试脚本：
   - 使用Django内置的测试框架进行功能测试
6. 检查租户数据完整性
7. 验证CSS样式和字体设置
8. 确认Admin Mixin正确应用

## 最佳实践

### 性能优化
- 使用`select_related`减少数据库查询
- 合理设置分页大小
- 避免在过滤器中执行复杂查询

### 用户体验
- 保持过滤器的响应速度
- 提供清晰的视觉反馈
- 支持键盘导航

### 安全性
- 严格验证用户权限
- 防止跨租户数据泄露
- 记录所有过滤操作

## 更新日志

### v1.0.0 (2025-01-14)
- 初始版本发布
- 支持基本的租户过滤功能
- 包含分类、文章、标签、评论管理页面

### v1.1.0 (2025-01-14)
- 新增Check_System租户过滤支持
- 支持打卡类型、任务、模板、记录管理页面
- 统一租户过滤UI和功能

### 计划功能
- 支持更多CMS页面
- 添加租户切换快捷键
- 支持批量操作时的租户过滤
- 添加租户统计信息显示

## 技术支持

如有问题或建议，请联系开发团队或查看相关文档。
