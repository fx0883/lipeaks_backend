"""
打卡系统序列化器
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import TaskCategory, Task, CheckRecord, TaskTemplate


class TaskCategorySerializer(serializers.ModelSerializer):
    """打卡类型序列化器"""
    
    # 添加翻译字段的辅助字段，方便前端使用
    translated_name = serializers.SerializerMethodField()
    translated_description = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskCategory
        fields = [
            'id', 'name', 'description', 'is_system', 'icon', 
            'user', 'tenant', 'translations', 'created_at', 
            'updated_at', 'translated_name', 'translated_description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
    
    def get_translated_name(self, obj) -> str:
        """获取当前语言的名称"""
        request = self.context.get('request')
        language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
        return obj.get_translated_name(language)
    
    def get_translated_description(self, obj) -> str:
        """获取当前语言的描述"""
        request = self.context.get('request')
        language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
        return obj.get_translated_description(language)


class TaskSerializer(serializers.ModelSerializer):
    """打卡任务序列化器"""
    
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'user', 'tenant', 'start_date', 'end_date', 'status',
            'reminder', 'reminder_time', 'frequency_type', 'frequency_days', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
    
    def get_category_name(self, obj) -> str:
        """获取类型名称"""
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
                return obj.category.get_translated_name(language)
            return obj.category.name
        return None


class CheckRecordSerializer(serializers.ModelSerializer):
    """打卡记录序列化器"""
    
    task_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckRecord
        fields = [
            'id', 'task', 'task_name', 'user', 'check_date', 
            'check_time', 'remarks', 'comment', 'completion_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_task_name(self, obj) -> str:
        """获取任务名称"""
        return obj.task.name if obj.task else None
    
    def validate(self, data):
        """验证同一用户同一任务在同一天只能打卡一次"""
        user = data.get('user')
        task = data.get('task')
        check_date = data.get('check_date')
        
        # 如果是更新操作，排除当前记录
        instance = self.instance
        if instance is None:  # 创建操作
            if CheckRecord.objects.filter(
                user=user, task=task, check_date=check_date
            ).exists():
                print('[CheckRecordSerializer] 用户重复打卡校验未通过')
                raise serializers.ValidationError(
                    _("您今天已经为该任务打过卡了")
                )
        
        return data


class TaskTemplateSerializer(serializers.ModelSerializer):
    """任务模板序列化器"""
    
    translated_name = serializers.SerializerMethodField()
    translated_description = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'is_system', 'user', 'tenant', 'translations', 
            'reminder', 'reminder_time', 'created_at', 'updated_at', 
            'translated_name', 'translated_description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']
    
    def get_translated_name(self, obj) -> str:
        """获取当前语言的名称"""
        request = self.context.get('request')
        language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
        return obj.get_translated_name(language)
    
    def get_translated_description(self, obj) -> str:
        """获取当前语言的描述"""
        request = self.context.get('request')
        language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
        return obj.get_translated_description(language)
    
    def get_category_name(self, obj) -> str:
        """获取类型名称"""
        if obj.category:
            request = self.context.get('request')
            if request:
                language = request.headers.get('Accept-Language', 'zh-hans').split(',')[0]
                return obj.category.get_translated_name(language)
            return obj.category.name
        return None
