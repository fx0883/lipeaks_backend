import os
import django
from django.db import IntegrityError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from check_system.models import TaskCategory

try:
    c = TaskCategory(is_system=True)
    c.set_current_language('en')
    c.name = 'Test Name'
    c.description = 'Test Desc'
    c.goal = ''
    c.tip = ''
    c.quote = ''
    c.save()
    print('Success')
except Exception as e:
    print(f'Error Type: {type(e)}')
    print(f'Error Message: {e}')
