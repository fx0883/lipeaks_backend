# 机器绑定注册码系统数据库设计

## 1. 设计原则

### 1.1 兼容性原则
- 继承现有系统的BaseModel设计模式
- 遵循现有的命名约定和数据类型标准
- 与多租户架构完全兼容
- 支持现有的软删除机制

### 1.2 安全性原则
- 敏感数据加密存储
- 关键操作审计记录
- 数据完整性约束
- 访问权限控制

### 1.3 性能原则
- 关键字段建立索引
- 分区表设计优化查询
- 合理的数据类型选择
- 冗余设计减少关联查询

## 2. 数据库表结构设计

### 2.1 软件产品表 (software_product)
```sql
CREATE TABLE `software_product` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `tenant_id` bigint DEFAULT NULL,
    `name` varchar(100) NOT NULL COMMENT '产品名称',
    `code` varchar(50) NOT NULL COMMENT '产品代码',
    `version` varchar(20) NOT NULL COMMENT '产品版本',
    `description` text COMMENT '产品描述',
    `platform` varchar(20) NOT NULL DEFAULT 'macos' COMMENT '支持平台',
    `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状态',
    `public_key` text NOT NULL COMMENT 'RSA公钥',
    `private_key_hash` varchar(64) NOT NULL COMMENT '私钥哈希',
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_product_code_tenant` (`tenant_id`, `code`),
    KEY `idx_product_status` (`status`),
    KEY `idx_product_platform` (`platform`),
    CONSTRAINT `fk_product_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='软件产品表';
```

**字段说明**:
- `tenant_id`: 租户ID，支持多租户隔离
- `code`: 产品唯一标识，用于生成注册码
- `public_key`: 用于客户端验证注册码签名
- `private_key_hash`: 私钥哈希，用于验证但不存储私钥明文

### 2.2 许可方案表 (license_plan)
```sql
CREATE TABLE `license_plan` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `tenant_id` bigint DEFAULT NULL,
    `product_id` bigint NOT NULL,
    `name` varchar(100) NOT NULL COMMENT '方案名称',
    `code` varchar(50) NOT NULL COMMENT '方案代码',
    `plan_type` varchar(20) NOT NULL COMMENT '方案类型',
    `max_activations` int NOT NULL DEFAULT 1 COMMENT '最大激活次数',
    `validity_days` int DEFAULT NULL COMMENT '有效天数',
    `features` json DEFAULT NULL COMMENT '功能特性配置',
    `price` decimal(10,2) DEFAULT NULL COMMENT '价格',
    `status` varchar(20) NOT NULL DEFAULT 'active',
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_plan_code_product` (`product_id`, `code`),
    KEY `idx_plan_type` (`plan_type`),
    KEY `idx_plan_status` (`status`),
    CONSTRAINT `fk_plan_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`),
    CONSTRAINT `fk_plan_product` FOREIGN KEY (`product_id`) REFERENCES `software_product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='许可方案表';
```

**字段说明**:
- `plan_type`: 方案类型 (trial/standard/professional/enterprise)
- `max_activations`: 同一注册码的最大激活设备数
- `validity_days`: 许可有效期，NULL表示永久有效
- `features`: JSON格式存储功能配置

### 2.3 许可证表 (license)
```sql
CREATE TABLE `license` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `tenant_id` bigint DEFAULT NULL,
    `plan_id` bigint NOT NULL,
    `license_key` varchar(29) NOT NULL COMMENT '注册码',
    `license_hash` varchar(64) NOT NULL COMMENT '注册码哈希',
    `customer_info` json DEFAULT NULL COMMENT '客户信息',
    `issued_at` datetime NOT NULL COMMENT '发放时间',
    `expires_at` datetime DEFAULT NULL COMMENT '到期时间',
    `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '许可证状态',
    `activation_count` int NOT NULL DEFAULT 0 COMMENT '已激活次数',
    `last_activated_at` datetime DEFAULT NULL COMMENT '最后激活时间',
    `notes` text DEFAULT NULL COMMENT '备注信息',
    `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_license_key` (`license_key`),
    UNIQUE KEY `uk_license_hash` (`license_hash`),
    KEY `idx_license_tenant` (`tenant_id`),
    KEY `idx_license_status` (`status`),
    KEY `idx_license_expires` (`expires_at`),
    KEY `idx_license_issued` (`issued_at`),
    CONSTRAINT `fk_license_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`),
    CONSTRAINT `fk_license_plan` FOREIGN KEY (`plan_id`) REFERENCES `license_plan` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='许可证表';
```

