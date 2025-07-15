# 水产养殖系统数据库模型

本文档描述了水产养殖系统的数据库表结构设计，作为系统开发的基础模型。系统已集成到多租户架构中，通过租户ID字段实现数据隔离。

## 多租户架构实现

系统使用 Django 框架实现了多租户架构，主要通过 `tenants` 应用模块来管理租户信息、配额和企业资料。多租户架构有以下几个核心组件：

### 核心模型

1. **租户模型 (Tenant)**：存储租户的基本信息，如名称、状态和联系方式。
2. **租户配额模型 (TenantQuota)**：控制租户可使用的资源上限，如用户数量、存储空间等。
3. **租户企业信息模型 (TenantBusinessInfo)**：记录租户的企业资质信息，如公司名称、营业执照等。

### 主要功能

1. **租户管理**：创建、查询、更新和删除(软删除)租户。
2. **配额控制**：设置和监控租户资源使用情况。
3. **用户隔离**：确保用户只能访问其所属租户的数据。
4. **状态管理**：支持激活、暂停租户服务。

### 数据隔离实现

系统采用共享数据库、共享架构(Shared Database, Shared Schema)的多租户模式，通过以下机制实现数据隔离：

1. 所有业务表包含 `tenant_id` 字段关联到租户表
2. API 请求时自动注入当前租户上下文
3. 数据查询自动添加租户过滤条件
4. 权限系统支持租户级别的权限控制

## 数据库表关系线框图

### 多租户架构关系图

```
+---------------+       +-------------------+       +------------------------+
|               |       |                   |       |                        |
|   Tenant      |<----->| TenantQuota      |       | TenantBusinessInfo     |
| (租户)        |       | (租户配额)        |       | (租户企业信息)          |
|               |       |                   |       |                        |
+-------+-------+       +-------------------+       +------------------------+
        |
        | 1:n (所有业务表)
        v
+-------+-------+
|               |
| 业务数据表     |
| (tenant_id)   |
|               |
+---------------+
```

### 基础数据关系图

```
+---------------+       +----------------+       +---------------------+
|               |       |                |       |                     |
|    Tenant     |<------| Base           |<------| Pond                |
| (租户)        |       | (基地)         |       | (池塘)              |
|               |       |                |       |                     |
+---------------+       +----------------+       +--------+------------+
                                                          |
                                                          |
                                                          v
+-----------------+     +----------------+     +----------+-----------+
|                 |     |                |     |                      |
| Species         |<----| Production     |<----| 各类记录表           |
| (养殖品种)      |     | Batch (批次)   |     | (水质/投喂/生长等)   |
|                 |     |                |     |                      |
+-----------------+     +----------------+     +----------------------+
```

### 物资管理关系图

```
+---------------+       +-----------------+       +-----------------+
|               |       |                 |       |                 |
|    Tenant     |<------| Feeds           |<------| FeedingRecords  |
| (租户)        |       | (饲料)          |       | (投喂记录)      |
|               |       |                 |       |                 |
+-------+-------+       +-----------------+       +-----------------+
        |
        |
        |               +-----------------+       +-----------------+
        |               |                 |       |                 |
        +-------------->| Medicines       |<------| DiseasePrevention|
                        | (药品)          |       | (病害防治)      |
                        |                 |       |                 |
                        +-----------------+       +-----------------+
                        
                        +-----------------+
                        |                 |
                        | Equipment       |
                        | (设备)          |
                        |                 |
                        +-----------------+
```

### 权限管理关系图

```
+---------------+       +-----------------+       +-----------------+
|               |       |                 |       |                 |
|    Tenant     |<------| Role            |<------| Permission      |
| (租户)        |       | (角色)          |        | (权限)           |
|               |       |                 |       |                 |
+-------+-------+       +--------+--------+       +-----------------+
        |                        |
        |                        |
        v                        v
+-------+-------+       +--------+--------+
|               |       |                 |
| User          |<------| UserRole        |
| (用户)        |       | (用户角色)      |
|               |       |                 |
+---------------+       +-----------------+
```

### 销售与批次关系图

```
+---------------+       +-----------------+       +-----------------+
|               |       |                 |       |                 |
| ProductionBatch|<------| SalesRecord    |       | GrowthRecord    |
| (生产批次)    |       | (销售记录)      |       | (生长记录)      |
|               |       |                 |       |                 |
+-------+-------+       +-----------------+       +-----------------+
        |
        |
        v
+-------+-------+
|               |
| WaterQuality  |
| (水质监测)    |
|               |
+---------------+
```

## 租户模块表结构详细设计

除了之前介绍的业务表外，租户模块本身包含以下表结构：

