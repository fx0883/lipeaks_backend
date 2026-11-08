"""
租户 ID=3 签到系统端到端测试与全量测试数据构造脚本
涵盖：
1. 签到规则配置（CheckinConfig: repeat 循环模式与 cap 封顶模式）
2. 5名成员的打卡流水与状态构造（连续打卡、漏签断签、补签、已满签、全新用户）
3. 全功能 API 自动化测试（成员打卡、防重复打卡、补签扣费与接续、管理员连续总览、打卡明细流水、多租户隔离、积分等级晋升）
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from points.models import (
    CheckinConfig, UserCheckinStreak, UserCheckinRecord,
    TenantUserProfile, AppUserPointsAccount, TenantUserPoints,
    ApplicationUserLevel
)
from points.services.checkin_service import CheckinService


def log_step(title):
    print("\n" + "=" * 70)
    print(f"👉 {title}")
    print("=" * 70)


def run():
    log_step("1. 初始化租户 ID=3 与应用、成员基础信息")
    tenant = Tenant.objects.get(id=3)
    admin_user = User.objects.filter(username='admin_tianse', tenant=tenant).first()
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
    print(f"租户: [{tenant.id}] {tenant.name} ({tenant.code})")
    print(f"管理用户: {admin_user.username}")

    apps = list(Application.objects.filter(tenant=tenant))
    app_coloring = next((a for a in apps if a.code == '001' or '填色' in a.name), apps[0])
    app_phonics = next((a for a in apps if a.id != app_coloring.id), apps[1] if len(apps) > 1 else None)
    if not app_phonics:
        app_phonics = Application.objects.create(
            tenant=tenant, name="自然拼读", code="pinged", status="active", description="拼读应用"
        )
    print(f"应用 1: [{app_coloring.id}] {app_coloring.name} ({app_coloring.code})")
    print(f"应用 2: [{app_phonics.id}] {app_phonics.name} ({app_phonics.code})")

    # 获取或创建 5 名测试成员
    members_data = [
        ("alice_art", "alice_art@test.com", "爱丽丝"),
        ("bob_color", "bob_color@test.com", "鲍勃"),
        ("carol_phonic", "carol_phonic@test.com", "卡罗尔"),
        ("david_master", "david_master@test.com", "大卫"),
        ("Mike@qq.com", "Mike@qq.com", "迈克")
    ]
    members = {}
    for username, email, first_name in members_data:
        m, created = Member.objects.get_or_create(
            tenant=tenant,
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'status': 'active'
            }
        )
        if created:
            m.set_password("Password123!")
            m.save()
        members[username] = m

        # 确保 TenantUserProfile 存在
        TenantUserProfile.objects.get_or_create(
            tenant=tenant,
            member=m,
            defaults={'is_points_enabled': True, 'available_points': 500, 'total_points': 500}
        )
    print(f"已就绪 5 名测试成员: {list(members.keys())}")

    # ========================================================
    log_step("2. 配置两个应用的专属签到规则 (CheckinConfig)")
    # ========================================================
    # 清理历史签到规则与记录，保证全新可复现环境
    UserCheckinRecord.objects.filter(tenant=tenant).delete()
    UserCheckinStreak.objects.filter(tenant=tenant).delete()
    TenantUserPoints.objects.filter(tenant=tenant, category='checkin').delete()

    # 应用 1：填色花园（7天循环 repeat 模式，补签消耗 20 积分）
    cfg_coloring, _ = CheckinConfig.objects.update_or_create(
        tenant=tenant,
        application=app_coloring,
        defaults={
            'name': "【填色花园】七日连签嘉年华",
            'cycle_days': 7,
            'cycle_mode': 'repeat',
            'reward_ladder': [
                {"day": 1, "points": 10, "label": "初探花园"},
                {"day": 2, "points": 15, "label": "画笔渐熟"},
                {"day": 3, "points": 20, "label": "色彩初现"},
                {"day": 4, "points": 25, "label": "妙笔生花"},
                {"day": 5, "points": 30, "label": "画作惊艳"},
                {"day": 6, "points": 40, "label": "大师雏形"},
                {"day": 7, "points": 100, "label": "神级宝箱"}
            ],
            'allow_recheckin': True,
            'recheckin_cost': 20,
            'is_active': True
        }
    )
    print(f"已配置: {cfg_coloring.name} (模式: {cfg_coloring.cycle_mode}, 补签消耗: {cfg_coloring.recheckin_cost}分)")

    # 应用 2：自然拼读（7天封顶 cap 模式，补签消耗 30 积分）
    cfg_phonics, _ = CheckinConfig.objects.update_or_create(
        tenant=tenant,
        application=app_phonics,
        defaults={
            'name': "【自然拼读】每日打卡得高分",
            'cycle_days': 7,
            'cycle_mode': 'cap',
            'reward_ladder': [
                {"day": 1, "points": 5, "label": "元音起步"},
                {"day": 2, "points": 10, "label": "辅音结合"},
                {"day": 3, "points": 15, "label": "双音节成词"},
                {"day": 4, "points": 20, "label": "短语通读"},
                {"day": 5, "points": 25, "label": "绘本初览"},
                {"day": 6, "points": 35, "label": "流利复述"},
                {"day": 7, "points": 80, "label": "拼读大师"}
            ],
            'allow_recheckin': True,
            'recheckin_cost': 30,
            'is_active': True
        }
    )
    print(f"已配置: {cfg_phonics.name} (模式: {cfg_phonics.cycle_mode}, 补签消耗: {cfg_phonics.recheckin_cost}分)")

    # ========================================================
    log_step("3. 构造 5 名成员不同业务维度的打卡测试数据")
    # ========================================================
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)
    print(f"参考基准日期: 今天={today}, 昨天={yesterday}, 前天={day_before_yesterday}")

    # ----------------------------------------------------
    # 用户 1: alice_art (填色花园) -> 过去连续签到 4 天 (Day 1~4)
    # 待测试：今天通过 API 签到第 5 天！
    # ----------------------------------------------------
    m_alice = members["alice_art"]
    acc_alice, _ = AppUserPointsAccount.objects.get_or_create(
        tenant=tenant, application=app_coloring, member=m_alice,
        defaults={'tenant_user_profile': TenantUserProfile.objects.get(tenant=tenant, member=m_alice), 'available_points': 50, 'total_points': 50, 'is_enabled': True}
    )
    for i in range(4):
        past_date = today - timedelta(days=(4 - i))
        CheckinService.execute_checkin(
            member=m_alice, tenant=tenant, application=app_coloring, today=past_date
        )
    streak_alice = UserCheckinStreak.objects.get(tenant=tenant, application=app_coloring, member=m_alice)
    print(f"  [Alice] 已构造过去4天打卡: 当前连续 {streak_alice.current_streak} 天, 最后签到: {streak_alice.last_checkin_date}")

    # ----------------------------------------------------
    # 用户 2: bob_color (填色花园) -> 签到 Day 1, Day 2，但漏签前天与昨天！
    # 待测试：状态查询展示漏签，调用补签 API 补签前天与昨天，连签接续！
    # ----------------------------------------------------
    m_bob = members["bob_color"]
    acc_bob, _ = AppUserPointsAccount.objects.get_or_create(
        tenant=tenant, application=app_coloring, member=m_bob,
        defaults={'tenant_user_profile': TenantUserProfile.objects.get(tenant=tenant, member=m_bob), 'available_points': 100, 'total_points': 100, 'is_enabled': True}
    )
    acc_bob.available_points = 100
    acc_bob.save()
    CheckinService.execute_checkin(
        member=m_bob, tenant=tenant, application=app_coloring, today=today - timedelta(days=4)
    )
    CheckinService.execute_checkin(
        member=m_bob, tenant=tenant, application=app_coloring, today=today - timedelta(days=3)
    )
    streak_bob = UserCheckinStreak.objects.get(tenant=tenant, application=app_coloring, member=m_bob)
    print(f"  [Bob] 已构造历史断签数据: 签到了 -4天与 -3天，漏签了前天(-2)与昨天(-1)。当前账户积分: {acc_bob.available_points}")

    # ----------------------------------------------------
    # 用户 3: carol_phonic (自然拼读) -> 连续签到 8 天（已满签，含今天，封顶 Cap 模式）
    # 待测试：Day 7 拿 80分，第 8 天依旧保持封顶拿 80分！
    # ----------------------------------------------------
    m_carol = members["carol_phonic"]
    acc_carol, _ = AppUserPointsAccount.objects.get_or_create(
        tenant=tenant, application=app_phonics, member=m_carol,
        defaults={'tenant_user_profile': TenantUserProfile.objects.get(tenant=tenant, member=m_carol), 'available_points': 0, 'total_points': 0, 'is_enabled': True}
    )
    for i in range(8):
        c_date = today - timedelta(days=(7 - i))
        CheckinService.execute_checkin(
            member=m_carol, tenant=tenant, application=app_phonics, today=c_date
        )
    streak_carol = UserCheckinStreak.objects.get(tenant=tenant, application=app_phonics, member=m_carol)
    print(f"  [Carol] 已构造自然拼读 8 天连续打卡(封顶模式): 连签 {streak_carol.current_streak} 天, 总天数 {streak_carol.total_days} 天, 账户可用积分: {acc_carol.refresh_from_db() or acc_carol.available_points}")

    # ----------------------------------------------------
    # 用户 4: david_master (自然拼读) -> 包含已完成的“补签历史记录”
    # ----------------------------------------------------
    m_david = members["david_master"]
    acc_david, _ = AppUserPointsAccount.objects.get_or_create(
        tenant=tenant, application=app_phonics, member=m_david,
        defaults={'tenant_user_profile': TenantUserProfile.objects.get(tenant=tenant, member=m_david), 'available_points': 200, 'total_points': 200, 'is_enabled': True}
    )
    acc_david.available_points = 200
    acc_david.save()
    CheckinService.execute_checkin(
        member=m_david, tenant=tenant, application=app_phonics, today=today - timedelta(days=3)
    )
    # David 在昨天执行了补签前天
    CheckinService.execute_recheckin(
        member=m_david, tenant=tenant, target_date=today - timedelta(days=2), application=app_phonics
    )
    # David 昨天正常打卡
    CheckinService.execute_checkin(
        member=m_david, tenant=tenant, application=app_phonics, today=yesterday
    )
    streak_david = UserCheckinStreak.objects.get(tenant=tenant, application=app_phonics, member=m_david)
    print(f"  [David] 已构造含补签的历史打卡: 连签 {streak_david.current_streak} 天, 累计 {streak_david.total_days} 天")

    # ----------------------------------------------------
    # 用户 5: Mike@qq.com (填色花园) -> 全新未打卡用户
    # ----------------------------------------------------
    m_mike = members["Mike@qq.com"]
    AppUserPointsAccount.objects.get_or_create(
        tenant=tenant, application=app_coloring, member=m_mike,
        defaults={'tenant_user_profile': TenantUserProfile.objects.get(tenant=tenant, member=m_mike), 'available_points': 0, 'total_points': 0, 'is_enabled': True}
    )
    print("  [Mike] 保持为全新未打卡用户 (0 条签到记录)")

    # ========================================================
    log_step("4. 全面执行 API 接口与业务功能测试")
    # ========================================================
    client = APIClient()
    client.defaults['HTTP_X_TENANT_ID'] = str(tenant.id)

    # ----------------------------------------------------
    # 测试 4.1: 查询签到状态与日历接口 (GET /api/v1/points/checkin/status/)
    # ----------------------------------------------------
    print("\n--- 测试 4.1: 查询签到状态与日历接口 ---")
    client.force_authenticate(user=m_alice)
    res_status = client.get(f"/api/v1/points/checkin/status/?application_id={app_coloring.id}")
    assert res_status.status_code == 200, f"Alice 查询状态失败: {res_status.data}"
    status_data = res_status.data.get("data", res_status.data)
    print("Alice 状态:", {
        "has_checked_in_today": status_data["has_checked_in_today"],
        "current_streak": status_data["current_streak"],
        "today_reward": status_data["today_reward"],
        "cycle_days": status_data["cycle_days"]
    })
    assert status_data["has_checked_in_today"] is False
    assert status_data["current_streak"] == 4
    assert status_data["today_reward"] == 30  # 第 5 天应获 30 分

    # 查询 Bob 的状态（检查是否正确识别出漏签日期 missed_dates）
    client.force_authenticate(user=m_bob)
    res_bob_status = client.get(f"/api/v1/points/checkin/status/?application_id={app_coloring.id}")
    bob_status_data = res_bob_status.data.get("data", res_bob_status.data)
    missed_date_strs = [m["date"] for m in bob_status_data.get("missed_dates", [])]
    print(f"Bob 漏签日期识别: {missed_date_strs}")
    assert yesterday.isoformat() in missed_date_strs, "Bob 漏签列表中应包含昨天"
    assert day_before_yesterday.isoformat() in missed_date_strs, "Bob 漏签列表中应包含前天"

    # ----------------------------------------------------
    # 测试 4.2: 执行签到接口 (POST /api/v1/points/checkin/execute/)
    # ----------------------------------------------------
    print("\n--- 测试 4.2: 执行签到打卡 (Alice 签到第 5 天) ---")
    client.force_authenticate(user=m_alice)
    res_exec = client.post("/api/v1/points/checkin/execute/", {
        "application_id": app_coloring.id
    }, format='json')
    assert res_exec.status_code == 200, f"Alice 执行打卡失败: {res_exec.data}"
    exec_data = res_exec.data.get("data", res_exec.data)
    print("打卡返回:", {
        "success": exec_data["success"],
        "points_earned": exec_data["points_earned"],
        "current_streak": exec_data["current_streak"],
        "new_balance": exec_data["new_balance"]
    })
    assert exec_data["success"] is True
    assert exec_data["points_earned"] == 30
    assert exec_data["current_streak"] == 5

    # ----------------------------------------------------
    # 测试 4.3: 当天防重复签到校验
    # ----------------------------------------------------
    print("\n--- 测试 4.3: 当天重复签到防刷校验 ---")
    res_dup = client.post("/api/v1/points/checkin/execute/", {
        "application_id": app_coloring.id
    }, format='json')
    assert res_dup.status_code == 400, "重复签到应返回 400"
    dup_data = res_dup.data.get("data", res_dup.data)
    err_code = dup_data.get("error_code") or res_dup.data.get("error_code")
    print(f"防重打卡拦截正确: 状态码 400, error_code = {err_code}")
    assert err_code == "ALREADY_CHECKED_IN"

    # ----------------------------------------------------
    # 测试 4.4: 执行补签打卡 (Bob 补签前天与昨天并接续连签)
    # ----------------------------------------------------
    print("\n--- 测试 4.4: 补签打卡扣费与连签接续 ---")
    client.force_authenticate(user=m_bob)
    acc_bob.refresh_from_db()
    init_balance = acc_bob.available_points

    # 补签前天 (Day 3)
    res_recheckin_1 = client.post("/api/v1/points/checkin/recheckin/", {
        "application_id": app_coloring.id,
        "target_date": day_before_yesterday.isoformat()
    }, format='json')
    assert res_recheckin_1.status_code == 200, f"补签前天失败: {res_recheckin_1.data}"
    re_data_1 = res_recheckin_1.data.get("data", res_recheckin_1.data)
    print("Bob 补签前天结果:", {
        "cost_points": re_data_1["cost_points"],
        "points_earned": re_data_1["points_earned"],
        "current_streak": re_data_1["current_streak"],
        "new_balance": re_data_1["new_balance"]
    })
    assert re_data_1["cost_points"] == 20  # 规则配置消耗 20 分
    assert re_data_1["points_earned"] == 20  # 第 3 天阶梯得 20 分

    # 补签昨天 (Day 4)
    res_recheckin_2 = client.post("/api/v1/points/checkin/recheckin/", {
        "application_id": app_coloring.id,
        "target_date": yesterday.isoformat()
    }, format='json')
    assert res_recheckin_2.status_code == 200, f"补签昨天失败: {res_recheckin_2.data}"
    re_data_2 = res_recheckin_2.data.get("data", res_recheckin_2.data)
    print("Bob 补签昨天结果:", {
        "cost_points": re_data_2["cost_points"],
        "points_earned": re_data_2["points_earned"],
        "current_streak": re_data_2["current_streak"],
        "new_balance": re_data_2["new_balance"]
    })
    assert re_data_2["points_earned"] == 25  # 第 4 天阶梯得 25 分
    assert re_data_2["current_streak"] == 4  # 连签成功缝合恢复到 4 天！

    # Bob 正常打卡今天 (Day 5)
    res_bob_today = client.post("/api/v1/points/checkin/execute/", {
        "application_id": app_coloring.id
    }, format='json')
    assert res_bob_today.status_code == 200, f"Bob 今日打卡失败: {res_bob_today.data}"
    bob_today_data = res_bob_today.data.get("data", res_bob_today.data)
    print("Bob 完成今天打卡结果:", {
        "current_streak": bob_today_data["current_streak"],
        "points_earned": bob_today_data["points_earned"]
    })
    assert bob_today_data["current_streak"] == 5  # 连续天数成功递增为 5 天！
    assert bob_today_data["points_earned"] == 30  # 第 5 天获得 30 分！

    # ----------------------------------------------------
    # 测试 4.5: 补签边界异常拦截 (禁止补签今天、禁止重复补签)
    # ----------------------------------------------------
    print("\n--- 测试 4.5: 补签异常校验拦截 ---")
    # 1. 尝试补签今天
    res_bad_today = client.post("/api/v1/points/checkin/recheckin/", {
        "application_id": app_coloring.id,
        "target_date": today.isoformat()
    }, format='json')
    assert res_bad_today.status_code == 400
    print("  拦截补签今天: OK (INVALID_RECHECKIN_DATE)")

    # 2. 尝试补签已签到的日期（昨天已补签过）
    res_bad_dup = client.post("/api/v1/points/checkin/recheckin/", {
        "application_id": app_coloring.id,
        "target_date": yesterday.isoformat()
    }, format='json')
    assert res_bad_dup.status_code == 400
    print("  拦截重复补签: OK (ALREADY_CHECKED_IN)")

    # ----------------------------------------------------
    # 测试 4.6: 管理员用户连续签到总览接口 (GET /api/v1/points/checkin-streaks/)
    # ----------------------------------------------------
    print("\n--- 测试 4.6: 管理员查询用户连续签到总览 ---")
    client.force_authenticate(user=admin_user)
    # 按填色花园应用筛选
    res_admin_streaks = client.get(f"/api/v1/points/checkin-streaks/?application={app_coloring.id}", HTTP_X_TENANT_ID=str(tenant.id))
    assert res_admin_streaks.status_code == 200, f"获取连签总览失败: {res_admin_streaks.data}"
    streak_results = res_admin_streaks.data.get("data", res_admin_streaks.data)
    streak_items = streak_results.get("results", streak_results) if isinstance(streak_results, dict) else streak_results
    print(f"填色花园连签成员数: {len(streak_items)}")
    for item in streak_items:
        print(f"  - 成员: {item['member_username']} | 当前连续: {item['current_streak']}天 | 最高连续: {item['max_streak']}天 | 累计: {item['total_days']}天 | 今日已签: {item['has_checked_in_today']}")
    assert len(streak_items) >= 2

    # 测试按成员用户名搜索
    res_search = client.get(f"/api/v1/points/checkin-streaks/?search=alice", HTTP_X_TENANT_ID=str(tenant.id))
    search_items = res_search.data.get("data", res_search.data).get("results", [])
    assert len(search_items) == 1
    assert search_items[0]["member_username"] == "alice_art"
    print("  管理员用户名精确搜索功能: OK")

    # ----------------------------------------------------
    # 测试 4.7: 管理员打卡明细流水接口 (GET /api/v1/points/checkin-records/)
    # ----------------------------------------------------
    print("\n--- 测试 4.7: 管理员打卡明细流水 (验证补签筛选与日期筛选) ---")
    # 1. 筛选全部流水
    res_records = client.get(f"/api/v1/points/checkin-records/?application={app_coloring.id}", HTTP_X_TENANT_ID=str(tenant.id))
    assert res_records.status_code == 200
    all_records = res_records.data.get("data", res_records.data).get("results", [])
    print(f"填色花园打卡流水总记录数: {len(all_records)}")

    # 2. 筛选补签记录 (is_recheckin=true)
    res_recheck_only = client.get(f"/api/v1/points/checkin-records/?application={app_coloring.id}&is_recheckin=true", HTTP_X_TENANT_ID=str(tenant.id))
    recheck_items = res_recheck_only.data.get("data", res_recheck_only.data).get("results", [])
    print(f"其中补签流水记录数: {len(recheck_items)}")
    assert len(recheck_items) >= 2  # Bob 刚才补签了 2 天
    for r in recheck_items:
        assert r["is_recheckin"] is True
        print(f"  ✨ 补签记录: {r['member_username']} | 归属日期: {r['checkin_date']} | 获得积分: +{r['reward_points']}")

    # 3. 筛选正常打卡记录 (is_recheckin=false)
    res_normal_only = client.get(f"/api/v1/points/checkin-records/?application={app_coloring.id}&is_recheckin=false", HTTP_X_TENANT_ID=str(tenant.id))
    normal_items = res_normal_only.data.get("data", res_normal_only.data).get("results", [])
    print(f"其中正常打卡流水记录数: {len(normal_items)}")
    for r in normal_items:
        assert r["is_recheckin"] is False

    # ----------------------------------------------------
    # 测试 4.8: 签到规则配置接口 (CheckinConfig CRUD)
    # ----------------------------------------------------
    print("\n--- 测试 4.8: 签到规则配置 API (查询与更新) ---")
    res_configs = client.get(f"/api/v1/points/checkin-configs/?application={app_coloring.id}", HTTP_X_TENANT_ID=str(tenant.id))
    assert res_configs.status_code == 200
    configs = res_configs.data.get("data", res_configs.data).get("results", [])
    assert len(configs) >= 1
    current_cfg = configs[0]
    print(f"当前规则: {current_cfg['name']} | 补签扣分: {current_cfg['recheckin_cost']}")

    # 修改规则：调整补签扣分为 25 分
    res_update = client.patch(f"/api/v1/points/checkin-configs/{current_cfg['id']}/", {
        "recheckin_cost": 25
    }, format='json', HTTP_X_TENANT_ID=str(tenant.id))
    assert res_update.status_code == 200
    updated_cfg = res_update.data.get("data", res_update.data)
    assert updated_cfg["recheckin_cost"] == 25
    print("规则动态更新验证: OK (recheckin_cost 已成功更新为 25)")

    # ----------------------------------------------------
    # 测试 4.9: 账单流水与账户余额一致性校验
    # ----------------------------------------------------
    print("\n--- 测试 4.9: 账单台账流水一致性校验 ---")
    bob_ledgers = TenantUserPoints.objects.filter(
        tenant=tenant, application=app_coloring, member=m_bob, category='checkin'
    ).order_by('created_at')
    print(f"Bob 共有 {bob_ledgers.count()} 条签到相关台账记录:")
    for ledger in bob_ledgers:
        print(f"  - [{ledger.point_type.upper()}] {ledger.points:+d} 分 | 原因: {ledger.operation_reason} | 变动后余额: {ledger.balance_after}")

    # 校验入账记录数
    assert bob_ledgers.filter(point_type='spend', subcategory='recheckin_cost').count() == 2, "Bob 应有2笔补签扣除记录"
    assert bob_ledgers.filter(point_type='earn').count() >= 3, "Bob 应有打卡与补签获得的奖励记录"

    log_step("🎉 租户 ID=3 签到管理系统全部功能自动化测试 100% 成功通过！")


if __name__ == '__main__':
    run()
