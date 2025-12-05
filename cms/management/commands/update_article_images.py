"""
更新文章封面图片管理命令
使用ComfyUI自动生成文章封面图片
"""
import os
import logging
from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection

from cms.utils.comfyui_client import ComfyUIClient
from cms.utils.article_prompt_generator import ArticlePromptGenerator

# 配置日志
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '为文章自动生成封面图片'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            default=1,
            help='租户ID (默认: 1)'
        )
        parser.add_argument(
            '--article-ids',
            type=str,
            help='指定文章ID，多个ID用逗号分隔，例如: 586,587,588'
        )
        parser.add_argument(
            '--comfyui-url',
            type=str,
            default='http://127.0.0.1:8188',
            help='ComfyUI服务器地址 (默认: http://127.0.0.1:8188)'
        )
        parser.add_argument(
            '--width',
            type=int,
            default=382,
            help='图片宽度 (默认: 382)'
        )
        parser.add_argument(
            '--height',
            type=int,
            default=256,
            help='图片高度 (默认: 256)'
        )
        parser.add_argument(
            '--concurrent',
            type=int,
            default=1,
            help='并发处理数量 (默认: 1，建议根据GPU显存调整)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行，不实际生成图片'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='跳过已有封面的文章'
        )

    def handle(self, *args, **options):
        self.tenant_id = options['tenant_id']
        self.article_ids = options.get('article_ids')
        self.comfyui_url = options['comfyui_url']
        self.width = options['width']
        self.height = options['height']
        self.concurrent = options['concurrent']
        self.dry_run = options['dry_run']
        self.skip_existing = options['skip_existing']
        
        # 初始化目录
        self.article_image_dir = Path(settings.MEDIA_ROOT) / 'article_image'
        self.article_image_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化客户端
        self.client = ComfyUIClient(base_url=self.comfyui_url)
        self.prompt_generator = ArticlePromptGenerator()
        
        try:
            print(f"\n开始更新租户 {self.tenant_id} 的文章图片")
            
            # 测试ComfyUI连接
            if not self.dry_run:
                if not self.client.test_connection():
                    raise CommandError(f"无法连接到ComfyUI服务器: {self.comfyui_url}")
                print("✓ ComfyUI服务器连接正常")
            
            # 获取文章数据
            articles = self.get_articles()
            if not articles:
                print("没有找到需要处理的文章")
                return
            
            print(f"找到 {len(articles)} 篇文章需要处理")
            
            # 处理文章
            if self.concurrent > 1:
                self.process_articles_parallel(articles)
            else:
                self.process_articles_sequential(articles)
            
            print("\n✓ 所有文章图片更新完成")
            
        except Exception as e:
            print(f"\n✗ 错误: {str(e)}")
            raise CommandError(str(e))
    
    def get_articles(self) -> List[Tuple[int, str, str, str]]:
        """
        获取需要处理的文章列表
        
        Returns:
            文章列表，每个元素为 (id, title, excerpt, current_cover)
        """
        with connection.cursor() as cursor:
            # 获取租户信息
            cursor.execute('SELECT name FROM tenant WHERE id = %s', [self.tenant_id])
            tenant_row = cursor.fetchone()
            if not tenant_row:
                raise CommandError(f"找不到租户ID: {self.tenant_id}")
            
            print(f"租户: {tenant_row[0]}")
            
            # 构建查询条件
            conditions = ['tenant_id = %s', 'is_deleted = FALSE']
            params = [self.tenant_id]
            
            if self.article_ids:
                ids = [int(id.strip()) for id in self.article_ids.split(',')]
                placeholders = ','.join(['%s'] * len(ids))
                conditions.append(f'id IN ({placeholders})')
                params.extend(ids)
            
            if self.skip_existing:
                conditions.append("(cover_image IS NULL OR cover_image = '')")
            
            where_clause = ' AND '.join(conditions)
            
            # 查询文章
            query = f'''
                SELECT id, title, excerpt, cover_image
                FROM cms_article
                WHERE {where_clause}
                ORDER BY id
            '''
            
            cursor.execute(query, params)
            articles = cursor.fetchall()
            
            return articles
    
    def process_articles_sequential(self, articles: List[Tuple[int, str, str, str]]):
        """顺序处理文章"""
        total = len(articles)
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for index, (art_id, title, excerpt, current_cover) in enumerate(articles, 1):
            print(f"\n[{index}/{total}] 处理文章: {title[:50]} (ID: {art_id})")
            
            result = self.process_single_article(art_id, title, excerpt, current_cover)
            
            if result == 'success':
                success_count += 1
                print(f"  ✓ 成功生成并保存图片")
            elif result == 'skip':
                skip_count += 1
                print(f"  ⊘ 跳过")
            else:
                fail_count += 1
                print(f"  ✗ 失败")
        
        print(f"\n处理完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  跳过: {skip_count}")
    
    def process_articles_parallel(self, articles: List[Tuple[int, str, str, str]]):
        """并发处理文章"""
        print(f"使用 {self.concurrent} 个并发任务处理...")
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            futures = {
                executor.submit(
                    self.process_single_article,
                    art_id, title, excerpt, current_cover
                ): (art_id, title)
                for art_id, title, excerpt, current_cover in articles
            }
            
            for future in as_completed(futures):
                art_id, title = futures[future]
                try:
                    result = future.result()
                    if result == 'success':
                        success_count += 1
                        print(f"✓ {title[:50]} (ID: {art_id})")
                    elif result == 'skip':
                        skip_count += 1
                        print(f"⊘ {title[:50]} (ID: {art_id}) - 跳过")
                    else:
                        fail_count += 1
                        print(f"✗ {title[:50]} (ID: {art_id}) - 失败")
                except Exception as e:
                    fail_count += 1
                    print(f"✗ {title[:50]} (ID: {art_id}) - 异常: {str(e)}")
        
        print(f"\n处理完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  跳过: {skip_count}")
    
    def process_single_article(self, art_id: int, title: str, excerpt: str, current_cover: str) -> str:
        """
        处理单篇文章
        
        Args:
            art_id: 文章ID
            title: 文章标题
            excerpt: 文章摘要
            current_cover: 当前封面路径
        
        Returns:
            'success', 'fail', 或 'skip'
        """
        try:
            # 模拟模式
            if self.dry_run:
                prompt_data = self.prompt_generator.generate_prompt(title, excerpt, article_id=art_id)
                logger.info(f"[模拟] 文章 {art_id}: {title}")
                logger.info(f"[模拟] 主提示词: {prompt_data['main_prompt'][:100]}...")
                logger.info(f"[模拟] 风格: {prompt_data['style']}")
                return 'success'
            
            # 生成提示词（传入article_id确保每篇文章风格不同）
            prompt_data = self.prompt_generator.generate_prompt(title, excerpt, article_id=art_id)
            logger.info(f"文章 {art_id} 使用风格: {prompt_data['style']}")
            
            # 生成图片
            image_data = self.client.generate_image(
                prompt=prompt_data,
                width=self.width,
                height=self.height
            )
            
            if not image_data:
                logger.error(f"文章 {art_id} 生成图片失败")
                return 'fail'
            
            # 保存图片
            image_filename = f"{art_id}.png"
            image_path = self.article_image_dir / image_filename
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"保存图片到: {image_path}")
            
            # 更新数据库
            relative_path = f"article_image/{image_filename}"
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    UPDATE cms_article 
                    SET cover_image = %s, updated_at = NOW()
                    WHERE id = %s
                    ''',
                    [relative_path, art_id]
                )
            
            logger.info(f"更新数据库记录: cover_image={relative_path}")
            
            return 'success'
            
        except Exception as e:
            logger.error(f"处理文章 {art_id} 时出错: {str(e)}", exc_info=True)
            return 'fail'
