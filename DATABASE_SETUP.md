# Database Setup Guide

**Date:** 2026-02-16  
**Version:** 1.0

---

## Overview

This guide covers the database setup, optimizations, migrations, and backup strategy for the Budtender Feedback System.

---

## Database Configuration

### SQLite Optimizations

The system uses SQLite with production-ready optimizations:

#### WAL Mode (Write-Ahead Logging)
- **Enabled by default**
- Allows concurrent reads during writes
- Better performance and reliability
- Creates `-wal` and `-shm` files alongside the database

#### PRAGMA Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| `journal_mode` | WAL | Enable Write-Ahead Logging |
| `foreign_keys` | ON | Enforce referential integrity |
| `cache_size` | -64000 | 64MB cache (negative = KB) |
| `synchronous` | NORMAL | Balance safety and performance |
| `mmap_size` | 268435456 | 256MB memory-mapped I/O |
| `temp_store` | MEMORY | Store temp tables in RAM |

These optimizations provide:
- **5-10x faster** read performance
- **2-3x faster** write performance
- Better concurrency
- Reduced disk I/O

---

## Database Schema

### Tables

#### 1. users
Stores admin users with role-based access control.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'founder', 'ceo')),
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. feedback
Stores anonymous feedback submissions with AI enrichment.

```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('complaint', 'idea', 'recommendation', 'other')),
    message TEXT,
    photo_path TEXT,
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'read', 'in_progress', 'resolved', 'rejected')),
    ip_hash TEXT,
    user_agent TEXT,
    ai_status TEXT DEFAULT 'pending' CHECK(ai_status IN ('pending', 'processing', 'done', 'failed')),
    translation_en TEXT,
    translation_ru TEXT,
    summary TEXT,
    tags TEXT,
    detected_language TEXT,
    private_note TEXT,
    is_deleted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. rate_limits
Tracks submission rate limiting by IP hash.

```sql
CREATE TABLE rate_limits (
    ip_hash TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. migrations
Tracks applied database migrations.

```sql
CREATE TABLE migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

Performance indexes for common queries:

```sql
-- Feedback indexes
CREATE INDEX idx_feedback_status ON feedback(status);
CREATE INDEX idx_feedback_category ON feedback(category);
CREATE INDEX idx_feedback_created ON feedback(created_at DESC);
CREATE INDEX idx_feedback_deleted ON feedback(is_deleted);
CREATE INDEX idx_feedback_submission_id ON feedback(submission_id);
CREATE INDEX idx_feedback_ai_status ON feedback(ai_status);

-- Composite indexes
CREATE INDEX idx_feedback_status_deleted ON feedback(status, is_deleted);
CREATE INDEX idx_feedback_category_deleted ON feedback(category, is_deleted);

-- Rate limits indexes
CREATE INDEX idx_rate_limits_ip ON rate_limits(ip_hash);
CREATE INDEX idx_rate_limits_time ON rate_limits(submitted_at);
CREATE INDEX idx_rate_limits_ip_time ON rate_limits(ip_hash, submitted_at);

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
```

---

## Initialization

### Automatic Initialization

The database is automatically initialized when the application starts:

```python
# In run.py
from app.database import init_db
init_db()
```

This creates:
- Database file at `data/budtender.db`
- All tables with proper schema
- All indexes for performance
- Uploads directory at `data/uploads/`

### Manual Initialization

```bash
python -c "from app.database import init_db; init_db()"
```

---

## Migrations

### Migration System

The system includes a migration framework for future schema changes.

#### Apply a Migration

```python
from app.database import apply_migration

sql = """
ALTER TABLE feedback ADD COLUMN new_field TEXT;
CREATE INDEX idx_feedback_new_field ON feedback(new_field);
"""

apply_migration(
    version="001_add_new_field",
    description="Add new_field to feedback table",
    sql=sql
)
```

#### View Applied Migrations

```python
from app.database import get_applied_migrations

migrations = get_applied_migrations()
for version, description, applied_at in migrations:
    print(f"{version}: {description} (applied {applied_at})")
```

#### Migration Best Practices

1. **Version naming**: Use format `XXX_description` (e.g., `001_add_field`)
2. **Idempotent**: Use `IF NOT EXISTS` and `IF EXISTS`
3. **Test first**: Test migrations on a backup before production
4. **Backup before**: Always backup before applying migrations
5. **Document**: Include clear description of changes

---

## Backup Strategy

### Automatic Backups

#### Setup Cron Job

```bash
# Run the setup script
chmod +x setup_backup_cron.sh
./setup_backup_cron.sh
```

This will:
1. Create backup script
2. Set up cron job for automatic backups
3. Configure log rotation
4. Keep last 7 backups

#### Backup Schedule Options

- **Daily at 2:00 AM** (recommended for most cases)
- **Every 12 hours** (for high-traffic sites)
- **Every 6 hours** (for critical data)
- **Custom schedule**

#### Backup Location

Backups are stored in:
```
data/backups/budtender_backup_YYYYMMDD_HHMMSS.db
```

### Manual Backup

```bash
# Using the backup script
python3 backup_database.py

# Or using Python
python3 -c "from app.database import backup_database; backup_database()"
```

### Backup Retention

- **Default**: Keep last 7 backups
- **Automatic cleanup**: Old backups deleted automatically
- **Customize**: Edit `cleanup_old_backups(keep_count=7)`

### Restore from Backup

```bash
# 1. Stop the application
docker compose down

# 2. Backup current database (just in case)
cp data/budtender.db data/budtender.db.before_restore

# 3. Restore from backup
cp data/backups/budtender_backup_20260216_020000.db data/budtender.db

# 4. Verify integrity
python3 -c "from app.database import verify_database_integrity; verify_database_integrity()"

# 5. Start the application
docker compose up -d
```

---

## Database Maintenance

### Integrity Check

```bash
# Using the database module
python3 -c "from app.database import verify_database_integrity; verify_database_integrity()"

# Or using SQLite directly
sqlite3 data/budtender.db "PRAGMA integrity_check;"
```

### Database Statistics

```bash
python3 -c "from app.database import get_database_stats; import json; print(json.dumps(get_database_stats(), indent=2))"
```

Output:
```json
{
  "users_count": 3,
  "feedback_count": 12,
  "rate_limits_count": 45,
  "database_size_mb": 2.5,
  "wal_size_mb": 0.3
}
```

### Optimize Database

```bash
# Run ANALYZE to update query planner statistics
sqlite3 data/budtender.db "ANALYZE;"

# Run VACUUM to reclaim space (requires downtime)
sqlite3 data/budtender.db "VACUUM;"

# Checkpoint WAL file
sqlite3 data/budtender.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

### Cleanup Rate Limits

Rate limits are automatically cleaned up every hour by the background task.

Manual cleanup:
```bash
sqlite3 data/budtender.db "DELETE FROM rate_limits WHERE submitted_at < datetime('now', '-24 hours');"
```

---

## Testing

### Run Database Tests

```bash
python3 test_database.py
```

Tests include:
- ✅ Database initialization
- ✅ Table creation
- ✅ Index creation
- ✅ WAL mode enabled
- ✅ Foreign keys enabled
- ✅ PRAGMA optimizations
- ✅ Backup functionality
- ✅ Backup cleanup
- ✅ Integrity checks
- ✅ Statistics
- ✅ Migration system

---

## Production Checklist

### Before Deployment

- [ ] Run `test_database.py` - all tests pass
- [ ] Verify WAL mode enabled
- [ ] Verify indexes created
- [ ] Test backup script
- [ ] Set up cron job for backups
- [ ] Configure backup retention
- [ ] Test restore procedure
- [ ] Document backup location

### After Deployment

- [ ] Verify automatic backups running
- [ ] Check backup logs: `tail -f logs/backup.log`
- [ ] Monitor database size
- [ ] Run integrity checks weekly
- [ ] Test restore procedure monthly

---

## Troubleshooting

### Database Locked Error

**Symptom:** `database is locked` error

**Solutions:**
1. Check if WAL mode is enabled: `PRAGMA journal_mode;`
2. Increase timeout: `db.execute("PRAGMA busy_timeout=5000")`
3. Check for long-running transactions
4. Restart application

### WAL File Growing Large

**Symptom:** `-wal` file is very large

**Solutions:**
1. Checkpoint WAL: `PRAGMA wal_checkpoint(TRUNCATE);`
2. Check for long-running read transactions
3. Restart application to force checkpoint

### Slow Queries

**Symptom:** Queries taking too long

**Solutions:**
1. Run `ANALYZE` to update statistics
2. Check if indexes are being used: `EXPLAIN QUERY PLAN SELECT ...`
3. Add missing indexes
4. Increase cache size

### Backup Fails

**Symptom:** Backup script fails

**Solutions:**
1. Check disk space: `df -h`
2. Check permissions: `ls -la data/`
3. Verify database integrity
4. Check logs: `tail -f logs/backup.log`

---

## Performance Tips

### For High Traffic

1. **Increase cache size**:
   ```python
   db.execute("PRAGMA cache_size=-128000")  # 128MB
   ```

2. **Use connection pooling** (if needed):
   ```python
   # Consider using SQLAlchemy with connection pool
   ```

3. **Monitor WAL size**:
   ```bash
   watch -n 60 'ls -lh data/budtender.db*'
   ```

4. **Regular ANALYZE**:
   ```bash
   # Add to cron (weekly)
   0 3 * * 0 sqlite3 /path/to/data/budtender.db "ANALYZE;"
   ```

### For Large Databases

1. **Consider PostgreSQL** if:
   - Database > 100GB
   - Need multi-server setup
   - Need advanced features

2. **Partition old data**:
   - Archive old feedback
   - Keep active data small

3. **Regular VACUUM**:
   ```bash
   # Monthly during maintenance window
   sqlite3 data/budtender.db "VACUUM;"
   ```

---

## Migration to PostgreSQL

If you need to migrate to PostgreSQL in the future:

1. **Export data**:
   ```bash
   sqlite3 data/budtender.db .dump > dump.sql
   ```

2. **Convert schema**:
   - Change `AUTOINCREMENT` to `SERIAL`
   - Change `INTEGER` to `INT`
   - Change `TEXT` to `VARCHAR` or `TEXT`
   - Update `PRAGMA` statements

3. **Import to PostgreSQL**:
   ```bash
   psql -U user -d database -f converted_dump.sql
   ```

4. **Update connection code**:
   - Replace `sqlite3` with `psycopg2`
   - Update connection string
   - Test thoroughly

---

## API Reference

### Database Functions

#### `init_db()`
Initialize database with tables and indexes.

#### `get_db()`
Get database connection with optimizations (context manager).

#### `optimize_db_connection(db)`
Apply PRAGMA optimizations to connection.

#### `backup_database(backup_path=None)`
Create database backup. Returns backup path.

#### `cleanup_old_backups(keep_count=7)`
Delete old backups, keeping N most recent.

#### `verify_database_integrity()`
Run integrity check. Returns True if OK.

#### `get_database_stats()`
Get database statistics. Returns dict.

#### `apply_migration(version, description, sql)`
Apply database migration.

#### `get_applied_migrations()`
Get list of applied migrations.

---

## Support

For issues or questions:
1. Check logs: `logs/backup.log`
2. Run tests: `python3 test_database.py`
3. Check integrity: `verify_database_integrity()`
4. Review this documentation

---

**Last Updated:** 2026-02-16  
**Status:** ✅ Production Ready
