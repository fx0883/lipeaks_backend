# 普全订单管理系统实现计划

## 1. 初始化阶段

- [x] 创建 `orders` 应用
  ```bash
  python manage.py startapp orders
  ```
- [x] 将 `orders` 应用添加到 `core/settings.py` 的 `INSTALLED_APPS` 中
  ```python
  INSTALLED_APPS = [
      # ...现有应用...
      'orders',  # 新增订单应用
  ]
  ```
- [x] 创建应用目录结构
  ```
  orders/
  ├── __init__.py
  ├── admin.py
  ├── apps.py
  ├── migrations/
  ├── models.py
  ├── serializers.py
  ├── urls.py
  ├── views/
  │   ├── __init__.py
  │   ├── order_views.py
  │   └── order_history_views.py
  └── tests/
      ├── __init__.py
      └── test_orders.py
  ```

## 2. 模型实现

- [x] 在 `models.py` 中实现 `Order` 模型
  - [x] 继承 `BaseModel` 以获得租户隔离和软删除功能
  - [x] 实现订单基本信息字段
  - [x] 实现服务和语种信息字段
  - [x] 实现费用相关信息字段
  - [x] 实现支付信息字段
  - [x] 实现发票和合同信息字段（JSON格式）
  - [x] 实现其他辅助信息字段
  - [x] 添加自动生成订单编号的逻辑
  - [x] 实现毛利和毛利率计算方法

- [x] 在 `models.py` 中实现 `OrderHistory` 模型
  - [x] 实现订单历史记录字段
  - [x] 实现版本号自增逻辑
  - [x] 实现变更详情和快照字段（JSON格式）

- [x] 创建并应用数据库迁移
  ```bash
  python manage.py makemigrations orders
  python manage.py migrate
  ```

## 3. 序列化器实现

- [x] 在 `serializers.py` 中实现序列化器
  - [x] 实现 `OrderSerializer` 基本序列化器
  - [x] 实现 `OrderCreateSerializer` 创建订单序列化器
  - [x] 实现 `OrderUpdateSerializer` 更新订单序列化器
  - [x] 实现 `OrderHistorySerializer` 订单历史序列化器
  - [x] 实现 `OrderListSerializer` 订单列表序列化器（简化版）
  - [x] 实现 `OrderDetailSerializer` 订单详情序列化器（包含关联数据）

## 4. 视图实现

- [ ] 在 `views/order_views.py` 中实现订单视图
  - [ ] 实现 `OrderViewSet` 视图集
    - [ ] 实现 `list` 方法（带筛选、排序和分页）
    - [ ] 实现 `retrieve` 方法（获取订单详情）
    - [ ] 实现 `create` 方法（创建订单并记录历史）
    - [ ] 实现 `update` 方法（更新订单并记录变更）
    - [ ] 实现 `destroy` 方法（软删除订单）
    - [ ] 实现 `export` 自定义方法（导出订单数据）
    - [ ] 实现 `statistics` 自定义方法（获取统计数据）

- [ ] 在 `views/order_history_views.py` 中实现订单历史视图
  - [ ] 实现 `OrderHistoryViewSet` 视图集
    - [ ] 实现 `list` 方法（获取订单的历史版本列表）
    - [ ] 实现 `retrieve` 方法（获取特定版本详情）
    - [ ] 实现 `compare` 自定义方法（比较两个版本）
    - [ ] 实现 `restore` 自定义方法（还原到特定版本）

## 5. URL配置

- [ ] 在 `urls.py` 中配置URL路由
  ```python
  from django.urls import path, include
  from rest_framework.routers import DefaultRouter
  from orders.views.order_views import OrderViewSet
  from orders.views.order_history_views import OrderHistoryViewSet
  
  app_name = 'orders'
  
  router = DefaultRouter()
  router.register(r'', OrderViewSet, basename='order')
  router.register(r'(?P<order_id>\d+)/history', OrderHistoryViewSet, basename='order-history')
  
  urlpatterns = [
      path('', include(router.urls)),
  ]
  ```

- [ ] 在项目主 `core/urls.py` 中添加应用路由
  ```python
  # 在 api/v1/ 路径下添加
  path('orders/', include('orders.urls', namespace='orders')),
  ```

## 6. 权限控制

- [ ] 实现订单相关权限类
  - [ ] 创建 `permissions.py` 文件
  - [ ] 实现 `IsOrderOwnerOrAdmin` 权限类
  - [ ] 实现 `CanViewOrderHistory` 权限类

- [ ] 在视图中应用权限控制
  - [ ] 在 `OrderViewSet` 中设置权限类
  - [ ] 在 `OrderHistoryViewSet` 中设置权限类

## 7. 管理员界面

- [ ] 在 `admin.py` 中注册模型到管理员界面
  ```python
  from django.contrib import admin
  from orders.models import Order, OrderHistory
  
  @admin.register(Order)
  class OrderAdmin(admin.ModelAdmin):
      list_display = ('order_number', 'customer', 'service_type', 'status', 'total_amount', 'payment_status', 'created_at')
      list_filter = ('status', 'payment_status', 'service_type')
      search_fields = ('order_number', 'customer__name', 'translator_name')
      readonly_fields = ('order_number', 'created_at', 'updated_at')
      
  @admin.register(OrderHistory)
  class OrderHistoryAdmin(admin.ModelAdmin):
      list_display = ('order', 'version', 'modified_by', 'modified_at')
      list_filter = ('modified_at',)
      search_fields = ('order__order_number',)
      readonly_fields = ('order', 'version', 'modified_by', 'modified_at', 'change_details', 'snapshot')
  ```

## 8. 单元测试

- [ ] 在 `tests/test_orders.py` 中实现单元测试
  - [ ] 测试 `Order` 模型
  - [ ] 测试 `OrderHistory` 模型
  - [ ] 测试订单创建 API
  - [ ] 测试订单查询 API
  - [ ] 测试订单更新 API
  - [ ] 测试订单删除 API
  - [ ] 测试订单历史 API

## 9. 信号处理

- [ ] 创建 `signals.py` 文件
  - [ ] 实现订单更新后自动创建历史记录的信号处理器
  - [ ] 实现订单创建后的初始历史记录

- [ ] 在 `apps.py` 中注册信号
  ```python
  class OrdersConfig(AppConfig):
      default_auto_field = 'django.db.models.BigAutoField'
      name = 'orders'
      
      def ready(self):
          import orders.signals
  ```

## 10. 文档和前端集成

- [ ] 更新 API 文档
  - [ ] 为订单 API 添加 Swagger/OpenAPI 文档
  - [ ] 编写 API 使用指南

- [ ] 前端集成指南
  - [ ] 创建订单表单设计指南
  - [ ] 订单列表和详情页面设计指南
  - [ ] 订单历史比较界面设计指南

## 11. 部署和测试

- [ ] 在开发环境中全面测试
  - [ ] 功能测试
  - [ ] 性能测试
  - [ ] 安全测试

- [ ] 准备部署
  - [ ] 检查数据库索引优化
  - [ ] 确保权限控制正确
  - [ ] 验证与其他模块的集成

## 12. 后续优化

- [ ] 实现订单提醒功能
  - [ ] 项目开始提醒
  - [ ] 项目截止提醒
  - [ ] 提醒管理

- [ ] 实现订单导入导出
  - [ ] Excel 格式导入
  - [ ] Excel/PDF/CSV 格式导出

- [ ] 实现订单统计分析
  - [ ] 销售额统计
  - [ ] 毛利率分析
  - [ ] 客户订单分析 