**字段说明**:
- `license_key`: 分发给客户的注册码
- `license_hash`: 注册码的SHA-256哈希，用于快速查找
- `customer_info`: JSON格式存储客户信息
- `status`: active/suspended/expired/revoked

### 2.4 机器绑定表 (machine_binding)
```sql
CREATE TABLE `machine_binding` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `license_id` bigint NOT NULL,
    `machine_fingerprint` varchar(64) NOT NULL COMMENT '机器指纹',
    `machine_info` json NOT NULL COMMENT '机器信息',
    `binding_data` text NOT NULL COMMENT '绑定数据(加密)',
    `first_activated_at` datetime NOT NULL COMMENT '首次激活时间',
    `last_verified_at` datetime DEFAULT NULL COMMENT '最后验证时间',
    `verification_count` int NOT NULL DEFAULT 0 COMMENT '验证次数',
    `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '绑定状态',
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_binding_license_machine` (`license_id`, `machine_fingerprint`),
    KEY `idx_binding_fingerprint` (`machine_fingerprint`),
    KEY `idx_binding_status` (`status`),
    KEY `idx_binding_last_verified` (`last_verified_at`),
    CONSTRAINT `fk_binding_license` FOREIGN KEY (`license_id`) REFERENCES `license` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器绑定表';
```

**字段说明**:
- `machine_fingerprint`: SHA-256哈希的机器唯一标识
- `machine_info`: JSON格式存储硬件信息（用于人工核查）
- `binding_data`: AES加密的绑定证书数据
- `verification_count`: 累计验证次数，用于使用统计

### 2.5 许可证激活记录表 (license_activation)
```sql
CREATE TABLE `license_activation` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `license_id` bigint NOT NULL,
    `machine_binding_id` bigint NOT NULL,
    `activation_type` varchar(20) NOT NULL COMMENT '激活类型',
    `client_ip` varchar(45) DEFAULT NULL COMMENT '客户端IP',
    `client_version` varchar(50) DEFAULT NULL COMMENT '客户端版本',
    `activation_data` json DEFAULT NULL COMMENT '激活数据',
    `result` varchar(20) NOT NULL COMMENT '激活结果',
    `error_message` text DEFAULT NULL COMMENT '错误信息',
    `activated_at` datetime NOT NULL COMMENT '激活时间',
    PRIMARY KEY (`id`),
    KEY `idx_activation_license` (`license_id`),
    KEY `idx_activation_machine` (`machine_binding_id`),
    KEY `idx_activation_type` (`activation_type`),
    KEY `idx_activation_result` (`result`),
    KEY `idx_activation_time` (`activated_at`),
    CONSTRAINT `fk_activation_license` FOREIGN KEY (`license_id`) REFERENCES `license` (`id`),
    CONSTRAINT `fk_activation_binding` FOREIGN KEY (`machine_binding_id`) REFERENCES `machine_binding` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='许可证激活记录表';
```

**字段说明**:
- `activation_type`: initial/renewal/verification/offline
- `result`: success/failed/pending
- 该表只记录不删除，用于完整的审计轨迹

