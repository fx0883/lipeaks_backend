"""
CMS系统管理后台配置
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from parler.admin import TranslatableAdmin
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
from .admin_mixins import CMSAdminMixin

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
class ArticleAdmin(CMSAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'author_display', 'status', 'is_featured', 'is_pinned', 'created_at', 'published_at', 'view_count', 'comment_count']
    list_filter = ['status', 'is_featured', 'is_pinned', 'created_at', 'published_at', 'tenant']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'author_display']
    autocomplete_fields = ['tenant']
    date_hierarchy = 'created_at'
    inlines = [ArticleCategoryInline, ArticleTagInline, ArticleMetaInline]
    save_on_top = True
    list_per_page = 20
    
    # 自定义模板
    change_list_template = 'admin/cms/change_list.html'
    
    def author_display(self, obj):
        """显示作者信息"""
        if obj.author:
            author_type = "Member" if obj.is_author_member else "Admin"
            return f"{obj.author.username} ({author_type})"
        return "-"
    author_display.short_description = _('作者')
    
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
            # 设置current用户为作者（Admin后台只有User类型）
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'member', 'tenant')
    
    def has_add_permission(self, request):
        # 超级管理员可以添加任何租户的文章
        if request.user.is_superuser:
            return True
        # 普通用户需要有租户关联
        return hasattr(request.user, 'tenant') and request.user.tenant is not None
    
    def has_change_permission(self, request, obj=None):
        # 超级管理员可以修改任何租户的文章
        if request.user.is_superuser:
            return True
        # 普通用户只能修改其租户的文章
        if obj and hasattr(request.user, 'tenant') and request.user.tenant:
            return obj.tenant == request.user.tenant
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 超级管理员可以删除任何租户的文章
        if request.user.is_superuser:
            return True
        # 普通用户只能删除其租户的文章
        if obj and hasattr(request.user, 'tenant') and request.user.tenant:
            return obj.tenant == request.user.tenant
        return False

@admin.register(Category)
class CategoryAdmin(CMSAdminMixin, TranslatableAdmin, admin.ModelAdmin):
    """分类管理（支持多语言）"""
    list_display = ['name', 'slug', 'parent', 'is_active', 'translation_status', 'article_count', 'created_at']
    list_filter = ['is_active', 'parent', 'tenant']
    search_fields = ['translations__name', 'translations__description', 'slug']  # 搜索翻译字段
    autocomplete_fields = ['parent', 'tenant']
    readonly_fields = ['created_at', 'updated_at', 'show_all_translations']
    list_per_page = 30
    
    # parler配置 - 明确定义翻译字段在fieldsets中的位置
    fieldsets = (
        (_('基本信息'), {
            'fields': ('slug', 'parent', 'cover_image', 'tenant'),
            'description': '这些字段对所有语言共享，只需填写一次'
        }),
        (_('多语言内容'), {
            'fields': ('name', 'description', 'seo_title', 'seo_description'),
            'description': '这些字段支持多语言，请切换上方的语言标签分别填写不同语言的内容'
        }),
        (_('翻译状态'), {
            'fields': ('show_all_translations',),
            'classes': ('collapse',),
            'description': '查看当前分类的所有语言翻译情况'
        }),
        (_('显示设置'), {
            'fields': ('sort_order', 'is_active', 'is_pinned')
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def translation_status(self, obj):
        """显示翻译状态：哪些语言已翻译"""
        from django.utils.html import format_html
        
        translations = obj.translations.all()
        lang_codes = [t.language_code for t in translations]
        
        status_icons = []
        lang_map = {
            'zh-hans': ('简', '#4CAF50'),
            'en': ('EN', '#2196F3'),
            'zh-hant': ('繁', '#FF9800'),
            'ja': ('日', '#F44336'),
            'ko': ('한', '#9C27B0'),
            'fr': ('FR', '#3F51B5')
        }
        
        for code, (label, color) in lang_map.items():
            if code in lang_codes:
                status_icons.append(
                    f'<span style="background:{color};color:white;padding:2px 6px;border-radius:3px;margin:0 2px;font-size:11px;">{label}</span>'
                )
            else:
                status_icons.append(
                    f'<span style="background:#ccc;color:white;padding:2px 6px;border-radius:3px;margin:0 2px;font-size:11px;">{label}</span>'
                )
        
        return format_html(''.join(status_icons))
    
    translation_status.short_description = _('翻译状态')
    
    def show_all_translations(self, obj):
        """显示所有语言的翻译详情"""
        from django.utils.html import format_html
        
        if not obj.pk:
            return '保存后显示翻译信息'
        
        translations = obj.translations.all()
        if not translations:
            return format_html('<p style="color:#f44336;">暂无翻译数据</p>')
        
        html = '<table style="width:100%;border-collapse:collapse;margin-top:10px;">'
        html += '<tr style="background:#f5f5f5;"><th style="padding:8px;border:1px solid #ddd;">语言</th>'
        html += '<th style="padding:8px;border:1px solid #ddd;">名称</th>'
        html += '<th style="padding:8px;border:1px solid #ddd;">描述</th>'
        html += '<th style="padding:8px;border:1px solid #ddd;">SEO标题</th></tr>'
        
        lang_names = {
            'zh-hans': '简体中文',
            'en': 'English',
            'zh-hant': '繁体中文',
            'ja': '日本語',
            'ko': '한국어',
            'fr': 'Français'
        }
        
        for trans in translations:
            html += f'<tr><td style="padding:8px;border:1px solid #ddd;"><strong>{lang_names.get(trans.language_code, trans.language_code)}</strong></td>'
            html += f'<td style="padding:8px;border:1px solid #ddd;">{trans.name or "-"}</td>'
            html += f'<td style="padding:8px;border:1px solid #ddd;">{(trans.description[:50] + "...") if trans.description and len(trans.description) > 50 else (trans.description or "-")}</td>'
            html += f'<td style="padding:8px;border:1px solid #ddd;">{trans.seo_title or "-"}</td></tr>'
        
        html += '</table>'
        html += '<p style="margin-top:10px;color:#666;font-size:12px;">💡 提示：点击上方的语言标签可切换编辑不同语言的内容</p>'
        
        return format_html(html)
    
    show_all_translations.short_description = _('所有语言翻译')
    

    
    def article_count(self, obj):
        return obj.article_categories.count()
    article_count.short_description = _('文章数')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'tenant')
    
    def has_add_permission(self, request):
        # 超级管理员可以添加任何租户的类别
        if request.user.is_superuser:
            return True
        # 普通用户需要有租户关联
        return hasattr(request.user, 'tenant') and request.user.tenant is not None
    
    def has_change_permission(self, request, obj=None):
        # 超级管理员可以修改任何租户的类别
        if request.user.is_superuser:
            return True
        # 普通用户只能修改其租户的类别
        if obj and hasattr(request.user, 'tenant') and request.user.tenant:
            return obj.tenant == request.user.tenant
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 超级管理员可以删除任何租户的类别
        if request.user.is_superuser:
            return True
        # 普通用户只能删除其租户的类别
        if obj and hasattr(request.user, 'tenant') and request.user.tenant:
            return obj.tenant == request.user.tenant
        return False

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
class TagAdmin(CMSAdminMixin, admin.ModelAdmin):
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
class CommentAdmin(CMSAdminMixin, admin.ModelAdmin):
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
