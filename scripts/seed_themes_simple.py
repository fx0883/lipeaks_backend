"""Seed 21 themes - simplified script for Django shell"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lipeaks_backend.settings')

import django
django.setup()

from check_system.models import TaskCategory

# Minimal theme data
THEMES = [
    (1, 'Awakening Self', '🔮', '#8B5CF6', 'text'),
    (2, 'Early Sleep', '😴', '#38BDF8', 'sleep'),
    (3, 'Healthy Eating', '🥗', '#4ADE80', 'text'),
    (4, 'Exercise', '🏃', '#F97316', 'exercise'),
    (5, 'Reading', '📚', '#FACC15', 'reading'),
    (6, 'Skills', '💻', '#1E3A5F', 'text'),
    (7, 'Time Management', '⏰', '#4B5563', 'work'),
    (8, 'Organizing', '🧹', '#FBCFE8', 'text'),
    (9, 'Positive Mind', '😊', '#FDBA74', 'text'),
    (10, 'Social', '👥', '#A3E635', 'text'),
    (11, 'Finance', '💰', '#EAB308', 'finance'),
    (12, 'Break Limits', '🚀', '#EC4899', 'text'),
    (13, 'Self Care', '💆', '#C4B5FD', 'text'),
    (14, 'Gratitude', '🙏', '#FB923C', 'text'),
    (15, 'Learning', '🎓', '#06B6D4', 'text'),
    (16, 'Efficient Work', '💼', '#1F2937', 'work'),
    (17, 'Broaden View', '🌍', '#4F46E5', 'text'),
    (18, 'Mood Control', '🧘', '#FDA4AF', 'mood'),
    (19, 'Expression', '🎤', '#10B981', 'text'),
    (20, 'Digital Detox', '📵', '#A16207', 'text'),
    (21, 'Review', '📝', '#7C3AED', 'text'),
]

created = 0
for idx, (id_, name, icon, color, form_type) in enumerate(THEMES):
    obj, was_created = TaskCategory.objects.update_or_create(
        name=name,
        is_system=True,
        user=None,
        tenant=None,
        defaults={
            'icon': icon,
            'color': color,
            'form_type': form_type,
            'sort_order': idx + 1,
        }
    )
    if was_created:
        created += 1
        print(f"+ {name}")
    else:
        print(f"= {name}")

print(f"\nTotal: {len(THEMES)}, Created: {created}")
