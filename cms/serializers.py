"""
CMS系统序列化器
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from users.serializers import UserSerializer
from tenants.serializers import TenantSerializer

from .models import (
    Article, Category, Tag, TagGroup, Comment, 
    ArticleCategory, ArticleTag, ArticleMeta,
    ArticleStatistics, ArticleVersion, Interaction,
    UserLevel, UserLevelRelation, AccessLog, OperationLog
)


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 
            'cover_image', 'created_at', 'updated_at', 'sort_order',
            'tenant', 'is_active', 'seo_title', 'seo_description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']


class TagGroupSerializer(serializers.ModelSerializer):
    """标签组序列化器"""
    
    class Meta:
        model = TagGroup
        fields = [
            'id', 'name', 'slug', 'description', 'created_at',
            'updated_at', 'is_active', 'tenant'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    
    group_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'description', 'group',
            'group_name', 'created_at', 'updated_at', 'color',
            'is_active', 'tenant'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
    
    def get_group_name(self, obj) -> str:
        return obj.group.name if obj.group else None


class ArticleMetaSerializer(serializers.ModelSerializer):
    """文章元数据序列化器"""
    
    class Meta:
        model = ArticleMeta
        fields = [
            'id', 'article', 'seo_title', 'seo_description', 'seo_keywords',
            'og_title', 'og_description', 'og_image', 'schema_markup',
            'canonical_url', 'robots', 'custom_meta', 'created_at', 
            'updated_at', 'tenant'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant', 'article']


class ArticleStatisticsSerializer(serializers.ModelSerializer):
    """文章统计序列化器"""
    
    class Meta:
        model = ArticleStatistics
        fields = [
            'id', 'article', 'views_count', 'unique_views_count', 'likes_count',
            'dislikes_count', 'comments_count', 'shares_count', 'bookmarks_count',
            'avg_reading_time', 'bounce_rate', 'last_updated_at', 'tenant'
        ]
        read_only_fields = ['id', 'last_updated_at', 'tenant']


class ArticleVersionSerializer(serializers.ModelSerializer):
    """文章版本序列化器"""
    
    editor_info = UserSerializer(source='editor', read_only=True)
    
    class Meta:
        model = ArticleVersion
        fields = [
            'id', 'article', 'title', 'content', 'content_type',
            'excerpt', 'editor', 'editor_info', 'version_number',
            'change_description', 'created_at', 'diff_data', 'tenant'
        ]
        read_only_fields = ['id', 'created_at', 'tenant', 'version_number']


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    
    user_info = UserSerializer(source='user', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'article', 'parent', 'user', 'user_info', 'guest_name',
            'guest_email', 'guest_website', 'content', 'status', 'ip_address',
            'user_agent', 'created_at', 'updated_at', 'is_pinned', 'likes_count',
            'tenant', 'replies_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ip_address', 'user_agent', 'tenant']
    
    def get_replies_count(self, obj) -> int:
        return obj.replies.count()
    
    def validate(self, data):
        """验证评论数据，确保用户信息或游客信息至少提供一项"""
        user = data.get('user')
        guest_name = data.get('guest_name')
        
        if not user and not guest_name:
            raise serializers.ValidationError(_("用户或游客名称至少提供一项"))
        
        return data


class SimpleCategorySerializer(serializers.ModelSerializer):
    """简化的分类序列化器，用于嵌套在文章序列化器中"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class SimpleTagSerializer(serializers.ModelSerializer):
    """简化的标签序列化器，用于嵌套在文章序列化器中"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color']


class ArticleListSerializer(serializers.ModelSerializer):
    """文章列表序列化器，用于返回文章列表，包含基本信息"""
    
    author_info = UserSerializer(source='author', read_only=True)
    categories = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author', 'author_info',
            'status', 'is_featured', 'is_pinned', 'cover_image',
            'published_at', 'categories', 'tags', 'comments_count',
            'likes_count', 'views_count'
        ]
    
    def get_categories(self, obj) -> list:
        """获取文章关联的分类"""
        categories = Category.objects.filter(
            article_categories__article=obj
        )
        return SimpleCategorySerializer(categories, many=True).data
    
    def get_tags(self, obj) -> list:
        """获取文章关联的标签"""
        tags = Tag.objects.filter(
            article_tags__article=obj
        )
        return SimpleTagSerializer(tags, many=True).data
    
    def get_comments_count(self, obj) -> int:
        """获取文章评论数"""
        try:
            return obj.statistics.comments_count
        except:
            return 0
    
    def get_likes_count(self, obj) -> int:
        """获取文章点赞数"""
        try:
            return obj.statistics.likes_count
        except:
            return 0
    
    def get_views_count(self, obj) -> int:
        """获取文章浏览数"""
        try:
            return obj.statistics.views_count
        except:
            return 0


class ArticleDetailSerializer(serializers.ModelSerializer):
    """文章详情序列化器，用于返回单篇文章详情，包含全部信息"""
    
    author_info = UserSerializer(source='author', read_only=True)
    categories = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    meta = ArticleMetaSerializer(read_only=True)
    stats = ArticleStatisticsSerializer(source='statistics', read_only=True)
    version_info = serializers.SerializerMethodField()
    tenant_info = TenantSerializer(source='tenant', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'content_type', 'excerpt',
            'author', 'author_info', 'status', 'is_featured', 'is_pinned',
            'allow_comment', 'visibility', 'password', 'created_at',
            'updated_at', 'published_at', 'cover_image', 'template',
            'sort_order', 'tenant', 'tenant_info', 'categories', 'tags',
            'meta', 'stats', 'version_info'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
    
    def get_categories(self, obj) -> list:
        """获取文章关联的分类"""
        categories = Category.objects.filter(
            article_categories__article=obj
        )
        return SimpleCategorySerializer(categories, many=True).data
    
    def get_tags(self, obj) -> list:
        """获取文章关联的标签"""
        tags = Tag.objects.filter(
            article_tags__article=obj
        )
        return SimpleTagSerializer(tags, many=True).data
    
    def get_version_info(self, obj) -> dict:
        """获取文章版本信息"""
        try:
            latest_version = obj.versions.order_by('-version_number').first()
            if latest_version:
                return {
                    'current_version': latest_version.version_number,
                    'last_updated_by': UserSerializer(latest_version.editor).data,
                    'last_updated_at': latest_version.created_at
                }
        except:
            pass
        return None


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """文章创建和更新序列化器"""
    
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    meta = ArticleMetaSerializer(required=False)
    change_description = serializers.CharField(required=False, write_only=True)
    create_new_version = serializers.BooleanField(default=True, write_only=True)
    publish_now = serializers.BooleanField(default=False, write_only=True)
    scheduled_publish_time = serializers.DateTimeField(required=False, write_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'content_type', 'excerpt',
            'status', 'is_featured', 'is_pinned', 'allow_comment',
            'visibility', 'password', 'cover_image', 'template',
            'sort_order', 'category_ids', 'tag_ids', 'meta',
            'change_description', 'create_new_version', 'publish_now',
            'scheduled_publish_time'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """验证文章数据"""
        # 验证分类和标签的存在性和权限
        category_ids = data.pop('category_ids', [])
        tag_ids = data.pop('tag_ids', [])
        tenant = self.context['request'].user.tenant
        
        if category_ids:
            for category_id in category_ids:
                try:
                    Category.objects.get(id=category_id, tenant=tenant)
                except Category.DoesNotExist:
                    raise serializers.ValidationError(_(f"分类ID {category_id} 不存在或无权限访问"))
        
        if tag_ids:
            for tag_id in tag_ids:
                try:
                    Tag.objects.get(id=tag_id, tenant=tenant)
                except Tag.DoesNotExist:
                    raise serializers.ValidationError(_(f"标签ID {tag_id} 不存在或无权限访问"))
        
        # 处理slug
        title = data.get('title')
        instance = getattr(self, 'instance', None)
        
        # 如果是更新且未提供标题，不需要重新生成slug
        if instance and not title:
            pass
        # 如果是创建或更新且提供了标题，生成新的slug
        elif title:
            slug = slugify(title)
            # 确保slug唯一
            i = 1
            original_slug = slug
            while Article.objects.filter(slug=slug).exclude(id=getattr(instance, 'id', None)).exists():
                slug = f"{original_slug}-{i}"
                i += 1
            data['slug'] = slug
        
        # 处理发布逻辑
        publish_now = data.pop('publish_now', False)
        scheduled_publish_time = data.pop('scheduled_publish_time', None)
        
        if publish_now:
            data['status'] = 'published'
            data['published_at'] = timezone.now()
        elif scheduled_publish_time:
            # 如果设置了计划发布时间，但时间已过，则立即发布
            if scheduled_publish_time <= timezone.now():
                data['status'] = 'published'
                data['published_at'] = timezone.now()
            else:
                # 设置状态为pending，等待定时任务发布
                data['status'] = 'pending'
                data['published_at'] = scheduled_publish_time
        
        # 为文章版本保存的数据
        self._category_ids = category_ids
        self._tag_ids = tag_ids
        self._change_description = data.pop('change_description', None)
        self._create_new_version = data.pop('create_new_version', True)
        
        return data
    
    def create(self, validated_data):
        """创建文章，并关联分类、标签和元数据"""
        meta_data = validated_data.pop('meta', None)
        tenant = self.context['request'].user.tenant
        validated_data['tenant'] = tenant
        
        # 如果没有指定作者，使用当前用户
        if 'author' not in validated_data:
            validated_data['author'] = self.context['request'].user
        
        # 创建文章
        article = super().create(validated_data)
        
        # 创建元数据
        if meta_data:
            ArticleMeta.objects.create(article=article, tenant=tenant, **meta_data)
        
        # 创建分类关联
        for category_id in self._category_ids:
            ArticleCategory.objects.create(
                article=article,
                category_id=category_id,
                tenant=tenant
            )
        
        # 创建标签关联
        for tag_id in self._tag_ids:
            ArticleTag.objects.create(
                article=article,
                tag_id=tag_id,
                tenant=tenant
            )
        
        # 创建初始版本
        ArticleVersion.objects.create(
            article=article,
            title=article.title,
            content=article.content,
            content_type=article.content_type,
            excerpt=article.excerpt,
            editor=validated_data['author'],
            version_number=1,
            change_description="初始版本",
            tenant=tenant
        )
        
        # 创建统计记录（使用get_or_create避免重复创建）
        ArticleStatistics.objects.get_or_create(
            article=article,
            defaults={'tenant': tenant}
        )
        
        return article
    
    def update(self, instance, validated_data):
        """更新文章，并更新关联的分类、标签和元数据"""
        meta_data = validated_data.pop('meta', None)
        tenant = self.context['request'].user.tenant
        
        # 更新前记录原始数据，用于版本控制
        old_title = instance.title
        old_content = instance.content
        old_content_type = instance.content_type
        old_excerpt = instance.excerpt
        
        # 更新文章
        article = super().update(instance, validated_data)
        
        # 更新元数据
        if meta_data:
            meta, created = ArticleMeta.objects.get_or_create(
                article=article,
                tenant=tenant,
                defaults=meta_data
            )
            if not created:
                for key, value in meta_data.items():
                    setattr(meta, key, value)
                meta.save()
        
        # 更新分类关联
        if hasattr(self, '_category_ids'):
            # 删除旧关联
            ArticleCategory.objects.filter(article=article).delete()
            # 创建新关联
            for category_id in self._category_ids:
                ArticleCategory.objects.create(
                    article=article,
                    category_id=category_id,
                    tenant=tenant
                )
        
        # 更新标签关联
        if hasattr(self, '_tag_ids'):
            # 删除旧关联
            ArticleTag.objects.filter(article=article).delete()
            # 创建新关联
            for tag_id in self._tag_ids:
                ArticleTag.objects.create(
                    article=article,
                    tag_id=tag_id,
                    tenant=tenant
                )
        
        # 创建新版本
        if hasattr(self, '_create_new_version') and self._create_new_version:
            # 检查是否有实质性变更
            if (old_title != article.title or 
                old_content != article.content or 
                old_content_type != article.content_type or 
                old_excerpt != article.excerpt):
                
                # 获取最新版本号
                latest_version = ArticleVersion.objects.filter(article=article).order_by('-version_number').first()
                new_version_number = latest_version.version_number + 1 if latest_version else 1
                
                # 创建新版本
                ArticleVersion.objects.create(
                    article=article,
                    title=article.title,
                    content=article.content,
                    content_type=article.content_type,
                    excerpt=article.excerpt,
                    editor=self.context['request'].user,
                    version_number=new_version_number,
                    change_description=getattr(self, '_change_description', None) or "更新文章",
                    tenant=tenant
                )
        
        return article


class InteractionSerializer(serializers.ModelSerializer):
    """用户互动序列化器"""
    
    class Meta:
        model = Interaction
        fields = [
            'id', 'user', 'article', 'type', 'created_at', 'updated_at',
            'ip_address', 'user_agent', 'extra_data', 'tenant'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ip_address', 'user_agent', 'tenant']
    
    def validate(self, data):
        """验证互动数据，确保用户和文章属于同一租户"""
        user = data.get('user')
        article = data.get('article')
        
        if user.tenant != article.tenant:
            raise serializers.ValidationError(_("用户和文章必须属于同一租户"))
        
        return data 