### 1. 租户表 (tenant)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 租户ID | 主键, 自增 |
| name | VARCHAR(100) | 租户名称 | 非空, 唯一 |
| code | VARCHAR(50) | 租户代码 | 唯一, 可空 |
| status | VARCHAR(20) | 状态(active/suspended/deleted) | 非空, 默认'active' |
| contact_name | VARCHAR(50) | 联系人姓名 | 可空 |
| contact_email | VARCHAR(100) | 联系人邮箱 | 可空 |
| contact_phone | VARCHAR(20) | 联系人电话 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 2. 租户配额表 (tenant_quota)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 配额ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空, 一对一 |
| max_users | INTEGER | 最大用户数 | 非空, 默认10 |
| max_admins | INTEGER | 最大管理员数 | 非空, 默认2 |
| max_storage_mb | INTEGER | 最大存储空间(MB) | 非空, 默认1024 |
| max_products | INTEGER | 最大产品数 | 非空, 默认100 |
| current_storage_used_mb | INTEGER | 当前已用存储空间(MB) | 非空, 默认0 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |

### 3. 租户企业信息表 (tenant_business_info)

该表与之前文档中描述的"租户信息附加表"对应，实际系统中已实现，包含以下字段：

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空, 一对一 |
| company_name | VARCHAR(100) | 公司名称 | 非空 |
| legal_representative | VARCHAR(50) | 法定代表人 | 非空 |
| unified_social_credit_code | VARCHAR(50) | 统一社会信用代码 | 非空, 唯一 |
| registration_number | VARCHAR(50) | 注册号 | 可空 |
| company_type | VARCHAR(50) | 公司类型 | 可空 |
| registered_capital | DECIMAL(15,2) | 注册资本 | 可空 |
| registered_capital_currency | VARCHAR(20) | 注册资本币种 | 默认'CNY', 可空 |
| business_scope | TEXT | 经营范围 | 可空 |
| establishment_date | DATE | 成立日期 | 可空 |
| business_term_start | DATE | 营业期限开始日期 | 可空 |
| business_term_end | DATE | 营业期限结束日期 | 可空 |
| registration_authority | VARCHAR(100) | 登记机关 | 可空 |
| approval_date | DATE | 核准日期 | 可空 |
| business_status | VARCHAR(50) | 企业状态 | 可空 |
| registered_address | VARCHAR(255) | 注册地址 | 可空 |
| office_address | VARCHAR(255) | 办公地址 | 可空 |
| contact_person | VARCHAR(50) | 联系人 | 可空 |
| contact_phone | VARCHAR(20) | 联系电话 | 可空 |
| email | VARCHAR(100) | 电子邮箱 | 可空 |
| website | VARCHAR(100) | 公司网站 | 可空 |
| license_image_url | VARCHAR(255) | 营业执照图片URL | 可空 |
| license_image_path | VARCHAR(255) | 营业执照图片存储路径 | 可空 |
| license_issue_date | DATE | 营业执照发证日期 | 可空 |
| license_expiry_date | DATE | 营业执照到期日期 | 可空 |
| verification_status | VARCHAR(20) | 验证状态(pending/verified/rejected/expired) | 非空, 默认'pending' |
| verification_time | TIMESTAMP | 验证时间 | 可空 |
| verification_user_id | BIGINT UNSIGNED | 验证人ID | 外键, 可空, 关联用户表 |
| rejection_reason | TEXT | 拒绝原因 | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |

