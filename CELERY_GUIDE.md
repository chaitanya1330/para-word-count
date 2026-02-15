# Celery, Redis & Celery Beat Setup Guide

This guide explains how to run the Celery worker and Celery Beat scheduler for asynchronous task processing.

## Architecture Overview

```
Django Web Server (Port 8000)
    ↓
    └→ Sends tasks to Redis Queue
        ↓
    ┌─────────────────────────────────────┐
    │      Redis (Message Broker)         │
    │  - Stores task queue                │
    │  - Stores task results              │
    │  - Scheduler coordination           │
    └─────────────────────────────────────┘
        ↑                          ↑
        │                          │
    Celery Worker              Celery Beat Scheduler
    (executes tasks)           (schedules periodic tasks)
```

## Prerequisites

Ensure Redis is running:

```bash
# On Windows with Docker:
docker run -d -p 6379:6379 redis

# Or with WSL2 + Linux:
redis-server

# Check Redis is running:
redis-cli ping  # Should return PONG
```

## Running Celery Worker

The Celery worker picks up tasks from Redis and executes them asynchronously.

### Option 1: Simple Worker (Development)

```bash
cd c:\Users\chaitu\PythonProjets\para-word-count-repo
celery -A para_word_count worker -l info
```

**Output should show:**
```
 -------------- celery@YOUR_COMPUTER v5.3.4
---- **** -----
--- * ***  * -- 
-- * - **** ---
- ** - *** ---
 -------------- [config]
.> app:         para_word_count:0x...
.> transport:   redis://localhost:6379/0
.> results:     redis://localhost:6379/0
.> concurrency: 4 (prefork)
 -------------- [queues]
.> celery           exchange=celery(direct) key=celery
```

### Option 2: Worker with Concurrency Control (Production)

```bash
celery -A para_word_count worker -l info --concurrency=8
```

- `--concurrency=8` - Use 8 parallel workers (adjust based on CPU cores)

### Option 3: Worker with Specific Queue

```bash
celery -A para_word_count worker -Q celery,high_priority -l info
```

### Option 4: High-Performance Setup (Auto-scale)

```bash
celery -A para_word_count worker -l info --autoscale=10,3
```

- `--autoscale=10,3` - Scale between 3-10 workers based on load

## Running Celery Beat Scheduler

Celery Beat schedules periodic tasks to run at specified times.

### Step 1: Create Directory for Beat Database

```bash
mkdir celery_beat_data
```

### Step 2: Start Celery Beat

```bash
celery -A para_word_count beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**For simple file-based scheduler:**

```bash
celery -A para_word_count beat -l info
```

**Output should show:**

```
  celery beat v5.3.4 (fin-leg-ume)
0 <- Local time [UTC]
[Config]
. scheduler -> celery.beat.PersistentScheduler
. db -> celerybeat-schedule
. maxinterval -> 5.00 seconds (5s)

[Schedules]
# v5 <- format
- {name: cleanup-old-paragraphs, schedule: <crontab: 0 0 * * * (m/h/d/dM/MY), args: (), kwargs: {}, options: {}, total run count: 0}
- {name: generate-statistics, schedule: <crontab: 0 1 * * * (m/h/d/dM/MY), args: (), kwargs: {}, options: {}, total run count: 0}

[2024-02-16 00:00:00,000: INFO/MainProcess] beat: Starting...
```

## Scheduled Tasks (Celery Beat)

Your project has two scheduled tasks:

| Task | Schedule | What it Does |
|------|----------|-------------|
| `cleanup-old-paragraphs` | Daily at 00:00 (midnight) | Deletes paragraphs older than 90 days |
| `generate-statistics` | Daily at 01:00 (1 AM) | Generates daily word usage statistics |

### Modifying Schedules

Edit [para_word_count/settings.py](para_word_count/settings.py) in the `CELERY_BEAT_SCHEDULE` section:

```python
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-paragraphs': {
        'task': 'user.tasks.cleanup_old_paragraphs',
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
    'generate-statistics': {
        'task': 'user.tasks.generate_daily_statistics',
        'schedule': crontab(hour=1, minute=0),  # 1 AM
    },
}
```

### Crontab Examples

```python
from celery.schedules import crontab

# Every hour
crontab(minute=0)

# Every 5 minutes
crontab(minute='*/5')

# Every day at 6 AM
crontab(hour=6, minute=0)

# Every Monday at 9 AM
crontab(hour=9, minute=0, day_of_week=1)

# Every 1st of month at midnight
crontab(hour=0, minute=0, day_of_month=1)

# Every 15 minutes
crontab(minute='*/15')
```

## Async Task Execution

When a user submits a paragraph, it's now processed **asynchronously**:

```python
# In views.py
tokenize_paragraph.delay(paragraph.id)  # Sends to Redis queue
# User gets response immediately ✓
# Worker processes in background
```

**Before**: User waits for processing (blocking)
**After**: User gets instant response, processing happens in background

## Monitoring

### Check Celery Worker Status

```bash
celery -A para_word_count inspect active
```

**See active tasks:**

```bash
celery -A para_word_count inspect active_queues
```

**Check worker stats:**

```bash
celery -A para_word_count inspect stats
```

### Check Redis Queue

```bash
redis-cli
> KEYS *  # List all keys
> LLEN celery  # Check task queue length
> PING  # Test connection
```

## Running Everything Together (Production)

### Terminal 1 - Django Web Server
```bash
python manage.py runserver
```

### Terminal 2 - Redis (if not Docker)
```bash
redis-server
```

### Terminal 3 - Celery Worker
```bash
celery -A para_word_count worker -l info
```

### Terminal 4 - Celery Beat
```bash
celery -A para_word_count beat -l info
```

## Troubleshooting

### Worker not picking up tasks?

1. Check Redis is running: `redis-cli ping`
2. Check worker is connected: `celery -A para_word_count inspect active_queues`
3. Verify CELERY_BROKER_URL in settings.py: `redis://localhost:6379/0`

### Beat not running scheduled tasks?

1. Check beat is running: Terminal should show schedule info
2. Check system time is correct
3. Verify task exists: `celery -A para_word_count inspect registered`

### Tasks failing?

Check worker output for errors or:

```bash
celery -A para_word_count inspect active
```

### "Connection refused" error?

Start Redis:

```bash
# Docker
docker run -d -p 6379:6379 redis

# Or WSL
redis-server
```

## Deployment with Docker Compose

Your [docker-compose.yml](docker-compose.yml) includes Redis. Just run:

```bash
docker-compose up --build
```

This starts:
- Django web server
- PostgreSQL database
- Redis broker
- (Celery worker needs separate command)

Inside Docker, start worker:

```bash
docker exec -it para-word-count-web celery -A para_word_count worker -l info
```

Start beat:

```bash
docker exec -it para-word-count-web celery -A para_word_count beat -l info
```

## Performance Tips

1. **Increase worker concurrency** if you have multiple CPU cores
2. **Use task routing** to separate long/short tasks
3. **Enable result backend pruning** to clean old results
4. **Monitor Redis memory** usage and increase if needed
5. **Use worker pool** with gevent for I/O-bound tasks

```bash
# Gevent-based worker for I/O-bound tasks
celery -A para_word_count worker -l info -P gevent
```

## Next Steps

1. Start Redis
2. Start Celery Worker: `celery -A para_word_count worker -l info`
3. Start Celery Beat: `celery -A para_word_count beat -l info`
4. Test by submitting a paragraph - should process in background instantly
5. Check worker terminal to see task execution

---

**Last Updated**: 2024-02-16  
**Celery Version**: 5.3.4  
**Redis Version**: 5.0+
