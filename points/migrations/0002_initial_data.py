# Generated manually for points app
# This migration creates initial data for user levels and type tags

from django.db import migrations


def create_initial_user_levels(apps, schema_editor):
    """Create initial user levels"""
    UserLevel = apps.get_model('points', 'UserLevel')
    
    levels = [
        {
            'level_name': '新手',
            'level_code': 'BRONZE',
            'level_order': 1,
            'min_points': 0,
            'max_points': 999,
            'level_color': '#CD7F32',
            'level_description': '新注册用户，刚开始使用系统',
            'is_active': True,
            'is_default': True,
            'permissions': {
                'api_access': True,
                'max_devices_per_license': 1,
            },
            'quota_config': {
                'storage_mb': 100,
                'api_calls_daily': 1000,
            }
        },
        {
            'level_name': '铜牌',
            'level_code': 'SILVER',
            'level_order': 2,
            'min_points': 1000,
            'max_points': 4999,
            'level_color': '#C0C0C0',
            'level_description': '活跃用户，具备基础权限',
            'is_active': True,
            'is_default': False,
            'permissions': {
                'api_access': True,
                'max_devices_per_license': 2,
                'can_share_license': True,
            },
            'quota_config': {
                'storage_mb': 500,
                'api_calls_daily': 5000,
                'export_count_daily': 10,
            }
        },
        {
            'level_name': '银牌',
            'level_code': 'GOLD',
            'level_order': 3,
            'min_points': 5000,
            'max_points': 19999,
            'level_color': '#FFD700',
            'level_description': '资深用户，享受更多权限',
            'is_active': True,
            'is_default': False,
            'permissions': {
                'api_access': True,
                'bulk_operations': True,
                'max_devices_per_license': 3,
                'can_share_license': True,
                'can_backup_license': True,
            },
            'quota_config': {
                'storage_mb': 2000,
                'api_calls_daily': 20000,
                'export_count_daily': 50,
                'support_tickets_monthly': 5,
            }
        },
        {
            'level_name': '金牌',
            'level_code': 'PLATINUM',
            'level_order': 4,
            'min_points': 20000,
            'max_points': 49999,
            'level_color': '#E5E4E2',
            'level_description': '高级用户，享受高级功能',
            'is_active': True,
            'is_default': False,
            'permissions': {
                'api_access': True,
                'bulk_operations': True,
                'advanced_analytics': True,
                'max_devices_per_license': 5,
                'can_share_license': True,
                'can_backup_license': True,
                'can_export_license': True,
            },
            'quota_config': {
                'storage_mb': 10000,
                'api_calls_daily': 100000,
                'export_count_daily': 200,
                'support_tickets_monthly': 10,
                'session_timeout_minutes': 60,
            }
        },
        {
            'level_name': '钻石',
            'level_code': 'DIAMOND',
            'level_order': 5,
            'min_points': 50000,
            'max_points': None,
            'level_color': '#B9F2FF',
            'level_description': '顶级用户，享受所有权限',
            'is_active': True,
            'is_default': False,
            'permissions': {
                'api_access': True,
                'bulk_operations': True,
                'advanced_analytics': True,
                'priority_support': True,
                'custom_integration': True,
                'max_devices_per_license': 10,
                'can_share_license': True,
                'can_backup_license': True,
                'can_export_license': True,
            },
            'quota_config': {
                'storage_mb': 50000,
                'api_calls_daily': 500000,
                'export_count_daily': 1000,
                'support_tickets_monthly': 50,
                'session_timeout_minutes': 120,
                'concurrent_sessions': 5,
            }
        },
    ]
    
    for level_data in levels:
        UserLevel.objects.get_or_create(
            level_code=level_data['level_code'],
            defaults=level_data
        )


