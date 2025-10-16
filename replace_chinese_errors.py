#!/usr/bin/env python3
"""
批量替换Python文件中的中文异常消息为英文
"""
import os
import re
from pathlib import Path

# 中文到英文的映射表
TRANSLATIONS = {
    # ValidationError 消息
    "两次输入的密码不一致": "Passwords do not match",
    "两次输入的新密码不一致": "New passwords do not match",
    "旧密码不正确": "Incorrect old password",
    "产品代码已存在": "Product code already exists",
    "该用户已拥有该产品的许可证": "User already has a license for this product",
    "您没有权限更改此用户的角色": "You do not have permission to change this user's role",
    "您不能取消自己的管理员权限": "You cannot remove your own admin privileges",
    "您不能修改超级管理员的角色": "You cannot modify the super admin role",
    "租户管理员配额已满": "Tenant admin quota is full",
    "用户必须至少有一个角色": "User must have at least one role",
    "用户名/邮箱或密码错误": "Invalid username/email or password",
    "用户已被禁用": "User is disabled",
    "用户已被删除": "User has been deleted",
    "子账号不允许登录": "Sub-accounts are not allowed to log in",
    "所属租户已被禁用或暂停": "Tenant has been disabled or suspended",
    "该租户下此邮箱已被注册": "Email already registered in this tenant",
    "该邮箱已被注册": "Email already registered",
    "该邮箱已被使用": "Email already in use",
    "该租户下此用户名已被使用": "Username already used in this tenant",
    "该用户名已被使用": "Username already in use",
    "该租户下此手机号已被注册": "Phone number already registered in this tenant",
    "该手机号已被注册": "Phone number already registered",
    "无效的租户ID": "Invalid tenant ID",
    "无效的重置令牌": "Invalid reset token",
    "重置令牌已过期": "Reset token has expired",
    "无效的租户ID格式": "Invalid tenant ID format",
    "超级管理员创建成员时必须提供租户ID": "Super admin must provide tenant ID when creating member",
    "当前管理员未关联租户，无法创建成员": "Current admin has no associated tenant and cannot create member",
    "权限代码应采用'resource:action'格式": "Permission code should follow 'resource:action' format",
    "不允许将系统权限修改为非系统权限": "Cannot modify system permission to non-system permission",
    "不允许修改系统角色的租户": "Cannot modify tenant of system role",
    "结束日期必须大于等于开始日期": "End date must be greater than or equal to start date",
    "模板角色必须是系统角色": "Template role must be a system role",
    "成员和许可证必须属于同一租户": "Member and license must belong to the same tenant",
    
    # Django国际化函数_()包裹的消息
    "用户未关联租户，无法创建任务": "User has no associated tenant and cannot create task",
    "无法为其他租户的用户创建任务": "Cannot create task for users of other tenants",
    "指定的用户不存在": "Specified user does not exist",
    "只能为自己的子账号创建任务": "Can only create tasks for own sub-accounts",
    "子账号必须属于同一租户": "Sub-accounts must belong to the same tenant",
    "用户未关联租户，无法更新任务": "User has no associated tenant and cannot update task",
    "无法为其他租户的用户修改任务": "Cannot modify task for users of other tenants",
    "只能为自己的子账号修改任务": "Can only modify tasks for own sub-accounts",
    "无法修改其他用户的任务": "Cannot modify other users' tasks",
    "用户未关联租户，无法创建打卡记录": "User has no associated tenant and cannot create check-in record",
    "不能为其他租户的任务创建打卡记录": "Cannot create check-in record for tasks of other tenants",
    "指定的任务不存在": "Specified task does not exist",
    "无法为其他租户的用户创建打卡记录": "Cannot create check-in record for users of other tenants",
    "只能为自己的子账号创建打卡记录": "Can only create check-in records for own sub-accounts",
    "用户未关联租户，无法更新打卡记录": "User has no associated tenant and cannot update check-in record",
    "不能为其他租户的任务更新打卡记录": "Cannot update check-in record for tasks of other tenants",
    "只能修改自己的打卡记录": "Can only modify own check-in records",
    "只能为自己的子账号修改打卡记录": "Can only modify check-in records for own sub-accounts",
    "无法修改其他用户的打卡记录": "Cannot modify other users' check-in records",
    
    # licenses相关消息
    "方案代码在该产品下已存在": "Plan code already exists for this product",
    "product字段是必需的": "product field is required",
    "plan字段是必需的": "plan field is required",
    "tenant字段是必需的": "tenant field is required",
    "许可证密钥格式无效": "Invalid license key format",
    "激活码格式无效": "Invalid activation code format",
    "机器指纹长度必须为64位": "Machine fingerprint must be 64 characters",
    "开始日期不能晚于结束日期": "Start date cannot be later than end date",
    "报告时间范围不能超过1年": "Report time range cannot exceed 1 year",
    "无法确定current用户的租户": "Cannot determine current user's tenant",
    "指定的成员不存在或不属于current租户": "Specified member does not exist or does not belong to current tenant",
    "指定的许可证不存在或不属于current租户": "Specified license does not exist or does not belong to current tenant",
    "该成员已拥有此许可证的活跃分配": "Member already has an active assignment for this license",
    "许可证激活配额已满": "License activation quota is full",
    "该产品没有可用的试用方案": "No trial plan available for this product",
    "产品不存在或不可用": "Product does not exist or is unavailable",
    "手机号格式无效": "Invalid phone number format",
    "公司名称过长": "Company name too long",
    "使用用途描述过长": "Intended use description too long",
    "用户未认证": "User is not authenticated",
    "您已经申请过该产品的许可证": "You have already applied for a license for this product",
    
    # CMS相关消息
    "您没有权限创建文章": "You do not have permission to create articles",
    "您没有权限编辑此文章": "You do not have permission to edit this article",
    "您没有权限更改文章作者": "You do not have permission to change article author",
    "您没有权限删除此文章": "You do not have permission to delete this article",
    "无法删除已关联文章的分类，请先移除关联的文章": "Cannot delete category with associated articles, please remove associated articles first",
    "无法删除有子分类的分类，请先删除所有子分类": "Cannot delete category with sub-categories, please delete all sub-categories first",
    "无法删除已关联标签的标签组，请先移除关联的标签": "Cannot delete tag group with associated tags, please remove associated tags first",
    "标签组不属于current租户": "Tag group does not belong to current tenant",
    "无法删除已关联文章的标签，请先移除关联的文章": "Cannot delete tag with associated articles, please remove associated articles first",
    "该文章不允许评论": "This article does not allow comments",
    "文章不存在或无权限访问": "Article does not exist or no permission to access",
    "用户或游客名称至少提供一项": "User or guest name must be provided",
    "用户和文章必须属于同一租户": "User and article must belong to the same tenant",
    "用户未关联租户，无法访问CMS系统": "User has no associated tenant and cannot access CMS system",
    "不能访问其他租户的资源": "Cannot access resources of other tenants",
    "不能操作其他租户的资源": "Cannot operate resources of other tenants",
    
    # customers相关消息
    "客户名称已存在，请使用其他名称": "Customer name already exists, please use another name",
    "结束日期不能早于开始日期": "End date cannot be earlier than start date",
    "批量创建的客户中存在重复名称": "Duplicate names found in batch customer creation",
    "批量更新的客户中存在重复名称": "Duplicate names found in batch customer update",
    "每个客户数据必须包含id字段": "Each customer data must contain id field",
    
    # orders相关消息
    "客户数量不能为空": "Customer count cannot be empty",
    "不能与version1相同": "Cannot be the same as version1",
    
    # menus相关消息
    "菜单不能将自己设为父菜单": "Menu cannot set itself as parent menu",
    "不能将子菜单设为父菜单，这会导致循环引用": "Cannot set child menu as parent menu, this will cause circular reference",
    
    # licenses ValueError消息
    "延长天数必须大于0": "Extension days must be greater than 0",
    "current分配不允许激活": "Current assignment does not allow activation",
    "分配已过期，无法激活": "Assignment has expired and cannot be activated",
    "许可证已过期，无法激活": "License has expired and cannot be activated",
    "当前硬件指纹不匹配": "Current hardware fingerprint does not match",
    
    # security_service Exception消息
    "密钥对生成失败": "Key pair generation failed",
    "签名失败": "Signature failed",
    "密钥生成失败": "Key generation failed",
    "加密失败": "Encryption failed",
    "解密失败": "Decryption failed",
    "哈希计算失败": "Hash calculation failed",
    "不支持的哈希算法": "Unsupported hash algorithm",
    
    # Management Commands消息
    "许可证密钥.*?不存在": "License key does not exist",
    "软件产品.*?不存在": "Software product does not exist",
    "租户.*?不存在": "Tenant does not exist",
    "许可证方案.*?不存在": "License plan does not exist",
    "许可证方案.*?未激活": "License plan is not activated",
    "命令执行失败": "Command execution failed",
    
    # PermissionDenied 消息
    "只有管理员才能修改其他用户的密码": "Only administrators can change other users' passwords",
    "不能删除当前登录的账号": "Cannot delete the currently logged-in account",
    "只有超级管理员可以删除其他超级管理员": "Only super admins can delete other super admins",
    "您没有关联的租户，无法创建管理员": "You have no associated tenant and cannot create an admin",
    "您只能在自己的租户下创建管理员": "You can only create admins in your own tenant",
    "只有超级管理员可以修改超级管理员标志": "Only super admins can modify the super admin flag",
    "租户管理员配额已满，无法创建更多管理员": "Tenant admin quota is full, cannot create more admins",
    "租户成员配额已满，无法创建更多成员": "Tenant member quota is full, cannot create more members",
    
    # jwt.InvalidTokenError 消息
    "令牌类型错误": "Token type error",
    "令牌中缺少用户ID": "User ID is missing in token",
    "用户状态异常": "User status is abnormal",
    "所属租户已被禁用或删除": "Tenant has been disabled or deleted",
    
    # Response 消息
    "刷新令牌成功": "Token refreshed successfully",
    "无效的刷新令牌": "Invalid refresh token",
    "用户不存在或已被禁用": "User not found or disabled",
    "刷新令牌失败": "Token refresh failed",
    
    # Throttled 消息
    "请求过于频繁，请稍后再试": "Too many requests, please try again later",
    
    # 其他常见消息
    "无效的许可证密钥": "Invalid license key",
    "许可证密钥格式不正确": "License key format is incorrect",
    "许可证不存在": "License not found",
    "许可证已过期": "License has expired",
    "许可证已被撤销": "License has been revoked",
    "许可证已被激活": "License already activated",
    "激活次数已达上限": "Maximum activation limit reached",
    "该用户已有激活的许可证": "User already has an active license",
    "许可证类型不匹配": "License type mismatch",
    "设备指纹不匹配": "Device fingerprint mismatch",
    "许可证状态异常": "License status is abnormal",
    "分配许可证失败": "Failed to assign license",
    "撤销许可证失败": "Failed to revoke license",
    "该用户暂未分配许可证": "No license assigned to this user",
    "无法找到指定的许可证": "Cannot find the specified license",
    "该许可证已分配给其他用户": "License already assigned to another user",
    "文件不存在": "File does not exist",
    "不支持的文件类型": "Unsupported file type",
    "文件大小超过限制": "File size exceeds limit",
    "上传文件失败": "File upload failed",
    "必须提供租户ID": "Tenant ID is required",
}

