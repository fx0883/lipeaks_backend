"""
CMS系统序列化器
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from users.serializers import UserSerializer, MemberSerializer
from tenants.serializers import TenantSerializer
from common.utils.image_url import add_domain_to_image_url
from common.mixins import ImageFieldNormalizerMixin
from common.utils.user_permissions import is_member
from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField
from parler_rest.fields import TranslatedField

from .models import (
    Article, Category, Tag, TagGroup, Comment, 
    ArticleCategory, ArticleTag, ArticleMeta,
    ArticleStatistics, ArticleVersion,
    UserLevel, UserLevelRelation, AccessLog, OperationLog
)


class CategorySerializer(ImageFieldNormalizerMixin, TranslatableModelSerializer):
    """分类序列化器（支持多语言）"""
    translations = TranslatedFieldsField(shared_model=Category)
    image_fields = ['cover_image']  # 需要标准化的图片字段
    application_name = serializers.CharField(source='application.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'slug', 'parent', 'cover_image', 'created_at', 'updated_at', 
            'sort_order', 'tenant', 'application', 'application_name', 
            'is_active', 'is_pinned', 'is_admin_only',
            'translations',  # 包含所有语言的翻译
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant', 'application_name']
        extra_kwargs = {
            'slug': {'required': False}  # slug可选，系统自动生成
        }
    
    def validate(self, data):
        """验证并自动生成slug"""
        # 校验：Member 不能创建/修改管理员专属分类
        request = self.context.get('request')
        if request and is_member(request.user) and data.get('is_admin_only'):
            raise PermissionDenied(
                _('只有管理员可以创建管理员专属分类')
            )

        # 如果没有提供slug，从translations中提取name并生成slug
        if 'slug' not in data or not data['slug']:
            translations = data.get('translations', {})
            # 尝试从中文名称生成slug
            if 'zh-hans' in translations and 'name' in translations['zh-hans']:
                name = translations['zh-hans']['name']
                data['slug'] = slugify(name) or f"category-{timezone.now().timestamp()}"
            else:
                # 如果没有中文名称，使用时间戳生成唯一slug
                data['slug'] = f"category-{int(timezone.now().timestamp())}"

        return data
    
    def to_representation(self, instance):
        """
        自定义序列化输出，添加当前语言的字段（向后兼容）
        """
        data = super().to_representation(instance)
        
        # 获取当前语言的翻译，如果没有则使用默认语言
        current_language = self.context.get('request').META.get('HTTP_ACCEPT_LANGUAGE', 'zh-hans').split(',')[0].strip()
        if current_language not in ['zh-hans', 'en', 'zh-hant', 'ja', 'ko', 'fr']:
            current_language = 'zh-hans'
        
        # 尝试获取当前语言的翻译
        instance.set_current_language(current_language, initialize=True)
        
        # 添加单语言字段
        data['name'] = instance.safe_translation_getter('name', any_language=True) or ''
        data['description'] = instance.safe_translation_getter('description', any_language=True) or ''
        data['seo_title'] = instance.safe_translation_getter('seo_title', any_language=True) or ''
        data['seo_description'] = instance.safe_translation_getter('seo_description', any_language=True) or ''
        
        # 处理cover_image：为相对路径添加domain
        if data.get('cover_image'):
            request = self.context.get('request')
            if request:
                data['cover_image'] = add_domain_to_image_url(request, data['cover_image'])
        
        return data


class TagGroupSerializer(serializers.ModelSerializer):
    """标签组序列化器"""
    
    class Meta:
        model = TagGroup
        fields = [
            'id', 'name', 'slug', 'description', 'created_at',
            'updated_at', 'is_active', 'tenant'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
        extra_kwargs = {
            'slug': {'required': False}  # slug可选，系统自动生成
        }
    
    def validate(self, data):
        """验证并自动生成slug"""
        if 'slug' not in data or not data['slug']:
            name = data.get('name', '')
            if name:
                data['slug'] = slugify(name) or f"tag-group-{int(timezone.now().timestamp())}"
            else:
                data['slug'] = f"tag-group-{int(timezone.now().timestamp())}"
        return data


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
        extra_kwargs = {
            'slug': {'required': False}  # slug可选，系统自动生成
        }
    
    def validate(self, data):
        """验证并自动生成slug"""
        if 'slug' not in data or not data['slug']:
            name = data.get('name', '')
            if name:
                data['slug'] = slugify(name) or f"tag-{int(timezone.now().timestamp())}"
            else:
                data['slug'] = f"tag-{int(timezone.now().timestamp())}"
        return data
    
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
            'avg_reading_time', 'bounce_rate', 'updated_at', 'tenant'
        ]
        read_only_fields = ['id', 'updated_at', 'tenant']


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
    """
    评论序列化器
    支持三种评论者类型：管理员用户、普通成员、游客
    """
    
    author_info = serializers.SerializerMethodField()
    author_type = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'article', 'parent', 'user', 'member', 'author_info', 'author_type',
            'guest_name', 'guest_email', 'guest_website', 'content',
            'status', 'ip_address', 'user_agent', 'created_at', 'updated_at', 
            'is_pinned', 'likes_count', 'tenant', 'replies_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ip_address', 'user_agent', 'tenant']
    
    def get_author_info(self, obj) -> dict:
        """获取评论者信息（支持User、Member和游客）"""
        if obj.member_id:
            # Member评论者
            return MemberSerializer(obj.member, context=self.context).data
        elif obj.user_id:
            # User评论者
            return UserSerializer(obj.user, context=self.context).data
        elif obj.guest_name:
            # 游客评论
            return {
                'name': obj.guest_name,
                'email': obj.guest_email,
                'website': obj.guest_website,
                'type': 'guest'
            }
        return None
    
    def get_author_type(self, obj) -> str:
        """获取评论者类型"""
        return obj.author_type
    
    def get_replies_count(self, obj) -> int:
        return obj.replies.count()
    
    def validate(self, data):
        """验证评论数据"""
        # 已认证用户的评论会在perform_create中自动设置user或member字段
        # 游客评论需要验证guest_name
        guest_name = data.get('guest_name')
        user = data.get('user')
        member = data.get('member')
        
        # 验证至少有一种评论者类型
        if not user and not member and not guest_name:
            # 如果三个都没有，说明是已认证用户调用，会在perform_create中设置
            # 这里不报错，让perform_create处理
            pass
        
        # 如果提供了guest_name，验证格式
        if guest_name is not None:
            if not guest_name.strip():
                raise serializers.ValidationError(_("Guest name cannot be empty"))
        
        return data


class SimpleCategorySerializer(serializers.ModelSerializer):
    """简化的分类序列化器，用于嵌套在文章序列化器中"""
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
    
    def get_name(self, obj):
        """获取分类名称（自动处理多语言）"""
        return obj.safe_translation_getter('name', any_language=True) or obj.slug


class SimpleTagSerializer(serializers.ModelSerializer):
    """简化的标签序列化器，用于嵌套在文章序列化器中"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color']


