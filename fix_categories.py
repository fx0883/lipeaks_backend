import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from check_system.models import TaskCategory

# Format: (name_en, icon, color, form_type, desc_en, name_zh, desc_zh, 
#          name_ja, desc_ja, name_ko, desc_ko, name_fr, desc_fr)
THEMES = [
    ('Awakening Self', '🔮', '#8B5CF6', 'text', 'Enhance self-awareness', '觉醒自我', '提升自我意识', 
     '自己覚醒', '自己意識を高める', '자아 각성', '자아 의식 고취', 'Éveil de soi', 'Développer la conscience de soi'),
    ('Early Sleep', '😴', '#38BDF8', 'sleep', 'Regular sleep schedule', '早睡早起', '规律的睡眠作息',
     '早寝早起き', '規則正しい睡眠', '일찍 자고 일찍 일어나기', '규칙적인 수면 습관', 'Se coucher tôt', 'Rythme de sommeil régulier'),
    ('Healthy Eating', '🥗', '#4ADE80', 'text', 'Balanced nutrition', '健康饮食', '均衡营养',
     '健康的な食事', 'バランスの取れた栄養', '건강한 식습관', '균형 잡힌 영양', 'Alimentation saine', 'Nutrition équilibrée'),
    ('Exercise', '🏃', '#F97316', 'exercise', 'Regular workout', '运动健身', '规律锻炼',
     '運動', '定期的なワークアウト', '운동', '규칙적인 운동', 'Exercice physique', 'Entraînement régulier'),
    ('Reading', '📚', '#FACC15', 'reading', 'Knowledge and wisdom', '阅读学习', '增长知识和智慧',
     '読書', '知識と知恵', '독서', '지식과 지혜', 'Lecture', 'Connaissance et sagesse'),
    ('Skills', '💻', '#1E3A5F', 'text', 'Professional growth', '技能提升', '专业成长',
     'スキルアップ', '専門的な成長', '기술 향상', '전문적 성장', 'Compétences', 'Développement professionnel'),
    ('Time Management', '⏰', '#4B5563', 'work', 'Efficient time use', '时间管理', '高效利用时间',
     '時間管理', '時間の有効活用', '시간 관리', '효율적인 시간 사용', 'Gestion du temps', 'Utilisation efficace du temps'),
    ('Organizing', '🧹', '#FBCFE8', 'text', 'Clean environment', '整理收纳', '整洁的环境',
     '整理整頓', '清潔な環境', '정리 정돈', '깨끗한 환경', 'Rangement', 'Environnement propre'),
    ('Positive Mind', '😊', '#FDBA74', 'text', 'Optimistic attitude', '积极心态', '保持乐观态度',
     '前向きな心', '楽観的な態度', '긍정적인 마음', '낙관적인 태도', 'Pensée positive', 'Attitude optimiste'),
    ('Social', '👥', '#A3E635', 'text', 'Build connections', '社交交流', '建立人际关系',
     '社交', 'つながりを築く', '사교 활동', '인맥 쌓기', 'Vie sociale', 'Tisser des liens'),
    ('Finance', '💰', '#EAB308', 'finance', 'Financial planning', '理财规划', '财务规划',
     '資産管理', '財務計画', '재무 관리', '재무 계획', 'Finances', 'Planification financière'),
    ('Break Limits', '🚀', '#EC4899', 'text', 'Push boundaries', '突破极限', '挑战自我边界',
     '限界突破', '境界を押し広げる', '한계 돌파', '자신의 한계 도전', 'Dépasser ses limites', 'Repousser les frontières'),
    ('Self Care', '💆', '#C4B5FD', 'text', 'Self love', '自我关爱', '爱护自己',
     'セルフケア', '自分を愛する', '자기 관리', '자신을 사랑하기', 'Soin de soi', 'S\'aimer soi-même'),
    ('Gratitude', '🙏', '#FB923C', 'text', 'Thankful heart', '感恩之心', '心怀感激',
     '感謝の心', '感謝する', '감사하는 마음', '감사하기', 'Gratitude', 'Cœur reconnaissant'),
    ('Learning', '🎓', '#06B6D4', 'text', 'Lifelong learning', '终身学习', '持续学习成长',
     '生涯学習', '継続的な学び', '평생 학습', '지속적인 배움', 'Apprentissage', 'Apprentissage continu'),
    ('Efficient Work', '💼', '#1F2937', 'work', 'Productivity', '高效工作', '提升工作效率',
     '効率的な仕事', '生産性向上', '효율적인 업무', '생산성', 'Travail efficace', 'Productivité'),
    ('Broaden View', '🌍', '#4F46E5', 'text', 'Expand horizons', '拓宽视野', '开阔眼界',
     '視野を広げる', '新たな視点', '시야 넓히기', '식견 넓히기', 'Élargir ses horizons', 'Ouvrir son esprit'),
    ('Mood Control', '🧘', '#FDA4AF', 'mood', 'Emotional stability', '情绪管理', '保持情绪稳定',
     '感情コントロール', '情緒の安定', '감정 조절', '정서적 안정', 'Gestion de l\'humeur', 'Stabilité émotionnelle'),
    ('Expression', '🎤', '#10B981', 'text', 'Clear communication', '表达能力', '清晰沟通',
     '表現力', '明確なコミュニケーション', '표현력', '명확한 의사소통', 'Expression', 'Communication claire'),
    ('Digital Detox', '📵', '#A16207', 'text', 'Screen time control', '数字断舍', '控制屏幕时间',
     'デジタルデトックス', 'スクリーンタイムの管理', '디지털 디톡스', '스크린 타임 조절', 'Détox numérique', 'Contrôle du temps d\'écran'),
    ('Review', '📝', '#7C3AED', 'text', 'Reflect and improve', '复盘反思', '反思和改进',
     '振り返り', '内省と改善', '회고', '반성과 개선', 'Bilan', 'Réflexion et amélioration'),
]

