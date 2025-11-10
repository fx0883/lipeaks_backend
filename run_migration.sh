#!/bin/bash
# Article模型迁移脚本 - GenericForeignKey替换为双外键

echo "================================================"
echo "Article模型迁移：GenericForeignKey -> 双外键"
echo "================================================"
echo ""

# 检查Python环境
echo "检查Python环境..."
python3 --version

echo ""
echo "步骤1: 显示当前迁移状态"
python3 manage.py showmigrations cms

echo ""
echo "步骤2: 应用迁移"
python3 manage.py migrate cms

echo ""
echo "步骤3: 验证迁移完成"
python3 manage.py showmigrations cms

echo ""
echo "步骤4: 测试模型导入"
python3 -c "
from cms.models import Article
print('✅ Article模型导入成功')
print(f'Article模型字段: user, member')

# 检查第一篇文章
article = Article.objects.first()
if article:
    print(f'✅ 示例文章: {article.title}')
    print(f'   作者类型: {article.author_type}')
    print(f'   作者: {article.author_username}')
else:
    print('⚠️  数据库中暂无文章')
"

echo ""
echo "================================================"
echo "迁移完成！"
echo "================================================"

