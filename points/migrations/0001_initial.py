# Generated manually for points app
# This migration creates the initial schema for the multi-tenant points system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),  # Assuming users app exists
        ('tenants', '0001_initial'),  # Assuming tenants app exists
    ]

    operations = [
        # Create UserLevel model
        migrations.CreateModel(
            name='UserLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level_name', models.CharField(max_length=50, verbose_name='等级名称')),
                ('level_code', models.CharField(max_length=20, unique=True, verbose_name='等级代码')),
                ('level_order', models.PositiveIntegerField(unique=True, verbose_name='等级序号')),
                ('min_points', models.PositiveIntegerField(default=0, verbose_name='最低积分要求')),
                ('max_points', models.PositiveIntegerField(blank=True, null=True, verbose_name='最高积分上限')),
                ('permissions', models.JSONField(blank=True, default=dict, verbose_name='权限配置')),
                ('quota_config', models.JSONField(blank=True, default=dict, verbose_name='配额配置')),
                ('level_color', models.CharField(default='#999999', max_length=7, verbose_name='等级颜色')),
                ('level_icon', models.CharField(blank=True, max_length=100, verbose_name='等级图标')),
                ('level_description', models.TextField(blank=True, verbose_name='等级描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('is_default', models.BooleanField(default=False, verbose_name='是否默认等级')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '用户等级',
                'verbose_name_plural': '用户等级',
                'db_table': 'user_level',
                'ordering': ['level_order'],
            },
        ),
        
        # Create UserTypeTag model
        migrations.CreateModel(
            name='UserTypeTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_name', models.CharField(max_length=50, verbose_name='标签名称')),
                ('tag_code', models.CharField(max_length=20, unique=True, verbose_name='标签代码')),
                ('tag_type', models.CharField(choices=[('vip', 'VIP用户'), ('enterprise', '企业用户'), ('education', '教育用户'), ('developer', '开发者'), ('partner', '合作伙伴'), ('trial', '试用用户'), ('custom', '自定义')], max_length=20, verbose_name='标签类型')),
                ('tag_color', models.CharField(default='#007bff', max_length=7, verbose_name='标签颜色')),
                ('tag_icon', models.CharField(blank=True, max_length=100, verbose_name='标签图标')),
                ('tag_description', models.TextField(blank=True, verbose_name='标签描述')),
                ('permission_modifiers', models.JSONField(blank=True, default=dict, verbose_name='权限修改器')),
                ('quota_modifiers', models.JSONField(blank=True, default=dict, verbose_name='配额修改器')),
                ('price_config', models.JSONField(blank=True, default=dict, verbose_name='价格配置')),
                ('default_duration_days', models.PositiveIntegerField(blank=True, null=True, verbose_name='默认有效期天数')),
                ('max_duration_days', models.PositiveIntegerField(blank=True, null=True, verbose_name='最大有效期天数')),
                ('tag_level', models.PositiveIntegerField(default=1, verbose_name='标签等级')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('is_assignable', models.BooleanField(default=True, verbose_name='是否可分配')),
                ('requires_payment', models.BooleanField(default=False, verbose_name='是否需要付费')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '用户标签定义',
                'verbose_name_plural': '用户标签定义',
                'db_table': 'user_type_tag',
                'ordering': ['-tag_level', 'tag_name'],
            },
        ),
        
        # Create TenantUserProfile model
        migrations.CreateModel(
            name='TenantUserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_points', models.PositiveIntegerField(default=0, verbose_name='总积分')),
                ('available_points', models.PositiveIntegerField(default=0, verbose_name='可用积分')),
                ('level_updated_at', models.DateTimeField(blank=True, null=True, verbose_name='等级更新时间')),
                ('points_earned_total', models.PositiveIntegerField(default=0, verbose_name='历史总获得积分')),
                ('points_spent_total', models.PositiveIntegerField(default=0, verbose_name='历史总消费积分')),
                ('points_expired_total', models.PositiveIntegerField(default=0, verbose_name='历史总过期积分')),
                ('last_points_update', models.DateTimeField(blank=True, null=True, verbose_name='最后积分变动时间')),
                ('last_level_check', models.DateTimeField(blank=True, null=True, verbose_name='最后等级检查时间')),
                ('consecutive_login_days', models.PositiveIntegerField(default=0, verbose_name='连续登录天数')),
                ('last_login_date', models.DateField(blank=True, null=True, verbose_name='最后登录日期')),
                ('points_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, verbose_name='积分倍数')),
                ('is_points_enabled', models.BooleanField(default=True, verbose_name='是否启用积分功能')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('current_level', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='points.userlevel', verbose_name='当前等级')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.member', verbose_name='关联成员')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tenants.tenant', verbose_name='关联租户')),
            ],
            options={
                'verbose_name': '租户用户档案',
                'verbose_name_plural': '租户用户档案',
                'db_table': 'tenant_user_profile',
            },
        ),
        
        # Create TenantUserPoints model
        migrations.CreateModel(
            name='TenantUserPoints',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('point_type', models.CharField(choices=[('earn', '获得'), ('spend', '消费'), ('expire', '过期'), ('adjust', '调整')], max_length=10, verbose_name='积分类型')),
                ('category', models.CharField(choices=[('login', '登录奖励'), ('license', '许可证相关'), ('referral', '推荐奖励'), ('payment', '支付奖励'), ('community', '社区活动'), ('manual', '手动调整'), ('system', '系统操作')], max_length=20, verbose_name='业务分类')),
                ('subcategory', models.CharField(blank=True, max_length=50, verbose_name='子分类')),
                ('points', models.IntegerField(verbose_name='积分变动数量')),
                ('balance_before', models.PositiveIntegerField(verbose_name='操作前积分余额')),
                ('balance_after', models.PositiveIntegerField(verbose_name='操作后积分余额')),
                ('tenant_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=3, verbose_name='租户积分倍数')),
                ('original_points', models.PositiveIntegerField(blank=True, null=True, verbose_name='倍数调整前的原始积分')),
                ('source_type', models.CharField(choices=[('manual', '手动操作'), ('system', '系统操作'), ('api', 'API操作'), ('migration', '数据迁移')], default='system', max_length=20, verbose_name='来源类型')),
                ('source_id', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='关联的源记录ID')),
                ('source_description', models.TextField(blank=True, verbose_name='来源描述')),
                ('earned_at', models.DateTimeField(auto_now_add=True, verbose_name='积分获得时间')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='积分过期时间')),
                ('expired_at', models.DateTimeField(blank=True, null=True, verbose_name='实际过期时间')),
                ('operation_reason', models.TextField(blank=True, verbose_name='操作原因说明')),
                ('operator_id', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='操作人员ID')),
                ('batch_id', models.CharField(blank=True, max_length=100, verbose_name='批量操作标识')),
                ('status', models.CharField(choices=[('active', '有效'), ('expired', '已过期'), ('cancelled', '已取消'), ('adjusted', '已调整')], default='active', max_length=20, verbose_name='状态')),
                ('is_manual', models.BooleanField(default=False, verbose_name='是否手动调整')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('created_by_id', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='创建人ID')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.member', verbose_name='成员')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tenants.tenant', verbose_name='租户')),
                ('tenant_user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='points_records', to='points.tenantuserprofile', verbose_name='租户用户档案')),
            ],
            options={
                'verbose_name': '租户用户积分记录',
                'verbose_name_plural': '租户用户积分记录',
                'db_table': 'tenant_user_points',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create TenantUserTypeTag model
        migrations.CreateModel(
            name='TenantUserTypeTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('granted_at', models.DateTimeField(auto_now_add=True, verbose_name='授予时间')),
                ('granted_by_id', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='授予人ID')),
                ('grant_reason', models.TextField(blank=True, verbose_name='授予原因')),
                ('grant_method', models.CharField(choices=[('payment', '付费获得'), ('manual', '手动授予'), ('auto', '自动授予'), ('promotion', '促销活动'), ('migration', '数据迁移')], max_length=20, verbose_name='授予方式')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='过期时间')),
                ('original_duration_days', models.PositiveIntegerField(blank=True, null=True, verbose_name='原始有效期天数')),
                ('extended_days', models.PositiveIntegerField(default=0, verbose_name='延期天数')),
                ('auto_renewal', models.BooleanField(default=False, verbose_name='是否自动续期')),
                ('renewal_count', models.PositiveIntegerField(default=0, verbose_name='续期次数')),
                ('grace_period_days', models.PositiveIntegerField(default=0, verbose_name='宽限期天数')),
                ('reminder_sent_at', models.DateTimeField(blank=True, null=True, verbose_name='过期提醒发送时间')),
                ('renewal_reminder_sent', models.BooleanField(default=False, verbose_name='是否已发送续期提醒')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='最后使用时间')),
                ('usage_count', models.PositiveIntegerField(default=0, verbose_name='使用次数')),
                ('benefits_used', models.JSONField(blank=True, default=dict, verbose_name='已使用的福利记录')),
                ('payment_id', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='关联的支付记录ID')),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='支付金额')),
                ('payment_currency', models.CharField(default='CNY', max_length=3, verbose_name='支付货币')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否有效')),
                ('status', models.CharField(choices=[('active', '有效'), ('expired', '已过期'), ('suspended', '已暂停'), ('cancelled', '已取消'), ('grace_period', '宽限期')], default='active', max_length=20, verbose_name='状态')),
                ('notes', models.TextField(blank=True, verbose_name='备注信息')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='扩展元数据')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.member', verbose_name='成员')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='points.usertypetag', verbose_name='用户标签')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tenants.tenant', verbose_name='租户')),
                ('tenant_user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_tags', to='points.tenantuserprofile', verbose_name='租户用户档案')),
            ],
            options={
                'verbose_name': '租户用户标签关联',
                'verbose_name_plural': '租户用户标签关联',
                'db_table': 'tenant_user_type_tag',
            },
        ),
        
        # Add constraints and indexes
        migrations.AddConstraint(
            model_name='userlevel',
            constraint=models.CheckConstraint(condition=models.Q(min_points__gte=0), name='valid_min_points'),
        ),
        migrations.AddConstraint(
            model_name='userlevel',
            constraint=models.CheckConstraint(condition=models.Q(max_points__isnull=True) | models.Q(max_points__gt=models.F('min_points')), name='valid_max_points'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserprofile',
            constraint=models.UniqueConstraint(fields=['member', 'tenant'], name='unique_member_tenant'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserprofile',
            constraint=models.CheckConstraint(condition=models.Q(total_points__gte=0) & models.Q(available_points__gte=0), name='valid_points'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserprofile',
            constraint=models.CheckConstraint(condition=models.Q(available_points__lte=models.F('total_points')), name='available_points_check'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserpoints',
            constraint=models.CheckConstraint(condition=models.Q(points__gt=0) | models.Q(points__lt=0), name='points_not_zero'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserpoints',
            constraint=models.CheckConstraint(condition=models.Q(balance_after=models.F('balance_before') + models.F('points')), name='valid_balance'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserpoints',
            constraint=models.CheckConstraint(condition=models.Q(balance_after__gte=0), name='valid_balance_positive'),
        ),
        migrations.AddConstraint(
            model_name='tenantuserpoints',
            constraint=models.CheckConstraint(condition=models.Q(tenant_multiplier__gt=0), name='valid_tenant_multiplier'),
        ),
        migrations.AddConstraint(
            model_name='tenantusertypetag',
            constraint=models.UniqueConstraint(fields=['tenant', 'member', 'tag'], name='unique_tenant_member_tag'),
        ),
        migrations.AddConstraint(
            model_name='tenantusertypetag',
            constraint=models.CheckConstraint(condition=models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=models.F('granted_at')), name='valid_expiry'),
        ),
        migrations.AddConstraint(
            model_name='tenantusertypetag',
            constraint=models.CheckConstraint(condition=models.Q(original_duration_days__isnull=True) | models.Q(original_duration_days__gt=0), name='valid_duration'),
        ),
        migrations.AddConstraint(
            model_name='tenantusertypetag',
            constraint=models.CheckConstraint(condition=models.Q(payment_amount__isnull=True) | models.Q(payment_amount__gte=0), name='valid_payment_amount'),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='userlevel',
            index=models.Index(fields=['is_active', 'level_order'], name='idx_user_level_active_order'),
        ),
        migrations.AddIndex(
            model_name='userlevel',
            index=models.Index(fields=['min_points'], name='idx_user_level_min_points'),
        ),
        migrations.AddIndex(
            model_name='usertypetag',
            index=models.Index(fields=['tag_type', 'is_active'], name='idx_user_type_tag_type_active'),
        ),
        migrations.AddIndex(
            model_name='usertypetag',
            index=models.Index(fields=['is_active', 'is_assignable'], name='idx_user_type_tag_assignable'),
        ),
        migrations.AddIndex(
            model_name='tenantuserprofile',
            index=models.Index(fields=['member'], name='idx_tenant_user_profile_member'),
        ),
        migrations.AddIndex(
            model_name='tenantuserprofile',
            index=models.Index(fields=['tenant'], name='idx_tenant_user_profile_tenant'),
        ),
        migrations.AddIndex(
            model_name='tenantuserprofile',
            index=models.Index(fields=['tenant', 'total_points'], name='idx_tenant_user_profile_points'),
        ),
        migrations.AddIndex(
            model_name='tenantuserprofile',
            index=models.Index(fields=['current_level'], name='idx_tenant_user_profile_level'),
        ),
        migrations.AddIndex(
            model_name='tenantuserprofile',
            index=models.Index(fields=['tenant', 'last_points_update'], name='idx_tenant_user_profile_active'),
        ),
    ]