### 4. 基地信息表 (bases)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 基地ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| name | VARCHAR(100) | 基地名称 | 非空 |
| code | VARCHAR(50) | 基地编码 | 可空, 唯一(租户内) |
| location | VARCHAR(255) | 地理位置 | 非空 |
| area | DECIMAL(10,2) | 面积(亩) | 非空 |
| latitude | DECIMAL(10,6) | 纬度 | 可空 |
| longitude | DECIMAL(10,6) | 经度 | 可空 |
| address | VARCHAR(255) | 详细地址 | 非空 |
| contact_person | VARCHAR(50) | 联系人 | 可空 |
| contact_phone | VARCHAR(20) | 联系电话 | 可空 |
| description | TEXT | 基地描述 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:正常,2:停用) | 非空, 默认1 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 5. 池塘信息表 (ponds)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 池塘ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| base_id | BIGINT UNSIGNED | 基地ID | 外键, 非空, 关联基地表 |
| name | VARCHAR(100) | 池塘名称 | 非空 |
| code | VARCHAR(50) | 池塘编码 | 可空, 唯一(租户内) |
| area | DECIMAL(10,2) | 面积(亩) | 非空 |
| depth | DECIMAL(5,2) | 水深(米) | 非空 |
| volume | DECIMAL(10,2) | 容积(立方米) | 可空 |
| shape | VARCHAR(50) | 形状 | 可空 |
| material | VARCHAR(50) | 材质 | 可空 |
| water_source | VARCHAR(50) | 水源 | 可空 |
| drainage_method | VARCHAR(50) | 排水方式 | 可空 |
| aeration_equipment | VARCHAR(255) | 增氧设备 | 可空 |
| monitoring_equipment | VARCHAR(255) | 监测设备 | 可空 |
| construction_date | DATE | 建造日期 | 可空 |
| last_maintenance_date | DATE | 上次维护日期 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:空闲,2:使用中,3:维护中,4:停用) | 非空, 默认1 |
| description | TEXT | 描述 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 6. 养殖品种表 (species)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 品种ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| name | VARCHAR(100) | 品种名称 | 非空 |
| scientific_name | VARCHAR(100) | 学名 | 可空 |
| code | VARCHAR(50) | 品种编码 | 可空, 唯一(租户内) |
| category | VARCHAR(50) | 类别(鱼类/虾类/蟹类等) | 非空 |
| growth_cycle | INT | 生长周期(天) | 可空 |
| optimal_temperature_min | DECIMAL(5,2) | 最适生长温度下限(°C) | 可空 |
| optimal_temperature_max | DECIMAL(5,2) | 最适生长温度上限(°C) | 可空 |
| optimal_ph_min | DECIMAL(4,2) | 最适pH值下限 | 可空 |
| optimal_ph_max | DECIMAL(4,2) | 最适pH值上限 | 可空 |
| optimal_dissolved_oxygen | DECIMAL(5,2) | 最适溶解氧(mg/L) | 可空 |
| feeding_habits | VARCHAR(255) | 饲养习性 | 可空 |
| common_diseases | TEXT | 常见疾病 | 可空 |
| market_value | DECIMAL(10,2) | 市场价值(元/kg) | 可空 |
| image_url | VARCHAR(255) | 图片URL | 可空 |
| description | TEXT | 描述 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:启用,2:停用) | 非空, 默认1 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 7. 生产批次表 (production_batches)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 批次ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| batch_number | VARCHAR(50) | 批次编号 | 非空, 唯一(租户内) |
| pond_id | BIGINT UNSIGNED | 池塘ID | 外键, 非空, 关联池塘表 |
| species_id | BIGINT UNSIGNED | 品种ID | 外键, 非空, 关联品种表 |
| start_date | DATE | 开始日期 | 非空 |
| expected_end_date | DATE | 预计结束日期 | 可空 |
| actual_end_date | DATE | 实际结束日期 | 可空 |
| initial_quantity | INT | 初始数量 | 非空 |
| initial_quantity_unit | VARCHAR(20) | 初始数量单位(尾/kg) | 非空 |
| initial_weight | DECIMAL(10,2) | 初始重量(kg) | 可空 |
| initial_avg_weight | DECIMAL(10,2) | 初始平均体重(g) | 可空 |
| expected_survival_rate | DECIMAL(5,2) | 预期成活率(%) | 可空 |
| actual_survival_rate | DECIMAL(5,2) | 实际成活率(%) | 可空 |
| expected_yield | DECIMAL(10,2) | 预期产量(kg) | 可空 |
| actual_yield | DECIMAL(10,2) | 实际产量(kg) | 可空 |
| seed_source | VARCHAR(255) | 种苗来源 | 可空 |
| seed_batch_number | VARCHAR(50) | 种苗批次号 | 可空 |
| seed_cost | DECIMAL(10,2) | 种苗成本(元) | 可空 |
| feed_cost | DECIMAL(10,2) | 饲料成本(元) | 可空 |
| medicine_cost | DECIMAL(10,2) | 药品成本(元) | 可空 |
| labor_cost | DECIMAL(10,2) | 人工成本(元) | 可空 |
| other_cost | DECIMAL(10,2) | 其他成本(元) | 可空 |
| total_cost | DECIMAL(10,2) | 总成本(元) | 可空 |
| sales_revenue | DECIMAL(10,2) | 销售收入(元) | 可空 |
| profit | DECIMAL(10,2) | 利润(元) | 可空 |
| status | TINYINT UNSIGNED | 状态(1:进行中,2:已完成,3:已终止) | 非空, 默认1 |
| termination_reason | VARCHAR(255) | 终止原因 | 可空 |
| description | TEXT | 描述 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 8. 水质监测表 (water_quality)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| batch_id | BIGINT UNSIGNED | 批次ID | 外键, 非空, 关联生产批次表 |
| pond_id | BIGINT UNSIGNED | 池塘ID | 外键, 非空, 关联池塘表 |
| test_time | TIMESTAMP | 监测时间 | 非空 |
| temperature | DECIMAL(5,2) | 水温(°C) | 可空 |
| ph | DECIMAL(4,2) | pH值 | 可空 |
| dissolved_oxygen | DECIMAL(5,2) | 溶解氧(mg/L) | 可空 |
| ammonia_nitrogen | DECIMAL(5,2) | 氨氮(mg/L) | 可空 |
| nitrite | DECIMAL(5,2) | 亚硝酸盐(mg/L) | 可空 |
| nitrate | DECIMAL(5,2) | 硝酸盐(mg/L) | 可空 |
| phosphate | DECIMAL(5,2) | 磷酸盐(mg/L) | 可空 |
| turbidity | DECIMAL(5,2) | 浊度(NTU) | 可空 |
| transparency | DECIMAL(5,2) | 透明度(cm) | 可空 |
| salinity | DECIMAL(5,2) | 盐度(‰) | 可空 |
| conductivity | DECIMAL(8,2) | 电导率(μS/cm) | 可空 |
| alkalinity | DECIMAL(5,2) | 碱度(mg/L) | 可空 |
| hardness | DECIMAL(5,2) | 硬度(mg/L) | 可空 |
| hydrogen_sulfide | DECIMAL(5,2) | 硫化氢(mg/L) | 可空 |
| chlorophyll | DECIMAL(5,2) | 叶绿素(μg/L) | 可空 |
| weather | VARCHAR(50) | 天气 | 可空 |
| water_color | VARCHAR(50) | 水色 | 可空 |
| water_smell | VARCHAR(50) | 水味 | 可空 |
| abnormal_phenomena | TEXT | 异常现象 | 可空 |
| treatment_measures | TEXT | 处理措施 | 可空 |
| test_method | VARCHAR(50) | 测试方法(手动/自动) | 非空, 默认'手动' |
| test_equipment | VARCHAR(100) | 测试设备 | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 9. 饲料管理表 (feeds)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 饲料ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| name | VARCHAR(100) | 饲料名称 | 非空 |
| code | VARCHAR(50) | 饲料编码 | 可空, 唯一(租户内) |
| type | VARCHAR(50) | 类型(颗粒饲料/粉状饲料等) | 非空 |
| specification | VARCHAR(100) | 规格 | 可空 |
| manufacturer | VARCHAR(100) | 生产厂家 | 可空 |
| protein_content | DECIMAL(5,2) | 蛋白质含量(%) | 可空 |
| fat_content | DECIMAL(5,2) | 脂肪含量(%) | 可空 |
| fiber_content | DECIMAL(5,2) | 纤维含量(%) | 可空 |
| ash_content | DECIMAL(5,2) | 灰分含量(%) | 可空 |
| moisture_content | DECIMAL(5,2) | 水分含量(%) | 可空 |
| calcium_content | DECIMAL(5,2) | 钙含量(%) | 可空 |
| phosphorus_content | DECIMAL(5,2) | 磷含量(%) | 可空 |
| other_nutrients | TEXT | 其他营养成分 | 可空 |
| applicable_species | VARCHAR(255) | 适用品种 | 可空 |
| applicable_stage | VARCHAR(50) | 适用阶段(苗种期/生长期/育成期等) | 可空 |
| storage_conditions | VARCHAR(255) | 存储条件 | 可空 |
| shelf_life | INT | 保质期(天) | 可空 |
| unit_price | DECIMAL(10,2) | 单价(元/kg) | 可空 |
| current_stock | DECIMAL(10,2) | 当前库存(kg) | 非空, 默认0 |
| stock_warning_threshold | DECIMAL(10,2) | 库存预警阈值(kg) | 可空 |
| description | TEXT | 描述 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:正常,2:停用) | 非空, 默认1 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 10. 投喂记录表 (feeding_records)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| batch_id | BIGINT UNSIGNED | 批次ID | 外键, 非空, 关联生产批次表 |
| pond_id | BIGINT UNSIGNED | 池塘ID | 外键, 非空, 关联池塘表 |
| feed_id | BIGINT UNSIGNED | 饲料ID | 外键, 非空, 关联饲料表 |
| feeding_time | TIMESTAMP | 投喂时间 | 非空 |
| feed_amount | DECIMAL(10,2) | 投喂量(kg) | 非空 |
| feed_cost | DECIMAL(10,2) | 饲料成本(元) | 可空 |
| feeding_method | VARCHAR(50) | 投喂方式(人工/自动) | 非空, 默认'人工' |
| feeding_location | VARCHAR(50) | 投喂位置 | 可空 |
| water_temperature | DECIMAL(5,2) | 水温(°C) | 可空 |
| weather | VARCHAR(50) | 天气 | 可空 |
| feeding_behavior | VARCHAR(255) | 摄食行为 | 可空 |
| feeding_response | VARCHAR(50) | 摄食反应(良好/一般/差) | 可空 |
| leftover_feed | DECIMAL(5,2) | 剩余饲料估计(%) | 可空 |
| abnormal_phenomena | TEXT | 异常现象 | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 11. 生长记录表 (growth_records)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| batch_id | BIGINT UNSIGNED | 批次ID | 外键, 非空, 关联生产批次表 |
| pond_id | BIGINT UNSIGNED | 池塘ID | 外键, 非空, 关联池塘表 |
| sample_time | TIMESTAMP | 采样时间 | 非空 |
| sample_quantity | INT | 采样数量(尾) | 非空 |
| avg_weight | DECIMAL(10,2) | 平均体重(g) | 非空 |
| avg_length | DECIMAL(10,2) | 平均体长(cm) | 可空 |
| max_weight | DECIMAL(10,2) | 最大体重(g) | 可空 |
| min_weight | DECIMAL(10,2) | 最小体重(g) | 可空 |
| weight_variance | DECIMAL(10,2) | 体重方差 | 可空 |
| daily_growth_rate | DECIMAL(5,2) | 日增长率(%) | 可空 |
| feed_conversion_ratio | DECIMAL(5,2) | 饲料转化率 | 可空 |
| estimated_survival_rate | DECIMAL(5,2) | 估计成活率(%) | 可空 |
| estimated_biomass | DECIMAL(10,2) | 估计生物量(kg) | 可空 |
| health_status | VARCHAR(50) | 健康状态(良好/一般/较差) | 可空 |
| abnormal_signs | TEXT | 异常迹象 | 可空 |
| sampling_method | VARCHAR(50) | 采样方法 | 可空 |
| sampling_location | VARCHAR(50) | 采样位置 | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 12. 药品管理表 (medicines)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 药品ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| name | VARCHAR(100) | 药品名称 | 非空 |
| code | VARCHAR(50) | 药品编码 | 可空, 唯一(租户内) |
| type | VARCHAR(50) | 类型(消毒剂/抗生素/驱虫剂等) | 非空 |
| specification | VARCHAR(100) | 规格 | 可空 |
| manufacturer | VARCHAR(100) | 生产厂家 | 可空 |
| approval_number | VARCHAR(50) | 批准文号 | 可空 |
| main_ingredients | TEXT | 主要成分 | 可空 |
| indications | TEXT | 适应症 | 可空 |
| usage_method | TEXT | 使用方法 | 可空 |
| dosage | VARCHAR(255) | 用量 | 可空 |
| contraindications | TEXT | 禁忌症 | 可空 |
| side_effects | TEXT | 副作用 | 可空 |
| storage_conditions | VARCHAR(255) | 存储条件 | 可空 |
| shelf_life | INT | 保质期(天) | 可空 |
| production_date | DATE | 生产日期 | 可空 |
| expiry_date | DATE | 有效期至 | 可空 |
| unit_price | DECIMAL(10,2) | 单价(元) | 可空 |
| unit | VARCHAR(20) | 单位(瓶/盒/袋等) | 非空 |
| current_stock | DECIMAL(10,2) | 当前库存 | 非空, 默认0 |
| stock_warning_threshold | DECIMAL(10,2) | 库存预警阈值 | 可空 |
| description | TEXT | 描述 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:正常,2:停用) | 非空, 默认1 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 13. 病害防治表 (disease_prevention)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| batch_id | BIGINT UNSIGNED | 批次ID | 外键, 非空, 关联生产批次表 |
| pond_id | BIGINT UNSIGNED | 池塘ID | 外键, 非空, 关联池塘表 |
| disease_id | BIGINT UNSIGNED | 疾病ID | 外键, 可空, 关联疾病信息表 |
| medicine_id | BIGINT UNSIGNED | 药品ID | 外键, 可空, 关联药品表 |
| treatment_time | TIMESTAMP | 处理时间 | 非空 |
| disease_name | VARCHAR(100) | 疾病名称 | 非空(当disease_id为空时) |
| symptoms | TEXT | 症状描述 | 可空 |
| diagnosis | TEXT | 诊断结果 | 可空 |
| treatment_method | VARCHAR(255) | 处理方法 | 非空 |
| medicine_name | VARCHAR(100) | 药品名称 | 可空(当medicine_id为空时) |
| dosage | VARCHAR(100) | 用药剂量 | 可空 |
| usage | TEXT | 使用方法 | 可空 |
| treatment_result | VARCHAR(50) | 处理结果(有效/部分有效/无效) | 可空 |
| mortality | INT | 死亡数量 | 可空 |
| mortality_unit | VARCHAR(20) | 死亡数量单位(尾/kg) | 可空 |
| mortality_rate | DECIMAL(5,2) | 死亡率(%) | 可空 |
| cost | DECIMAL(10,2) | 防治成本(元) | 可空 |
| prevention_measures | TEXT | 预防措施 | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 14. 设备管理表 (equipment)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 设备ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| base_id | BIGINT UNSIGNED | 基地ID | 外键, 非空, 关联基地表 |
| pond_id | BIGINT UNSIGNED | 池塘ID | 外键, 可空, 关联池塘表 |
| name | VARCHAR(100) | 设备名称 | 非空 |
| code | VARCHAR(50) | 设备编码 | 可空, 唯一(租户内) |
| type | VARCHAR(50) | 类型(增氧机/投饵机/水质监测仪等) | 非空 |
| model | VARCHAR(100) | 型号 | 可空 |
| specification | VARCHAR(100) | 规格 | 可空 |
| manufacturer | VARCHAR(100) | 生产厂家 | 可空 |
| serial_number | VARCHAR(100) | 序列号 | 可空 |
| purchase_date | DATE | 购买日期 | 可空 |
| purchase_price | DECIMAL(10,2) | 购买价格(元) | 可空 |
| warranty_period | INT | 保修期(月) | 可空 |
| warranty_end_date | DATE | 保修截止日期 | 可空 |
| power | VARCHAR(50) | 功率 | 可空 |
| voltage | VARCHAR(50) | 电压 | 可空 |
| installation_date | DATE | 安装日期 | 可空 |
| installation_location | VARCHAR(255) | 安装位置 | 可空 |
| maintenance_cycle | INT | 维护周期(天) | 可空 |
| last_maintenance_date | DATE | 上次维护日期 | 可空 |
| next_maintenance_date | DATE | 下次维护日期 | 可空 |
| maintenance_records | TEXT | 维护记录 | 可空 |
| running_status | TINYINT UNSIGNED | 运行状态(1:正常,2:故障,3:维修中,4:停用) | 非空, 默认1 |
| fault_description | TEXT | 故障描述 | 可空 |
| responsible_person | VARCHAR(50) | 责任人 | 可空 |
| contact_phone | VARCHAR(20) | 联系电话 | 可空 |
| description | TEXT | 描述 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:正常,2:停用) | 非空, 默认1 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 15. 销售记录表 (sales_records)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| batch_id | BIGINT UNSIGNED | 批次ID | 外键, 非空, 关联生产批次表 |
| sale_number | VARCHAR(50) | 销售编号 | 非空, 唯一(租户内) |
| sale_date | DATE | 销售日期 | 非空 |
| customer_name | VARCHAR(100) | 客户名称 | 非空 |
| customer_contact | VARCHAR(50) | 客户联系人 | 可空 |
| customer_phone | VARCHAR(20) | 客户电话 | 可空 |
| customer_address | VARCHAR(255) | 客户地址 | 可空 |
| species_id | BIGINT UNSIGNED | 品种ID | 外键, 非空, 关联品种表 |
| species_name | VARCHAR(100) | 品种名称 | 非空 |
| quantity | DECIMAL(10,2) | 销售数量 | 非空 |
| quantity_unit | VARCHAR(20) | 数量单位(尾/kg) | 非空 |
| unit_price | DECIMAL(10,2) | 单价(元) | 非空 |
| total_amount | DECIMAL(10,2) | 总金额(元) | 非空 |
| payment_method | VARCHAR(50) | 支付方式(现金/转账/支票等) | 可空 |
| payment_status | TINYINT UNSIGNED | 支付状态(1:未支付,2:部分支付,3:已支付) | 非空, 默认1 |
| paid_amount | DECIMAL(10,2) | 已支付金额(元) | 非空, 默认0 |
| payment_date | DATE | 支付日期 | 可空 |
| invoice_number | VARCHAR(50) | 发票号码 | 可空 |
| invoice_date | DATE | 开票日期 | 可空 |
| invoice_amount | DECIMAL(10,2) | 开票金额(元) | 可空 |
| transport_method | VARCHAR(50) | 运输方式 | 可空 |
| transport_cost | DECIMAL(10,2) | 运输成本(元) | 可空 |
| delivery_date | DATE | 交付日期 | 可空 |
| delivery_address | VARCHAR(255) | 交付地址 | 可空 |
| quality_grade | VARCHAR(50) | 质量等级 | 可空 |
| average_weight | DECIMAL(10,2) | 平均体重(g) | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 16. 环境监测表 (environment_monitoring)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 记录ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| base_id | BIGINT UNSIGNED | 基地ID | 外键, 非空, 关联基地表 |
| monitor_time | TIMESTAMP | 监测时间 | 非空 |
| air_temperature | DECIMAL(5,2) | 气温(°C) | 可空 |
| air_humidity | DECIMAL(5,2) | 空气湿度(%) | 可空 |
| wind_direction | VARCHAR(50) | 风向 | 可空 |
| wind_speed | DECIMAL(5,2) | 风速(m/s) | 可空 |
| rainfall | DECIMAL(5,2) | 降雨量(mm) | 可空 |
| sunshine_duration | DECIMAL(5,2) | 日照时长(h) | 可空 |
| atmospheric_pressure | DECIMAL(8,2) | 大气压(hPa) | 可空 |
| weather_condition | VARCHAR(50) | 天气状况 | 可空 |
| soil_temperature | DECIMAL(5,2) | 土壤温度(°C) | 可空 |
| soil_moisture | DECIMAL(5,2) | 土壤湿度(%) | 可空 |
| soil_ph | DECIMAL(4,2) | 土壤pH值 | 可空 |
| light_intensity | DECIMAL(10,2) | 光照强度(lux) | 可空 |
| co2_concentration | DECIMAL(6,2) | 二氧化碳浓度(ppm) | 可空 |
| monitor_method | VARCHAR(50) | 监测方法(手动/自动) | 非空, 默认'手动' |
| monitor_equipment | VARCHAR(100) | 监测设备 | 可空 |
| monitor_location | VARCHAR(255) | 监测位置 | 可空 |
| abnormal_phenomena | TEXT | 异常现象 | 可空 |
| remark | TEXT | 备注 | 可空 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

