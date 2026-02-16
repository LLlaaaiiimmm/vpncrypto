#!/usr/bin/env python3
"""
Rate Limit Cleanup Demonstration Script
Shows how the cleanup mechanism works
"""
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import DATABASE_PATH
from app.background_tasks import cleanup_old_rate_limits, get_rate_limit_stats

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_stats(stats):
    """Print rate limit statistics in a nice format"""
    if not stats:
        print(f"{Colors.RED}✗ Could not retrieve statistics{Colors.END}")
        return
    
    print(f"{Colors.CYAN}Rate Limit Statistics:{Colors.END}")
    print(f"  Total entries:        {stats['total']}")
    print(f"  Last hour:            {stats['last_hour']}")
    print(f"  Last 24 hours:        {stats['last_24h']}")
    print(f"  {Colors.YELLOW}Old entries (>24h):   {stats['old_entries']}{Colors.END}")
    print()

def insert_test_data():
    """Insert test data with various timestamps"""
    print_header("Inserting Test Data")
    
    db = sqlite3.connect(DATABASE_PATH)
    
    # Insert entries with different ages
    test_data = [
        ("test_hash_1", datetime.utcnow()),  # Now
        ("test_hash_2", datetime.utcnow() - timedelta(hours=1)),  # 1 hour ago
        ("test_hash_3", datetime.utcnow() - timedelta(hours=12)),  # 12 hours ago
        ("test_hash_4", datetime.utcnow() - timedelta(hours=23)),  # 23 hours ago
        ("test_hash_5", datetime.utcnow() - timedelta(hours=25)),  # 25 hours ago (OLD)
        ("test_hash_6", datetime.utcnow() - timedelta(hours=48)),  # 48 hours ago (OLD)
        ("test_hash_7", datetime.utcnow() - timedelta(days=7)),    # 7 days ago (OLD)
    ]
    
    for ip_hash, timestamp in test_data:
        db.execute(
            "INSERT INTO rate_limits (ip_hash, submitted_at) VALUES (?, ?)",
            (ip_hash, timestamp.isoformat())
        )
    
    db.commit()
    db.close()
    
    print(f"{Colors.GREEN}✓ Inserted {len(test_data)} test entries{Colors.END}")
    print(f"  - 4 entries within 24 hours (should be kept)")
    print(f"  - 3 entries older than 24 hours (should be deleted)")
    print()

def demonstrate_cleanup():
    """Demonstrate the cleanup process"""
    print_header("Rate Limit Cleanup Demonstration")
    
    # Get initial stats
    print(f"{Colors.CYAN}BEFORE CLEANUP:{Colors.END}\n")
    stats_before = get_rate_limit_stats()
    print_stats(stats_before)
    
    # Run cleanup
    print(f"{Colors.YELLOW}Running cleanup...{Colors.END}\n")
    deleted_count = cleanup_old_rate_limits()
    
    if deleted_count > 0:
        print(f"{Colors.GREEN}✓ Deleted {deleted_count} old entries{Colors.END}\n")
    else:
        print(f"{Colors.YELLOW}⚠ No old entries to delete{Colors.END}\n")
    
    # Get stats after cleanup
    print(f"{Colors.CYAN}AFTER CLEANUP:{Colors.END}\n")
    stats_after = get_rate_limit_stats()
    print_stats(stats_after)
    
    # Verify cleanup worked
    if stats_after and stats_after['old_entries'] == 0:
        print(f"{Colors.GREEN}✓ SUCCESS: All old entries removed!{Colors.END}")
    else:
        print(f"{Colors.RED}✗ WARNING: Some old entries remain{Colors.END}")

def show_current_stats():
    """Show current rate limit statistics"""
    print_header("Current Rate Limit Statistics")
    
    stats = get_rate_limit_stats()
    print_stats(stats)
    
    if stats:
        if stats['old_entries'] > 0:
            print(f"{Colors.YELLOW}⚠ Warning: {stats['old_entries']} old entries need cleanup{Colors.END}")
            print(f"  Run cleanup with: python -c 'from app.background_tasks import cleanup_old_rate_limits; cleanup_old_rate_limits()'")
        else:
            print(f"{Colors.GREEN}✓ No old entries - cleanup is working!{Colors.END}")

def verify_automatic_cleanup():
    """Verify that automatic cleanup is configured"""
    print_header("Automatic Cleanup Configuration")
    
    try:
        # Check if cleanup is called in startup
        with open('app/main.py', 'r') as f:
            content = f.read()
            
        has_import = 'from app.background_tasks import' in content
        has_scheduler = 'start_cleanup_scheduler' in content
        has_initial = 'cleanup_old_rate_limits()' in content
        
        print(f"Import background_tasks:     {Colors.GREEN + '✓' if has_import else Colors.RED + '✗'}{Colors.END}")
        print(f"Start cleanup scheduler:     {Colors.GREEN + '✓' if has_scheduler else Colors.RED + '✗'}{Colors.END}")
        print(f"Run initial cleanup:         {Colors.GREEN + '✓' if has_initial else Colors.RED + '✗'}{Colors.END}")
        print()
        
        if has_import and has_scheduler and has_initial:
            print(f"{Colors.GREEN}✓ Automatic cleanup is properly configured!{Colors.END}")
            print(f"  - Cleanup runs every 1 hour in background")
            print(f"  - Initial cleanup runs on application startup")
        else:
            print(f"{Colors.RED}✗ Automatic cleanup is NOT properly configured{Colors.END}")
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error checking configuration: {e}{Colors.END}")

def main():
    """Main function"""
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Rate Limit Cleanup Demonstration{Colors.END}")
    print(f"{Colors.YELLOW}Budtender Feedback System{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    
    # Check if database exists
    if not Path(DATABASE_PATH).exists():
        print(f"\n{Colors.RED}✗ Database not found: {DATABASE_PATH}{Colors.END}")
        print("Please run the application first to create the database.\n")
        return
    
    print(f"\nDatabase: {DATABASE_PATH}\n")
    
    # Menu
    while True:
        print(f"\n{Colors.CYAN}Options:{Colors.END}")
        print("  1. Show current statistics")
        print("  2. Insert test data and demonstrate cleanup")
        print("  3. Run cleanup now")
        print("  4. Verify automatic cleanup configuration")
        print("  5. Exit")
        
        choice = input(f"\n{Colors.YELLOW}Enter choice (1-5): {Colors.END}").strip()
        
        if choice == '1':
            show_current_stats()
        elif choice == '2':
            insert_test_data()
            demonstrate_cleanup()
        elif choice == '3':
            print_header("Manual Cleanup")
            deleted = cleanup_old_rate_limits()
            if deleted > 0:
                print(f"{Colors.GREEN}✓ Deleted {deleted} old entries{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠ No old entries to delete{Colors.END}")
            show_current_stats()
        elif choice == '4':
            verify_automatic_cleanup()
        elif choice == '5':
            print(f"\n{Colors.GREEN}Goodbye!{Colors.END}\n")
            break
        else:
            print(f"{Colors.RED}Invalid choice. Please enter 1-5.{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}\n")
