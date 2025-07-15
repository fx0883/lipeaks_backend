"""
CMS系统管理后台配置
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import (
    Article, 
    Category, 
    Tag, 
    TagGroup, 
    Comment, 
    ArticleCategory, 
    ArticleTag, 
    ArticleMeta,
    ArticleStatistics,
    ArticleVersion,
    Interaction,
    UserLevel,
    UserLevelRelation,
    AccessLog,
    OperationLog
)

class ArticleCategoryInline(admin.TabularInline):
    model = ArticleCategory
    extra = 1
    autocomplete_fields = ['category']

class ArticleTagInline(admin.TabularInline):
    model = ArticleTag
    extra = 1
    autocomplete_fields = ['tag']

class ArticleMetaInline(admin.StackedInline):
    model = ArticleMeta
    can_delete = False
    verbose_name_plural = _('文章元数据')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'is_featured', 'is_pinned', 'created_at', 'published_at', 'view_count', 'comment_count']
    list_filter = ['status', 'is_featured', 'is_pinned', 'created_at', 'published_at', 'tenant']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['tenant']
    date_hierarchy = 'created_at'
    inlines = [ArticleCategoryInline, ArticleTagInline, ArticleMetaInline]
    save_on_top = True
    list_per_page = 20
    
    def view_count(self, obj):
        try:
            return obj.statistics.views_count
        except:
            return 0
    view_count.short_description = _('浏览次数')
    
    def comment_count(self, obj):
        try:
            return obj.statistics.comments_count
        except:
            return 0
    comment_count.short_description = _('评论数')
    
    def save_model(self, request, obj, form, change):
        if not change:  # 如果是创建新对象
            obj.author = request.user  # 设置当前用户为作者
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author', 'tenant')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'article_count', 'created_at']
    list_filter = ['is_active', 'parent', 'tenant']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent', 'tenant']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 30
    
    def article_count(self, obj):
        return obj.article_categories.count()
    article_count.short_description = _('文章数')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'tenant')

@admin.register(TagGroup)
class TagGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'tag_count', 'created_at']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at']
    
    def tag_count(self, obj):
        return obj.tags.count()
    tag_count.short_description = _('标签数')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(tag_count=Count('tags'))

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'color', 'is_active', 'article_count', 'created_at']
    list_filter = ['is_active', 'group', 'tenant']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['group', 'tenant']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 30
    
    def article_count(self, obj):
        return obj.article_tags.count()
    article_count.short_description = _('文章数')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('group', 'tenant')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['get_content', 'article', 'user', 'guest_name', 'status', 'created_at', 'is_pinned']
    list_filter = ['status', 'is_pinned', 'created_at', 'tenant']
    search_fields = ['content', 'user__username', 'guest_name', 'article__title']
    raw_id_fields = ['article', 'user', 'parent']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    list_per_page = 30
    
    def get_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    get_content.short_description = _('评论内容')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'user', 'tenant')

@admin.register(ArticleMeta)
class ArticleMetaAdmin(admin.ModelAdmin):
    list_display = ['article', 'created_at', 'updated_at']
    search_fields = ['article__title', 'seo_title', 'seo_keywords']
    raw_id_fields = ['article']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'tenant')

@admin.register(ArticleStatistics)
class ArticleStatisticsAdmin(admin.ModelAdmin):
    list_display = ['article', 'views_count', 'likes_count', 'comments_count', 'bounce_rate', 'avg_reading_time']
    search_fields = ['article__title']
    raw_id_fields = ['article']
    autocomplete_fields = ['tenant']
    readonly_fields = ['last_updated_at']
    list_per_page = 20
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'tenant')

@admin.register(ArticleVersion)
class ArticleVersionAdmin(admin.ModelAdmin):
    list_display = ['article', 'version_number', 'editor', 'created_at']
    list_filter = ['created_at', 'tenant']
    search_fields = ['article__title', 'change_description']
    raw_id_fields = ['article', 'editor']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at']
    list_per_page = 20
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'editor', 'tenant')

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'type', 'created_at', 'ip_address']
    list_filter = ['type', 'created_at', 'tenant']
    search_fields = ['user__username', 'article__title', 'ip_address']
    raw_id_fields = ['user', 'article']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    list_per_page = 30
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'article', 'tenant')

@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'is_default', 'max_articles', 'max_storage_mb']
    list_filter = ['is_default', 'tenant']
    search_fields = ['name', 'description']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant')

@admin.register(UserLevelRelation)
class UserLevelRelationAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'start_time', 'end_time']
    list_filter = ['start_time', 'end_time', 'tenant']
    search_fields = ['user__username', 'level__name']
    raw_id_fields = ['user', 'level']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'level', 'tenant')

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'ip_address', 'created_at', 'reading_time', 'country']
    list_filter = ['created_at', 'country', 'device', 'browser', 'tenant']
    search_fields = ['article__title', 'user__username', 'ip_address', 'referer']
    raw_id_fields = ['article', 'user']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at']
    list_per_page = 30
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'user', 'tenant')

@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'entity_type', 'entity_id', 'created_at', 'ip_address']
    list_filter = ['action', 'entity_type', 'created_at', 'tenant']
    search_fields = ['user__username', 'details', 'ip_address']
    raw_id_fields = ['user']
    autocomplete_fields = ['tenant']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    list_per_page = 30
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'tenant')

# 为多对多关系表注册简单的管理界面
@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['article', 'category', 'created_at']
    list_filter = ['category', 'tenant']
    search_fields = ['article__title', 'category__name']
    raw_id_fields = ['article', 'category']
    autocomplete_fields = ['tenant']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'category', 'tenant')

@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ['article', 'tag', 'created_at']
    list_filter = ['tag', 'tenant']
    search_fields = ['article__title', 'tag__name']
    raw_id_fields = ['article', 'tag']
    autocomplete_fields = ['tenant']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('article', 'tag', 'tenant')