### 17. 疾病信息表 (diseases)

| 字段名 | 数据类型 | 描述 | 约束 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | 疾病ID | 主键, 自增 |
| tenant_id | BIGINT UNSIGNED | 租户ID | 外键, 非空 |
| name | VARCHAR(100) | 疾病名称 | 非空 |
| code | VARCHAR(50) | 疾病编码 | 可空, 唯一(租户内) |
| scientific_name | VARCHAR(100) | 学名 | 可空 |
| category | VARCHAR(50) | 类别(病毒性/细菌性/寄生虫等) | 非空 |
| pathogen | VARCHAR(255) | 病原体 | 可空 |
| applicable_species | VARCHAR(255) | 适用品种 | 可空 |
| symptoms | TEXT | 症状 | 可空 |
| diagnosis_method | TEXT | 诊断方法 | 可空 |
| treatment_method | TEXT | 治疗方法 | 可空 |
| prevention_method | TEXT | 预防方法 | 可空 |
| recommended_medicines | TEXT | 推荐药品 | 可空 |
| infection_route | VARCHAR(255) | 感染途径 | 可空 |
| incubation_period | VARCHAR(100) | 潜伏期 | 可空 |
| mortality_rate | VARCHAR(50) | 死亡率 | 可空 |
| seasonal_characteristics | VARCHAR(255) | 季节特性 | 可空 |
| environmental_factors | TEXT | 环境因素 | 可空 |
| image_url | VARCHAR(255) | 图片URL | 可空 |
| reference | TEXT | 参考文献 | 可空 |
| description | TEXT | 描述 | 可空 |
| status | TINYINT UNSIGNED | 状态(1:启用,2:停用) | 非空, 默认1 |
| created_at | TIMESTAMP | 创建时间 | 非空, 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空, 默认当前时间, ON UPDATE当前时间 |
| created_by | BIGINT UNSIGNED | 创建人ID | 外键, 非空, 关联用户表 |
| updated_by | BIGINT UNSIGNED | 更新人ID | 外键, 可空, 关联用户表 |
| is_deleted | BOOLEAN | 是否删除 | 非空, 默认false |

