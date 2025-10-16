"""
机器指纹服务模块
负责生成和验证机器硬件指纹
"""

import json
import hashlib
import platform
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger('licenses.fingerprint')


@dataclass
class MachineInfo:
    """机器信息数据类"""
    hardware_uuid: str
    cpu_info: Dict[str, Any]
    memory_info: Dict[str, Any]
    disk_info: Dict[str, Any]
    network_info: Dict[str, Any]
    system_info: Dict[str, Any]


class MachineFingerprintService:
    """机器指纹服务"""
    
    @staticmethod
    def collect_hardware_info() -> Dict[str, Any]:
        """
        收集硬件信息（模拟实现，实际需要客户端提供）
        
        Returns:
            Dict[str, Any]: 硬件信息字典
        """
        try:
            # 基本系统信息
            hardware_info = {
                'hardware_uuid': str(uuid.getnode()),  # MAC地址
                'cpu_info': {
                    'processor': platform.processor(),
                    'machine': platform.machine(),
                    'architecture': platform.architecture(),
                    # 实际实现中需要CPU序列号、型号等
                },
                'memory_info': {
                    'total': 16 * 1024 * 1024 * 1024,  # 16GB (模拟)
                    'available': 8 * 1024 * 1024 * 1024,  # 8GB (模拟)
                    # 实际实现中需要内存条序列号
                },
                'disk_info': {
                    'total': 512 * 1024 * 1024 * 1024,  # 512GB (模拟)
                    'serial': 'DISK001234567890',  # 硬盘序列号 (模拟)
                },
                'network_info': {
                    'interfaces': ['en0', 'lo0'],  # 网络接口
                    'mac_addresses': ['00:11:22:33:44:55'],  # MAC地址
                },
                'system_info': {
                    'os_version': platform.platform(),
                    'kernel_version': platform.release(),
                    'hostname': platform.node(),
                }
            }
            
            logger.debug("硬件信息收集完成")
            return hardware_info
            
        except Exception as e:
            logger.error(f"硬件信息收集失败: {str(e)}")
            raise Exception(f"硬件信息收集失败: {str(e)}")
    
    @staticmethod
    def generate_fingerprint(hardware_info: Dict[str, Any], salt: str = None) -> str:
        """
        生成机器指纹
        
        Args:
            hardware_info: 硬件信息
            salt: 盐值
            
        Returns:
            str: 机器指纹哈希值
        """
        try:
            # 1. 提取关键硬件特征
            key_features = []
            
            # CPU特征
            cpu_info = hardware_info.get('cpu_info', {})
            key_features.append(cpu_info.get('processor', ''))
            key_features.append(cpu_info.get('machine', ''))
            
            # 内存特征
            memory_info = hardware_info.get('memory_info', {})
            key_features.append(str(memory_info.get('total', 0)))
            
            # 磁盘特征
            disk_info = hardware_info.get('disk_info', {})
            key_features.append(disk_info.get('serial', ''))
            
            # 网络特征（MAC地址）
            network_info = hardware_info.get('network_info', {})
            mac_addresses = network_info.get('mac_addresses', [])
            key_features.append('|'.join(sorted(mac_addresses)))
            
            # 系统特征
            system_info = hardware_info.get('system_info', {})
            key_features.append(system_info.get('os_version', ''))
            
            # 2. 标准化处理
            normalized_features = []
            for feature in key_features:
                if feature:
                    normalized_features.append(str(feature).lower().strip())
            
            # 3. 生成指纹字符串
            fingerprint_data = '|'.join(normalized_features)
            
            # 4. 添加盐值（如果提供）
            if salt:
                fingerprint_data = f"{fingerprint_data}|{salt}"
            
            # 5. 生成SHA256哈希
            fingerprint = hashlib.sha256(fingerprint_data.encode('utf-8')).hexdigest()
            
            logger.debug(f"机器指纹生成成功: {fingerprint[:8]}...")
            return fingerprint
            
        except Exception as e:
            logger.error(f"机器指纹生成失败: {str(e)}")
            raise Exception(f"指纹生成失败: {str(e)}")
    
    @staticmethod
    def calculate_fingerprint_similarity(fingerprint1: str, fingerprint2: str) -> float:
        """
        计算两个机器指纹的相似度
        
        Args:
            fingerprint1: 第一个指纹
            fingerprint2: 第二个指纹
            
        Returns:
            float: 相似度 (0.0 - 1.0)
        """
        try:
            if fingerprint1 == fingerprint2:
                return 1.0
            
            # 使用Hamming距离计算相似度
            if len(fingerprint1) != len(fingerprint2):
                return 0.0
            
            matching_chars = sum(c1 == c2 for c1, c2 in zip(fingerprint1, fingerprint2))
            similarity = matching_chars / len(fingerprint1)
            
            logger.debug(f"指纹相似度计算: {similarity:.3f}")
            return similarity
            
        except Exception as e:
            logger.error(f"指纹相似度计算失败: {str(e)}")
            return 0.0
    
    @staticmethod
    def verify_fingerprint_match(
        stored_fingerprint: str, 
        current_fingerprint: str, 
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        验证机器指纹匹配
        
        Args:
            stored_fingerprint: 存储的指纹
            current_fingerprint: current指纹
            similarity_threshold: 相似度阈值
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            similarity = MachineFingerprintService.calculate_fingerprint_similarity(
                stored_fingerprint, current_fingerprint
            )
            
            is_match = similarity >= similarity_threshold
            
            result = {
                'is_match': is_match,
                'similarity': similarity,
                'threshold': similarity_threshold,
                'confidence': 'HIGH' if similarity > 0.95 else 'MEDIUM' if similarity > 0.8 else 'LOW'
            }
            
            if is_match:
                logger.info(f"机器指纹匹配成功，相似度: {similarity:.3f}")
            else:
                logger.warning(f"机器指纹匹配失败，相似度: {similarity:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"机器指纹验证失败: {str(e)}")
            return {
                'is_match': False,
                'similarity': 0.0,
                'error': str(e)
            }
    
    @staticmethod
    def detect_hardware_changes(
        old_hardware_info: Dict[str, Any], 
        new_hardware_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检测硬件变化
        
        Args:
            old_hardware_info: 旧硬件信息
            new_hardware_info: 新硬件信息
            
        Returns:
            Dict[str, Any]: 变化检测结果
        """
        try:
            changes = []
            change_score = 0.0
            
            # 检查CPU变化
            old_cpu = old_hardware_info.get('cpu_info', {})
            new_cpu = new_hardware_info.get('cpu_info', {})
            if old_cpu.get('processor') != new_cpu.get('processor'):
                changes.append('CPU处理器变化')
                change_score += 0.3
            
            # 检查内存变化
            old_memory = old_hardware_info.get('memory_info', {})
            new_memory = new_hardware_info.get('memory_info', {})
            memory_change = abs(
                old_memory.get('total', 0) - new_memory.get('total', 0)
            ) / max(old_memory.get('total', 1), 1)
            if memory_change > 0.2:  # 内存变化超过20%
                changes.append('内存容量显著变化')
                change_score += 0.2
            
            # 检查磁盘变化
            old_disk = old_hardware_info.get('disk_info', {})
            new_disk = new_hardware_info.get('disk_info', {})
            if old_disk.get('serial') != new_disk.get('serial'):
                changes.append('主要存储设备变化')
                change_score += 0.4
            
            # 检查网络接口变化
            old_network = old_hardware_info.get('network_info', {})
            new_network = new_hardware_info.get('network_info', {})
            old_macs = set(old_network.get('mac_addresses', []))
            new_macs = set(new_network.get('mac_addresses', []))
            if old_macs != new_macs:
                changes.append('网络接口变化')
                change_score += 0.1
            
            # 检查系统信息变化
            old_system = old_hardware_info.get('system_info', {})
            new_system = new_hardware_info.get('system_info', {})
            if old_system.get('os_version') != new_system.get('os_version'):
                changes.append('操作系统版本变化')
                change_score += 0.1
            
            # 确定变化等级
            if change_score >= 0.5:
                change_level = 'MAJOR'
            elif change_score >= 0.2:
                change_level = 'MODERATE'
            elif change_score > 0:
                change_level = 'MINOR'
            else:
                change_level = 'NONE'
            
            result = {
                'change_level': change_level,
                'change_score': change_score,
                'changes': changes,
                'is_suspicious': change_score >= 0.4
            }
            
            logger.info(f"硬件变化检测完成，变化等级: {change_level}")
            return result
            
        except Exception as e:
            logger.error(f"硬件变化检测失败: {str(e)}")
            return {
                'change_level': 'ERROR',
                'error': str(e)
            }
    
    @staticmethod
    def generate_machine_id(hardware_info: Dict[str, Any]) -> str:
        """
        生成机器ID（用户友好的标识符）
        
        Args:
            hardware_info: 硬件信息
            
        Returns:
            str: 机器ID
        """
        try:
            # 使用主要硬件特征生成短ID
            system_info = hardware_info.get('system_info', {})
            hostname = system_info.get('hostname', 'unknown')
            
            # 使用硬件UUID的前8位
            hardware_uuid = hardware_info.get('hardware_uuid', '')
            uuid_part = hardware_uuid[-8:] if len(hardware_uuid) >= 8 else hardware_uuid
            
            # 组合生成机器ID
            machine_id = f"{hostname[:8]}-{uuid_part}".upper()
            
            logger.debug(f"机器ID生成: {machine_id}")
            return machine_id
            
        except Exception as e:
            logger.error(f"机器ID生成失败: {str(e)}")
            # 降级方案：使用随机ID
            import secrets
            return f"MACHINE-{secrets.token_hex(4).upper()}"
    
    @staticmethod
    def create_hardware_summary(hardware_info: Dict[str, Any]) -> Dict[str, str]:
        """
        创建硬件摘要信息
        
        Args:
            hardware_info: 详细硬件信息
            
        Returns:
            Dict[str, str]: 硬件摘要
        """
        try:
            cpu_info = hardware_info.get('cpu_info', {})
            memory_info = hardware_info.get('memory_info', {})
            system_info = hardware_info.get('system_info', {})
            
            # 格式化内存大小
            total_memory_gb = memory_info.get('total', 0) / (1024**3)
            
            summary = {
                'cpu': cpu_info.get('processor', 'Unknown CPU'),
                'memory': f"{total_memory_gb:.1f}GB",
                'os': system_info.get('os_version', 'Unknown OS'),
                'hostname': system_info.get('hostname', 'Unknown Host'),
            }
            
            logger.debug("硬件摘要创建完成")
            return summary
            
        except Exception as e:
            logger.error(f"硬件摘要创建失败: {str(e)}")
            return {
                'cpu': 'Unknown',
                'memory': 'Unknown',
                'os': 'Unknown',
                'hostname': 'Unknown'
            }


class FingerprintAnalyzer:
    """指纹分析器"""
    
    @staticmethod
    def analyze_binding_pattern(machine_bindings: list) -> Dict[str, Any]:
        """
        分析机器绑定模式
        
        Args:
            machine_bindings: 机器绑定列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            if not machine_bindings:
                return {'pattern': 'EMPTY', 'risk_level': 'LOW'}
            
            binding_count = len(machine_bindings)
            
            # 分析绑定时间模式
            timestamps = [binding.get('first_seen_at', 0) for binding in machine_bindings]
            timestamps.sort()
            
            # 检查是否为批量绑定
            if binding_count > 1:
                time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                avg_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0
                
                if avg_diff < 300:  # 5分钟内批量绑定
                    pattern = 'BATCH'
                    risk_level = 'HIGH'
                elif binding_count > 5:  # 超过5个绑定
                    pattern = 'EXCESSIVE'
                    risk_level = 'MEDIUM'
                else:
                    pattern = 'NORMAL'
                    risk_level = 'LOW'
            else:
                pattern = 'SINGLE'
                risk_level = 'LOW'
            
            return {
                'pattern': pattern,
                'risk_level': risk_level,
                'binding_count': binding_count,
                'recommendation': FingerprintAnalyzer._get_pattern_recommendation(pattern)
            }
            
        except Exception as e:
            logger.error(f"绑定模式分析失败: {str(e)}")
            return {'pattern': 'ERROR', 'risk_level': 'HIGH'}
    
    @staticmethod
    def _get_pattern_recommendation(pattern: str) -> str:
        """获取模式建议"""
        recommendations = {
            'BATCH': '检测到批量绑定，建议人工审核',
            'EXCESSIVE': '绑定设备过多，建议限制数量',
            'NORMAL': '正常绑定模式',
            'SINGLE': '单设备绑定，安全',
            'EMPTY': '无绑定记录'
        }
        return recommendations.get(pattern, '未知模式')