class ArticleListSerializer(serializers.ModelSerializer):
    """文章列表序列化器，用于返回文章列表，包含基本信息"""
    
    author_info = serializers.SerializerMethodField()
    author_type = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    cover_image_small = serializers.SerializerMethodField()
    parent_info = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author_info', 'author_type',
            'status', 'is_featured', 'is_pinned', 'is_locked', 'cover_image', 'cover_image_small',
            'published_at', 'created_at', 'updated_at', 'categories', 'tags', 
            'comments_count', 'likes_count', 'views_count',
            'parent', 'parent_info', 'children_count'
        ]
    
    def get_author_info(self, obj) -> dict:
        """获取作者信息（支持User和Member）"""
        if obj.member_id:
            # Member作者
            return MemberSerializer(obj.member, context=self.context).data
        elif obj.user_id:
            # User作者
            return UserSerializer(obj.user, context=self.context).data
        return None
    
    def get_author_type(self, obj) -> str:
        """获取作者类型"""
        if obj.member_id:
            return 'member'
        elif obj.user_id:
            return 'admin'
        return None
    
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
    
    def get_cover_image(self, obj) -> str:
        """获取完整的封面图片URL"""
        if not obj.cover_image:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.cover_image)
        
        return obj.cover_image
    
    def get_cover_image_small(self, obj) -> str:
        """获取封面小图的完整URL"""
        if not obj.cover_image_small:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.cover_image_small)
        
        return obj.cover_image_small
    
    def get_parent_info(self, obj) -> dict:
        """获取父文章信息"""
        if obj.parent:
            return {
                'id': obj.parent.id,
                'title': obj.parent.title,
                'slug': obj.parent.slug
            }
        return None
    
    def get_children_count(self, obj) -> int:
        """获取子文章数量"""
        return obj.children.count()