## 数据库表结构概览

| 序号 | 表名 | 描述 |
|------|------|------|
| 1 | 租户表(tenant) | 存储租户基本信息 |
| 2 | 租户配额表(tenant_quota) | 控制租户资源使用上限 |
| 3 | 租户企业信息表(tenant_business_info) | 记录租户的公司注册信息和营业执照 |
| 4 | 基地信息表(bases) | 记录养殖基地的基本信息 |
| 5 | 池塘信息表(ponds) | 记录养殖池塘的基本信息 |
| 6 | 养殖品种表(species) | 记录养殖的品种信息 |
| 7 | 生产批次表(production_batches) | 记录养殖批次信息 |
| 8 | 水质监测表(water_quality) | 记录水质监测数据 |
| 9 | 饲料管理表(feeds) | 记录饲料使用和库存 |
| 10 | 投喂记录表(feeding_records) | 记录日常投喂情况 |
| 11 | 生长记录表(growth_records) | 记录养殖品种的生长情况 |
| 12 | 药品管理表(medicines) | 记录药品使用和库存 |
| 13 | 病害防治表(disease_prevention) | 记录疾病防治情况 |
| 14 | 设备管理表(equipment) | 记录养殖设备信息 |
| 15 | 销售记录表(sales_records) | 记录产品销售情况 |
| 16 | 环境监测表(environment_monitoring) | 记录养殖环境监测数据 |
| 17 | 疾病信息表(diseases) | 记录疾病的基本信息 |
| 18 | 角色表(roles) | 定义系统角色 |
| 19 | 权限表(permissions) | 定义系统权限 |
| 20 | 角色权限关联表(role_permissions) | 关联角色和权限 |
| 21 | 用户角色关联表(user_roles) | 关联用户和角色 |
| 22 | 操作日志表(operation_logs) | 记录系统操作日志 |