### 2.6 许可证使用日志表 (license_usage_log)
```sql
CREATE TABLE `license_usage_log` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `license_id` bigint NOT NULL,
    `machine_binding_id` bigint NOT NULL,
    `usage_type` varchar(20) NOT NULL COMMENT '使用类型',
    `client_ip` varchar(45) DEFAULT NULL,
    `client_version` varchar(50) DEFAULT NULL,
    `session_duration` int DEFAULT NULL COMMENT '会话时长(秒)',
    `feature_usage` json DEFAULT NULL COMMENT '功能使用情况',
    `logged_at` datetime NOT NULL COMMENT '记录时间',
    PRIMARY KEY (`id`),
    KEY `idx_usage_license` (`license_id`),
    KEY `idx_usage_machine` (`machine_binding_id`),
    KEY `idx_usage_type` (`usage_type`),
    KEY `idx_usage_time` (`logged_at`),
    CONSTRAINT `fk_usage_license` FOREIGN KEY (`license_id`) REFERENCES `license` (`id`),
    CONSTRAINT `fk_usage_binding` FOREIGN KEY (`machine_binding_id`) REFERENCES `machine_binding` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='许可证使用日志表';

-- 按月分区优化查询性能
ALTER TABLE `license_usage_log` 
PARTITION BY RANGE (TO_DAYS(`logged_at`)) (
    PARTITION p202509 VALUES LESS THAN (TO_DAYS('2025-10-01')),
    PARTITION p202510 VALUES LESS THAN (TO_DAYS('2025-11-01')),
    PARTITION p202511 VALUES LESS THAN (TO_DAYS('2025-12-01')),
    PARTITION p202512 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

**字段说明**:
- `usage_type`: startup/heartbeat/shutdown/feature_access
- 按月分区存储，提高查询性能
- 定期归档历史数据

### 2.7 许可证配额扩展表 (tenant_license_quota)
```sql
CREATE TABLE `tenant_license_quota` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `tenant_id` bigint NOT NULL,
    `product_id` bigint NOT NULL,
    `max_licenses` int NOT NULL DEFAULT 0 COMMENT '最大许可证数量',
    `current_licenses` int NOT NULL DEFAULT 0 COMMENT '当前已用数量',
    `max_activations` int NOT NULL DEFAULT 0 COMMENT '最大激活数量',
    `current_activations` int NOT NULL DEFAULT 0 COMMENT '当前激活数量',
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_quota_tenant_product` (`tenant_id`, `product_id`),
    CONSTRAINT `fk_quota_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`),
    CONSTRAINT `fk_quota_product` FOREIGN KEY (`product_id`) REFERENCES `software_product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户许可证配额表';
```

## 3. Django模型设计

### 3.1 基础模型类
```python
# licenses/models/__init__.py
from django.db import models
from common.models import BaseModel

class LicenseBaseModel(BaseModel):
    """许可证系统基础模型"""
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # 添加许可证特有的保存逻辑
        super().save(*args, **kwargs)
```

### 3.2 软件产品模型
```python
# licenses/models/product_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel
from cryptography.hazmat.primitives import serialization

