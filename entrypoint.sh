#!/bin/sh
set -e

echo "=== [Backend] Waiting for MySQL database (${DB_HOST:-db}:${DB_PORT:-3306})... ==="
until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${DB_HOST:-db}', int('${DB_PORT:-3306}')))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "MySQL is unavailable - sleeping 2s..."
    sleep 2
done

echo "=== [Backend] MySQL is reachable! Running database migrations... ==="
python manage.py migrate --noinput

echo "=== [Backend] Ensuring default superuser exists... ==="
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE:-core.settings_docker}')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('SUPERUSER_USERNAME', 'admin')
email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('SUPERUSER_PASSWORD', 'admin_main')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created successfully.')
else:
    print(f'Superuser {username} already exists.')
" || true

echo "=== [Backend] Collecting static files... ==="
python manage.py collectstatic --noinput || true

echo "=== [Backend] Starting server on 0.0.0.0:8000... ==="
exec "$@"
