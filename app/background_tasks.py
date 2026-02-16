"""
Background tasks for maintenance and cleanup
"""
import sqlite3
import logging
import threading
import time
from datetime import datetime, timedelta
from app.config import DATABASE_PATH

logger = logging.getLogger(__name__)


def cleanup_old_rate_limits():
    """
    Remove rate limit entries older than 24 hours.
    This prevents the rate_limits table from growing indefinitely.
    """
    try:
        db = sqlite3.connect(DATABASE_PATH)
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        cursor = db.execute(
            "DELETE FROM rate_limits WHERE submitted_at < ?",
            (cutoff,)
        )
        deleted_count = cursor.rowcount
        db.commit()
        db.close()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old rate limit entries")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up rate limits: {e}", exc_info=True)
        return 0


def start_cleanup_scheduler(interval_hours=1):
    """
    Start a background thread that runs cleanup tasks periodically.
    
    Args:
        interval_hours: How often to run cleanup (default: 1 hour)
    """
    def cleanup_loop():
        logger.info(f"Started cleanup scheduler (interval: {interval_hours}h)")
        while True:
            try:
                time.sleep(interval_hours * 3600)  # Convert hours to seconds
                logger.info("Running scheduled cleanup tasks...")
                cleanup_old_rate_limits()
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {e}", exc_info=True)
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info("Cleanup scheduler thread started")


def get_rate_limit_stats():
    """
    Get statistics about rate limiting.
    Returns dict with total entries and entries by age.
    """
    try:
        db = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
        
        # Total entries
        total = db.execute("SELECT COUNT(*) as count FROM rate_limits").fetchone()['count']
        
        # Entries in last hour
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        last_hour = db.execute(
            "SELECT COUNT(*) as count FROM rate_limits WHERE submitted_at > ?",
            (one_hour_ago,)
        ).fetchone()['count']
        
        # Entries in last 24 hours
        twenty_four_hours_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        last_24h = db.execute(
            "SELECT COUNT(*) as count FROM rate_limits WHERE submitted_at > ?",
            (twenty_four_hours_ago,)
        ).fetchone()['count']
        
        # Entries older than 24 hours (should be cleaned up)
        old_entries = db.execute(
            "SELECT COUNT(*) as count FROM rate_limits WHERE submitted_at < ?",
            (twenty_four_hours_ago,)
        ).fetchone()['count']
        
        db.close()
        
        return {
            'total': total,
            'last_hour': last_hour,
            'last_24h': last_24h,
            'old_entries': old_entries
        }
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}", exc_info=True)
        return None