## 表关系说明

1. 租户与数据的关系：
   - 每个表都通过tenant_id字段关联到租户表
   - 所有操作都在租户范围内进行，确保数据隔离

2. 用户与记录的关系：
   - 系统使用现有的用户管理模块
   - 记录通过created_by字段关联到用户表的ID
   - 用户只能查看和管理其所属租户的数据
   - 所有业务表增加updated_by字段，完善审计跟踪

3. 基地与池塘的关系：
   - 一个租户可以有多个基地
   - 一个基地可以有多个池塘
   - 池塘表(ponds)通过base_id关联到基地表(bases)

4. 池塘与批次的关系：
   - 一个池塘可以有多个养殖批次（不同时间段）
   - 一个批次只能在一个池塘中
   - 生产批次表(production_batches)通过pond_id关联到池塘表(ponds)

5. 批次与记录的关系：
   - 一个批次可以有多个投喂记录、生长记录、水质监测记录等
   - 每个记录都属于特定的批次
   - 投喂记录表(feeding_records)、生长记录表(growth_records)等通过batch_id关联到生产批次表

6. 品种与批次的关系：
   - 一个品种可以有多个养殖批次
   - 一个批次通常养殖一种品种
   - 生产批次表通过species_id关联到养殖品种表(species)

7. 饲料/药品与记录的关系：
   - 饲料被用于多个投喂记录
   - 药品被用于多个疾病防治记录
   - 投喂记录表通过feed_id关联到饲料管理表(feeds)
   - 病害防治表通过medicine_id关联到药品管理表(medicines)

