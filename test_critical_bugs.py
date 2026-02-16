#!/usr/bin/env python3
"""
Critical Bugs and Error Handling Test Suite
Tests for paths, error pages, and rate limiting
"""
import requests
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if details:
        print(f"      {details}")

def print_section(name):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

# ==================== FILE PATHS TESTS ====================

def test_upload_dir_exists():
    """Test 1.1: UPLOAD_DIR is created automatically"""
    print_section("1. File Paths Tests")
    
    # Check if data/uploads directory exists
    upload_dir = Path("data/uploads")
    passed = upload_dir.exists() and upload_dir.is_dir()
    print_test("UPLOAD_DIR created automatically", passed,
              f"Path: {upload_dir.absolute()}")

def test_static_files_accessible():
    """Test 1.2: Static files are accessible"""
    
    # Test CSS file
    response = requests.get(f"{BASE_URL}/static/css/style.css")
    passed = response.status_code == 200
    print_test("/static/css/style.css accessible", passed,
              f"Status: {response.status_code}")

def test_uploads_accessible():
    """Test 1.3: Uploads directory is accessible (if files exist)"""
    
    # Try to access uploads (should return 404 if no files, or 403 if directory listing disabled)
    response = requests.get(f"{BASE_URL}/uploads/")
    # Either 404 (no files) or 403 (directory listing disabled) is acceptable
    passed = response.status_code in [403, 404]
    print_test("/uploads/ protected from directory listing", passed,
              f"Status: {response.status_code}")

# ==================== ERROR PAGES TESTS ====================

def test_404_page():
    """Test 2.1: Custom 404 page"""
    print_section("2. Error Pages Tests")
    
    response = requests.get(f"{BASE_URL}/nonexistent-page")
    passed = response.status_code == 404 and "404" in response.text
    print_test("Custom 404 page displayed", passed,
              f"Status: {response.status_code}")

def test_404_feedback_not_found():
    """Test 2.2: Nonexistent feedback_id returns 404"""
    
    # Try to access nonexistent feedback
    response = requests.get(f"{BASE_URL}/admin/feedback/999999")
    # Should redirect to login (302) or return 404
    passed = response.status_code in [302, 404]
    print_test("Nonexistent feedback_id handled", passed,
              f"Status: {response.status_code}")

def test_403_page():
    """Test 2.3: Custom 403 page for forbidden access"""
    
    # Login as founder
    session = requests.Session()
    session.post(f"{BASE_URL}/admin/login", data={
        "email": "founder@weeden.com",
        "password": "founder12345"
    })
    
    # Try to access admin-only page
    response = session.get(f"{BASE_URL}/admin/users")
    passed = response.status_code == 403 and "403" in response.text
    print_test("Custom 403 page displayed", passed,
              f"Status: {response.status_code}")

