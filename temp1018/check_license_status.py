"""
许可证状态诊断脚本

用于检查特定用户的许可证分配状态，帮助排查 already_applied 显示错误的问题

使用方法：
python manage.py shell < temp1018/check_license_status.py

或者在 Django shell 中：
>>> from temp1018.check_license_status import check_user_licenses
>>> check_user_licenses('fx0883')  # 替换为实际用户名
"""

from licenses.models import LicenseAssignment, SoftwareProduct
from users.models import Member


def check_user_licenses(username='fx0883'):
    """
    检查指定用户的所有许可证分配状态
    
    Args:
        username: 用户名，默认为 'fx0883'
    """
    print(f"\n{'='*80}")
    print(f"检查用户 {username} 的许可证分配状态")
    print(f"{'='*80}\n")
    
    try:
        # 获取用户
        user = User.objects.get(username=username, model_type='member')
        print(f"✓ 找到用户: {user.username} (ID: {user.id})")
        print(f"  - 租户: {user.tenant.name if user.tenant else 'N/A'}")
        print(f"  - 状态: {user.is_active}\n")
        
        # 获取所有许可证分配（包括已撤销的）
        all_assignments = LicenseAssignment.objects.filter(
            member=user
        ).select_related('license', 'license__product', 'license__plan').order_by('-created_at')
        
        print(f"总共找到 {all_assignments.count()} 个许可证分配记录\n")
        
        # 按产品分组统计
        products = {}
        for assignment in all_assignments:
            product = assignment.license.product
            product_name = product.name
            
            if product_name not in products:
                products[product_name] = {
                    'product_id': product.id,
                    'assignments': []
                }
            
            products[product_name]['assignments'].append({
                'assignment_id': assignment.id,
                'license_id': assignment.license.id,
                'license_key': f"{assignment.license.license_key[:5]}...{assignment.license.license_key[-5:]}",
                'status': assignment.status,
                'plan_name': assignment.license.plan.name,
                'plan_type': assignment.license.plan.plan_type,
                'assigned_at': assignment.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if assignment.assigned_at else 'N/A',
                'revoked_at': assignment.revoked_at.strftime('%Y-%m-%d %H:%M:%S') if assignment.revoked_at else 'N/A',
                'is_deleted': assignment.license.is_deleted
            })
        
        # 打印每个产品的详细信息
        for product_name, data in products.items():
            print(f"\n{'─'*80}")
            print(f"产品: {product_name} (ID: {data['product_id']})")
            print(f"{'─'*80}")
            
            # 统计各状态数量
            active_count = sum(1 for a in data['assignments'] if a['status'] == 'active')
            pending_count = sum(1 for a in data['assignments'] if a['status'] == 'pending')
            revoked_count = sum(1 for a in data['assignments'] if a['status'] == 'revoked')
            expired_count = sum(1 for a in data['assignments'] if a['status'] == 'expired')
            suspended_count = sum(1 for a in data['assignments'] if a['status'] == 'suspended')
            
            print(f"  状态统计:")
            print(f"    - active (有效): {active_count}")
            print(f"    - pending (待激活): {pending_count}")
            print(f"    - revoked (已撤销): {revoked_count}")
            print(f"    - expired (已过期): {expired_count}")
            print(f"    - suspended (已挂起): {suspended_count}")
            
            # 计算 already_applied 的值
            already_applied = (active_count + pending_count) > 0
            print(f"\n  ➤ already_applied 应该为: {already_applied}")
            
            if already_applied:
                print(f"     原因: 有 {active_count} 个 active + {pending_count} 个 pending 状态的许可证")
            
            # 打印详细列表
            print(f"\n  详细许可证分配列表:")
            for idx, a in enumerate(data['assignments'], 1):
                print(f"\n    [{idx}] 分配ID: {a['assignment_id']}")
                print(f"        - 许可证ID: {a['license_id']}")
                print(f"        - 许可证密钥: {a['license_key']}")
                print(f"        - 状态: {a['status']} {'🟢' if a['status'] in ['active', 'pending'] else '🔴'}")
                print(f"        - 方案: {a['plan_name']} ({a['plan_type']})")
                print(f"        - 分配时间: {a['assigned_at']}")
                if a['revoked_at'] != 'N/A':
                    print(f"        - 撤销时间: {a['revoked_at']}")
                print(f"        - 许可证已删除: {a['is_deleted']}")
        
        print(f"\n{'='*80}")
        print(f"诊断完成")
        print(f"{'='*80}\n")
        
        # 检查 available-products API 的行为
        print("\n分析 available-products API 行为:")
        print("─" * 80)
        
        available_products = SoftwareProduct.objects.filter(
            status='active',
            is_deleted=False,
            tenant=user.tenant
        )
        
        for product in available_products:
            # 模拟 get_already_applied 的查询
            has_valid_assignment = LicenseAssignment.objects.filter(
                member=user,
                license__product=product,
                license__is_deleted=False,
                status__in=['active', 'pending']
            ).exists()
            
            print(f"\n产品: {product.name} (ID: {product.id})")
            print(f"  - already_applied: {has_valid_assignment}")
            
            if has_valid_assignment:
                valid_assignments = LicenseAssignment.objects.filter(
                    member=user,
                    license__product=product,
                    license__is_deleted=False,
                    status__in=['active', 'pending']
                ).values('id', 'status', 'license_id')
                print(f"  - 有效分配: {list(valid_assignments)}")
        
    except User.DoesNotExist:
        print(f"✗ 错误: 找不到用户名为 '{username}' 的 Member 用户")
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 如果直接运行脚本，检查默认用户
    check_user_licenses('fx0883')