def replace_in_file(file_path):
    """替换单个文件中的中文消息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 对每个翻译进行替换
        for chinese, english in TRANSLATIONS.items():
            # 转义特殊字符
            escaped_chinese = re.escape(chinese)
            # 替换各种格式的中文消息
            patterns = [
                (f'"{escaped_chinese}"', f'"{english}"'),
                (f"'{escaped_chinese}'", f"'{english}'"),
                (f'detail="{escaped_chinese}"', f'detail="{english}"'),
                (f"detail='{escaped_chinese}'", f"detail='{english}'"),
            ]
            
            for pattern, replacement in patterns:
                content = content.replace(pattern, replacement)
        
        # 处理Django国际化函数_()包裹的消息
        # 例如: _("中文消息") -> _("English message")
        for chinese, english in TRANSLATIONS.items():
            escaped_chinese = re.escape(chinese)
            content = content.replace(f'_("{chinese}")', f'_("{english}")')
            content = content.replace(f"_('{chinese}')", f"_('{english}')")
            
        # 处理Exception类型的消息
        # 例如: raise Exception("中文消息") -> raise Exception("English message")
        for chinese, english in TRANSLATIONS.items():
            content = content.replace(f'Exception(f"{chinese}:', f'Exception(f"{english}:')
            content = content.replace(f"Exception(f'{chinese}:", f"Exception(f'{english}:")
            content = content.replace(f'ValueError(f"{chinese}:', f'ValueError(f"{english}:')
            content = content.replace(f"ValueError(f'{chinese}:", f"ValueError(f'{english}:")
            content = content.replace(f'CommandError(f"{chinese}:', f'CommandError(f"{english}:')
            content = content.replace(f"CommandError(f'{chinese}:", f"CommandError(f'{english}:")
        
        # 处理f-string中的动态内容(简单模式)
        # 例如: f"无效的租户ID: {tenant_id}" -> f"Invalid tenant ID: {tenant_id}"
        dynamic_patterns = [
            # ValidationError动态消息
            (r'f"无效的租户ID: \{', 'f"Invalid tenant ID: {'),
            (r"f'无效的租户ID: \{", "f'Invalid tenant ID: {"),
            (r'f"权限不存在: \{', 'f"Permissions not found: {'),
            (r'f"角色ID \{.*?\} 不存在"', lambda m: m.group(0).replace('角色ID', 'Role ID').replace('不存在', 'not found')),
            (r'f"系统角色ID \{.*?\} 不存在"', lambda m: m.group(0).replace('系统角色ID', 'System role ID').replace('不存在', 'not found')),
            # 权限相关
            (r'您只能在自己的租户下创建用户', 'You can only create users in your own tenant'),
            (r'您只能在自己的租户下创建管理员', 'You can only create admins in your own tenant'),
            (r'您没有关联的租户，无法创建普通用户', 'You have no associated tenant and cannot create member'),
            (r'f"需要 \{.*?\} 权限"', lambda m: m.group(0).replace('需要', 'Required permission:').replace('权限', '')),
            # ValueError动态消息
            (r'积分数量必须大于0', 'Points amount must be greater than 0'),
            (r'f"积分不足，可用积分: \{', 'f"Insufficient points, available: {'),
            (r'f"余额计算错误: \{', 'f"Balance calculation error: {'),
            (r'f"只能标记有效积分为过期，当前状态: \{', 'f"Can only mark valid points as expired, current status: {'),
            (r'f"只能取消有效积分，当前状态: \{', 'f"Can only cancel valid points, current status: {'),
            (r'f"积分余额不足: 当前\{', 'f"Insufficient points balance: current {'),
            (r'f"新计划 \{.*?\} 不属于当前产品 \{', lambda m: m.group(0).replace('新计划', 'New plan').replace('不属于当前产品', 'does not belong to current product')),
            (r'f"许可证激活配额已满，最大支持 \{', 'f"License activation quota is full, maximum supported: {'),
            (r'f"只能激活待激活状态的分配，当前状态: \{', 'f"Can only activate pending assignments, current status: {'),
            (r'f"许可证状态不允许激活: \{', 'f"License status does not allow activation: {'),
            (r'f"无法撤销已撤销或已过期的分配，当前状态: \{', 'f"Cannot revoke revoked or expired assignment, current status: {'),
            (r'f"成员租户\(\{.*?\}\)与许可证租户\(\{', lambda m: m.group(0).replace('成员租户', 'Member tenant').replace('与许可证租户', 'does not match license tenant')),
            (r'f"成员 \{.*?\} 已分配许可证 \{', lambda m: m.group(0).replace('成员', 'Member').replace('已分配许可证', 'already assigned license')),
            # 带动态参数的消息
            (r'客户信息缺少必要字段:', 'Customer information missing required field:'),
            (r'硬件信息缺少必要字段:', 'Hardware information missing required field:'),
            (r'小时内申请次数过多，请稍后再试', 'hours. Too many applications, please try again later'),
            (r'current限制:', 'Current limit:'),
            (r'您的试用许可证数量已达上限', 'Your trial license quota has been reached'),
            (r'以下客户名称已存在:', 'The following customer names already exist:'),
            (r'分类ID.*?不存在或无权限访问', 'Category ID does not exist or no permission to access'),
            (r'标签ID.*?不存在或无权限访问', 'Tag ID does not exist or no permission to access'),
            (r'订单.*?不存在版本', 'Order does not have version'),
            (r'检测到循环引用: 菜单', 'Circular reference detected: menu'),
            (r'不能将', 'cannot set'),
            (r'设为父菜单', 'as parent menu'),
            # 通用替换
            (r'当前状态:', 'Current status:'),
            (r'可用积分:', 'Available points:'),
            (r'需要:', 'Required:'),
            (r'变动', 'Change'),
            (r'当前', 'current'),
        ]
        
        for pattern, replacement in dynamic_patterns:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = content.replace(pattern, replacement)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已更新: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"✗ 处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    # 获取项目根目录
    root_dir = Path(__file__).parent
    
    # 需要处理的目录列表
    directories = [
        root_dir / 'users',
        root_dir / 'licenses',
        root_dir / 'tenants',
        root_dir / 'cms',
        root_dir / 'rbac',
        root_dir / 'check_system',
        root_dir / 'customers',
        root_dir / 'orders',
        root_dir / 'points',
        root_dir / 'menus',
        root_dir / 'common',
    ]
    
    updated_files = 0
    total_files = 0
    
    # 遍历所有目录
    for directory in directories:
        if not directory.exists():
            print(f"跳过不存在的目录: {directory}")
            continue
        
        # 查找所有Python文件
        for py_file in directory.rglob('*.py'):
            if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            total_files += 1
            if replace_in_file(py_file):
                updated_files += 1
    
    print(f"\n" + "="*60)
    print(f"处理完成！")
    print(f"总文件数: {total_files}")
    print(f"更新文件数: {updated_files}")
    print("="*60)

if __name__ == '__main__':
    main()
