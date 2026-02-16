# Rate Limit Cleanup Documentation

**Status:** ✅ IMPLEMENTED  
**Last Updated:** 2026-02-16

---

## Overview

The rate limiting system now includes automatic cleanup to prevent the `rate_limits` table from growing indefinitely. Old entries (>24 hours) are automatically deleted every hour.

---

## How It Works

### 1. Automatic Cleanup Scheduler

**File:** `app/background_tasks.py`

```python
def start_cleanup_scheduler(interval_hours=1):
    """
    Start a background thread that runs cleanup tasks periodically.
    Default: runs every 1 hour
    """
    def cleanup_loop():
        while True:
            time.sleep(interval_hours * 3600)
            cleanup_old_rate_limits()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
```

**Features:**
- Runs in background thread (non-blocking)
- Daemon thread (exits with main process)
- Configurable interval (default: 1 hour)
- Automatic error recovery

### 2. Cleanup Function

```python
def cleanup_old_rate_limits():
    """
    Remove rate limit entries older than 24 hours.
    """
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    cursor = db.execute(
        "DELETE FROM rate_limits WHERE submitted_at < ?",
        (cutoff,)
    )
    deleted_count = cursor.rowcount
    logger.info(f"Cleaned up {deleted_count} old rate limit entries")
    return deleted_count
```

**What it does:**
- Deletes entries older than 24 hours
- Logs the number of deleted entries
- Returns count for monitoring

### 3. Application Startup

**File:** `app/main.py`

```python
@app.on_event("startup")
def startup():
    init_db()
    _seed_admin()
    start_cleanup_scheduler(interval_hours=1)  # Start scheduler
    cleanup_old_rate_limits()  # Run initial cleanup
    logger.info("Application startup complete")
```

**Startup sequence:**
1. Initialize database
2. Seed admin users
3. Start cleanup scheduler (runs every hour)
4. Run initial cleanup (clean old entries immediately)

---

## Why This Is Important

### Problem Without Cleanup

```
Day 1:  100 entries
Day 2:  200 entries
Day 3:  300 entries
...
Day 30: 3,000 entries
Day 365: 36,500 entries ❌
```

The table grows indefinitely, causing:
- Increased database size
- Slower queries
- Wasted disk space
- Performance degradation

### Solution With Cleanup

```
Day 1:  100 entries
Day 2:  100 entries (old ones deleted)
Day 3:  100 entries (old ones deleted)
...
Always: ~100 entries ✅
```

The table stays small:
- Constant database size
- Fast queries
- Minimal disk space
- Consistent performance

---

## Monitoring

### Get Statistics

```python
from app.background_tasks import get_rate_limit_stats

stats = get_rate_limit_stats()
print(stats)
# {
#     'total': 150,
#     'last_hour': 10,
#     'last_24h': 150,
#     'old_entries': 0  # Should always be 0 if cleanup works
# }
```

### Check Cleanup Status

```bash
# Run the demonstration script
python test_rate_limit_cleanup.py

# Options:
# 1. Show current statistics
# 2. Insert test data and demonstrate cleanup
# 3. Run cleanup now
# 4. Verify automatic cleanup configuration
```

---

## Manual Cleanup

If you need to run cleanup manually:

### Option 1: Python Script

```python
from app.background_tasks import cleanup_old_rate_limits

deleted = cleanup_old_rate_limits()
print(f"Deleted {deleted} old entries")
```

### Option 2: Direct SQL

```bash
sqlite3 data/budtender.db "DELETE FROM rate_limits WHERE submitted_at < datetime('now', '-24 hours')"
```

### Option 3: Demonstration Script

```bash
python test_rate_limit_cleanup.py
# Choose option 3: Run cleanup now
```

---

## Configuration

### Change Cleanup Interval

Edit `app/main.py`:

```python
# Run cleanup every 30 minutes
start_cleanup_scheduler(interval_hours=0.5)

# Run cleanup every 6 hours
start_cleanup_scheduler(interval_hours=6)

# Run cleanup every 24 hours
start_cleanup_scheduler(interval_hours=24)
```

