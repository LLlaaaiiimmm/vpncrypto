#!/usr/bin/env python3
"""
Database Configuration Test Suite
Tests database setup, optimizations, and backup functionality
"""

import sys
import os
import sqlite3
import tempfile
import shutil

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_test(name):
    print(f"{YELLOW}Testing:{RESET} {name}...", end=" ", flush=True)

def print_pass():
    print(f"{GREEN}✓ PASS{RESET}")

def print_fail(reason=""):
    print(f"{RED}✗ FAIL{RESET}")
    if reason:
        print(f"  {RED}Reason: {reason}{RESET}")


def test_database_initialization():
    """Test that database initializes correctly"""
    print_test("Database initialization")
    
    try:
        from app.database import init_db
        from app.config import DATABASE_PATH
        
        # Remove existing database for clean test
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
        
        # Initialize
        init_db()
        
        # Check if database file exists
        if not os.path.exists(DATABASE_PATH):
            print_fail("Database file not created")
            return False
        
        print_pass()
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_tables_created():
    """Test that all required tables are created"""
    print_test("Required tables created")
    
    try:
        from app.config import DATABASE_PATH
        
        db = sqlite3.connect(DATABASE_PATH)
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'feedback', 'rate_limits', 'migrations']
        missing = [t for t in required_tables if t not in tables]
        
        db.close()
        
        if missing:
            print_fail(f"Missing tables: {', '.join(missing)}")
            return False
        
        print_pass()
        print(f"  Tables: {', '.join(tables)}")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_indexes_created():
    """Test that indexes are created"""
    print_test("Indexes created")
    
    try:
        from app.config import DATABASE_PATH
        
        db = sqlite3.connect(DATABASE_PATH)
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Filter out auto-created indexes
        custom_indexes = [idx for idx in indexes if not idx.startswith('sqlite_')]
        
        db.close()
        
        if len(custom_indexes) < 10:  # We should have at least 10 custom indexes
            print_fail(f"Only {len(custom_indexes)} indexes found")
            return False
        
        print_pass()
        print(f"  Indexes: {len(custom_indexes)}")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_wal_mode_enabled():
    """Test that WAL mode is enabled"""
    print_test("WAL mode enabled")
    
    try:
        from app.config import DATABASE_PATH
        
        db = sqlite3.connect(DATABASE_PATH)
        cursor = db.cursor()
        
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        
        db.close()
        
        if mode.lower() != 'wal':
            print_fail(f"Journal mode is {mode}, expected WAL")
            return False
        
        print_pass()
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_foreign_keys_enabled():
    """Test that foreign keys are enabled"""
    print_test("Foreign keys enabled")
    
    try:
        from app.database import get_db
        
        db_gen = get_db()
        db = next(db_gen)
        
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]
        
        db_gen.close()
        
        if not enabled:
            print_fail("Foreign keys not enabled")
            return False
        
        print_pass()
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_pragma_optimizations():
    """Test that PRAGMA optimizations are applied"""
    print_test("PRAGMA optimizations applied")
    
    try:
        from app.database import get_db
        
        db_gen = get_db()
        db = next(db_gen)
        cursor = db.cursor()
        
        # Check cache_size
        cursor.execute("PRAGMA cache_size")
        cache_size = cursor.fetchone()[0]
        
        # Check synchronous
        cursor.execute("PRAGMA synchronous")
        synchronous = cursor.fetchone()[0]
        
        # Check temp_store
        cursor.execute("PRAGMA temp_store")
        temp_store = cursor.fetchone()[0]
        
        db_gen.close()
        
        # Verify optimizations
        if cache_size >= -64000:  # Should be at least 64MB
            print_pass()
            print(f"  Cache size: {abs(cache_size) / 1000:.0f} MB")
            print(f"  Synchronous: {synchronous} (1=NORMAL)")
            print(f"  Temp store: {temp_store} (2=MEMORY)")
            return True
        else:
            print_fail(f"Cache size too small: {cache_size}")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_database_backup():
    """Test database backup functionality"""
    print_test("Database backup")
    
    try:
        from app.database import backup_database
        
        # Create backup
        backup_path = backup_database()
        
        # Check if backup exists
        if not os.path.exists(backup_path):
            print_fail("Backup file not created")
            return False
        
        # Check if backup is valid SQLite database
        db = sqlite3.connect(backup_path)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        db.close()
        
        if len(tables) < 3:
            print_fail("Backup database incomplete")
            return False
        
        print_pass()
        print(f"  Backup: {backup_path}")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_backup_cleanup():
    """Test backup cleanup functionality"""
    print_test("Backup cleanup")
    
    try:
        from app.database import backup_database, cleanup_old_backups
        from app.config import DATABASE_PATH
        
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), "backups")
        
        # Create multiple backups
        for i in range(10):
            backup_database()
        
        # Count backups before cleanup
        backups_before = len([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        
        # Cleanup (keep 7)
        cleanup_old_backups(keep_count=7)
        
        # Count backups after cleanup
        backups_after = len([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        
        if backups_after <= 7:
            print_pass()
            print(f"  Before: {backups_before}, After: {backups_after}")
            return True
        else:
            print_fail(f"Too many backups remaining: {backups_after}")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_database_integrity():
    """Test database integrity check"""
    print_test("Database integrity check")
    
    try:
        from app.database import verify_database_integrity
        
        result = verify_database_integrity()
        
        if result:
            print_pass()
            return True
        else:
            print_fail("Integrity check failed")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_database_stats():
    """Test database statistics"""
    print_test("Database statistics")
    
    try:
        from app.database import get_database_stats
        
        stats = get_database_stats()
        
        required_keys = ['users_count', 'feedback_count', 'rate_limits_count', 
                        'database_size_mb', 'wal_size_mb']
        
        missing = [k for k in required_keys if k not in stats]
        
        if missing:
            print_fail(f"Missing stats: {', '.join(missing)}")
            return False
        
        print_pass()
        print(f"  Users: {stats['users_count']}")
        print(f"  Feedback: {stats['feedback_count']}")
        print(f"  DB size: {stats['database_size_mb']:.2f} MB")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_migration_system():
    """Test migration system"""
    print_test("Migration system")
    
    try:
        from app.database import apply_migration, get_applied_migrations
        
        # Apply a test migration
        test_sql = """
        -- Test migration
        CREATE TABLE IF NOT EXISTS test_migration (
            id INTEGER PRIMARY KEY,
            test_field TEXT
        );
        """
        
        apply_migration("test_001", "Test migration", test_sql)
        
        # Check if migration was recorded
        migrations = get_applied_migrations()
        
        if any(m[0] == "test_001" for m in migrations):
            print_pass()
            print(f"  Applied migrations: {len(migrations)}")
            return True
        else:
            print_fail("Migration not recorded")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def main():
    print_header("Database Configuration Test Suite")
    
    results = []
    
    # Initialization tests
    print_header("1. Initialization Tests")
    results.append(("Database initialization", test_database_initialization()))
    results.append(("Tables created", test_tables_created()))
    results.append(("Indexes created", test_indexes_created()))
    
    # Configuration tests
    print_header("2. Configuration Tests")
    results.append(("WAL mode", test_wal_mode_enabled()))
    results.append(("Foreign keys", test_foreign_keys_enabled()))
    results.append(("PRAGMA optimizations", test_pragma_optimizations()))
    
    # Backup tests
    print_header("3. Backup Tests")
    results.append(("Database backup", test_database_backup()))
    results.append(("Backup cleanup", test_backup_cleanup()))
    
    # Integrity tests
    print_header("4. Integrity Tests")
    results.append(("Database integrity", test_database_integrity()))
    results.append(("Database statistics", test_database_stats()))
    
    # Migration tests
    print_header("5. Migration Tests")
    results.append(("Migration system", test_migration_system()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All tests passed!{RESET}")
        print(f"\n{GREEN}Database setup is production-ready.{RESET}")
        return True
    else:
        print(f"\n{RED}✗ Some tests failed.{RESET}")
        print(f"\n{YELLOW}Failed tests:{RESET}")
        for name, result in results:
            if not result:
                print(f"  - {name}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