class SoftwareProduct(BaseModel):
    """软件产品模型"""
    
    PLATFORM_CHOICES = [
        ('macos', 'macOS'),
        ('windows', 'Windows'),
        ('linux', 'Linux'),
    ]
    
    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '禁用'),
        ('deprecated', '已弃用'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='software_products',
        verbose_name=_("所属租户"),
        null=True, blank=True
    )
    name = models.CharField(_("产品名称"), max_length=100)
    code = models.CharField(_("产品代码"), max_length=50)
    version = models.CharField(_("产品版本"), max_length=20)
    description = models.TextField(_("产品描述"), blank=True)
    platform = models.CharField(
        _("支持平台"), 
        max_length=20, 
        choices=PLATFORM_CHOICES,
        default='macos'
    )
    status = models.CharField(
        _("状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    public_key = models.TextField(_("RSA公钥"))
    private_key_hash = models.CharField(_("私钥哈希"), max_length=64)
    
    class Meta:
        verbose_name = _('软件产品')
        verbose_name_plural = _('软件产品')
        db_table = 'software_product'
        unique_together = [['tenant', 'code']]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def generate_keypair(self):
        """生成RSA密钥对"""
        from licenses.services.crypto_service import CryptoService
        crypto = CryptoService()
        private_key, public_key = crypto.generate_rsa_keypair()
        
        self.public_key = public_key
        self.private_key_hash = crypto.hash_private_key(private_key)
        
        return private_key  # 返回私钥供调用者安全保存
```

### 3.3 许可方案模型
```python
# licenses/models/product_models.py (续)
class LicensePlan(BaseModel):
    """许可方案模型"""
    
    PLAN_TYPE_CHOICES = [
        ('trial', '试用版'),
        ('standard', '标准版'),
        ('professional', '专业版'),
        ('enterprise', '企业版'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='license_plans',
        null=True, blank=True
    )
    product = models.ForeignKey(
        SoftwareProduct,
        on_delete=models.CASCADE,
        related_name='plans'
    )
    name = models.CharField(_("方案名称"), max_length=100)
    code = models.CharField(_("方案代码"), max_length=50)
    plan_type = models.CharField(
        _("方案类型"),
        max_length=20,
        choices=PLAN_TYPE_CHOICES
    )
    max_activations = models.IntegerField(_("最大激活次数"), default=1)
    validity_days = models.IntegerField(
        _("有效天数"), 
        null=True, blank=True,
        help_text=_("留空表示永久有效")
    )
    features = models.JSONField(_("功能特性"), null=True, blank=True)
    price = models.DecimalField(
        _("价格"), 
        max_digits=10, 
        decimal_places=2,
        null=True, blank=True
    )
    status = models.CharField(_("状态"), max_length=20, default='active')
    
    class Meta:
        verbose_name = _('许可方案')
        verbose_name_plural = _('许可方案')
        db_table = 'license_plan'
        unique_together = [['product', 'code']]
        ordering = ['product', 'plan_type']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
```

### 3.4 许可证模型
```python
# licenses/models/license_models.py
class License(BaseModel):
    """许可证模型"""
    
    STATUS_CHOICES = [
        ('active', '有效'),
        ('suspended', '暂停'),
        ('expired', '过期'),
        ('revoked', '撤销'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='licenses',
        null=True, blank=True
    )
    plan = models.ForeignKey(
        'licenses.LicensePlan',
        on_delete=models.CASCADE,
        related_name='licenses'
    )
    license_key = models.CharField(_("注册码"), max_length=29, unique=True)
    license_hash = models.CharField(_("注册码哈希"), max_length=64, unique=True)
    customer_info = models.JSONField(_("客户信息"), null=True, blank=True)
    issued_at = models.DateTimeField(_("发放时间"))
    expires_at = models.DateTimeField(_("到期时间"), null=True, blank=True)
    status = models.CharField(
        _("许可证状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    activation_count = models.IntegerField(_("已激活次数"), default=0)
    last_activated_at = models.DateTimeField(_("最后激活时间"), null=True, blank=True)
    notes = models.TextField(_("备注信息"), blank=True)
    created_by = models.CharField(_("创建者"), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('许可证')
        verbose_name_plural = _('许可证')
        db_table = 'license'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.plan.name} - {self.license_key}"
    
    def is_valid(self):
        """检查许可证是否有效"""
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
    
    def can_activate(self):
        """检查是否可以激活"""
        if not self.is_valid():
            return False
        return self.activation_count < self.plan.max_activations
    
    @property
    def remaining_activations(self):
        """剩余激活次数"""
        return max(0, self.plan.max_activations - self.activation_count)
```

## 4. 索引优化策略

### 4.1 核心查询索引
```sql
-- 许可证快速查找
CREATE INDEX idx_license_key_hash ON license (license_hash);
CREATE INDEX idx_license_tenant_status ON license (tenant_id, status);

-- 机器绑定查询优化
CREATE INDEX idx_binding_license_machine ON machine_binding (license_id, machine_fingerprint);
CREATE INDEX idx_binding_last_verified ON machine_binding (last_verified_at);

-- 使用日志查询优化
CREATE INDEX idx_usage_license_time ON license_usage_log (license_id, logged_at);
CREATE INDEX idx_usage_machine_time ON license_usage_log (machine_binding_id, logged_at);

-- 激活记录查询优化
CREATE INDEX idx_activation_license_time ON license_activation (license_id, activated_at);
CREATE INDEX idx_activation_result_time ON license_activation (result, activated_at);
```

### 4.2 复合索引设计
```sql
-- 支持多维度查询
CREATE INDEX idx_license_composite ON license (tenant_id, status, expires_at);
CREATE INDEX idx_binding_composite ON machine_binding (status, last_verified_at);
CREATE INDEX idx_usage_composite ON license_usage_log (usage_type, logged_at);
```

## 5. 数据安全设计

### 5.1 敏感数据加密
- `binding_data`: AES-256加密存储
- `private_key_hash`: SHA-256哈希存储
- `license_hash`: SHA-256哈希用于快速查找
- `machine_fingerprint`: SHA-256哈希的机器标识

### 5.2 数据完整性约束
- 外键约束保证数据一致性
- 唯一性约束防止重复数据
- 检查约束验证数据有效性
- 软删除机制保护历史数据

## 6. 性能优化建议

### 6.1 分区策略
- 使用日志表按月分区
- 历史数据定期归档
- 冷数据迁移到归档表

### 6.2 缓存策略
- 热点许可证信息缓存
- 机器绑定状态缓存
- 产品配置信息缓存

这个数据库设计充分考虑了与现有系统的兼容性，采用了多层安全机制，并针对性能进行了优化。所有表都继承了现有的BaseModel模式，支持软删除和审计功能。

---

*设计完成时间: 2025-09-05*  
*设计原则: 兼容性、安全性、性能优化*
