"""
在租户ID=3下初始化丰富的积分管理测试数据
涵盖：
1. 两个应用的完整积分等级阶梯（填色花园 6阶梯，自然拼读 3阶梯）
2. 5名活跃测试成员与租户画像
3. 多个应用的专属积分账户与匹配的等级
4. 丰富的历史台账流水明细
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from django.db import models

from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from points.models import (
    TenantUserProfile, TenantUserPoints, ApplicationUserLevel,
    AppUserPointsAccount
)

def run():
    print("=" * 60)
    print("开始在 租户ID=3 下创建完整的积分测试数据")
    print("=" * 60)

    tenant = Tenant.objects.get(id=3)
    admin_user = User.objects.filter(username='admin_tianse').first() or User.objects.filter(is_superuser=True).first()
    print(f"当前租户: [{tenant.id}] {tenant.name} ({tenant.code})")

    # 获取当前租户下的应用
    apps = list(Application.objects.filter(tenant=tenant))
    if not apps:
        print("未找到租户下的应用，自动创建...")
        app1 = Application.objects.create(
            tenant=tenant, name="填色花园", code="001", status="active", description="趣味填色填图互动应用"
        )
        app2 = Application.objects.create(
            tenant=tenant, name="自然拼读", code="pinged", status="active", description="儿童英语自然拼读学习应用"
        )
        apps = [app1, app2]
    
    app_coloring = next((a for a in apps if a.code == '001' or '填色' in a.name), apps[0])
    app_phonics = next((a for a in apps if a.id != app_coloring.id), None)
    if not app_phonics:
        app_phonics = Application.objects.create(
            tenant=tenant, name="自然拼读", code="pinged", status="active", description="英语拼读应用"
        )
    print(f"应用1 (主测): [{app_coloring.id}] {app_coloring.name} ({app_coloring.code})")
    print(f"应用2 (隔离测试): [{app_phonics.id}] {app_phonics.name} ({app_phonics.code})")

    # 1. 配置「填色花园」的 6 级成长阶梯
    coloring_levels_config = [
        {
            "level_name": "青铜学员",
            "level_code": "LV_BRONZE",
            "level_order": 1,
            "min_points": 0,
            "max_points": 499,
            "icon": "application/images/level_bronze.png",
            "level_color": "#CD7F32",
            "level_description": "初入填色花园的新手画师，享新手专属每日涂色调色板。",
            "is_default": True,
        },
        {
            "level_name": "白银达人",
            "level_code": "LV_SILVER",
            "level_order": 2,
            "min_points": 500,
            "max_points": 1499,
            "icon": "application/images/level_silver.png",
            "level_color": "#A0A0A0",
            "level_description": "涂色小能手，解锁渐变色填充工具与社区点赞双倍积分。",
            "is_default": False,
        },
        {
            "level_name": "黄金大师",
            "level_code": "LV_GOLD",
            "level_order": 3,
            "min_points": 1500,
            "max_points": 3999,
            "icon": "application/images/level_gold.png",
            "level_color": "#FFD700",
            "level_description": "熟练掌握色彩美学，作品可获得首页画廊轮播推荐机会。",
            "is_default": False,
        },
        {
            "level_name": "铂金精英",
            "level_code": "LV_PLATINUM",
            "level_order": 4,
            "min_points": 4000,
            "max_points": 7999,
            "icon": "application/images/level_platinum.png",
            "level_color": "#00CED1",
            "level_description": "精英画师，享高级滤镜导出、无限次撤销历史特权。",
            "is_default": False,
        },
        {
            "level_name": "璀璨钻石",
            "level_code": "LV_DIAMOND",
            "level_order": 5,
            "min_points": 8000,
            "max_points": 14999,
            "icon": "application/images/level_diamond.png",
            "level_color": "#1E90FF",
            "level_description": "殿堂级艺术大师，享专属动态勋章头饰与定制签名水印。",
            "is_default": False,
        },
        {
            "level_name": "王者至尊",
            "level_code": "LV_CROWN",
            "level_order": 6,
            "min_points": 15000,
            "max_points": None,
            "icon": "application/images/level_crown.png",
            "level_color": "#FF4500",
            "level_description": "登峰造极的王者画皇，拥有全套高级线稿库永久免费解锁特权。",
            "is_default": False,
        },
    ]

    print("\n--- 1. 配置「填色花园」应用积分等级 ---")
    coloring_levels = []
    for cfg in coloring_levels_config:
        lvl, created = ApplicationUserLevel.objects.update_or_create(
            tenant=tenant,
            application=app_coloring,
            level_order=cfg["level_order"],
            defaults={
                "level_name": cfg["level_name"],
                "level_code": cfg["level_code"],
                "min_points": cfg["min_points"],
                "max_points": cfg["max_points"],
                "icon": cfg["icon"],
                "level_color": cfg["level_color"],
                "level_description": cfg["level_description"],
                "is_default": cfg["is_default"],
                "is_active": True,
            }
        )
        status = "已创建" if created else "已更新"
        print(f"  [{status}] 阶梯 {lvl.level_order}: {lvl.level_name} ({lvl.level_code}) [{lvl.min_points} - {lvl.max_points or '无上限'}]")
        coloring_levels.append(lvl)

    # 2. 配置「自然拼读」的 3 级成长阶梯
    phonics_levels_config = [
        {
            "level_name": "拼读萌新",
            "level_code": "PIN_NOVICE",
            "level_order": 1,
            "min_points": 0,
            "max_points": 499,
            "icon": "application/images/level_bronze.png",
            "level_color": "#CD7F32",
            "level_description": "学习26个英文字母基本发音与短元音规则。",
            "is_default": True,
        },
        {
            "level_name": "词根探索者",
            "level_code": "PIN_EXPLORER",
            "level_order": 2,
            "min_points": 500,
            "max_points": 1999,
            "icon": "application/images/level_silver.png",
            "level_color": "#A0A0A0",
            "level_description": "掌握辅音丛与常见长元音组合拼读技巧。",
            "is_default": False,
        },
        {
            "level_name": "发音大师",
            "level_code": "PIN_MASTER",
            "level_order": 3,
            "min_points": 2000,
            "max_points": None,
            "icon": "application/images/level_gold.png",
            "level_color": "#FFD700",
            "level_description": "自主朗读分级绘本，标准美式发音达标评级。",
            "is_default": False,
        },
    ]

    print("\n--- 2. 配置「自然拼读」应用积分等级 ---")
    phonics_levels = []
    for cfg in phonics_levels_config:
        lvl, created = ApplicationUserLevel.objects.update_or_create(
            tenant=tenant,
            application=app_phonics,
            level_order=cfg["level_order"],
            defaults={
                "level_name": cfg["level_name"],
                "level_code": cfg["level_code"],
                "min_points": cfg["min_points"],
                "max_points": cfg["max_points"],
                "icon": cfg["icon"],
                "level_color": cfg["level_color"],
                "level_description": cfg["level_description"],
                "is_default": cfg["is_default"],
                "is_active": True,
            }
        )
        status = "已创建" if created else "已更新"
        print(f"  [{status}] 阶梯 {lvl.level_order}: {lvl.level_name} ({lvl.level_code}) [{lvl.min_points} - {lvl.max_points or '无上限'}]")
        phonics_levels.append(lvl)

    # 3. 创建测试成员与租户用户档案
    print("\n--- 3. 准备测试成员与租户档案 ---")
    members_data = [
        {"username": "Mike@qq.com", "email": "Mike@qq.com"},
        {"username": "alice_art", "email": "alice_art@test.com"},
        {"username": "bob_color", "email": "bob_color@test.com"},
        {"username": "carol_phonic", "email": "carol_phonic@test.com"},
        {"username": "david_master", "email": "david_master@test.com"},
    ]

    test_members = []
    for md in members_data:
        member = Member.objects.filter(tenant=tenant, username=md["username"]).first()
        if not member:
            member = Member.objects.create_user(
                username=md["username"],
                email=md["email"],
                password="TestPassword123!",
                tenant=tenant
            )
            print(f"  [创建成员] {member.username} ({member.email})")
        else:
            print(f"  [现有成员] {member.username} ({member.email})")
        test_members.append(member)

        # 确保 TenantUserProfile 存在
        profile, p_created = TenantUserProfile.objects.get_or_create(
            tenant=tenant,
            member=member,
            defaults={
                "total_points": 0,
                "available_points": 0,
                "is_points_enabled": True
            }
        )

    # 4. 为每个成员建立应用积分账户与初始积分及匹配的等级
    print("\n--- 4. 为成员建立应用积分账户并匹配等级 ---")
    
    # 模拟不同的积分档次分布：
    # Mike: 填色 320分 -> 青铜学员；拼读 150分 -> 拼读萌新
    # Alice: 填色 980分 -> 白银达人
    # Bob: 填色 2650分 -> 黄金大师
    # Carol: 填色 5800分 -> 铂金精英；拼读 2300分 -> 发音大师
    # David: 填色 16800分 -> 王者至尊
    accounts_plan = [
        {
            "member": test_members[0], # Mike
            "app": app_coloring,
            "total_points": 320,
            "available_points": 320,
            "earned_total": 420,
            "spent_total": 100,
            "desc": "青铜阶梯学员"
        },
        {
            "member": test_members[0], # Mike
            "app": app_phonics,
            "total_points": 150,
            "available_points": 150,
            "earned_total": 150,
            "spent_total": 0,
            "desc": "自然拼读萌新"
        },
        {
            "member": test_members[1], # Alice
            "app": app_coloring,
            "total_points": 980,
            "available_points": 880,
            "earned_total": 1080,
            "spent_total": 200,
            "desc": "白银阶梯达人"
        },
        {
            "member": test_members[2], # Bob
            "app": app_coloring,
            "total_points": 2650,
            "available_points": 2150,
            "earned_total": 3150,
            "spent_total": 1000,
            "desc": "黄金阶梯大师"
        },
        {
            "member": test_members[3], # Carol
            "app": app_coloring,
            "total_points": 5800,
            "available_points": 4800,
            "earned_total": 6800,
            "spent_total": 2000,
            "desc": "铂金阶梯精英"
        },
        {
            "member": test_members[3], # Carol
            "app": app_phonics,
            "total_points": 2300,
            "available_points": 2300,
            "earned_total": 2300,
            "spent_total": 0,
            "desc": "自然拼读大师"
        },
        {
            "member": test_members[4], # David
            "app": app_coloring,
            "total_points": 16800,
            "available_points": 15000,
            "earned_total": 21800,
            "spent_total": 6800,
            "desc": "王者至尊画皇"
        },
    ]

    created_accounts = []
    for plan in accounts_plan:
        m = plan["member"]
        app = plan["app"]
        profile = TenantUserProfile.objects.get(tenant=tenant, member=m)
        
        # 匹配对应等级
        matched_level = ApplicationUserLevel.objects.filter(
            tenant=tenant,
            application=app,
            is_active=True,
            min_points__lte=plan["total_points"]
        ).filter(
            models.Q(max_points__isnull=True) | models.Q(max_points__gte=plan["total_points"])
        ).order_by('-level_order').first()

        acct, created = AppUserPointsAccount.objects.update_or_create(
            tenant=tenant,
            application=app,
            member=m,
            defaults={
                "tenant_user_profile": profile,
                "total_points": plan["total_points"],
                "available_points": plan["available_points"],
                "points_earned_total": plan["earned_total"],
                "points_spent_total": plan["spent_total"],
                "current_level": matched_level,
                "is_enabled": True,
                "last_points_update": timezone.now(),
            }
        )
        created_accounts.append(acct)
        status = "已创建" if created else "已更新"
        lvl_name = acct.current_level.level_name if acct.current_level else "无等级"
        print(f"  [{status}] 账户: {m.username} @ {app.name} -> 积分: {acct.available_points}/{acct.total_points} (等级: {lvl_name})")

    # 5. 生成多样化的积分收支流水台账 (TenantUserPoints)
    print("\n--- 5. 生成模拟积分流水记录 ---")
    now = timezone.now()
    
    for acct in created_accounts:
        # 清理旧测试流水
        TenantUserPoints.objects.filter(app_account=acct).delete()
        
        # 严格遵守 balance_before + points == balance_after 的财务平衡
        records = []
        curr = 0
        
        # 1. 签到打卡奖励 (+50)
        p1 = 50
        records.append({
            "point_type": "earn",
            "category": "checkin",
            "points": p1,
            "balance_before": curr,
            "balance_after": curr + p1,
            "reason": "连续签到7日奖励",
            "time_offset": 10,
        })
        curr += p1
        
        # 2. 挑战任务奖励
        p2 = max(acct.total_points - curr, 100)
        records.append({
            "point_type": "earn",
            "category": "task",
            "points": p2,
            "balance_before": curr,
            "balance_after": curr + p2,
            "reason": f"在应用【{acct.application.name}】中完成高阶挑战",
            "time_offset": 5,
        })
        curr += p2

        # 3. 消费/兑换 (-points_spent_total)
        if acct.points_spent_total > 0 and curr >= acct.points_spent_total:
            p3 = -acct.points_spent_total
            records.append({
                "point_type": "spend",
                "category": "exchange",
                "points": p3,
                "balance_before": curr,
                "balance_after": curr + p3,
                "reason": "积分商城兑换【高级笔刷调色包】",
                "time_offset": 2,
            })
            curr += p3

        # 4. 调整差异至当前 available_points
        diff = acct.available_points - curr
        if diff != 0:
            records.append({
                "point_type": "adjust",
                "category": "manual",
                "points": diff,
                "balance_before": curr,
                "balance_after": curr + diff,
                "reason": "系统核算调账或活动补贴",
                "time_offset": 1,
            })
            curr += diff

        for r in records:
            p_rec = TenantUserPoints.objects.create(
                tenant=tenant,
                member=acct.member,
                tenant_user_profile=acct.tenant_user_profile,
                application=acct.application,
                app_account=acct,
                point_type=r["point_type"],
                category=r["category"],
                points=r["points"],
                balance_before=r["balance_before"],
                balance_after=r["balance_after"],
                operation_reason=r["reason"],
                operator_id=admin_user.id if admin_user else 1,
                source_type="system" if r["category"] != "manual" else "manual",
                status="valid"
            )
            # 更新创建时间模拟时间分布
            TenantUserPoints.objects.filter(id=p_rec.id).update(created_at=now - timedelta(days=r["time_offset"]))

        print(f"  [流水生成] 账户 {acct.member.username} @ {acct.application.name} 已生成 {len(records)} 条流水明细")

    print("\n" + "=" * 60)
    print("✅ 租户 3 积分管理测试数据初始化完毕！")
    print(f"   应用等级: 填色花园 ({ApplicationUserLevel.objects.filter(application=app_coloring).count()} 阶梯) / 自然拼读 ({ApplicationUserLevel.objects.filter(application=app_phonics).count()} 阶梯)")
    print(f"   积分账户: 总共 {AppUserPointsAccount.objects.filter(tenant=tenant).count()} 个应用账户")
    print(f"   流水记录: 总共 {TenantUserPoints.objects.filter(tenant=tenant, app_account__isnull=False).count()} 条明细")
    print("=" * 60)

if __name__ == '__main__':
    run()
