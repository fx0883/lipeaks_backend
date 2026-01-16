"""
21天自律打卡 - 种子数据脚本
创建21个系统预设主题

使用方法:
    python scripts/seed_21day_themes.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lipeaks_backend.settings')
import django
django.setup()

from check_system.models import TaskCategory

# 21天自律打卡主题数据（来自前端 data.js）
THEMES = [
    {'id': 1, 'name': '觉醒的自我', 'icon': '🔮', 'color': '#8B5CF6', 
     'goal': '提升自我认知，了解内心真实想法', 
     'tip': '找一个安静的时间进行自省',
     'quote': '认识你自己，方能掌控人生',
     'form_type': 'text'},
    {'id': 2, 'name': '早睡早起', 'icon': '😴', 'color': '#38BDF8', 
     'goal': '规律作息，精力充沛', 
     'tip': '建议22:30前入睡，保证7-8小时睡眠',
     'quote': '早睡早起，身体好，头脑清醒效率高',
     'form_type': 'sleep'},
    {'id': 3, 'name': '健康饮食', 'icon': '🥗', 'color': '#4ADE80', 
     'goal': '均衡营养，感受食物能量', 
     'tip': '多吃绿叶菜，少油少盐',
     'quote': '你吃什么，你就是什么',
     'form_type': 'text'},
    {'id': 4, 'name': '坚持运动', 'icon': '🏃', 'color': '#F97316', 
     'goal': '规律锻炼，提升身体素质', 
     'tip': '每天至少30分钟中等强度运动',
     'quote': '生命在于运动，运动赋予生命活力',
     'form_type': 'exercise'},
    {'id': 5, 'name': '养成阅读习惯', 'icon': '📚', 'color': '#FACC15', 
     'goal': '拓展知识，滋养心灵', 
     'tip': '每天至少20页，早晚固定时间阅读',
     'quote': '书籍是人类进步的阶梯',
     'form_type': 'reading'},
    {'id': 6, 'name': '精进专业技能', 'icon': '💻', 'color': '#1E3A5F', 
     'goal': '持续进步，增强竞争力', 
     'tip': '制定学习计划，分解目标',
     'quote': '技能傍身，走遍天下都不怕',
     'form_type': 'text'},
    {'id': 7, 'name': '时间管理', 'icon': '⏰', 'color': '#4B5563', 
     'goal': '高效利用时间，提升效率', 
     'tip': '使用番茄工作法，集中精力',
     'quote': '时间就是金钱，效率就是生命',
     'form_type': 'work'},
    {'id': 8, 'name': '整理与收纳', 'icon': '🧹', 'color': '#FBCFE8', 
     'goal': '整洁环境，清晰思维', 
     'tip': '每天整理一个小区域',
     'quote': '收纳是对生活的整理，也是对内心的整理',
     'form_type': 'text'},
    {'id': 9, 'name': '培养积极心态', 'icon': '😊', 'color': '#FDBA74', 
     'goal': '发现生活中的美好', 
     'tip': '关注积极面，感受当下',
     'quote': '积极心态是成功的起点',
     'form_type': 'text'},
    {'id': 10, 'name': '积极社交', 'icon': '👥', 'color': '#A3E635', 
     'goal': '拓展人脉，增进连接', 
     'tip': '主动与他人交流',
     'quote': '独行快，众行远',
     'form_type': 'text'},
    {'id': 11, 'name': '理财规划', 'icon': '💰', 'color': '#EAB308', 
     'goal': '培养财富意识', 
     'tip': '记录每笔消费，量入为出',
     'quote': '你不理财，财不理你',
     'form_type': 'finance'},
    {'id': 12, 'name': '勇于突破自我', 'icon': '🚀', 'color': '#EC4899', 
     'goal': '走出舒适区，不断成长', 
     'tip': '每天做一件以前不敢做的事',
     'quote': '成长始于舒适区的边缘',
     'form_type': 'text'},
    {'id': 13, 'name': '自我关爱', 'icon': '💆', 'color': '#C4B5FD', 
     'goal': '善待自己，充电恢复', 
     'tip': '可以是敷面膜、泡澡、看电影',
     'quote': '爱自己是终身浪漫的开始',
     'form_type': 'text'},
    {'id': 14, 'name': '感恩之心', 'icon': '🙏', 'color': '#FB923C', 
     'goal': '培养感恩心态，提升幸福感', 
     'tip': '每天发现一件值得感恩的事',
     'quote': '感恩让平凡变得珍贵',
     'form_type': 'text'},
    {'id': 15, 'name': '持续学习', 'icon': '🎓', 'color': '#06B6D4', 
     'goal': '终身学习，不断进步', 
     'tip': '学外语/摄影/绘画等',
     'quote': '学无止境，进无止境',
     'form_type': 'text'},
    {'id': 16, 'name': '高效工作', 'icon': '💼', 'color': '#1F2937', 
     'goal': '提升工作产出', 
     'tip': '每日三件事，专注重要任务',
     'quote': '专注于重要的少数',
     'form_type': 'work'},
    {'id': 17, 'name': '拓宽眼界', 'icon': '🌍', 'color': '#4F46E5', 
     'goal': '拓展视野，别样体验', 
     'tip': '看纪录片、读新闻、参观展览',
     'quote': '世界那么大，我想去看看',
     'form_type': 'text'},
    {'id': 18, 'name': '情绪管理', 'icon': '🧘', 'color': '#FDA4AF', 
     'goal': '掌控情绪，保持平和', 
     'tip': '深呼吸、运动、冥想或写日记',
     'quote': '情绪稳定是一个人最好的修养',
     'form_type': 'mood'},
    {'id': 19, 'name': '提升表达能力', 'icon': '🎤', 'color': '#10B981', 
     'goal': '清晰表达，有效沟通', 
     'tip': '练习当众讲话或跟朋友交流',
     'quote': '会说话是一种能力，敢说话是一种勇气',
     'form_type': 'text'},
    {'id': 20, 'name': '数字排毒', 'icon': '📵', 'color': '#A16207', 
     'goal': '减少屏幕时间，回归真实', 
     'tip': '离开手机，阅读/散步/运动',
     'quote': '放下手机，拥抱真实世界',
     'form_type': 'text'},
    {'id': 21, 'name': '学会复盘', 'icon': '📝', 'color': '#7C3AED', 
     'goal': '总结经验，持续优化', 
     'tip': '真诚面对自己，计划下一个周期',
     'quote': '复盘是成长最快的方式',
     'form_type': 'text'},
]


def seed_themes():
    """创建或更新21个系统预设主题"""
    created_count = 0
    updated_count = 0
    
    for idx, theme_data in enumerate(THEMES):
        theme, created = TaskCategory.objects.update_or_create(
            name=theme_data['name'],
            is_system=True,
            user=None,
            tenant=None,
            defaults={
                'icon': theme_data['icon'],
                'color': theme_data['color'],
                'goal': theme_data['goal'],
                'tip': theme_data['tip'],
                'quote': theme_data['quote'],
                'form_type': theme_data['form_type'],
                'sort_order': idx + 1,
                'description': theme_data['goal'],
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {theme.name}")
        else:
            updated_count += 1
            print(f"↻ Updated: {theme.name}")
    
    print(f"\nDone! Created: {created_count}, Updated: {updated_count}")
    return created_count, updated_count


if __name__ == '__main__':
    print("Seeding 21-day check-in themes...")
    seed_themes()
