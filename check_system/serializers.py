"""
打卡系统序列化器

租户隔离架构：
- TaskCategory/TaskTemplate: 由租户管理员管理，无 member 字段
- Task/CheckRecord/CheckinCycle: 关联到 Member
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import TaskCategory, Task, CheckRecord, TaskTemplate, CheckinCycle


def normalize_language_code(request):
    """
    从请求中获取并标准化语言代码
    """
    if not request:
        return 'zh-hans'
        
    accept_language = request.headers.get('Accept-Language', '')
    if not accept_language:
        return 'zh-hans'
        
    # 获取主语言代码 (e.g. "zh-CN,zh;q=0.9" -> "zh-cn")
    lang_code = accept_language.split(',')[0].strip().lower()
    
    # 映射常见变体到内部key
    if lang_code in ['zh-cn', 'zh-sg', 'zh']:
        return 'zh-hans'
    elif lang_code in ['zh-tw', 'zh-hk', 'zh-mo']:
        return 'zh-hant'
    elif lang_code.startswith('en'):
        return 'en'
        
    return lang_code


from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField

class TaskCategorySerializer(TranslatableModelSerializer):
    """
    打卡类型序列化器
    
    API Response Schema:
    - translations: 包含所有语言的翻译（仅Admin可见）
    - name, description, etc: 当前语言的翻译（通过Accept-Language自动选择）
    - is_system, etc: 元数据（仅Admin可见）
    """
    translations = TranslatedFieldsField(shared_model=TaskCategory)
    
    class Meta:
        model = TaskCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color', 
            'goal', 'tip', 'quote', 'translations',
            'is_system', 'form_type', 'sort_order', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """
        根据用户角色定制返回字段
        1. 自动根据 Accept-Language 返回对应语言的 name/description 等
        2. Admin: 返回完整信息（包括 translations 字段）
        3. Member: 隐藏 translations, is_system, created_at, updated_at 等管理字段
        """
        # 获取当前语言
        current_language = self.context.get('request').META.get('HTTP_ACCEPT_LANGUAGE', 'zh-hans').split(',')[0].strip().lower()
        
        # 简单映射常见语言代码，parler会自动处理备选语言
        if 'zh' in current_language:
            if 'tw' in current_language or 'hk' in current_language or 'hant' in current_language:
                current_language = 'zh-hant'
            else:
                current_language = 'zh-hans'
        elif current_language.startswith('en'):
            current_language = 'en'
        elif current_language.startswith('ja'):
            current_language = 'ja'
        elif current_language.startswith('ko'):
            current_language = 'ko'
        elif current_language.startswith('fr'):
            current_language = 'fr'
        else:
            current_language = 'zh-hans'
            
        # 设置实例的当前语言，确保序列化时读取正确的翻译
        instance.set_current_language(current_language, initialize=True)
            
        # 调用父类方法获取基本数据（此时 name 等字段已经是翻译后的值了）
        data = super().to_representation(instance)
        
        # Parler的getter如果找不到当前语言，会根据fallback配置找备用语言
        # 确保字段存在
        for field in ['name', 'description', 'goal', 'tip', 'quote']:
            if field not in data or data[field] is None:
                data[field] = instance.safe_translation_getter(field, default='')

        request = self.context.get('request')
        is_staff = request and hasattr(request.user, 'is_staff') and request.user.is_staff

        if not is_staff:
            # Member: 移除管理字段和完整翻译包
            fields_to_remove = ['translations', 'is_system', 'created_at', 'updated_at']
            for field in fields_to_remove:
                data.pop(field, None)
                
        return data



class TaskSerializer(serializers.ModelSerializer):
    """
    打卡任务序列化器
    
    关联到 Member，Member 可以 CRUD 自己的任务。
    """
    category_name = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'member', 'member_name', 'start_date', 'end_date', 'status',
            'reminder', 'reminder_time', 'frequency_type', 'frequency_days', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member']
    
    def get_category_name(self, obj) -> str:
        """获取类型名称"""
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
                return obj.category.get_translated_name(language)
            return obj.category.name
        return None
    
    def get_member_name(self, obj) -> str:
        """获取成员名称"""
        return obj.member.username if obj.member else None


class CheckRecordSerializer(serializers.ModelSerializer):
    """
    打卡记录序列化器
    
    关联到 Member，支持两种打卡方式：
    1. 关联 Task（任务型打卡）
    2. 关联 Theme（21天主题打卡）
    """
    task_name = serializers.SerializerMethodField()
    theme_name = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckRecord
        fields = [
            'id', 'task', 'task_name', 'theme', 'theme_name',
            'member', 'member_name', 'check_date', 'check_time', 
            'remarks', 'comment', 'completion_time', 'extra_data', 
            'delayed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member']
    
    def get_task_name(self, obj) -> str:
        """获取任务名称"""
        return obj.task.name if obj.task else None
    
    def get_theme_name(self, obj) -> str:
        """获取主题名称"""
        return obj.theme.name if obj.theme else None
    
    def get_member_name(self, obj) -> str:
        """获取成员名称"""
        return obj.member.username if obj.member else None
    
    def validate(self, data):
        """验证同一成员同一主题/任务在同一天只能打卡一次"""
        # 从 context 获取 member（由 view 设置）
        request = self.context.get('request')
        member = request.user if request else data.get('member')
        
        task = data.get('task')
        theme = data.get('theme')
        check_date = data.get('check_date')
        
        instance = self.instance
        if instance is None:  # 创建操作
            # 检查任务重复
            if task and CheckRecord.objects.filter(
                member=member, task=task, check_date=check_date
            ).exists():
                raise serializers.ValidationError(
                    _("您今天已经为该任务打过卡了")
                )
            # 检查主题重复（21天打卡用）
            if theme and CheckRecord.objects.filter(
                member=member, theme=theme, check_date=check_date
            ).exists():
                raise serializers.ValidationError(
                    _("您今天已经为该主题打过卡了")
                )
        
        return data


class TaskTemplateSerializer(serializers.ModelSerializer):
    """
    任务模板序列化器
    
    由租户管理员管理，Member 只读。
    """
    translated_name = serializers.SerializerMethodField()
    translated_description = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'is_system', 'translations', 'reminder', 'reminder_time', 
            'created_at', 'updated_at', 'translated_name', 'translated_description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_translated_name(self, obj) -> str:
        """获取current语言的名称"""
        language = normalize_language_code(self.context.get('request'))
        return obj.get_translated_name(language)
    
    def get_translated_description(self, obj) -> str:
        """获取current语言的描述"""
        language = normalize_language_code(self.context.get('request'))
        return obj.get_translated_description(language)
    
    def get_category_name(self, obj) -> str:
        """获取类型名称"""
        if obj.category:
            language = normalize_language_code(self.context.get('request'))
            return obj.category.get_translated_name(language)
        return None
        
    def to_representation(self, instance):
        """
        根据用户身份处理返回字段
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # 如果不是管理员，移除 translations 字段
        if request and hasattr(request.user, 'is_staff') and not request.user.is_staff:
            data.pop('translations', None)
            data.pop('is_system', None)
            data.pop('created_at', None)
            data.pop('updated_at', None)
            
        return data


class CheckinCycleSerializer(serializers.ModelSerializer):
    """
    打卡周期序列化器（21天自律打卡）
    
    关联到 Member。
    """
    current_day = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    themes = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckinCycle
        fields = [
            'id', 'member', 'member_name', 'start_date', 'end_date',
            'selected_themes', 'is_active', 'current_day', 'progress',
            'themes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'end_date', 'current_day', 'progress', 'created_at', 'updated_at', 'member']
    
    def get_current_day(self, obj) -> int:
        """获取当前是周期的第几天"""
        return obj.get_current_day()
    
    def get_progress(self, obj) -> int:
        """获取周期进度百分比"""
        return obj.get_progress()
    
    def get_themes(self, obj) -> list:
        """获取选中主题的详细信息"""
        if not obj.selected_themes:
            return []
        themes = TaskCategory.objects.filter(id__in=obj.selected_themes, is_system=True)
        return TaskCategorySerializer(themes, many=True, context=self.context).data
    
    def get_member_name(self, obj) -> str:
        """获取成员名称"""
        return obj.member.username if obj.member else None
