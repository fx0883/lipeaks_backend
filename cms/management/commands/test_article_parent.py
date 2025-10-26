# cms/management/commands/test_article_parent.py

from django.core.management.base import BaseCommand
from cms.models import Article
from users.models import User
from tenants.models import Tenant


class Command(BaseCommand):
    help = '测试 Article parent 字段功能'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始测试 Article parent 字段...'))
        self.stdout.write('')
        
        # 获取测试用的租户和用户
        try:
            tenant = Tenant.objects.first()
            user = User.objects.first()
            
            if not tenant or not user:
                self.stdout.write(self.style.ERROR('错误：找不到测试用的租户或用户'))
                return
            
            self.stdout.write(f'使用租户: {tenant.name}')
            self.stdout.write(f'使用用户: {user.username}')
            self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'错误：{e}'))
            return
        
        # 测试1：创建根文章
        self.stdout.write(self.style.SUCCESS('[测试1] 创建根文章'))
        try:
            root = Article.objects.create(
                title='Python 从入门到精通',
                slug='python-tutorial-series',
                content='本系列将带你学习 Python 编程',
                author=user,
                tenant=tenant,
                status='published',
                parent=None
            )
            self.stdout.write(f'[PASS] 创建根文章成功: {root.title} (ID: {root.id})')
            self.stdout.write(f'  - is_root(): {root.is_root()}')
            self.stdout.write(f'  - is_leaf(): {root.is_leaf()}')
            self.stdout.write(f'  - get_depth(): {root.get_depth()}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
            return
        
        self.stdout.write('')
        
        # 测试2：创建子文章（第1章）
        self.stdout.write(self.style.SUCCESS('[测试2] 创建子文章'))
        try:
            chapter1 = Article.objects.create(
                title='第1章：Python 基础',
                slug='python-tutorial-chapter-1',
                content='本章介绍 Python 基础知识',
                author=user,
                tenant=tenant,
                status='published',
                parent=root
            )
            self.stdout.write(f'[PASS] 创建子文章成功: {chapter1.title} (ID: {chapter1.id})')
            self.stdout.write(f'  - parent: {chapter1.parent.title if chapter1.parent else None}')
            self.stdout.write(f'  - parent_id: {chapter1.parent.id if chapter1.parent else None}')
            self.stdout.write(f'  - is_root(): {chapter1.is_root()}')
            self.stdout.write(f'  - get_depth(): {chapter1.get_depth()}')
            self.stdout.write(f'  - get_root(): {chapter1.get_root().title}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
            return
        
        self.stdout.write('')
        
        # 测试3：创建第2章
        self.stdout.write(self.style.SUCCESS('[测试3] 创建第2章（兄弟文章）'))
        try:
            chapter2 = Article.objects.create(
                title='第2章：数据类型',
                slug='python-tutorial-chapter-2',
                content='本章介绍 Python 数据类型',
                author=user,
                tenant=tenant,
                status='published',
                parent=root
            )
            self.stdout.write(f'[PASS] 创建第2章成功: {chapter2.title} (ID: {chapter2.id})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
            return
        
        self.stdout.write('')
        
        # 测试4：创建子章节（第1.1节）
        self.stdout.write(self.style.SUCCESS('[测试4] 创建子章节'))
        try:
            section1_1 = Article.objects.create(
                title='1.1 变量和常量',
                slug='python-tutorial-1-1',
                content='变量的定义和使用',
                author=user,
                tenant=tenant,
                status='published',
                parent=chapter1
            )
            self.stdout.write(f'[PASS] 创建子章节成功: {section1_1.title} (ID: {section1_1.id})')
            self.stdout.write(f'  - parent: {section1_1.parent.title}')
            self.stdout.write(f'  - get_depth(): {section1_1.get_depth()}')
            self.stdout.write(f'  - get_root(): {section1_1.get_root().title}')
            self.stdout.write(f'  - ancestors: {[a.title for a in section1_1.get_ancestors()]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
            return
        
        self.stdout.write('')
        
        # 测试5：查询子文章
        self.stdout.write(self.style.SUCCESS('[测试5] 查询子文章'))
        try:
            children = root.children.all()
            self.stdout.write(f'[PASS] 根文章的子文章数量: {children.count()}')
            for child in children:
                self.stdout.write(f'  - {child.title} (ID: {child.id})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
        
        self.stdout.write('')
        
        # 测试6：获取兄弟文章
        self.stdout.write(self.style.SUCCESS('[测试6] 获取兄弟文章'))
        try:
            siblings = chapter1.get_siblings()
            self.stdout.write(f'[PASS] 第1章的兄弟文章数量: {siblings.count()}')
            for sibling in siblings:
                self.stdout.write(f'  - {sibling.title}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
        
        self.stdout.write('')
        
        # 测试7：叶子节点检测
        self.stdout.write(self.style.SUCCESS('[测试7] 叶子节点检测'))
        try:
            self.stdout.write(f'[PASS] 根文章是叶子? {root.is_leaf()}')
            self.stdout.write(f'[PASS] 第1章是叶子? {chapter1.is_leaf()}')
            self.stdout.write(f'[PASS] 1.1节是叶子? {section1_1.is_leaf()}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] {e}'))
        
        self.stdout.write('')
        
        # 测试8：循环引用保护
        self.stdout.write(self.style.SUCCESS('[测试8] 循环引用保护'))
        try:
            chapter1.parent = chapter1  # 尝试将自己设为父文章
            chapter1.save()
            self.stdout.write(self.style.ERROR('[FAIL] 应该阻止自己引用自己！'))
        except ValueError as e:
            self.stdout.write(f'[PASS] 正确阻止了循环引用: {e}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[FAIL] 未预期的错误: {e}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('所有测试完成！'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # 清理测试数据
        cleanup = input('\n是否删除测试数据？ (y/N): ')
        if cleanup.lower() == 'y':
            try:
                # 删除根文章会级联删除所有子文章
                root.delete()
                self.stdout.write(self.style.SUCCESS('测试数据已删除'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'删除失败: {e}'))
        else:
            self.stdout.write('测试数据保留')
            self.stdout.write(f'根文章ID: {root.id}')

