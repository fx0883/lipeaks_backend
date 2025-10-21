"""
安全服务模块
提供RSA签名、AES加密、哈希计算等核心安全功能
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Dict, Tuple, Optional, Any
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
import logging

logger = logging.getLogger('licenses.security')


class RSASecurityManager:
    """RSA非对称加密安全管理器"""
    
    @staticmethod
    def generate_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        生成RSA密钥对
        
        Args:
            key_size: 密钥长度，默认2048位
            
        Returns:
            Tuple[bytes, bytes]: (私钥PEM格式, 公钥PEM格式)
        """
        try:
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size
            )
            
            # 序列化私钥
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # 获取公钥并序列化
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            logger.info(f"RSA密钥对生成成功，密钥长度: {key_size}位")
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"RSA密钥对生成失败: {str(e)}")
            raise Exception(f"Key pair generation failed: {str(e)}")
    
    @staticmethod
    def sign_data(private_key_pem: bytes, data: str) -> bytes:
        """
        使用私钥对数据进行签名
        
        Args:
            private_key_pem: 私钥PEM格式
            data: 要签名的数据
            
        Returns:
            bytes: 签名数据
        """
        try:
            # 加载私钥
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None
            )
            
            # 使用PSS padding和SHA256进行签名
            signature = private_key.sign(
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.debug("数据签名成功")
            return signature
            
        except Exception as e:
            logger.error(f"数据签名失败: {str(e)}")
            raise Exception(f"Signature failed: {str(e)}")
    
    @staticmethod
    def verify_signature(public_key_pem: bytes, data: str, signature: bytes) -> bool:
        """
        使用公钥验证签名
        
        Args:
            public_key_pem: 公钥PEM格式
            data: 原始数据
            signature: 签名数据
            
        Returns:
            bool: 验证结果
        """
        try:
            # 加载公钥
            public_key = serialization.load_pem_public_key(public_key_pem)
            
            # 验证签名
            public_key.verify(
                signature,
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.debug("签名验证成功")
            return True
            
        except Exception as e:
            logger.warning(f"签名验证失败: {str(e)}")
            return False


class AESSecurityManager:
    """AES对称加密安全管理器"""
    
    @staticmethod
    def generate_key_from_password(password: str, salt: bytes = None) -> Tuple[Fernet, bytes]:
        """
        基于密码生成AES密钥
        
        Args:
            password: 密码
            salt: 盐值，如果为None则自动生成
            
        Returns:
            Tuple[Fernet, bytes]: (Fernet对象, 盐值)
        """
        try:
            if salt is None:
                salt = os.urandom(16)
            
            # 使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            fernet = Fernet(key)
            
            logger.debug("AES密钥生成成功")
            return fernet, salt
            
        except Exception as e:
            logger.error(f"AES密钥生成失败: {str(e)}")
            raise Exception(f"Key generation failed: {str(e)}")
    
    @staticmethod
    def encrypt_data(data: Any, encryption_password: str) -> Dict[str, str]:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            encryption_password: 加密密码
            
        Returns:
            Dict[str, str]: 包含加密数据和盐值的字典
        """
        try:
            # 序列化数据
            if isinstance(data, dict) or isinstance(data, list):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = str(data)
            
            # 生成密钥和盐值
            fernet, salt = AESSecurityManager.generate_key_from_password(encryption_password)
            
            # 加密数据
            encrypted_data = fernet.encrypt(data_str.encode('utf-8'))
            
            return {
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'salt': base64.b64encode(salt).decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"数据加密失败: {str(e)}")
            raise Exception(f"Encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt_data(encrypted_data: str, salt: str, decryption_password: str) -> Any:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据
            salt: 盐值
            decryption_password: 解密密码
            
        Returns:
            Any: 解密后的数据
        """
        try:
            # 解码盐值和加密数据
            salt_bytes = base64.b64decode(salt.encode('utf-8'))
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # 重新生成密钥
            fernet, _ = AESSecurityManager.generate_key_from_password(
                decryption_password, salt_bytes
            )
            
            # 解密数据
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # 尝试解析JSON
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except Exception as e:
            logger.error(f"数据解密失败: {str(e)}")
            raise Exception(f"Decryption failed: {str(e)}")


class HashManager:
    """哈希计算管理器"""
    
    @staticmethod
    def generate_salt(length: int = 16) -> str:
        """
        生成随机盐值
        
        Args:
            length: 盐值长度
            
        Returns:
            str: Base64编码的盐值
        """
        salt = os.urandom(length)
        return base64.b64encode(salt).decode('utf-8')
    
    @staticmethod
    def hash_data(data: str, salt: str = None, algorithm: str = 'sha256') -> str:
        """
        计算数据哈希值
        
        Args:
            data: 要哈希的数据
            salt: 盐值
            algorithm: 哈希算法
            
        Returns:
            str: 哈希值
        """
        try:
            if salt:
                data_with_salt = f"{data}|{salt}"
            else:
                data_with_salt = data
            
            if algorithm == 'sha256':
                hash_obj = hashlib.sha256(data_with_salt.encode('utf-8'))
            elif algorithm == 'sha512':
                hash_obj = hashlib.sha512(data_with_salt.encode('utf-8'))
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"哈希计算失败: {str(e)}")
            raise Exception(f"Hash calculation failed: {str(e)}")
    
    @staticmethod
    def verify_hash(data: str, expected_hash: str, salt: str = None, algorithm: str = 'sha256') -> bool:
        """
        验证哈希值
        
        Args:
            data: 原始数据
            expected_hash: 期望的哈希值
            salt: 盐值
            algorithm: 哈希算法
            
        Returns:
            bool: 验证结果
        """
        try:
            calculated_hash = HashManager.hash_data(data, salt, algorithm)
            return calculated_hash == expected_hash
        except Exception:
            return False


class SecurityTokenManager:
    """安全令牌管理器"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        生成安全的随机令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            str: 安全令牌
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_uuid_token() -> str:
        """
        生成UUID格式的令牌
        
        Returns:
            str: UUID令牌
        """
        import uuid
        return str(uuid.uuid4()).replace('-', '')
    
    @staticmethod
    def generate_activation_code(product_code: str, timestamp: int = None) -> str:
        """
        生成激活码
        
        Args:
            product_code: 产品代码
            timestamp: 时间戳
            
        Returns:
            str: 激活码
        """
        import time
        
        if timestamp is None:
            timestamp = int(time.time())
        
        # 组合产品代码、时间戳和随机数
        random_part = secrets.token_hex(8)
        raw_code = f"{product_code}_{timestamp}_{random_part}"
        
        # 计算哈希并截取前16位
        code_hash = hashlib.sha256(raw_code.encode()).hexdigest()[:16]
        
        # 格式化为用户友好的格式
        formatted_code = '-'.join([code_hash[i:i+4] for i in range(0, 16, 4)]).upper()
        
        return formatted_code


class SecurityValidator:
    """安全验证器"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        验证IP地址格式
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否有效
        """
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def detect_suspicious_pattern(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测可疑模式
        
        Args:
            data: 要检测的数据
            
        Returns:
            Dict[str, Any]: 检测结果
        """
        suspicious_indicators = []
        risk_score = 0
        
        # 检查频率异常
        if 'request_frequency' in data:
            frequency = data['request_frequency']
            if frequency > 100:  # 每分钟超过100次请求
                suspicious_indicators.append('高频请求')
                risk_score += 30
        
        # 检查地理位置异常
        if 'location_change' in data:
            if data['location_change']:
                suspicious_indicators.append('地理位置异常变化')
                risk_score += 20
        
        # 检查硬件指纹变化
        if 'fingerprint_change_rate' in data:
            change_rate = data['fingerprint_change_rate']
            if change_rate > 0.3:  # 30%以上的硬件特征发生变化
                suspicious_indicators.append('硬件指纹大幅变化')
                risk_score += 25
        
        # 检查激活时间模式
        if 'activation_time_pattern' in data:
            pattern = data['activation_time_pattern']
            if pattern == 'batch':  # 批量激活模式
                suspicious_indicators.append('批量激活模式')
                risk_score += 15
        
        # 确定风险等级
        if risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 25:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'suspicious_indicators': suspicious_indicators,
            'recommendation': SecurityValidator._get_security_recommendation(risk_level)
        }
    
    @staticmethod
    def _get_security_recommendation(risk_level: str) -> str:
        """获取安全建议"""
        recommendations = {
            'HIGH': '立即暂停许可证并进行人工审核',
            'MEDIUM': '加强监控并要求额外验证',
            'LOW': '继续正常监控'
        }
        return recommendations.get(risk_level, '未知风险级别')


# 单例模式的安全服务管理器
class SecurityService:
    """统一的安全服务管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not SecurityService._initialized:
            self.rsa_manager = RSASecurityManager()
            self.aes_manager = AESSecurityManager()
            self.hash_manager = HashManager()
            self.token_manager = SecurityTokenManager()
            self.validator = SecurityValidator()
            
            # 初始化日志
            self.logger = logging.getLogger('licenses.security')
            
            SecurityService._initialized = True
            self.logger.info("安全服务管理器初始化完成")
    
    def get_encryption_password(self, context: str = 'default') -> str:
        """
        获取加密密码
        
        Args:
            context: 上下文标识
            
        Returns:
            str: 加密密码
        """
        # 从Django settings或环境变量获取密码
        base_key = getattr(settings, 'SECRET_KEY', 'default-secret-key')
        return f"{base_key}:{context}"
