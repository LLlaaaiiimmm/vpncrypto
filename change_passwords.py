#!/usr/bin/env python3
"""
Change Default Passwords Script
Interactive script to change default admin passwords
"""

import sys
import sqlite3
import getpass
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.auth import get_password_hash

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

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def get_password(prompt):
    """Get password with confirmation"""
    while True:
        password = getpass.getpass(f"{prompt}: ")
        
        if len(password) < 10:
            print_error("Password must be at least 10 characters long")
            continue
        
        confirm = getpass.getpass("Confirm password: ")
        
        if password != confirm:
            print_error("Passwords do not match")
            continue
        
        return password

def change_user_password(db, email, new_password):
    """Change password for a user"""
    try:
        hashed = get_password_hash(new_password)
        db.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (hashed, email)
        )
        db.commit()
        return True
    except Exception as e:
        print_error(f"Failed to update password: {e}")
        return False

def main():
    print_header("Change Default Passwords")
    
    print("This script will help you change the default admin passwords.")
    print("All passwords must be at least 10 characters long.")
    print()
    
    # Check database
    db_path = "data/budtender.db"
    if not Path(db_path).exists():
        print_error(f"Database not found: {db_path}")
        print("Please run the application first to initialize the database.")
        return 1
    
    # Connect to database
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        
        # Get all users
        cursor.execute("SELECT email, name, role FROM users ORDER BY role")
        users = cursor.fetchall()
        
        if not users:
            print_error("No users found in database")
            return 1
        
        print("Current users:")
        for email, name, role in users:
            print(f"  - {name} ({email}) - {role}")
        print()
        
    except Exception as e:
        print_error(f"Failed to connect to database: {e}")
        return 1
    
    # Change passwords
    print_header("Change Passwords")
    
    changed = []
    
    for email, name, role in users:
        print(f"\n{BLUE}User: {name} ({email}) - {role}{RESET}")
        
        response = input("Change password for this user? [y/N]: ").strip().lower()
        
        if response in ['y', 'yes']:
            password = get_password(f"New password for {name}")
            
            if change_user_password(db, email, password):
                print_success(f"Password changed for {name}")
                changed.append(name)
            else:
                print_error(f"Failed to change password for {name}")
    
    db.close()
    
    # Summary
    print_header("Summary")
    
    if changed:
        print_success(f"Changed passwords for {len(changed)} user(s):")
        for name in changed:
            print(f"  - {name}")
        print()
        print_warning("IMPORTANT:")
        print("  - Save these passwords in a secure location")
        print("  - Do not share passwords via insecure channels")
        print("  - Consider using a password manager")
    else:
        print("No passwords were changed.")
    
    print()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Cancelled by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
