"""
许可证系统信号处理器
实现事件驱动的许可证配置同步
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LicensePlan, License
import logging

logger = logging.getLogger('licenses.signals')


@receiver(post_save, sender=LicensePlan)
def sync_licenses_on_plan_change(sender, instance, created, update_fields, **kwargs):
    """
    当LicensePlan发生变更时，同步相关许可证的配置
    
    Args:
        sender: 发送信号的模型类
        instance: LicensePlan实例
        created: 是否为新建
        update_fields: 更新的字段列表
        **kwargs: 其他参数
    """
    # 只处理更新操作，且涉及模板配置字段
    if created or not update_fields:
        return
    
    # 检查是否更新了模板配置字段
    template_fields = {'default_max_activations', 'default_validity_days'}
    if not template_fields.intersection(set(update_fields)):
        return
    
    # 获取使用此计划的所有许可证
    related_licenses = License.objects.filter(
        plan=instance,
        status__in=['generated', 'activated']  # 只同步活跃状态的许可证
    )
    
    updated_count = 0
    for license_obj in related_licenses:
        try:
            if license_obj.update_from_plan():
                updated_count += 1
        except Exception as e:
            logger.error(f"许可证 {license_obj.id} 配置同步失败: {str(e)}")
    
    if updated_count > 0:
        logger.info(f"计划 {instance.id} 变更触发 {updated_count} 个许可证配置同步")


@receiver(post_save, sender=License)
def log_license_status_change(sender, instance, created, update_fields, **kwargs):
    """
    记录许可证状态变更日志
    
    Args:
        sender: 发送信号的模型类
        instance: License实例
        created: 是否为新建
        update_fields: 更新的字段列表
        **kwargs: 其他参数
    """
    if created:
        logger.info(f"新许可证创建: {instance.id} ({instance.license_key})")
        return
    
    if update_fields and 'status' in update_fields:
        logger.info(f"许可证 {instance.id} 状态变更为: {instance.status}")
    
    if update_fields and 'max_activations' in update_fields:
        logger.info(f"许可证 {instance.id} 最大激活数变更为: {instance.max_activations}")
    
    if update_fields and 'expires_at' in update_fields:
        logger.info(f"许可证 {instance.id} 过期时间变更为: {instance.expires_at}")
