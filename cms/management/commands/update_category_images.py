"""
Django管理命令：使用ComfyUI更新分类封面图片
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

# 添加项目路径以导入模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from cms.models import Category
from cms.utils.comfyui_client import ComfyUIClient
from cms.utils.prompt_generator import PromptGenerator
from tenants.models import Tenant
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """使用ComfyUI更新分类图片的命令"""
    
    help = '使用ComfyUI根据分类名称生成并更新封面图片'
    
    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument(
            '--tenant-id',
            type=int,
            default=3,
            help='租户ID (默认: 3)'
        )
        
        parser.add_argument(
            '--comfyui-url',
            type=str,
            default='http://127.0.0.1:8188',
            help='ComfyUI服务器URL (默认: http://127.0.0.1:8188)'
        )
        
        parser.add_argument(
            '--width',
            type=int,
            default=670,
            help='图片宽度 (默认: 670)'
        )
        
        parser.add_argument(
            '--height',
            type=int,
            default=360,
            help='图片高度 (默认: 360)'
        )
        
        parser.add_argument(
            '--style',
            type=str,
            choices=['modern', 'tech', 'nature', 'business', 'creative', 'auto'],
            default='auto',
            help='图片风格 (默认: auto - 自动检测)'
        )
        
        parser.add_argument(
            '--concurrent',
            type=int,
            default=1,
            help='并发生成数量 (默认: 1，建议不超过3)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行，不实际生成和保存图片'
        )
        
        parser.add_argument(
            '--category-ids',
            type=str,
            help='指定要更新的分类ID，用逗号分隔 (例如: 10,11,12)'
        )
        
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='跳过已有封面图片的分类'
        )
        
        parser.add_argument(
            '--backup',
            action='store_true',
            help='备份原有图片'
        )
        
        parser.add_argument(
            '--language',
            type=str,
            default='zh-hans',
            choices=['zh-hans', 'en', 'zh-hant', 'ja', 'ko', 'fr'],
            help='使用哪种语言的分类名称作为提示词 (默认: zh-hans)'
        )
        
    def handle(self, *args, **options):
        """执行命令"""
        self.tenant_id = options['tenant_id']
        self.comfyui_url = options['comfyui_url']
        self.width = options['width']
        self.height = options['height']
        self.style = None if options['style'] == 'auto' else options['style']
        self.concurrent = options['concurrent']
        self.dry_run = options['dry_run']
        self.skip_existing = options['skip_existing']
        self.backup = options['backup']
        self.language = options['language']
        
        # 解析分类ID
        self.category_ids = None
        if options['category_ids']:
            try:
                self.category_ids = [int(id_str.strip()) for id_str in options['category_ids'].split(',')]
            except ValueError:
                raise CommandError("分类ID格式错误，应为逗号分隔的数字")
                
        # 初始化组件
        self.client = ComfyUIClient(self.comfyui_url)
        self.prompt_generator = PromptGenerator()
        self.media_root = Path(settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else 'media')
        self.category_image_dir = self.media_root / 'category_image'
        
        # 确保目录存在
        self.category_image_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果需要备份，创建备份目录
        if self.backup:
            self.backup_dir = self.category_image_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
        # 执行主流程
        try:
            print(f"\n开始更新租户 {self.tenant_id} 的分类图片")
            
            # 测试ComfyUI连接
            if not self.dry_run:
                if not self.client.test_connection():
                    raise CommandError(f"无法连接到ComfyUI服务器: {self.comfyui_url}")
                print("✓ ComfyUI服务器连接正常")
                
            # 获取分类数据
            categories = self.get_categories()
            if not categories:
                print("没有找到需要处理的分类")
                return
                
            print(f"找到 {len(categories)} 个分类需要处理")
            
            # 处理分类
            if self.concurrent > 1:
                self.process_categories_parallel(categories)
            else:
                self.process_categories_sequential(categories)
                
            print("\n✓ 所有分类图片更新完成")
            
        except Exception as e:
            print(f"\n✗ 错误: {str(e)}")
            raise CommandError(str(e))
            
    def get_categories(self) -> List[Tuple[int, str, str]]:
        """
        获取需要处理的分类
        
        Returns:
            分类列表，每个元素为(id, name, current_cover_image)元组
        """
        try:
            # 验证租户是否存在
            tenant = Tenant.objects.get(id=self.tenant_id)
            print(f"租户: {tenant.name}")
            
            # 查询分类
            queryset = Category.objects.filter(
                tenant_id=self.tenant_id,
                is_deleted=False
            )
            
            # 如果指定了分类ID，进行过滤
            if self.category_ids:
                queryset = queryset.filter(id__in=self.category_ids)
                
            # 如果跳过已有图片的分类
            if self.skip_existing:
                queryset = queryset.filter(cover_image__isnull=True) | queryset.filter(cover_image='')
                
            categories = []
            for category in queryset:
                # 设置语言获取翻译
                category.set_current_language(self.language, initialize=True)
                name = category.safe_translation_getter('name', any_language=True) or 'Unnamed'
                
                # 获取ID、名称和当前封面
                categories.append((
                    category.id,
                    name,
                    category.cover_image or ''
                ))
                
            return categories
            
        except Tenant.DoesNotExist:
            raise CommandError(f"租户 {self.tenant_id} 不存在")
        except Exception as e:
            raise CommandError(f"获取分类数据失败: {str(e)}")
            
    def process_categories_sequential(self, categories: List[Tuple[int, str, str]]):
        """
        顺序处理分类
        
        Args:
            categories: 分类列表
        """
        total = len(categories)
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for index, (cat_id, cat_name, current_cover) in enumerate(categories, 1):
            print(f"\n[{index}/{total}] 处理分类: {cat_name} (ID: {cat_id})")
            
            result = self.process_single_category(cat_id, cat_name, current_cover)
            
            if result == 'success':
                success_count += 1
                print(f"  ✓ 成功生成并保存图片")
            elif result == 'skip':
                skip_count += 1
                print(f"  ⊘ 跳过")
            else:
                fail_count += 1
                print(f"  ✗ 失败")
                
        # 输出统计
        print(f"\n处理完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  跳过: {skip_count}")
        
    def process_categories_parallel(self, categories: List[Tuple[int, str, str]]):
        """
        并行处理分类
        
        Args:
            categories: 分类列表
        """
        total = len(categories)
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        print(f"使用 {self.concurrent} 个并发任务处理...")
        
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            # 提交所有任务
            future_to_category = {
                executor.submit(self.process_single_category, cat_id, cat_name, current_cover): (cat_id, cat_name)
                for cat_id, cat_name, current_cover in categories
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_category):
                cat_id, cat_name = future_to_category[future]
                
                try:
                    result = future.result()
                    
                    if result == 'success':
                        success_count += 1
                        print(f"✓ {cat_name} (ID: {cat_id})")
                    elif result == 'skip':
                        skip_count += 1
                        print(f"⊘ {cat_name} (ID: {cat_id}) - 跳过")
                    else:
                        fail_count += 1
                        print(f"✗ {cat_name} (ID: {cat_id}) - 失败")
                        
                except Exception as e:
                    fail_count += 1
                    print(f"✗ {cat_name} (ID: {cat_id}) - 异常: {str(e)}")
                    
        # 输出统计
        print(f"\n处理完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  跳过: {skip_count}")
        
    def process_single_category(self, cat_id: int, cat_name: str, current_cover: str) -> str:
        """
        处理单个分类
        
        Args:
            cat_id: 分类ID
            cat_name: 分类名称
            current_cover: 当前封面路径
            
        Returns:
            处理结果: 'success', 'skip', 'fail'
        """
        try:
            # 如果是模拟运行
            if self.dry_run:
                prompt_data = self.prompt_generator.generate_prompt(cat_name, style=self.style)
                logger.info(f"[模拟] 分类 {cat_id}: {cat_name}")
                logger.info(f"[模拟] 主提示词: {prompt_data['main_prompt'][:100]}...")
                logger.info(f"[模拟] 风格: {prompt_data['style']}")
                return 'success'
                
            # 生成提示词
            prompt_data = self.prompt_generator.generate_prompt(cat_name, style=self.style)
            logger.info(f"分类 {cat_id} 使用风格: {prompt_data['style']}")
            
            # 生成图片（传递完整的提示词数据）
            image_data = self.client.generate_image(
                prompt=prompt_data,  # 传递整个字典，包含clip_l和t5xxl
                width=self.width,
                height=self.height
            )
            
            if not image_data:
                logger.error(f"分类 {cat_id} 生成图片失败")
                return 'fail'
                
            # 保存图片
            image_filename = f"{cat_id}.png"
            image_path = self.category_image_dir / image_filename
            
            # 如果需要备份且文件存在
            if self.backup and image_path.exists():
                backup_path = self.backup_dir / image_filename
                import shutil
                shutil.copy2(image_path, backup_path)
                logger.info(f"已备份原图片到: {backup_path}")
                
            # 保存新图片
            with open(image_path, 'wb') as f:
                f.write(image_data)
            logger.info(f"保存图片到: {image_path}")
            
            # 更新数据库
            relative_path = f"category_image/{image_filename}"
            Category.objects.filter(id=cat_id).update(
                cover_image=relative_path,
                updated_at=datetime.now()
            )
            logger.info(f"更新数据库记录: cover_image={relative_path}")
            
            return 'success'
            
        except Exception as e:
            logger.error(f"处理分类 {cat_id} 时出错: {str(e)}")
            return 'fail'
            
    def backup_image(self, image_path: Path):
        """
        备份图片
        
        Args:
            image_path: 图片路径
        """
        if image_path.exists():
            backup_path = self.backup_dir / image_path.name
            import shutil
            shutil.copy2(image_path, backup_path)
            logger.info(f"备份图片: {backup_path}")
