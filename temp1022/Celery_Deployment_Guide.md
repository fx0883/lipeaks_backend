# Celery Deployment Guide for Feedback System

## Overview

The Feedback System uses Celery for asynchronous task processing, particularly for sending emails. This guide covers how to deploy and manage Celery workers.

## Prerequisites

1. Redis server running (used as message broker)
2. All dependencies installed from `feedbacks/requirements.txt`

## Running Celery Workers

### Development Environment

#### 1. Start Redis
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

#### 2. Start Celery Worker
```bash
# In your project directory
celery -A core worker -l info --queue=feedbacks,celery
```

#### 3. Start Celery Beat (for periodic tasks)
```bash
# In another terminal
celery -A core beat -l info
```

### Production Environment

#### Using Supervisor

Create `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A core worker -l info --queue=feedbacks,celery
directory=/path/to/lipeaks_backend
user=www-data
numprocs=2
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998

[program:celery_beat]
command=/path/to/venv/bin/celery -A core beat -l info
directory=/path/to/lipeaks_backend
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
priority=999

[group:celery]
programs=celery_worker,celery_beat
priority=999
```

Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery:*
```

#### Using systemd

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Service
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/etc/default/celery
WorkingDirectory=/path/to/lipeaks_backend
ExecStart=/bin/sh -c '${CELERY_BIN} -A $CELERY_APP multi start $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} \
    --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} -A $CELERY_APP multi restart $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} \
    --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/default/celery`:

```bash
# Names of nodes to start
CELERYD_NODES="worker1 worker2"

# Absolute path to "manage.py"
CELERY_BIN="/path/to/venv/bin/celery"

# App instance to use
CELERY_APP="core"

# Where to chdir at start
CELERYD_CHDIR="/path/to/lipeaks_backend/"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8 --queue=feedbacks,celery"

# %n will be replaced with the first part of the nodename.
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Workers should run as an unprivileged user.
CELERYD_USER="www-data"
CELERYD_GROUP="www-data"

# If enabled pid and log directories will be created if missing,
# and owned by the userid/group configured.
CELERY_CREATE_DIRS=1
```

Create Celery Beat service `/etc/systemd/system/celerybeat.service`:

```ini
[Unit]
Description=Celery Beat Service
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
EnvironmentFile=/etc/default/celery
WorkingDirectory=/path/to/lipeaks_backend
ExecStart=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} beat \
    --pidfile=${CELERYBEAT_PID_FILE} \
    --logfile=${CELERYBEAT_LOG_FILE} \
    --loglevel=${CELERYD_LOG_LEVEL}'
Restart=always

[Install]
WantedBy=multi-user.target
```

Add to `/etc/default/celery`:
```bash
# Celery Beat
CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"
```

Start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery celerybeat
sudo systemctl start celery celerybeat
```

## Docker Deployment

### docker-compose.yml Addition

```yaml
version: '3.8'

services:
  # ... existing services ...
  
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    networks:
      - backend
  
  celery_worker:
    build: .
    command: celery -A core worker -l info --queue=feedbacks,celery
    volumes:
      - .:/app
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - db
    networks:
      - backend
    restart: always
  
  celery_beat:
    build: .
    command: celery -A core beat -l info
    volumes:
      - .:/app
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - db
    networks:
      - backend
    restart: always

volumes:
  redis_data:

networks:
  backend:
```

## Monitoring

### 1. Flower (Web-based monitoring)

Install:
```bash
pip install flower
```

Run:
```bash
celery -A core flower --port=5555
```

Access at: http://localhost:5555

### 2. Command Line Monitoring

```bash
# Check worker status
celery -A core inspect active

# Check scheduled tasks
celery -A core inspect scheduled

# Check task statistics
celery -A core inspect stats

# Purge all tasks
celery -A core purge
```

### 3. Django Admin Integration

The system logs all email sending attempts in the `FeedbackEmailLog` model, which can be viewed in Django Admin.

## Troubleshooting

### Common Issues

1. **Tasks not executing**
   - Check Redis connection: `redis-cli ping`
   - Verify worker is running: `ps aux | grep celery`
   - Check logs: `/var/log/celery/worker.log`

2. **Email sending failures**
   - Check SMTP settings in Django settings
   - Verify email templates exist
   - Check `FeedbackEmailLog` for error messages

3. **Memory issues**
   - Limit concurrent tasks: `--concurrency=4`
   - Set task time limits: `--time-limit=300`
   - Monitor with Flower

4. **Task retries failing**
   - Check retry delays in task definitions
   - Verify broker connection stability
   - Monitor dead letter queue

### Debug Mode

Run worker with debug logging:
```bash
celery -A core worker -l debug --queue=feedbacks,celery
```

### Task Testing

Test email sending manually:
```python
# Django shell
from feedbacks.tasks import send_feedback_reply_email
result = send_feedback_reply_email.delay(reply_id=1)
print(result.get())  # Wait for result
```

## Performance Tuning

### Worker Configuration

```bash
# Production optimized settings
celery -A core worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --time-limit=300 \
  --soft-time-limit=240 \
  --queue=feedbacks,celery \
  --without-gossip \
  --without-mingle \
  --without-heartbeat
```

### Redis Configuration

Add to `/etc/redis/redis.conf`:
```
maxmemory 256mb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for cache-only use
```

### Task Routing

Configure in Django settings:
```python
CELERY_TASK_ROUTES = {
    'feedbacks.tasks.send_feedback_reply_email': {'queue': 'email'},
    'feedbacks.tasks.send_status_change_email': {'queue': 'email'},
    'feedbacks.tasks.send_verification_email': {'queue': 'email'},
    'feedbacks.tasks.cleanup_old_email_logs': {'queue': 'maintenance'},
}
```

Run specialized workers:
```bash
# Email worker with higher priority
celery -A core worker -Q email -l info --concurrency=2

# Maintenance worker
celery -A core worker -Q maintenance -l info --concurrency=1
```

## Security Considerations

1. **Redis Security**
   - Enable authentication in Redis
   - Use SSL/TLS for connections
   - Restrict network access

2. **Task Security**
   - Validate all task inputs
   - Use task signatures for sensitive operations
   - Implement rate limiting

3. **Monitoring Security**
   - Secure Flower with authentication
   - Use HTTPS for web interfaces
   - Restrict admin access

## Backup and Recovery

### Backup Task Results
```bash
# Export pending tasks
celery -A core inspect active --json > active_tasks.json

# Backup Redis
redis-cli --rdb /backup/redis_backup.rdb
```

### Recovery
```bash
# Restore Redis
sudo systemctl stop redis
sudo cp /backup/redis_backup.rdb /var/lib/redis/dump.rdb
sudo systemctl start redis
```

## Scaling Considerations

1. **Horizontal Scaling**
   - Add more worker nodes
   - Use Redis Cluster for high availability
   - Implement task routing by priority

2. **Vertical Scaling**
   - Increase worker concurrency
   - Optimize task execution time
   - Use connection pooling

3. **Queue Management**
   - Separate queues by priority
   - Implement dead letter queues
   - Monitor queue lengths

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Test Celery Tasks
  run: |
    celery -A core worker --loglevel=info --detach
    python manage.py test feedbacks.tests.test_tasks
    celery -A core control shutdown
```

### Pre-deployment Checklist
- [ ] Test all Celery tasks
- [ ] Verify Redis connection
- [ ] Check email configurations
- [ ] Validate task routing
- [ ] Test retry mechanisms
- [ ] Monitor memory usage
