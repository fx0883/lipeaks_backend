"""
批量操作工具函数
提供高效的批量创建、更新和删除功能
"""
from django.db import transaction
from typing import List, Dict, Any, Type
from django.db.models import Model


def bulk_create_objects(model_class: Type[Model], objects_data: List[Dict[str, Any]], batch_size: int = 100):
    """
    批量创建对象
    
    Args:
        model_class: 模型类
        objects_data: 对象数据列表
        batch_size: 批次大小，默认100
        
    Returns:
        创建的对象列表
    """
    objects = [model_class(**data) for data in objects_data]
    return model_class.objects.bulk_create(objects, batch_size=batch_size)


def bulk_update_objects(objects: List[Model], fields: List[str], batch_size: int = 100):
    """
    批量更新对象
    
    Args:
        objects: 要更新的对象列表
        fields: 要更新的字段列表
        batch_size: 批次大小，默认100
        
    Returns:
        更新的对象数量
    """
    return model_class.objects.bulk_update(objects, fields, batch_size=batch_size)


def bulk_create_with_related(model_class: Type[Model], objects_data: List[Dict[str, Any]], 
                           related_data: Dict[str, List[Dict[str, Any]]] = None, batch_size: int = 100):
    """
    批量创建对象及其关联对象
    
    Args:
        model_class: 主模型类
        objects_data: 主对象数据列表
        related_data: 关联对象数据，格式为 {'related_field': [data_list]}
        batch_size: 批次大小，默认100
        
    Returns:
        创建的主对象列表
    """
    with transaction.atomic():
        # 批量创建主对象
        main_objects = bulk_create_objects(model_class, objects_data, batch_size)
        
        # 批量创建关联对象
        if related_data:
            for field_name, related_objects_data in related_data.items():
                if hasattr(model_class, field_name):
                    related_model = getattr(model_class, field_name).field.related_model
                    for i, obj in enumerate(main_objects):
                        if i < len(related_objects_data):
                            related_data = related_objects_data[i]
                            related_data[f'{model_class.__name__.lower()}_id'] = obj.id
                            related_model.objects.create(**related_data)
        
        return main_objects


def bulk_delete_objects(queryset, batch_size: int = 100):
    """
    批量删除对象（软删除）
    
    Args:
        queryset: 要删除的查询集
        batch_size: 批次大小，默认100
        
    Returns:
        删除的对象数量
    """
    count = 0
    for i in range(0, queryset.count(), batch_size):
        batch = queryset[i:i + batch_size]
        for obj in batch:
            if hasattr(obj, 'soft_delete'):
                obj.soft_delete()
            else:
                obj.delete()
        count += len(batch)
    return count
