#!/usr/bin/env python
"""
更新MySQL配置文件，添加时区设置
"""

import os
import sys
import re
import logging
import shutil
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_mysql_config():
    """查找MySQL配置文件位置"""
    # 常见的MySQL配置文件位置
    possible_locations = [
        # Windows
        r'C:\ProgramData\MySQL\MySQL Server 8.0\my.ini',
        r'C:\ProgramData\MySQL\MySQL Server 5.7\my.ini',
        # Linux
        '/etc/mysql/my.cnf',
        '/etc/my.cnf',
        # macOS
        '/usr/local/etc/my.cnf',
        '/etc/my.cnf',
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            logger.info(f"找到MySQL配置文件: {location}")
            return location
    
    logger.error("未找到MySQL配置文件")
    return None

def update_config(config_path):
    """更新MySQL配置文件，添加时区设置"""
    if not config_path:
        return False
    
    # 备份原始配置文件
    backup_path = f"{config_path}.bak"
    try:
        shutil.copy2(config_path, backup_path)
        logger.info(f"已备份原始配置文件到: {backup_path}")
    except Exception as e:
        logger.error(f"备份配置文件失败: {e}")
        return False
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return False
    
    # 检查是否已经有时区设置
    if re.search(r'default-time-zone\s*=', content):
        logger.info("配置文件中已存在时区设置")
        
        # 更新现有的时区设置
        updated_content = re.sub(
            r'(default-time-zone\s*=\s*)([\'"]?[^\'"\n]*[\'"]?)',
            r'\1"+08:00"',
            content
        )
    else:
        # 查找[mysqld]部分
        if '[mysqld]' in content:
            # 在[mysqld]部分添加时区设置
            updated_content = re.sub(
                r'(\[mysqld\][^\[]*)',
                r'\1\n# 设置默认时区为中国标准时间\ndefault-time-zone="+08:00"\n',
                content
            )
        else:
            # 如果没有[mysqld]部分，则添加
            updated_content = content + '\n\n[mysqld]\n# 设置默认时区为中国标准时间\ndefault-time-zone="+08:00"\n'
    
    # 写入更新后的配置
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        logger.info("已更新MySQL配置文件，添加时区设置")
    except Exception as e:
        logger.error(f"更新配置文件失败: {e}")
        # 恢复备份
        try:
            shutil.copy2(backup_path, config_path)
            logger.info("已恢复原始配置文件")
        except Exception as e2:
            logger.error(f"恢复配置文件失败: {e2}")
        return False
    
    return True

def main():
    logger.info("开始更新MySQL配置...")
    
    # 查找MySQL配置文件
    config_path = find_mysql_config()
    if not config_path:
        logger.error("无法找到MySQL配置文件，请手动更新配置")
        logger.info("请在MySQL配置文件的[mysqld]部分添加以下行:")
        logger.info("default-time-zone='+08:00'")
        return 1
    
    # 更新配置文件
    if update_config(config_path):
        logger.info("MySQL配置文件更新成功")
        logger.info("请重启MySQL服务以应用新的配置")
        logger.info("Windows: 在服务管理器中重启MySQL服务")
        logger.info("Linux: sudo systemctl restart mysql")
        logger.info("macOS: brew services restart mysql")
        return 0
    else:
        logger.error("更新MySQL配置文件失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 