8. 疾病与防治的关系：
   - 疾病信息表记录常见疾病的基本信息
   - 病害防治表记录具体的疾病防治行为
   - 病害防治表可以通过添加disease_id字段关联到疾病信息表

9. 租户信息与租户附加信息的关系：
   - 租户表记录租户的基本信息
   - 租户信息附加表记录租户的详细企业信息和营业执照
   - 租户信息附加表通过tenant_id与租户表一对一关联

10. 角色与权限的关系：
    - 一个角色可以拥有多个权限
    - 一个权限可以被多个角色拥有
    - 角色权限关联表(role_permissions)实现多对多关系
    - 角色权限关联表通过role_id关联到角色表(roles)，通过permission_id关联到权限表(permissions)

11. 用户与角色的关系：
    - 一个用户可以拥有多个角色
    - 一个角色可以被多个用户拥有
    - 用户角色关联表(user_roles)实现多对多关系
    - 用户角色关联表通过user_id关联到系统用户表，通过role_id关联到角色表

12. 角色与租户的关系：
    - 角色定义在租户级别，每个租户可以有自己的角色定义
    - 系统预定义角色(is_system=1)由平台管理，租户无法修改
    - 角色表包含tenant_id字段，确保角色在租户内隔离

13. 权限模型：
    - 权限表不包含tenant_id，由平台统一定义
    - 通过角色权限关联表在租户级别分配权限
    - 权限表按模块和操作类型组织，提供细粒度的权限控制

