# 机器绑定注册码系统安全策略

## 1. 安全威胁分析

### 1.1 威胁模型
基于对macOS软件许可证系统的安全分析，识别以下主要威胁：

#### A. 注册码相关威胁
- **注册码破解**: 逆向工程分析注册码生成算法
- **注册码伪造**: 生成虚假的有效注册码
- **注册码泄露**: 合法注册码被恶意传播
- **注册码重放**: 截获的激活请求被重复使用

#### B. 机器绑定威胁
- **硬件指纹伪造**: 模拟合法设备的硬件特征
- **虚拟机克隆**: 在虚拟环境中复制已激活的系统
- **硬件更换绕过**: 通过替换硬件组件逃避检测
- **指纹碰撞攻击**: 利用哈希碰撞生成相同指纹

#### C. 网络通信威胁
- **中间人攻击**: 拦截和篡改激活通信
- **重放攻击**: 重复发送激活请求
- **DDoS攻击**: 对激活服务器进行拒绝服务攻击
- **数据窃听**: 截获敏感的激活数据

#### D. 服务器端威胁
- **数据库泄露**: 许可证数据被非法访问
- **权限提升**: 获得管理员权限进行恶意操作
- **内部威胁**: 内部人员滥用系统权限
- **备份数据泄露**: 备份文件被恶意获取

## 2. 多层安全防护体系

### 2.1 加密安全层

#### A. 非对称加密保护
```python
# RSA-2048密钥对生成
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class RSASecurityManager:
    """RSA加密安全管理器"""
    
    @staticmethod
    def generate_keypair():
        """生成2048位RSA密钥对"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def sign_license_key(private_key, license_data):
        """使用私钥签名许可证数据"""
        signature = private_key.sign(
            license_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    @staticmethod
    def verify_signature(public_key, license_data, signature):
        """使用公钥验证签名"""
        try:
            public_key.verify(
                signature,
                license_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
```

#### B. 对称加密保护
```python
# AES-256加密机器绑定数据
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64, os

class AESSecurityManager:
    """AES对称加密管理器"""
    
    @staticmethod
    def generate_key(password: str, salt: bytes = None):
        """基于密码生成AES密钥"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key), salt
    
    @staticmethod
    def encrypt_binding_data(binding_data: dict, encryption_key: str):
        """加密机器绑定数据"""
        fernet, salt = AESSecurityManager.generate_key(encryption_key)
        encrypted_data = fernet.encrypt(json.dumps(binding_data).encode())
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'salt': base64.b64encode(salt).decode()
        }
```

### 2.2 机器指纹安全层

#### A. 多维度硬件指纹
```python
class MachineFingerprint:
    """安全的机器指纹生成"""
    
    @staticmethod
    def collect_hardware_info():
        """收集硬件信息"""
        return {
            'hardware_uuid': platform.node(),  # 系统UUID
            'cpu_info': {
                'brand': cpuinfo.get_cpu_info()['brand_raw'],
                'arch': platform.machine(),
                'cores': psutil.cpu_count()
            },
            'memory_info': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available
            },
            'disk_info': {
                'total': psutil.disk_usage('/').total,
                'serial': get_disk_serial()  # 硬盘序列号
            },
            'network_info': {
                'interfaces': get_network_interfaces(),
                'mac_addresses': get_mac_addresses()
            },
            'system_info': {
                'os_version': platform.platform(),
                'kernel_version': platform.release()
            }
        }
    
    @staticmethod
    def generate_fingerprint(hardware_info: dict, salt: str):
        """生成安全的机器指纹"""
        # 1. 提取关键硬件特征
        key_features = [
            hardware_info.get('hardware_uuid', ''),
            hardware_info.get('cpu_info', {}).get('brand', ''),
            str(hardware_info.get('memory_info', {}).get('total', 0)),
            hardware_info.get('disk_info', {}).get('serial', ''),
            '-'.join(sorted(hardware_info.get('network_info', {}).get('mac_addresses', [])))
        ]
        
        # 2. 标准化处理
        normalized_data = '|'.join(key_features).lower().strip()
        
        # 3. 加盐哈希生成指纹
        fingerprint_data = f"{normalized_data}|{salt}"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return fingerprint
    
    @staticmethod
    def verify_fingerprint_similarity(stored_fp: str, current_fp: str, threshold: float = 0.8):
        """验证机器指纹相似度（容忍硬件变化）"""
        # 允许一定程度的硬件变化，如内存升级、外设变化等
        # 实现Levenshtein距离算法或其他相似度算法
        similarity = calculate_similarity(stored_fp, current_fp)
        return similarity >= threshold
```

