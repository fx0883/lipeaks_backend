#!/bin/bash
# 修复Python环境架构问题

echo "================================================"
echo "Python环境架构修复脚本"
echo "================================================"
echo ""

# 检查当前架构
echo "检查当前Python架构..."
ARCH=$(python3 -c "import platform; print(platform.machine())")
echo "当前架构: $ARCH"

echo ""
echo "检查Python版本..."
python3 --version

echo ""
echo "================================================"
echo "修复方案1: 重新安装cryptography相关包"
echo "================================================"
echo ""

echo "卸载现有的cryptography和cffi..."
pip3 uninstall cryptography cffi -y

echo ""
echo "重新安装cryptography和cffi..."
pip3 install --upgrade pip
pip3 install cryptography cffi

echo ""
echo "验证安装..."
python3 -c "
try:
    import cryptography
    print('✅ cryptography安装成功')
except ImportError as e:
    print('❌ cryptography安装失败:', e)
"

echo ""
echo "================================================"
echo "测试Django启动"
echo "================================================"
echo ""

cd /Users/fengxuan/Documents/Github/lipeaks_backend

echo "尝试导入Django settings..."
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
print('✅ Django启动成功')
" 2>&1 | head -20

echo ""
echo "================================================"
echo "修复完成！请运行 ./run_migration.sh 执行数据库迁移"
echo "================================================"