def test_api_404_returns_json():
    """Test 2.4: API endpoints return JSON for 404"""
    
    response = requests.get(f"{BASE_URL}/api/nonexistent")
    passed = response.status_code == 404 and response.headers.get('content-type', '').startswith('application/json')
    print_test("API 404 returns JSON", passed,
              f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")

# ==================== RATE LIMITING TESTS ====================

def test_rate_limiting():
    """Test 3.1: Rate limiting blocks after 10 submissions"""
    print_section("3. Rate Limiting Tests")
    
    print(f"{Colors.YELLOW}Note: This test will make 11 submissions. It may take a minute.{Colors.END}\n")
    
    # Make 10 submissions (should all succeed)
    success_count = 0
    for i in range(10):
        response = requests.post(f"{BASE_URL}/submit", data={
            "category": "complaint",
            "message": f"Test message {i+1}",
            "anonymity_consent": "on"
        })
        if response.status_code in [200, 302]:
            success_count += 1
        time.sleep(0.1)  # Small delay between requests
    
    print_test(f"First 10 submissions accepted", success_count == 10,
              f"Accepted: {success_count}/10")
    
    # 11th submission should be rate limited
    response = requests.post(f"{BASE_URL}/submit", data={
        "category": "complaint",
        "message": "Test message 11 (should be blocked)",
        "anonymity_consent": "on"
    })
    
    # Should show rate limited page
    passed = "rate" in response.text.lower() and "limit" in response.text.lower()
    print_test("11th submission blocked by rate limit", passed,
              f"Status: {response.status_code}, Contains 'rate limit': {passed}")

def test_ip_hashing():
    """Test 3.2: IP addresses are hashed"""
    
    # Submit feedback
    response = requests.post(f"{BASE_URL}/submit", data={
        "category": "idea",
        "message": "Test IP hashing",
        "anonymity_consent": "on"
    })
    
    # Check database to verify IP is hashed (not raw)
    import sqlite3
    db = sqlite3.connect("data/budtender.db")
    db.row_factory = sqlite3.Row
    
    # Get latest feedback
    row = db.execute(
        "SELECT ip_hash FROM feedback ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    
    if row:
        ip_hash = row['ip_hash']
        # Hash should be 64 characters (SHA-256 hex)
        passed = len(ip_hash) == 64 and all(c in '0123456789abcdef' for c in ip_hash)
        print_test("IP addresses are hashed (SHA-256)", passed,
                  f"Hash length: {len(ip_hash)}, Format: {'hex' if passed else 'invalid'}")
    else:
        print_test("IP addresses are hashed (SHA-256)", False, "No feedback found")
    
    db.close()

def test_rate_limit_cleanup():
    """Test 3.3: Old rate limit entries can be cleaned up"""
    
    # Check if cleanup function exists and works
    try:
        from app.background_tasks import cleanup_old_rate_limits, get_rate_limit_stats
        
        # Get stats before cleanup
        stats_before = get_rate_limit_stats()
        
        # Run cleanup
        deleted = cleanup_old_rate_limits()
        
        # Get stats after cleanup
        stats_after = get_rate_limit_stats()
        
        passed = stats_after is not None and stats_after['old_entries'] == 0
        print_test("Rate limit cleanup function works", passed,
                  f"Deleted: {deleted}, Old entries after cleanup: {stats_after['old_entries'] if stats_after else 'N/A'}")
    except Exception as e:
        print_test("Rate limit cleanup function works", False, f"Error: {str(e)}")

# ==================== EXCEPTION HANDLING TESTS ====================

def test_global_exception_handler():
    """Test 4: Global exception handler catches errors"""
    print_section("4. Exception Handling Tests")
    
    # This would require triggering an actual exception
    # For now, we just verify the handlers are registered
    try:
        import app.main
        # Check if exception handlers are defined
        has_handlers = hasattr(app.main, 'http_exception_handler')
        print_test("Global exception handlers registered", has_handlers,
                  "Exception handlers found in app.main")
    except Exception as e:
        print_test("Global exception handlers registered", False, f"Error: {str(e)}")

# ==================== DOCKER PATHS TESTS ====================

def test_docker_paths():
    """Test 5: Paths work correctly (Docker-ready)"""
    print_section("5. Docker Compatibility Tests")
    
    # Check if paths are relative and work in Docker
    try:
        from app.config import DATABASE_PATH, UPLOAD_DIR
        import os
        
        # Paths should be absolute or relative to project root
        db_exists = os.path.exists(os.path.dirname(DATABASE_PATH))
        upload_exists = os.path.exists(UPLOAD_DIR)
        
        passed = db_exists and upload_exists
        print_test("Database and upload paths exist", passed,
                  f"DB dir: {db_exists}, Upload dir: {upload_exists}")
        
        # Check if paths are Docker-compatible (no hardcoded absolute paths)
        db_relative = not DATABASE_PATH.startswith('/Users/') and not DATABASE_PATH.startswith('C:\\')
        upload_relative = not UPLOAD_DIR.startswith('/Users/') and not UPLOAD_DIR.startswith('C:\\')
        
        passed = db_relative and upload_relative
        print_test("Paths are Docker-compatible (not hardcoded)", passed,
                  f"DB: {db_relative}, Upload: {upload_relative}")
    except Exception as e:
        print_test("Paths are Docker-compatible", False, f"Error: {str(e)}")

# ==================== MAIN ====================

def run_all_tests():
    """Run all critical bug tests"""
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Critical Bugs & Error Handling Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Budtender Feedback System{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"\nTesting against: {BASE_URL}\n")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"{Colors.GREEN}✓ Server is running{Colors.END}\n")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Server is not running at {BASE_URL}{Colors.END}")
        print(f"Please start the server with: python run.py\n")
        return
    
    # Run tests
    test_upload_dir_exists()
    test_static_files_accessible()
    test_uploads_accessible()
    
    test_404_page()
    test_404_feedback_not_found()
    test_403_page()
    test_api_404_returns_json()
    
    test_rate_limiting()
    test_ip_hashing()
    test_rate_limit_cleanup()
    
    test_global_exception_handler()
    
    test_docker_paths()
    
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Test suite completed{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")
    
    print(f"{Colors.BLUE}Note:{Colors.END} Rate limiting test creates 11 submissions.")
    print(f"You may need to wait 24 hours or clear rate_limits table to test again.\n")

if __name__ == "__main__":
    run_all_tests()
