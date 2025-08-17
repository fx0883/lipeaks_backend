# 数据迁移方案

## 概述

将现有的单一User模型拆分为User和Member两个模型需要进行数据迁移，以确保数据的完整性和一致性。本文档详细说明数据迁移的步骤、注意事项和回滚策略。

## 迁移策略

数据迁移将采用以下策略：

1. **保留原始数据**：在迁移过程中，保留原始User表数据，以便在出现问题时可以回滚
2. **分阶段迁移**：将迁移过程分为多个阶段，每个阶段完成后进行验证
3. **先结构后数据**：先完成模型结构的迁移，再进行数据迁移
4. **维护外键关系**：确保迁移过程中保持所有外键关系的完整性
5. **测试环境验证**：在生产环境迁移前，在测试环境进行完整的迁移测试

## 迁移步骤

### 阶段一：准备工作

1. **创建备份**
   ```bash
   # 备份数据库
   python manage.py dumpdata users --indent 4 > users_backup.json
   python manage.py dumpdata auth --indent 4 > auth_backup.json
   
   # 备份相关代码
   cp -r users users_backup
   ```

2. **冻结相关功能**
   - 在迁移期间，暂时禁用用户注册、用户管理等功能
   - 添加系统维护提示

### 阶段二：模型结构迁移

1. **创建新模型**
   - 创建BaseUserModel抽象基类
   - 创建User模型（继承自BaseUserModel）
   - 创建Member模型（继承自BaseUserModel）

2. **创建初始迁移文件**
   ```bash
   python manage.py makemigrations users
   ```

3. **修改迁移文件**
   - 手动编辑迁移文件，确保数据迁移的正确性
   - 添加自定义SQL操作，处理特殊情况

### 阶段三：数据迁移

1. **创建数据迁移脚本**

   ```python
   from django.db import migrations
   
   def migrate_users_to_new_models(apps, schema_editor):
       """
       将原有User表数据迁移到新的User和Member表
       """
       # 获取模型类
       OldUser = apps.get_model('users', 'User')
       NewUser = apps.get_model('users', 'User')
       Member = apps.get_model('users', 'Member')
       
       # 迁移超级管理员和租户管理员到User表
       for old_user in OldUser.objects.filter(is_admin=True):
           NewUser.objects.create(
               id=old_user.id,
               username=old_user.username,
               password=old_user.password,
               email=old_user.email,
               phone=old_user.phone,
               nick_name=old_user.nick_name,
               avatar=old_user.avatar,
               first_name=old_user.first_name,
               last_name=old_user.last_name,
               is_active=old_user.is_active,
               is_staff=old_user.is_staff,
               is_superuser=old_user.is_superuser,
               is_admin=True,
               is_super_admin=old_user.is_super_admin,
               is_deleted=old_user.is_deleted,
               status=old_user.status,
               tenant=old_user.tenant,
               last_login=old_user.last_login,
               last_login_ip=old_user.last_login_ip,
               date_joined=old_user.date_joined
           )
       
       # 迁移普通成员到Member表
       parent_map = {}  # 用于记录父子关系
       
       # 先创建所有Member记录
       for old_user in OldUser.objects.filter(is_member=True):
           member = Member.objects.create(
               id=old_user.id,
               username=old_user.username,
               password=old_user.password,
               email=old_user.email,
               phone=old_user.phone,
               nick_name=old_user.nick_name,
               avatar=old_user.avatar,
               first_name=old_user.first_name,
               last_name=old_user.last_name,
               is_active=old_user.is_active,
               is_superuser=False,
               is_deleted=old_user.is_deleted,
               status=old_user.status,
               tenant=old_user.tenant,
               last_login=old_user.last_login,
               last_login_ip=old_user.last_login_ip,
               date_joined=old_user.date_joined
           )
           
           # 记录父子关系
           if old_user.parent_id:
               parent_map[member.id] = old_user.parent_id
       
       # 更新父子关系
       for member_id, parent_id in parent_map.items():
           try:
               member = Member.objects.get(id=member_id)
               parent = Member.objects.get(id=parent_id)
               member.parent = parent
               member.save(update_fields=['parent'])
           except Member.DoesNotExist:
               print(f"警告：成员ID {member_id} 或父账号ID {parent_id} 不存在")
   
   def reverse_migrate(apps, schema_editor):
       """
       回滚迁移，删除新创建的记录
       """
       NewUser = apps.get_model('users', 'User')
       Member = apps.get_model('users', 'Member')
       
       NewUser.objects.all().delete()
       Member.objects.all().delete()
   
   class Migration(migrations.Migration):
       dependencies = [
           ('users', '0002_create_new_models'),
       ]
       
       operations = [
           migrations.RunPython(migrate_users_to_new_models, reverse_migrate),
       ]
   ```

2. **应用迁移**
   ```bash
   python manage.py migrate users
   ```

