"""Seed 21 themes via Django management command"""
from django.core.management.base import BaseCommand
from check_system.models import TaskCategory


THEMES = [
    ('Awakening Self', '\U0001F52E', '#8B5CF6', 'text', 'Enhance self-awareness'),
    ('Early Sleep', '\U0001F634', '#38BDF8', 'sleep', 'Regular sleep schedule'),
    ('Healthy Eating', '\U0001F957', '#4ADE80', 'text', 'Balanced nutrition'),
    ('Exercise', '\U0001F3C3', '#F97316', 'exercise', 'Regular workout'),
    ('Reading', '\U0001F4DA', '#FACC15', 'reading', 'Knowledge and wisdom'),
    ('Skills', '\U0001F4BB', '#1E3A5F', 'text', 'Professional growth'),
    ('Time Management', '\u23F0', '#4B5563', 'work', 'Efficient time use'),
    ('Organizing', '\U0001F9F9', '#FBCFE8', 'text', 'Clean environment'),
    ('Positive Mind', '\U0001F60A', '#FDBA74', 'text', 'Optimistic attitude'),
    ('Social', '\U0001F465', '#A3E635', 'text', 'Build connections'),
    ('Finance', '\U0001F4B0', '#EAB308', 'finance', 'Financial planning'),
    ('Break Limits', '\U0001F680', '#EC4899', 'text', 'Push boundaries'),
    ('Self Care', '\U0001F486', '#C4B5FD', 'text', 'Self love'),
    ('Gratitude', '\U0001F64F', '#FB923C', 'text', 'Thankful heart'),
    ('Learning', '\U0001F393', '#06B6D4', 'text', 'Lifelong learning'),
    ('Efficient Work', '\U0001F4BC', '#1F2937', 'work', 'Productivity'),
    ('Broaden View', '\U0001F30D', '#4F46E5', 'text', 'Expand horizons'),
    ('Mood Control', '\U0001F9D8', '#FDA4AF', 'mood', 'Emotional stability'),
    ('Expression', '\U0001F3A4', '#10B981', 'text', 'Clear communication'),
    ('Digital Detox', '\U0001F4F5', '#A16207', 'text', 'Screen time control'),
    ('Review', '\U0001F4DD', '#7C3AED', 'text', 'Reflect and improve'),
]


class Command(BaseCommand):
    help = 'Seed 21-day check-in themes'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        
        for i, (name, icon, color, form_type, desc) in enumerate(THEMES):
            obj, was_created = TaskCategory.objects.update_or_create(
                name=name,
                is_system=True,
                user=None,
                tenant=None,
                defaults={
                    'icon': icon,
                    'color': color,
                    'form_type': form_type,
                    'description': desc,
                    'sort_order': i + 1,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'+ Created: {name}'))
            else:
                updated += 1
                self.stdout.write(f'= Updated: {name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal: {len(THEMES)}, Created: {created}, Updated: {updated}'))