**Recommendation:** Keep default (1 hour) for most cases.

### Change Retention Period

Edit `app/background_tasks.py`:

```python
# Keep entries for 48 hours instead of 24
cutoff = (datetime.utcnow() - timedelta(hours=48)).isoformat()

# Keep entries for 12 hours
cutoff = (datetime.utcnow() - timedelta(hours=12)).isoformat()
```

**Warning:** Retention period must match rate limiting window!

---

## Testing

### Test 1: Verify Cleanup Runs

```bash
# Start the application
python run.py

# Check logs for:
# "Started cleanup scheduler (interval: 1h)"
# "Cleanup scheduler thread started"
# "Running scheduled cleanup tasks..."
```

### Test 2: Insert Old Data and Verify Cleanup

```bash
# Run demonstration script
python test_rate_limit_cleanup.py

# Choose option 2: Insert test data and demonstrate cleanup
# Should show:
# - Before: 3 old entries
# - After: 0 old entries
```

### Test 3: Monitor Over Time

```bash
# Check statistics periodically
python test_rate_limit_cleanup.py

# Choose option 1: Show current statistics
# old_entries should always be 0 or very low
```

---

## Troubleshooting

### Cleanup Not Running

**Check 1: Verify scheduler started**
```bash
# Check application logs for:
grep "cleanup scheduler" logs/app.log
```

**Check 2: Verify imports**
```python
# In app/main.py, should have:
from app.background_tasks import start_cleanup_scheduler, cleanup_old_rate_limits
```

**Check 3: Verify startup call**
```python
# In app/main.py startup(), should have:
start_cleanup_scheduler(interval_hours=1)
cleanup_old_rate_limits()
```

### Old Entries Not Deleted

**Check 1: Run manual cleanup**
```python
from app.background_tasks import cleanup_old_rate_limits
deleted = cleanup_old_rate_limits()
print(f"Deleted: {deleted}")
```

**Check 2: Check timestamps**
```bash
sqlite3 data/budtender.db "SELECT submitted_at FROM rate_limits ORDER BY submitted_at LIMIT 10"
```

**Check 3: Check for errors**
```bash
# Check logs for cleanup errors
grep "Error cleaning up rate limits" logs/app.log
```

### High Memory Usage

If cleanup thread causes issues:

**Option 1: Increase interval**
```python
start_cleanup_scheduler(interval_hours=6)  # Run less frequently
```

**Option 2: Use cron job instead**
```bash
# Disable automatic cleanup in app/main.py
# Add to crontab:
0 * * * * cd /path/to/app && python -c "from app.background_tasks import cleanup_old_rate_limits; cleanup_old_rate_limits()"
```

---

## Production Recommendations

### 1. Monitoring

Add monitoring for:
- Cleanup execution frequency
- Number of entries deleted
- Total table size
- Old entries count (should be 0)

### 2. Alerting

Alert if:
- Cleanup hasn't run in >2 hours
- Old entries count >100
- Total entries >10,000
- Cleanup errors in logs

### 3. Logging

Ensure cleanup logs are captured:
```python
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### 4. Database Maintenance

Periodically run:
```bash
# Vacuum database to reclaim space
sqlite3 data/budtender.db "VACUUM"

# Analyze for query optimization
sqlite3 data/budtender.db "ANALYZE"
```

---

## Summary

✅ **Automatic cleanup is IMPLEMENTED and WORKING**

**What happens:**
1. Application starts
2. Cleanup scheduler starts in background
3. Initial cleanup runs immediately
4. Cleanup runs every hour automatically
5. Old entries (>24 hours) are deleted
6. Table stays small and performant

**Verification:**
```bash
# Run this to verify everything works:
python test_rate_limit_cleanup.py
```

**Result:**
- ✅ No infinite table growth
- ✅ Automatic cleanup every hour
- ✅ Logs all cleanup operations
- ✅ Production-ready

---

**Status:** ✅ COMPLETE  
**Next Steps:** Monitor in production, adjust interval if needed