### 2.3 注册码生成安全层

#### A. 安全的注册码格式
```python
class SecureLicenseGenerator:
    """安全的注册码生成器"""
    
    @staticmethod
    def generate_license_key(product_code: str, plan_code: str, private_key) -> str:
        """生成安全的注册码"""
        
        # 1. 生成唯一标识符
        unique_id = str(uuid.uuid4()).replace('-', '')[:16]
        
        # 2. 时间戳（避免重放攻击）
        timestamp = int(time.time())
        
        # 3. 随机因子（增加熵值）
        random_factor = secrets.token_hex(8)
        
        # 4. 构建原始数据
        raw_data = {
            'product': product_code,
            'plan': plan_code,
            'id': unique_id,
            'timestamp': timestamp,
            'random': random_factor,
            'version': 1  # 格式版本
        }
        
        # 5. JSON序列化并签名
        data_str = json.dumps(raw_data, separators=(',', ':'), sort_keys=True)
        signature = RSASecurityManager.sign_license_key(private_key, data_str)
        
        # 6. 组合数据和签名
        license_payload = {
            'data': raw_data,
            'signature': base64.b64encode(signature).decode()
        }
        
        # 7. Base58编码生成最终注册码
        encoded_payload = base64.b64encode(
            json.dumps(license_payload).encode()
        ).decode()
        
        # 8. 格式化为用户友好的格式
        license_key = base58.b58encode(encoded_payload.encode()).decode()
        formatted_key = '-'.join([
            license_key[i:i+4] for i in range(0, len(license_key), 4)
        ])[:29]  # 限制长度
        
        return formatted_key
    
    @staticmethod
    def verify_license_key(license_key: str, public_key) -> dict:
        """验证注册码有效性"""
        try:
            # 1. 反向解析注册码
            clean_key = license_key.replace('-', '')
            decoded_payload = base64.b64decode(
                base58.b58decode(clean_key)
            ).decode()
            
            # 2. 解析JSON数据
            license_payload = json.loads(decoded_payload)
            raw_data = license_payload['data']
            signature = base64.b64decode(license_payload['signature'])
            
            # 3. 验证签名
            data_str = json.dumps(raw_data, separators=(',', ':'), sort_keys=True)
            if not RSASecurityManager.verify_signature(public_key, data_str, signature):
                return {'valid': False, 'error': 'Invalid signature'}
            
            # 4. 检查时间戳（防重放攻击）
            current_time = int(time.time())
            license_time = raw_data['timestamp']
            if abs(current_time - license_time) > 86400 * 365 * 10:  # 10年有效期
                return {'valid': False, 'error': 'Timestamp out of range'}
            
            return {'valid': True, 'data': raw_data}
            
        except Exception as e:
            return {'valid': False, 'error': f'Parsing error: {str(e)}'}
```

### 2.4 网络通信安全层

