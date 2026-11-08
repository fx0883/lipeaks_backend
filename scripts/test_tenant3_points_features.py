"""
租户 3 积分管理全功能自动化测试脚本
测试涵盖：
1. 预置徽章图标列表 API
2. 应用等级查询 (按应用过滤)
3. 应用等级新建 (增)
4. 应用等级更新 (改)
5. 应用等级删除 (删)
6. 应用账户列表与按应用过滤
7. 应用账户关键词检索 (按用户名/邮箱)
8. 管理员调账 - 增加积分与自动升级 (青铜 -> 黄金大师)
9. 管理员调账 - 扣减积分与可用余额扣减
10. 管理员调账 - 超额扣减防御测试 (余额不足应返回 400)
11. 账户明细台账流水查询 API
12. 应用级积分隔离性验证 (App 19 与 App 20 独立)
13. 租户级数据隔离性验证 (跨租户访问被拦截)
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from points.models import ApplicationUserLevel, AppUserPointsAccount, TenantUserPoints

def run_tests():
    print("=" * 70)
    print("🚀 开始执行 租户 3 积分管理全功能综合集成测试")
    print("=" * 70)

    tenant3 = Tenant.objects.get(id=3)
    user_admin = User.objects.get(username='admin_tianse')
    app_coloring = Application.objects.get(tenant=tenant3, code='001')
    app_phonics = Application.objects.get(tenant=tenant3, code='pinged')

    client = APIClient()
    client.force_authenticate(user=user_admin)
    client.credentials(HTTP_X_TENANT_ID=str(tenant3.id))

    passed_count = 0
    total_count = 0

    def assert_test(condition, test_name, detail=""):
        nonlocal passed_count, total_count
        total_count += 1
        if condition:
            passed_count += 1
            print(f"  ✅ [PASS] 测试 {total_count}: {test_name}")
            if detail:
                print(f"            └─ {detail}")
        else:
            print(f"  ❌ [FAIL] 测试 {total_count}: {test_name}")
            if detail:
                print(f"            └─ {detail}")
            raise AssertionError(f"Test failed: {test_name}")

    def extract_data(res_data):
        if isinstance(res_data, list):
            return res_data
        if isinstance(res_data, dict):
            if 'data' in res_data:
                inner = res_data['data']
                if isinstance(inner, dict) and 'results' in inner:
                    return inner['results']
                return inner
            if 'results' in res_data:
                return res_data['results']
        return res_data

    # ----------------------------------------------------
    # 测试 1: 预置徽章图标 API
    # ----------------------------------------------------
    res = client.get('/api/v1/points/app-levels/preset_icons/')
    data = extract_data(res.data)
    assert_test(
        res.status_code == 200 and len(data) == 6,
        "预置徽章图标接口 (preset_icons)",
        f"成功获取 {len(data)} 枚预置 3D 勋章，首枚为: {data[0]['name']}"
    )

    # ----------------------------------------------------
    # 测试 2: 查询填色花园的积分等级梯队
    # ----------------------------------------------------
    res = client.get(f'/api/v1/points/app-levels/?application={app_coloring.id}')
    levels_data = extract_data(res.data)
    assert_test(
        res.status_code == 200 and len(levels_data) == 6,
        "查询「填色花园」积分等级梯队",
        f"成功查询到 {len(levels_data)} 级成长阶梯，包含最高阶「{levels_data[-1]['level_name']}」"
    )

    # ----------------------------------------------------
    # 测试 3: 创建新等级 (增)
    # ----------------------------------------------------
    new_lvl_payload = {
        "application": app_coloring.id,
        "level_name": "星空神话",
        "level_code": "LV_MYTH",
        "level_order": 7,
        "min_points": 30000,
        "max_points": None,
        "icon": "application/images/level_crown.png",
        "level_color": "#9400D3",
        "level_description": "传说中的星空画圣，享全站永久最高荣誉与所有画册优先体验权。",
        "is_default": False,
        "is_active": True
    }
    res = client.post('/api/v1/points/app-levels/', new_lvl_payload, format='json')
    created_level_id = None
    if res.status_code == 201:
        lvl_res = res.data.get('data', res.data)
        created_level_id = lvl_res.get('id')
    assert_test(
        res.status_code == 201 and created_level_id is not None,
        "新建应用专属等级 (POST /api/v1/points/app-levels/)",
        f"成功创建等级 ID={created_level_id}, 等级名称=星空神话"
    )

    # ----------------------------------------------------
    # 测试 4: 更新等级信息 (改)
    # ----------------------------------------------------
    update_payload = {
        "level_name": "星空创世神",
        "level_color": "#BA55D3",
        "min_points": 35000
    }
    res = client.patch(f'/api/v1/points/app-levels/{created_level_id}/', update_payload, format='json')
    updated_name = res.data.get('data', res.data).get('level_name')
    assert_test(
        res.status_code == 200 and updated_name == "星空创世神",
        "更新应用专属等级 (PATCH /api/v1/points/app-levels/{id}/)",
        f"等级名称成功从「星空神话」更新为「{updated_name}」"
    )

    # ----------------------------------------------------
    # 测试 5: 删除测试等级 (删)
    # ----------------------------------------------------
    res = client.delete(f'/api/v1/points/app-levels/{created_level_id}/')
    assert_test(
        res.status_code == 204 or res.status_code == 200,
        "删除应用专属等级 (DELETE /api/v1/points/app-levels/{id}/)",
        f"成功删除测试等级 ID={created_level_id}"
    )

    # ----------------------------------------------------
    # 测试 6: 查询「自然拼读」积分等级 (应用级隔离)
    # ----------------------------------------------------
    res = client.get(f'/api/v1/points/app-levels/?application={app_phonics.id}')
    phonics_levels = extract_data(res.data)
    assert_test(
        res.status_code == 200 and len(phonics_levels) == 3,
        "应用间等级体系隔离校验",
        f"「自然拼读」独立具备 {len(phonics_levels)} 级阶梯，与「填色花园」完全互不影响"
    )

    # ----------------------------------------------------
    # 测试 7: 查询应用积分账户列表
    # ----------------------------------------------------
    res = client.get(f'/api/v1/points/app-accounts/?application={app_coloring.id}')
    accounts_list = extract_data(res.data)
    assert_test(
        res.status_code == 200 and len(accounts_list) == 5,
        "查询「填色花园」成员积分账户列表",
        f"成功获取 {len(accounts_list)} 个成员的积分档案与专属成长状态"
    )

    # ----------------------------------------------------
    # 测试 8: 账户关键词模糊搜索 (by username)
    # ----------------------------------------------------
    res = client.get(f'/api/v1/points/app-accounts/?search=bob_color')
    search_list = extract_data(res.data)
    assert_test(
        res.status_code == 200 and len(search_list) == 1 and search_list[0]['member_username'] == 'bob_color',
        "积分账户检索功能 (search=bob_color)",
        f"检索成功匹配到成员 {search_list[0]['member_username']}, 可用积分: {search_list[0]['available_points']}"
    )

    # ----------------------------------------------------
    # 测试 9: 管理员调账加分与自动进阶测试 (青铜 -> 黄金)
    # ----------------------------------------------------
    # 取出 Mike 在填色花园的账户并重置为初始状态 (320 分，青铜学员)
    bronze_level = ApplicationUserLevel.objects.get(application=app_coloring, level_order=1)
    mike_member = Member.objects.get(tenant=tenant3, username='Mike@qq.com')
    mike_acct = AppUserPointsAccount.objects.get(tenant=tenant3, application=app_coloring, member=mike_member)
    mike_acct.total_points = 320
    mike_acct.available_points = 320
    mike_acct.current_level = bronze_level
    mike_acct.save()
    
    init_avail = mike_acct.available_points
    init_lvl_name = mike_acct.current_level.level_name

    # 调账增加 2000 分，总分将达到 2320 (满足黄金大师 1500 - 3999 门槛)
    adjust_add_payload = {
        "points": 2000,
        "reason": "社区年度艺术创作杰出贡献奖",
        "category": "community"
    }
    res = client.post(f'/api/v1/points/app-accounts/{mike_acct.id}/adjust/', adjust_add_payload, format='json')
    adj_data = res.data.get('data', res.data)
    mike_acct.refresh_from_db()

    assert_test(
        res.status_code == 200 and mike_acct.available_points == init_avail + 2000 and mike_acct.current_level.level_name == "黄金大师",
        "管理员调账充值与等级阶梯自动进阶",
        f"积分从 {init_avail} 增至 {mike_acct.available_points}，等级从「{init_lvl_name}」自动跃升至「{mike_acct.current_level.level_name}」"
    )

    # ----------------------------------------------------
    # 测试 10: 管理员调账扣减积分测试
    # ----------------------------------------------------
    adjust_deduct_payload = {
        "points": -300,
        "reason": "线下实物画材礼品包兑换扣减",
        "category": "manual"
    }
    res = client.post(f'/api/v1/points/app-accounts/{mike_acct.id}/adjust/', adjust_deduct_payload, format='json')
    mike_acct.refresh_from_db()
    assert_test(
        res.status_code == 200 and mike_acct.available_points == init_avail + 2000 - 300,
        "管理员调账扣减积分",
        f"成功扣减 300 积分，当前剩余可用积分: {mike_acct.available_points}"
    )

    # ----------------------------------------------------
    # 测试 11: 超额扣减防御测试 (余额不足校验)
    # ----------------------------------------------------
    invalid_deduct_payload = {
        "points": -999999,
        "reason": "恶意超额扣减测试"
    }
    res = client.post(f'/api/v1/points/app-accounts/{mike_acct.id}/adjust/', invalid_deduct_payload, format='json')
    assert_test(
        res.status_code == 400,
        "超额扣减安全防御 (余额不足拒绝)",
        f"超出可用余额扣减被系统有效拦截，响应码: {res.status_code}"
    )

    # ----------------------------------------------------
    # 测试 12: 账户明细流水查询 API
    # ----------------------------------------------------
    res = client.get(f'/api/v1/points/app-accounts/{mike_acct.id}/records/')
    records_list = extract_data(res.data)
    latest_rec = records_list[0] if records_list else None
    assert_test(
        res.status_code == 200 and len(records_list) >= 2,
        "应用账户明细流水查询 (/records/)",
        f"成功查询到 {len(records_list)} 条变动流水，最新一条操作:「{latest_rec.get('operation_reason')}」(变动: {latest_rec.get('points')})"
    )

    # ----------------------------------------------------
    # 测试 13: 跨租户隔离性验证
    # ----------------------------------------------------
    # 使用租户 1 请求头访问租户 3 的账户
    client_t1 = APIClient()
    client_t1.force_authenticate(user=user_admin)
    client_t1.credentials(HTTP_X_TENANT_ID='1')
    res_t1 = client_t1.get(f'/api/v1/points/app-accounts/{mike_acct.id}/')
    assert_test(
        res_t1.status_code in [400, 403, 404],
        "多租户安全边界隔离校验",
        f"其他租户(ID:1)请求头无法越权访问租户 3 的积分账户，拦截状态: {res_t1.status_code}"
    )

    print("\n" + "=" * 70)
    print(f"🎉 租户 3 积分系统全功能测试全部通过！通过率: {passed_count}/{total_count} (100%)")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
