import sqlite3
import os
import logging
from app.config import DATABASE_PATH, UPLOAD_DIR

logger = logging.getLogger(__name__)


def optimize_db_connection(db):
    """Apply production-ready SQLite optimizations"""
    # Enable WAL mode for better concurrency
    db.execute("PRAGMA journal_mode=WAL")
    
    # Enable foreign keys
    db.execute("PRAGMA foreign_keys=ON")
    
    # Increase cache size (default is 2MB, set to 64MB)
    db.execute("PRAGMA cache_size=-64000")
    
    # Set synchronous to NORMAL for better performance (still safe with WAL)
    db.execute("PRAGMA synchronous=NORMAL")
    
    # Enable memory-mapped I/O (256MB)
    db.execute("PRAGMA mmap_size=268435456")
    
    # Set temp store to memory
    db.execute("PRAGMA temp_store=MEMORY")
    
    # Optimize for better query performance
    db.execute("PRAGMA optimize")


def get_db():
    """Get database connection with optimizations"""
    db = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    optimize_db_connection(db)
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with tables, indexes, and optimizations"""
    logger.info("Initializing database...")
    
    # Create directories
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Connect and optimize
    db = sqlite3.connect(DATABASE_PATH)
    optimize_db_connection(db)
    
    # Create tables
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'founder', 'ceo')),
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS feedback (
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

    CREATE TABLE IF NOT EXISTS rate_limits (
        ip_hash TEXT NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Database migrations tracking
    CREATE TABLE IF NOT EXISTS migrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT UNIQUE NOT NULL,
        description TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create indexes for performance
    db.executescript("""
    -- Feedback indexes
    CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
    CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
    CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_feedback_deleted ON feedback(is_deleted);
    CREATE INDEX IF NOT EXISTS idx_feedback_submission_id ON feedback(submission_id);
    CREATE INDEX IF NOT EXISTS idx_feedback_ai_status ON feedback(ai_status);
    
    -- Composite indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_feedback_status_deleted ON feedback(status, is_deleted);
    CREATE INDEX IF NOT EXISTS idx_feedback_category_deleted ON feedback(category, is_deleted);
    
    -- Rate limits indexes
    CREATE INDEX IF NOT EXISTS idx_rate_limits_ip ON rate_limits(ip_hash);
    CREATE INDEX IF NOT EXISTS idx_rate_limits_time ON rate_limits(submitted_at);
    CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_time ON rate_limits(ip_hash, submitted_at);
    
    -- Users indexes
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
    """)
    
    db.commit()
    
    # Verify tables were created
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"Database initialized with tables: {', '.join(tables)}")
    
    # Run ANALYZE to update query planner statistics
    db.execute("ANALYZE")
    db.commit()
    
    db.close()
    logger.info("Database initialization complete")



def apply_migration(version: str, description: str, sql: str):
    """Apply a database migration"""
    db = sqlite3.connect(DATABASE_PATH)
    optimize_db_connection(db)
    
    try:
        # Check if migration already applied
        cursor = db.cursor()
        cursor.execute("SELECT version FROM migrations WHERE version = ?", (version,))
        if cursor.fetchone():
            logger.info(f"Migration {version} already applied, skipping")
            return
        
        # Apply migration
        logger.info(f"Applying migration {version}: {description}")
        db.executescript(sql)
        
        # Record migration
        db.execute(
            "INSERT INTO migrations (version, description) VALUES (?, ?)",
            (version, description)
        )
        db.commit()
        logger.info(f"Migration {version} applied successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration {version} failed: {e}")
        raise
    finally:
        db.close()


def get_applied_migrations():
    """Get list of applied migrations"""
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()
    cursor.execute("SELECT version, description, applied_at FROM migrations ORDER BY applied_at")
    migrations = cursor.fetchall()
    db.close()
    return migrations


def backup_database(backup_path: str = None):
    """Create a backup of the database
    
    Args:
        backup_path: Path to backup file. If None, generates timestamped backup.
    
    Returns:
        Path to backup file
    """
    import shutil
    from datetime import datetime
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"budtender_backup_{timestamp}.db")
    
    try:
        # Use SQLite backup API for safe backup
        source = sqlite3.connect(DATABASE_PATH)
        backup = sqlite3.connect(backup_path)
        
        with backup:
            source.backup(backup)
        
        source.close()
        backup.close()
        
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise


def cleanup_old_backups(keep_count: int = 7):
    """Keep only the N most recent backups
    
    Args:
        keep_count: Number of backups to keep (default: 7)
    """
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), "backups")
    
    if not os.path.exists(backup_dir):
        return
    
    # Get all backup files
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.startswith("budtender_backup_") and filename.endswith(".db"):
            filepath = os.path.join(backup_dir, filename)
            backups.append((filepath, os.path.getmtime(filepath)))
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x[1], reverse=True)
    
    # Delete old backups
    for filepath, _ in backups[keep_count:]:
        try:
            os.remove(filepath)
            logger.info(f"Deleted old backup: {filepath}")
        except Exception as e:
            logger.error(f"Failed to delete backup {filepath}: {e}")


def verify_database_integrity():
    """Verify database integrity
    
    Returns:
        True if database is OK, False otherwise
    """
    try:
        db = sqlite3.connect(DATABASE_PATH)
        cursor = db.cursor()
        
        # Run integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        db.close()
        
        if result == "ok":
            logger.info("Database integrity check: OK")
            return True
        else:
            logger.error(f"Database integrity check failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Database integrity check error: {e}")
        return False


def get_database_stats():
    """Get database statistics
    
    Returns:
        Dictionary with database statistics
    """
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()
    
    stats = {}
    
    # Get table counts
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['users_count'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM feedback WHERE is_deleted = 0")
    stats['feedback_count'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM rate_limits")
    stats['rate_limits_count'] = cursor.fetchone()[0]
    
    # Get database size
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    stats['database_size_mb'] = (page_count * page_size) / (1024 * 1024)
    
    # Get WAL size if exists
    wal_path = DATABASE_PATH + "-wal"
    if os.path.exists(wal_path):
        stats['wal_size_mb'] = os.path.getsize(wal_path) / (1024 * 1024)
    else:
        stats['wal_size_mb'] = 0
    
    db.close()
    
    return stats