def create_initial_user_type_tags(apps, schema_editor):
    """Create initial user type tags"""
    UserTypeTag = apps.get_model('points', 'UserTypeTag')
    
    tags = [
        {
            'tag_name': 'VIP用户',
            'tag_code': 'VIP',
            'tag_type': 'vip',
            'tag_color': '#FF6B6B',
            'tag_description': '享受VIP特权的用户',
            'tag_level': 3,
            'requires_payment': True,
            'default_duration_days': 30,
            'max_duration_days': 365,
            'is_active': True,
            'is_assignable': True,
            'permission_modifiers': {
                'priority_support': True,
                'max_devices_per_license': 1.5,  # 150% 倍数
                'storage_mb': 2.0,  # 200% 倍数
                'api_calls_daily': 2.0,
            },
            'quota_modifiers': {
                'storage_mb': 2.0,
                'api_calls_daily': 2.0,
                'export_count_daily': 3.0,
                'support_tickets_monthly': 5.0,
            },
            'price_config': {
                'prices': {
                    'CNY': 99.00,
                    'USD': 14.99,
                }
            }
        },
        {
            'tag_name': '超级VIP',
            'tag_code': 'SUPER_VIP',
            'tag_type': 'vip',
            'tag_color': '#FF4757',
            'tag_description': '享受最高级别VIP特权',
            'tag_level': 5,
            'requires_payment': True,
            'default_duration_days': 365,
            'max_duration_days': 1095,  # 3年
            'is_active': True,
            'is_assignable': True,
            'permission_modifiers': {
                'priority_support': True,
                'advanced_analytics': True,
                'custom_integration': True,
                'max_devices_per_license': 3.0,  # 300% 倍数
                'white_label': True,
            },
            'quota_modifiers': {
                'storage_mb': 10.0,
                'api_calls_daily': 10.0,
                'export_count_daily': 10.0,
                'support_tickets_monthly': 20.0,
                'session_timeout_minutes': 3.0,
            },
            'price_config': {
                'prices': {
                    'CNY': 999.00,
                    'USD': 149.99,
                }
            }
        },
        {
            'tag_name': '企业用户',
            'tag_code': 'ENTERPRISE',
            'tag_type': 'enterprise',
            'tag_color': '#5352ED',
            'tag_description': '企业级用户，享受企业特权',
            'tag_level': 4,
            'requires_payment': True,
            'default_duration_days': 365,
            'max_duration_days': 1095,
            'is_active': True,
            'is_assignable': True,
            'permission_modifiers': {
                'bulk_operations': True,
                'advanced_analytics': True,
                'priority_support': True,
                'custom_integration': True,
                'max_devices_per_license': 5.0,
            },
            'quota_modifiers': {
                'storage_mb': 50.0,
                'api_calls_daily': 50.0,
                'export_count_daily': 100.0,
                'support_tickets_monthly': 100.0,
            },
            'price_config': {
                'prices': {
                    'CNY': 1999.00,
                    'USD': 299.99,
                }
            }
        },
        {
            'tag_name': '教育用户',
            'tag_code': 'EDUCATION',
            'tag_type': 'education',
            'tag_color': '#2ED573',
            'tag_description': '教育机构用户，享受教育优惠',
            'tag_level': 2,
            'requires_payment': False,
            'default_duration_days': 180,
            'max_duration_days': 365,
            'is_active': True,
            'is_assignable': True,
            'permission_modifiers': {
                'bulk_operations': True,
                'max_devices_per_license': 3.0,
            },
            'quota_modifiers': {
                'storage_mb': 5.0,
                'api_calls_daily': 5.0,
                'export_count_daily': 10.0,
                'support_tickets_monthly': 10.0,
            },
            'price_config': {}
        },
        {
            'tag_name': '开发者',
            'tag_code': 'DEVELOPER',
            'tag_type': 'developer',
            'tag_color': '#FFA726',
            'tag_description': '开发者用户，享受开发者工具',
            'tag_level': 2,
            'requires_payment': False,
            'default_duration_days': 90,
            'max_duration_days': 365,
            'is_active': True,
            'is_assignable': True,
            'permission_modifiers': {
                'api_access': True,
                'custom_integration': True,
                'max_devices_per_license': 2.0,
            },
            'quota_modifiers': {
                'api_calls_daily': 10.0,
                'export_count_daily': 20.0,
            },
            'price_config': {}
        },
    ]
    
    for tag_data in tags:
        UserTypeTag.objects.get_or_create(
            tag_code=tag_data['tag_code'],
            defaults=tag_data
        )


def reverse_initial_data(apps, schema_editor):
    """Remove initial data (for rollback)"""
    UserLevel = apps.get_model('points', 'UserLevel')
    UserTypeTag = apps.get_model('points', 'UserTypeTag')
    
    # Delete initial user levels
    level_codes = ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND']
    UserLevel.objects.filter(level_code__in=level_codes).delete()
    
    # Delete initial user type tags
    tag_codes = ['VIP', 'SUPER_VIP', 'ENTERPRISE', 'EDUCATION', 'DEVELOPER']
    UserTypeTag.objects.filter(tag_code__in=tag_codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_user_levels,
            reverse_initial_data,
        ),
        migrations.RunPython(
            create_initial_user_type_tags,
            reverse_initial_data,
        ),
    ]