#### A. HTTPS强制加密
```python
# settings.py 安全配置
SECURE_SSL_REDIRECT = True  # 强制HTTPS
SECURE_HSTS_SECONDS = 31536000  # HSTS策略
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

#### B. API请求签名验证
```python
class APISecurityMiddleware:
    """API安全中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 验证请求签名（对敏感API）
        if self.is_sensitive_endpoint(request.path):
            if not self.verify_request_signature(request):
                return JsonResponse({
                    'success': False,
                    'code': 4001,
                    'message': '请求签名验证失败'
                }, status=401)
        
        response = self.get_response(request)
        return response
    
    def verify_request_signature(self, request):
        """验证请求签名"""
        # 实现请求签名验证逻辑
        # 包含时间戳检查、Nonce验证等
        pass
```

## 3. 访问控制安全

### 3.1 基于角色的权限控制
```python
# 许可证管理权限定义
class LicensePermissions:
    """许可证相关权限"""
    
    # 产品管理权限
    PRODUCT_VIEW = 'licenses.view_product'
    PRODUCT_ADD = 'licenses.add_product'
    PRODUCT_CHANGE = 'licenses.change_product'
    PRODUCT_DELETE = 'licenses.delete_product'
    PRODUCT_GENERATE_KEYPAIR = 'licenses.generate_product_keypair'
    
    # 许可证管理权限
    LICENSE_VIEW = 'licenses.view_license'
    LICENSE_ADD = 'licenses.add_license'
    LICENSE_CHANGE = 'licenses.change_license'
    LICENSE_DELETE = 'licenses.delete_license'
    LICENSE_GENERATE = 'licenses.generate_license'
    LICENSE_REVOKE = 'licenses.revoke_license'
    
    # 激活管理权限
    ACTIVATION_VIEW = 'licenses.view_activation'
    ACTIVATION_MANAGE = 'licenses.manage_activation'
    
    # 报告查看权限
    REPORT_VIEW = 'licenses.view_report'
    REPORT_EXPORT = 'licenses.export_report'

# 权限检查装饰器
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_license_permission(permission):
    """许可证权限检查装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                raise PermissionDenied(f"需要权限: {permission}")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 3.2 多租户数据隔离
```python
class TenantSecurityMixin:
    """租户安全混合类"""
    
    def get_queryset(self):
        """确保查询结果按租户隔离"""
        queryset = super().get_queryset()
        
        # 超级管理员可以查看所有数据
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能查看自己租户的数据
        if hasattr(self.request.user, 'tenant') and self.request.user.tenant:
            return queryset.filter(tenant=self.request.user.tenant)
        
        # 其他用户无权限
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动关联租户"""
        if hasattr(serializer.Meta.model, 'tenant'):
            # 超级管理员可以指定租户
            if self.request.user.is_super_admin:
                tenant = serializer.validated_data.get('tenant', self.request.user.tenant)
            else:
                tenant = self.request.user.tenant
            
            serializer.save(tenant=tenant)
        else:
            serializer.save()
```

## 4. 数据安全保护

### 4.1 敏感数据加密存储
```python
# 数据库字段加密
from django_cryptography.fields import encrypt

class License(BaseModel):
    """许可证模型（安全版本）"""
    
    # 注册码哈希存储
    license_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    # 客户信息加密存储
    encrypted_customer_info = encrypt(models.TextField(blank=True))
    
    # 私钥哈希（不存储明文私钥）
    private_key_hash = models.CharField(max_length=64)
    
    def set_customer_info(self, customer_info: dict):
        """设置加密的客户信息"""
        self.encrypted_customer_info = json.dumps(customer_info)
    
    def get_customer_info(self) -> dict:
        """获取解密的客户信息"""
        if self.encrypted_customer_info:
            return json.loads(self.encrypted_customer_info)
        return {}
```

### 4.2 数据库安全配置
```python
# 数据库连接安全配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'sql_mode': 'STRICT_TRANS_TABLES',
            'isolation_level': 'READ_COMMITTED',
            # SSL连接
            'ssl': {
                'ssl_ca': '/path/to/ca-cert.pem',
                'ssl_cert': '/path/to/client-cert.pem',
                'ssl_key': '/path/to/client-key.pem',
            }
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# 数据库查询监控
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['file'],
    'level': 'DEBUG',
    'propagate': False,
}
```

## 5. 运行时安全监控