class ArticleDetailSerializer(serializers.ModelSerializer):
    """文章详情序列化器，用于返回单篇文章详情，包含全部信息"""
    
    author_info = serializers.SerializerMethodField()
    author_type = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    meta = ArticleMetaSerializer(read_only=True)
    stats = ArticleStatisticsSerializer(source='statistics', read_only=True)
    version_info = serializers.SerializerMethodField()
    tenant_info = TenantSerializer(source='tenant', read_only=True)
    cover_image = serializers.SerializerMethodField()
    cover_image_small = serializers.SerializerMethodField()
    parent_info = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'content_type', 'excerpt',
            'author_info', 'author_type', 'status', 'is_featured', 'is_pinned',
            'is_locked', 'allow_comment', 'visibility', 'password', 'created_at',
            'updated_at', 'published_at', 'cover_image', 'cover_image_small', 'template',
            'sort_order', 'tenant', 'tenant_info', 'categories', 'tags',
            'meta', 'stats', 'version_info',
            'parent', 'parent_info', 'children', 'breadcrumb'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
    
    def get_author_info(self, obj) -> dict:
        """获取作者信息（支持User和Member）"""
        if obj.member_id:
            # Member作者
            return MemberSerializer(obj.member, context=self.context).data
        elif obj.user_id:
            # User作者
            return UserSerializer(obj.user, context=self.context).data
        return None
    
    def get_author_type(self, obj) -> str:
        """获取作者类型"""
        if obj.member_id:
            return 'member'
        elif obj.user_id:
            return 'admin'
        return None
    
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
                    'last_updated_by': UserSerializer(latest_version.editor, context=self.context).data,
                    'last_updated_at': latest_version.created_at
                }
        except:
            pass
        return None
    
    def get_cover_image(self, obj) -> str:
        """获取完整的封面图片URL"""
        if not obj.cover_image:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.cover_image)
        
        return obj.cover_image
    
    def get_cover_image_small(self, obj) -> str:
        """获取封面小图的完整URL"""
        if not obj.cover_image_small:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.cover_image_small)
        
        return obj.cover_image_small
    
    def get_parent_info(self, obj) -> dict:
        """获取父文章信息"""
        if obj.parent:
            return {
                'id': obj.parent.id,
                'title': obj.parent.title,
                'slug': obj.parent.slug
            }
        return None
    
    def get_children(self, obj) -> list:
        """获取子文章列表（简化版本）"""
        children = obj.children.filter(status='published').order_by('sort_order', 'created_at')[:20]
        return [{
            'id': child.id,
            'title': child.title,
            'slug': child.slug,
            'excerpt': child.excerpt,
            'published_at': child.published_at
        } for child in children]
    
    def get_breadcrumb(self, obj) -> list:
        """获取面包屑导航"""
        ancestors = obj.get_ancestors()
        breadcrumb = []
        
        # 从根到当前文章的路径（反转祖先列表）
        for ancestor in reversed(ancestors):
            breadcrumb.append({
                'id': ancestor.id,
                'title': ancestor.title,
                'slug': ancestor.slug
            })
        
        # 添加当前文章
        breadcrumb.append({
            'id': obj.id,
            'title': obj.title,
            'slug': obj.slug
        })
        
        return breadcrumb


class ArticleCreateUpdateSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
    """文章创建和更新序列化器"""
    image_fields = ['cover_image', 'cover_image_small']  # 需要标准化的图片字段
    
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
    applications = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,  # 在validate中根据创建/更新区分
        write_only=True,
        help_text="关联的应用ID列表，创建时必填"
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
            'status', 'is_featured', 'is_pinned', 'is_locked', 'allow_comment',
            'visibility', 'password', 'cover_image', 'cover_image_small', 'template',
            'sort_order', 'parent', 'category_ids', 'tag_ids', 'applications', 'meta',
            'change_description', 'create_new_version', 'publish_now',
            'scheduled_publish_time'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """验证文章数据"""
        # 验证分类、标签和应用的存在性和权限
        category_ids = data.pop('category_ids', [])
        tag_ids = data.pop('tag_ids', [])
        applications = data.pop('applications', None)
        tenant = self.context['request'].user.tenant
        instance = getattr(self, 'instance', None)
        
        # applications 为可选：允许文章不关联任何应用
        # 验证应用存在性（仅当提供了 applications 时）
        from applications.models import Application
        if applications:
            for app_id in applications:
                try:
                    Application.objects.get(id=app_id, tenant=tenant, is_deleted=False)
                except Application.DoesNotExist:
                    raise serializers.ValidationError(_(f"应用ID {app_id} 不存在或无权限访问"))
        
        if category_ids:
            for category_id in category_ids:
                try:
                    Category.objects.get(id=category_id, tenant=tenant)
                except Category.DoesNotExist:
                    raise serializers.ValidationError(_(f"分类ID {category_id} 不存在或无权限访问"))

            # 校验管理员专属分类：Member 不能在管理员专属分类下创建文章
            if is_member(self.context['request'].user):
                restricted_categories = Category.objects.filter(
                    id__in=category_ids,
                    tenant=tenant,
                    is_admin_only=True
                )
                if restricted_categories.exists():
                    restricted_names = []
                    for cat in restricted_categories:
                        name = cat.safe_translation_getter('name', any_language=True) or f"ID-{cat.id}"
                        restricted_names.append(name)
                    raise serializers.ValidationError(
                        _('分类 [{}] 是管理员专属分类，您无法在此分类下创建文章').format(
                            ', '.join(restricted_names)
                        )
                    )
        
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
        self._applications = applications
        self._change_description = data.pop('change_description', None)
        self._create_new_version = data.pop('create_new_version', True)
        
        return data
    
    def create(self, validated_data):
        """创建文章，并关联分类、标签和元数据"""
        meta_data = validated_data.pop('meta', None)
        tenant = self.context['request'].user.tenant
        validated_data['tenant'] = tenant
        
        # 如果没有指定作者，根据当前用户类型设置user或member
        current_user = self.context['request'].user
        from users.models import Member, User
        
        # 根据用户类型设置对应的外键字段
        if isinstance(current_user, Member):
            validated_data['member'] = current_user
        elif isinstance(current_user, User):
            validated_data['user'] = current_user
        
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
        
        # 创建应用关联
        if self._applications:
            from .models import ArticleApplication
            for app_id in self._applications:
                ArticleApplication.objects.create(
                    article=article,
                    application_id=app_id,
                    tenant=tenant
                )
        
        # 创建初始版本（仅支持User类型作为editor）
        if isinstance(current_user, User):
            ArticleVersion.objects.create(
                article=article,
                title=article.title,
                content=article.content,
                content_type=article.content_type,
                excerpt=article.excerpt,
                editor=current_user,
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
        
        # 更新应用关联
        if hasattr(self, '_applications') and self._applications is not None:
            from .models import ArticleApplication
            # 删除旧关联
            ArticleApplication.objects.filter(article=article).delete()
            # 创建新关联
            for app_id in self._applications:
                ArticleApplication.objects.create(
                    article=article,
                    application_id=app_id,
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
                
                # 创建新版本（仅支持User类型作为editor）
                from users.models import User
                current_user = self.context['request'].user
                if isinstance(current_user, User):
                    ArticleVersion.objects.create(
                        article=article,
                        title=article.title,
                        content=article.content,
                        content_type=article.content_type,
                        excerpt=article.excerpt,
                        editor=current_user,
                        version_number=new_version_number,
                        change_description=getattr(self, '_change_description', None) or "更新文章",
                        tenant=tenant
                    )
        
        return article


class MemberArticleCreateUpdateSerializer(ArticleCreateUpdateSerializer):
    """
    Member用户文章创建和更新序列化器
    
    与管理员版本的区别：
    - 使用单值 application 参数代替数组 applications
    - 简化前端调用
    """
    
    # 覆盖 applications 字段为单值 application
    application = serializers.IntegerField(
        required=False,  # 在validate中根据创建/更新区分
        write_only=True,
        help_text="关联的应用ID，创建时必填"
    )
    
    class Meta(ArticleCreateUpdateSerializer.Meta):
        fields = [
            'id', 'title', 'content', 'content_type', 'excerpt',
            'status', 'is_featured', 'is_pinned', 'is_locked', 'allow_comment',
            'visibility', 'password', 'cover_image', 'cover_image_small', 'template',
            'sort_order', 'parent', 'category_ids', 'tag_ids', 'application', 'meta',
            'change_description', 'create_new_version', 'publish_now',
            'scheduled_publish_time'
        ]
    
    def validate(self, data):
        """验证文章数据 - Member版本使用单值application"""
        # 提取 application 并转换为 applications 列表
        application = data.pop('application', None)
        
        # 将单值转换为列表，供父类处理
        if application is not None:
            data['applications'] = [application]
        
        # 调用父类验证
        return super().validate(data)