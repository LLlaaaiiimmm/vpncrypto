#!/usr/bin/env python3
"""
Database Backup Script
Run this script via cron for automatic backups
"""

import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import backup_database, cleanup_old_backups, verify_database_integrity, get_database_stats


def main():
    print("=" * 60)
    print("Database Backup Script")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verify database integrity before backup
    print("1. Verifying database integrity...")
    if not verify_database_integrity():
        print("❌ Database integrity check failed!")
        print("⚠️  Backup aborted. Please check database.")
        return 1
    print("✓ Database integrity OK")
    print()
    
    # Get database stats
    print("2. Database statistics:")
    stats = get_database_stats()
    print(f"   Users: {stats['users_count']}")
    print(f"   Feedback: {stats['feedback_count']}")
    print(f"   Rate limits: {stats['rate_limits_count']}")
    print(f"   Database size: {stats['database_size_mb']:.2f} MB")
    print(f"   WAL size: {stats['wal_size_mb']:.2f} MB")
    print()
    
    # Create backup
    print("3. Creating backup...")
    try:
        backup_path = backup_database()
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"✓ Backup created: {backup_path}")
        print(f"   Size: {backup_size:.2f} MB")
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return 1
    print()
    
    # Cleanup old backups
    print("4. Cleaning up old backups (keeping last 7)...")
    try:
        cleanup_old_backups(keep_count=7)
        print("✓ Old backups cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    print()
    
    print("=" * 60)
    print("✓ Backup completed successfully")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