### 5.1 异常行为检测
```python
class SecurityMonitor:
    """安全监控服务"""
    
    @staticmethod
    def detect_suspicious_activation(license_key: str, machine_info: dict):
        """检测可疑的激活行为"""
        
        # 1. 检查激活频率
        recent_activations = LicenseActivation.objects.filter(
            license__license_key=license_key,
            activated_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_activations > 5:  # 1小时内超过5次激活
            return {'suspicious': True, 'reason': 'High activation frequency'}
        
        # 2. 检查地理位置异常
        previous_activation = LicenseActivation.objects.filter(
            license__license_key=license_key
        ).order_by('-activated_at').first()
        
        if previous_activation:
            # 实现地理位置检查逻辑
            pass
        
        # 3. 检查硬件指纹变化
        existing_bindings = MachineBinding.objects.filter(
            license__license_key=license_key,
            status='active'
        )
        
        if existing_bindings.count() >= 3:  # 超过正常绑定数量
            return {'suspicious': True, 'reason': 'Too many active bindings'}
        
        return {'suspicious': False}
    
    @staticmethod
    def log_security_event(event_type: str, details: dict, severity: str = 'INFO'):
        """记录安全事件"""
        SecurityLog.objects.create(
            event_type=event_type,
            details=details,
            severity=severity,
            timestamp=timezone.now(),
            ip_address=details.get('ip_address'),
            user_agent=details.get('user_agent')
        )
```

### 5.2 自动安全响应
```python
class AutoSecurityResponse:
    """自动安全响应系统"""
    
    @staticmethod
    def handle_suspicious_activity(license_key: str, threat_type: str):
        """处理可疑活动"""
        
        if threat_type == 'brute_force_activation':
            # 临时锁定许可证
            License.objects.filter(license_key=license_key).update(
                status='suspended'
            )
            
            # 发送告警
            send_security_alert(
                f"License {license_key} suspended due to brute force attempts"
            )
        
        elif threat_type == 'multiple_machine_binding':
            # 标记为需要人工审核
            License.objects.filter(license_key=license_key).update(
                notes='Flagged for manual review - multiple bindings detected'
            )
    
    @staticmethod
    def rate_limit_activation(ip_address: str):
        """激活请求频率限制"""
        cache_key = f"activation_limit:{ip_address}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= 10:  # 每小时最多10次激活
            raise ValidationError("Too many activation attempts. Please try later.")
        
        cache.set(cache_key, current_count + 1, 3600)  # 1小时过期
```

## 6. 安全配置规范

### 6.1 生产环境安全配置
```python
# production_security_settings.py

# 基础安全设置
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'api.your-domain.com']

# 安全中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... 其他中间件
    'licenses.middleware.SecurityMonitoringMiddleware',
    'licenses.middleware.RateLimitMiddleware',
]

# 会话安全
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1小时

# CSRF保护
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# 密码安全
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'licenses.validators.ComplexPasswordValidator',
    }
]

# 日志安全
LOGGING_CONFIG = 'licenses.logging.SecurityLoggingConfig'

# 许可证系统专用安全配置
LICENSE_SECURITY = {
    'RSA_KEY_SIZE': 2048,
    'AES_KEY_SIZE': 256,
    'SIGNATURE_ALGORITHM': 'RSA-PSS',
    'HASH_ALGORITHM': 'SHA-256',
    'ACTIVATION_RATE_LIMIT': '10/hour',
    'VERIFICATION_RATE_LIMIT': '1440/day',
    'OFFLINE_GRACE_PERIOD': 3 * 24 * 3600,  # 3天
    'MAX_MACHINE_BINDINGS': 5,
    'FINGERPRINT_SIMILARITY_THRESHOLD': 0.8,
}
```