@transaction.atomic
def fix():
    # 2. 修复原始记录 (ID 1-21)
    
    print("Repairing original categories (ID 1-21) with new translations...")
    for i, (name_en, icon, color, form_type, desc_en, name_zh, desc_zh, name_ja, desc_ja, name_ko, desc_ko, name_fr, desc_fr) in enumerate(THEMES):
        sort_order = i + 1
        
        # 查找对应的旧记录
        cat = TaskCategory.objects.filter(sort_order=sort_order, is_system=True, id__lte=21).first()
        
        if not cat:
            print(f"Warning: Could not find original category for sort_order {sort_order}. Creating new...")
            cat = TaskCategory(is_system=True, sort_order=sort_order)
        else:
             print(f"Updating ID {cat.id} for {name_en}...")

        # 更新基本字段
        cat.icon = icon
        cat.color = color
        cat.form_type = form_type
        cat.tenant = None
        cat.save() 
        
        # 强制设置翻译
        # zh-hans
        cat.set_current_language('zh-hans')
        cat.name = name_zh
        cat.description = desc_zh
        cat.goal = ''
        cat.tip = ''
        cat.quote = ''
        cat.save()
        
        # en
        cat.set_current_language('en')
        cat.name = name_en
        cat.description = desc_en
        cat.goal = ''
        cat.tip = ''
        cat.quote = ''
        cat.save()
        
        # zh-hant (Reuse zh-hans for now)
        cat.set_current_language('zh-hant')
        cat.name = name_zh
        cat.description = desc_zh
        cat.goal = ''
        cat.tip = ''
        cat.quote = ''
        cat.save()

        # ja
        cat.set_current_language('ja')
        cat.name = name_ja
        cat.description = desc_ja
        cat.goal = ''
        cat.tip = ''
        cat.quote = ''
        cat.save()

        # ko
        cat.set_current_language('ko')
        cat.name = name_ko
        cat.description = desc_ko
        cat.goal = ''
        cat.tip = ''
        cat.quote = ''
        cat.save()

        # fr
        cat.set_current_language('fr')
        cat.name = name_fr
        cat.description = desc_fr
        cat.goal = ''
        cat.tip = ''
        cat.quote = ''
        cat.save()

    print("Translation update completed.")

if __name__ == '__main__':
    fix()