3. **验证数据迁移**
   - 检查数据完整性
   - 验证用户数量是否一致
   - 验证父子关系是否正确

### 阶段四：更新外键关系

1. **创建外键更新脚本**

   ```python
   from django.db import migrations
   
   def update_foreign_keys(apps, schema_editor):
       """
       更新引用User模型的外键关系
       """
       # 获取相关模型
       User = apps.get_model('users', 'User')
       Member = apps.get_model('users', 'Member')
       
       # 更新各个模型的外键关系
       # 例如：更新文章的作者关系
       Article = apps.get_model('blog', 'Article')
       
       for article in Article.objects.all():
           old_author_id = article.author_id
           
           # 检查作者是管理员还是普通成员
           if User.objects.filter(id=old_author_id).exists():
               # 作者是管理员，不需要更改
               pass
           elif Member.objects.filter(id=old_author_id).exists():
               # 作者是普通成员，需要更新外键类型
               # 这里需要根据具体情况处理
               pass
   
   def reverse_update_foreign_keys(apps, schema_editor):
       """
       回滚外键更新
       """
       # 根据具体情况实现回滚逻辑
       pass
   
   class Migration(migrations.Migration):
       dependencies = [
           ('users', '0003_migrate_data'),
           # 添加其他依赖的应用
       ]
       
       operations = [
           migrations.RunPython(update_foreign_keys, reverse_update_foreign_keys),
       ]
   ```

2. **应用迁移**
   ```bash
   python manage.py migrate
   ```

3. **验证外键关系**
   - 检查外键关系是否正确
   - 验证相关功能是否正常

### 阶段五：更新代码和配置

1. **更新认证系统**
   - 实现MultiModelAuthBackend
   - 更新JWT令牌生成和验证逻辑

2. **更新API端点**
   - 分离User和Member的API端点
   - 更新权限控制逻辑

3. **更新配置**
   - 更新AUTH_USER_MODEL设置
   - 更新中间件配置

4. **部署更新后的代码**
   ```bash
   # 部署代码
   git pull
   
   # 重启服务
   systemctl restart gunicorn
   systemctl restart nginx
   ```

### 阶段六：测试和验证

1. **功能测试**
   - 测试用户登录和认证
   - 测试用户管理功能
   - 测试子账号功能

2. **性能测试**
   - 测试系统响应时间
   - 测试数据库查询性能

3. **回归测试**
   - 测试所有与用户系统相关的功能

## 回滚策略

如果在迁移过程中出现问题，可以使用以下回滚策略：

1. **回滚代码**
   ```bash
   git checkout <previous-commit>
   ```

2. **回滚数据库迁移**
   ```bash
   python manage.py migrate users <previous-migration>
   ```

3. **恢复数据备份**
   ```bash
   python manage.py flush
   python manage.py loaddata users_backup.json
   python manage.py loaddata auth_backup.json
   ```

## 迁移风险和缓解措施

| 风险 | 可能性 | 影响 | 缓解措施 |
|-----|-------|-----|---------|
| 数据丢失 | 低 | 高 | 创建完整备份；分阶段迁移；验证每个步骤 |
| 功能中断 | 中 | 高 | 在低峰期进行迁移；提前通知用户；准备回滚方案 |
| 外键关系错误 | 中 | 高 | 仔细规划外键更新；全面测试；准备修复脚本 |
| 性能问题 | 低 | 中 | 优化查询；监控系统性能；准备扩展资源 |
| 认证失败 | 中 | 高 | 全面测试认证系统；保留旧认证方式作为备份 |

## 迁移时间表

| 阶段 | 预计时间 | 负责人 | 验收标准 |
|-----|---------|-------|---------|
| 准备工作 | 1天 | 系统管理员 | 完成备份；冻结相关功能 |
| 模型结构迁移 | 2天 | 后端开发 | 新模型结构创建完成；迁移文件准备就绪 |
| 数据迁移 | 1天 | 后端开发 | 所有数据迁移完成；数据完整性验证通过 |
| 更新外键关系 | 2天 | 后端开发 | 所有外键关系更新完成；关系完整性验证通过 |
| 更新代码和配置 | 3天 | 全栈开发 | 所有代码更新完成；配置更新完成 |
| 测试和验证 | 2天 | QA团队 | 所有测试通过；系统稳定运行 |

## 注意事项

1. **数据备份**：确保在迁移前创建完整的数据库备份
2. **通知用户**：提前通知用户系统维护时间和可能的影响
3. **监控系统**：在迁移过程中和迁移后密切监控系统性能和错误日志
4. **分批处理**：对于大量数据，考虑分批处理以减少系统负载
5. **测试环境验证**：在生产环境迁移前，在测试环境进行完整的迁移测试
6. **回滚准备**：确保回滚策略可行，并进行回滚演练
7. **文档记录**：记录迁移过程中的所有步骤和问题，以便将来参考 