14. 操作日志与监控：
    - 所有重要操作通过操作日志表(operation_logs)进行记录
    - 操作日志按租户隔离，关联到具体用户
    - 记录操作类型、模块、结果等信息，便于审计和问题排查

## 索引设计

为提高查询效率，建议在以下字段上创建索引：

1. 各表的主键字段：`id`(主键索引，自动创建)
2. 所有表的`tenant_id`字段：创建普通索引，提高租户隔离查询效率
3. 外键字段：如`pond_id`, `batch_id`, `species_id`等，创建普通索引
4. 频繁查询的字段：
   - `batch_number`：创建普通索引
   - `status`：创建普通索引（结合tenant_id的复合索引）
   - `sale_date`, `cost_date`等时间字段：创建普通索引
5. 时间相关字段：
   - `created_at`：创建普通索引
   - `test_time`, `feeding_time`, `monitor_time`等业务时间字段：创建普通索引
6. 以下字段应创建唯一索引：
   - 角色表的`tenant_id`和`code`组合：确保租户内角色编码唯一
   - 权限表的`code`字段：确保系统内权限代码唯一
   - 生产批次表的`tenant_id`和`batch_number`组合：确保租户内批次编号唯一
7. 其他推荐索引：
   - 角色权限关联表的`role_id`和`permission_id`字段：创建复合索引
   - 用户角色关联表的`user_id`和`role_id`字段：创建复合索引
   - 操作日志表的`operation_time`字段：创建普通索引

## 权限控制说明

1. 基于RBAC(基于角色的访问控制)模型
   - 用户关联到角色
   - 角色关联到权限
   - 系统根据用户所属角色的权限确定操作许可

2. 权限分类
   - 功能模块权限：控制用户对系统各功能模块的访问
   - 数据操作权限：控制用户对数据的查看(view)、创建(create)、编辑(edit)、删除(delete)操作

3. 权限代码命名规则
   - 格式：`module.operation`
   - 示例：`pond.view`, `pond.create`, `pond.edit`, `pond.delete`

4. 预定义角色
   - 超级管理员：系统最高权限，可管理所有租户
   - 租户管理员：租户内最高权限，可管理租户内所有模块
   - 养殖技术员：负责养殖技术相关模块
   - 销售人员：负责销售相关模块
   - 数据录入员：负责数据录入
   - 系统管理员：负责系统配置和角色权限管理
   - 只读用户：只有查看权限，不能修改数据

## 注意事项

1. 数据库引擎与字符集
   - 所有表应使用InnoDB存储引擎，支持事务和外键约束
   - 所有表的字符集应使用utf8mb4，排序规则使用utf8mb4_unicode_ci，以支持完整的Unicode字符集

2. 数据隔离与安全
   - 所有操作都应在租户上下文中进行，确保数据隔离
   - 系统应自动为所有新记录设置当前租户ID
   - 所有接口应进行权限验证，确保用户只能访问有权限的数据
   - 数据库应配置适当的连接数限制，防止资源耗尽

3. 字段设计规范
   - ID类字段统一使用BIGINT UNSIGNED类型，便于未来扩展
   - 状态类字段使用TINYINT UNSIGNED，提高存储效率
   - 所有有外键关系的字段数据类型必须保持一致
   - 所有日期时间类型使用TIMESTAMP标准类型，并设置默认值和自动更新

4. 审计与日志
   - 所有表都应包含created_at, created_by, updated_at, updated_by审计字段
   - 更新时间字段设置ON UPDATE CURRENT_TIMESTAMP自动更新
   - 创建人/更新人字段设为非空，明确责任
   - 角色和权限变更操作应记录审计日志
   - 重要操作应通过操作日志表详细记录

5. 性能优化
   - 针对大数据量的表（如水质监测表、投喂记录表等），应考虑数据分区或归档策略
   - 批量操作应使用事务，保证数据一致性
   - 用户权限应在每次会话开始时加载并缓存，提高性能
   - 查询时尽可能使用索引字段进行过滤，避免全表扫描
   - 对于频繁查询但不常更新的数据，可考虑使用缓存机制

6. 扩展性考虑
   - 表设计预留扩展字段，便于后续功能扩展
   - 枚举类字段（如状态、类型等）预留足够空间，便于增加新的选项
   - 设计时考虑水平扩展能力，避免强耦合

7. 数据备份
   - 建立定期备份机制，确保数据安全
   - 对于重要数据变更，考虑实现数据变更历史记录表 