"""
打卡系统序列化器

租户隔离架构：
- TaskCategory/TaskTemplate: 由租户管理员管理，无 member 字段
- Task/CheckRecord/CheckinCycle: 关联到 Member
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import TaskCategory, Task, CheckRecord, TaskTemplate, CheckinCycle


class TaskCategorySerializer(serializers.ModelSerializer):
    """
    打卡类型序列化器
    
    由租户管理员管理，Member 只读。
    """
    translated_name = serializers.SerializerMethodField()
    translated_description = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskCategory
        fields = [
            'id', 'name', 'description', 'is_system', 'icon',
            'color', 'goal', 'tip', 'quote', 'form_type', 'sort_order',
            'translations', 'created_at', 'updated_at', 
            'translated_name', 'translated_description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_translated_name(self, obj) -> str:
        """获取current语言的名称"""
        request = self.context.get('request')
        if request:
            language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
            return obj.get_translated_name(language)
        return obj.name
    
    def get_translated_description(self, obj) -> str:
        """获取current语言的描述"""
        request = self.context.get('request')
        if request:
            language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
            return obj.get_translated_description(language)
        return obj.description


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
        request = self.context.get('request')
        if request:
            language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
            return obj.get_translated_name(language)
        return obj.name
    
    def get_translated_description(self, obj) -> str:
        """获取current语言的描述"""
        request = self.context.get('request')
        if request:
            language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
            return obj.get_translated_description(language)
        return obj.description
    
    def get_category_name(self, obj) -> str:
        """获取类型名称"""
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
                return obj.category.get_translated_name(language)
            return obj.category.name
        return None


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