### 6.2 密钥管理规范
```python
class KeyManagement:
    """密钥管理最佳实践"""
    
    @staticmethod
    def store_private_key_securely(private_key, key_id: str):
        """安全存储私钥"""
        
        # 1. 使用硬件安全模块（HSM）存储
        # 2. 或使用密钥管理服务（如AWS KMS）
        # 3. 本地存储时必须加密
        
        # 示例：使用主密钥加密存储
        master_key = get_master_encryption_key()
        encrypted_key = encrypt_with_master_key(private_key, master_key)
        
        # 存储到安全位置
        store_encrypted_key(key_id, encrypted_key)
        
        # 仅存储密钥哈希到数据库
        key_hash = hashlib.sha256(private_key.encode()).hexdigest()
        return key_hash
    
    @staticmethod
    def rotate_keypair(product_id: str):
        """定期轮换密钥对"""
        
        # 1. 生成新密钥对
        new_private_key, new_public_key = RSASecurityManager.generate_keypair()
        
        # 2. 更新产品配置
        product = SoftwareProduct.objects.get(id=product_id)
        old_public_key = product.public_key
        
        product.public_key = serialize_public_key(new_public_key)
        product.private_key_hash = KeyManagement.store_private_key_securely(
            serialize_private_key(new_private_key),
            f"product_{product_id}_{int(time.time())}"
        )
        product.save()
        
        # 3. 保留旧密钥一段时间（向后兼容）
        KeyRotationHistory.objects.create(
            product=product,
            old_public_key=old_public_key,
            rotated_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=90)  # 90天后删除
        )
        
        # 4. 通知相关系统更新
        notify_key_rotation(product_id, new_public_key)
```

## 7. 安全审计与合规

### 7.1 审计日志系统
```python
class SecurityAuditLog(models.Model):
    """安全审计日志"""
    
    EVENT_TYPES = [
        ('license_generated', '许可证生成'),
        ('license_activated', '许可证激活'),
        ('license_revoked', '许可证撤销'),
        ('keypair_generated', '密钥对生成'),
        ('suspicious_activity', '可疑活动'),
        ('authentication_failed', '认证失败'),
        ('privilege_escalation', '权限提升'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', '低'),
        ('MEDIUM', '中'),
        ('HIGH', '高'),
        ('CRITICAL', '严重'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'security_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
```

### 7.2 合规性检查
```python
class ComplianceChecker:
    """合规性检查器"""
    
    @staticmethod
    def check_gdpr_compliance():
        """GDPR合规性检查"""
        
        # 1. 检查数据保留期限
        expired_data = License.objects.filter(
            expires_at__lt=timezone.now() - timedelta(days=365)
        )
        
        # 2. 检查个人数据加密
        unencrypted_customer_data = License.objects.filter(
            encrypted_customer_info__isnull=True
        )
        
        # 3. 生成合规报告
        return {
            'expired_data_count': expired_data.count(),
            'unencrypted_data_count': unencrypted_customer_data.count(),
            'compliance_status': 'COMPLIANT' if not unencrypted_customer_data else 'NON_COMPLIANT'
        }
    
    @staticmethod
    def generate_security_report():
        """生成安全报告"""
        
        # 收集安全指标
        last_30_days = timezone.now() - timedelta(days=30)
        
        metrics = {
            'total_activations': LicenseActivation.objects.filter(
                activated_at__gte=last_30_days
            ).count(),
            'failed_activations': LicenseActivation.objects.filter(
                activated_at__gte=last_30_days,
                result='failed'
            ).count(),
            'suspicious_activities': SecurityAuditLog.objects.filter(
                timestamp__gte=last_30_days,
                event_type='suspicious_activity'
            ).count(),
            'security_incidents': SecurityAuditLog.objects.filter(
                timestamp__gte=last_30_days,
                severity__in=['HIGH', 'CRITICAL']
            ).count(),
        }
        
        return metrics
```

这个安全策略文档全面分析了机器绑定注册码系统面临的各种安全威胁，并提供了多层次的防护措施。通过RSA签名、AES加密、机器指纹验证、访问控制、异常监控等技术手段，构建了一个安全可靠的许可证管理系统。

---

*设计完成时间: 2025-09-05*  
*设计原则: 深度防护、零信任、持续监控*
