#!/usr/bin/env python3
"""
RBAC and Authentication Test Suite
Tests for Budtender Feedback System security
"""
import requests
import time
from datetime import datetime, timedelta

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

# Test credentials
ADMIN_CREDS = {"email": "admin@weeden.com", "password": "admin12345!"}
FOUNDER_CREDS = {"email": "founder@weeden.com", "password": "founder12345"}
CEO_CREDS = {"email": "ceo@weeden.com", "password": "ceo1234567!"}
INVALID_CREDS = {"email": "admin@weeden.com", "password": "wrongpassword"}

def login(credentials):
    """Login and return session with cookies"""
    session = requests.Session()
    response = session.post(f"{BASE_URL}/admin/login", data=credentials, allow_redirects=False)
    return session, response

def test_login_valid_credentials():
    """Test 1.1: Valid credentials should login successfully"""
    print_section("1. Authentication Tests")
    
    session, response = login(ADMIN_CREDS)
    passed = response.status_code == 302 and "access_token" in response.cookies
    print_test("Valid admin login", passed, f"Status: {response.status_code}")
    
    session, response = login(FOUNDER_CREDS)
    passed = response.status_code == 302 and "access_token" in response.cookies
    print_test("Valid founder login", passed, f"Status: {response.status_code}")
    
    session, response = login(CEO_CREDS)
    passed = response.status_code == 302 and "access_token" in response.cookies
    print_test("Valid CEO login", passed, f"Status: {response.status_code}")

def test_login_invalid_credentials():
    """Test 1.2: Invalid credentials should fail"""
    session, response = login(INVALID_CREDS)
    passed = response.status_code == 200 and "Invalid email or password" in response.text
    print_test("Invalid credentials rejected", passed, f"Status: {response.status_code}")

def test_inactive_user_cannot_login():
    """Test 1.3: Inactive users cannot login"""
    # First, login as admin and deactivate founder
    admin_session, _ = login(ADMIN_CREDS)
    
    # Get founder user ID (assuming it's 2)
    # In real test, we'd query the API to get the ID
    print_test("Inactive user login test", None, "Skipped - requires user deactivation setup")

def test_httponly_cookies():
    """Test 2.1: Cookies should be httpOnly"""
    session, response = login(ADMIN_CREDS)
    cookie = response.cookies.get("access_token")
    
    # Check if cookie exists
    passed = cookie is not None
    print_section("2. JWT Token Tests")
    print_test("Access token cookie set", passed)
    
    # Note: httpOnly flag is not directly accessible via requests library
    # This needs to be tested in browser or by inspecting Set-Cookie header
    set_cookie_header = response.headers.get("Set-Cookie", "")
    passed = "HttpOnly" in set_cookie_header
    print_test("Cookie has HttpOnly flag", passed, f"Set-Cookie: {set_cookie_header[:100]}...")

def test_token_expiration():
    """Test 2.2: Token expiration (8 hours)"""
    session, response = login(ADMIN_CREDS)
    
    # Access protected route
    response = session.get(f"{BASE_URL}/admin/inbox")
    passed = response.status_code == 200
    print_test("Valid token grants access", passed, f"Status: {response.status_code}")
    
    # Test with no token
    session_no_token = requests.Session()
    response = session_no_token.get(f"{BASE_URL}/admin/inbox", allow_redirects=False)
    passed = response.status_code == 302 and "/admin/login" in response.headers.get("Location", "")
    print_test("No token redirects to login", passed, f"Status: {response.status_code}")

def test_expired_token_handling():
    """Test 2.3: Expired token handling"""
    # This would require creating a token with past expiration
    # For now, we test invalid token
    session = requests.Session()
    session.cookies.set("access_token", "invalid.token.here")
    
    response = session.get(f"{BASE_URL}/admin/inbox", allow_redirects=False)
    passed = response.status_code == 302 and "/admin/login" in response.headers.get("Location", "")
    print_test("Invalid token redirects to login", passed, f"Status: {response.status_code}")

def test_admin_only_routes():
    """Test 3.1: Admin-only routes (/admin/users)"""
    print_section("3. RBAC Tests")
    
    # Admin should have access
    admin_session, _ = login(ADMIN_CREDS)
    response = admin_session.get(f"{BASE_URL}/admin/users")
    passed = response.status_code == 200
    print_test("Admin can access /admin/users", passed, f"Status: {response.status_code}")
    
    # Founder should NOT have access
    founder_session, _ = login(FOUNDER_CREDS)
    response = founder_session.get(f"{BASE_URL}/admin/users")
    passed = response.status_code == 403
    print_test("Founder cannot access /admin/users", passed, f"Status: {response.status_code}")
    
    # CEO should NOT have access
    ceo_session, _ = login(CEO_CREDS)
    response = ceo_session.get(f"{BASE_URL}/admin/users")
    passed = response.status_code == 403
    print_test("CEO cannot access /admin/users", passed, f"Status: {response.status_code}")

def test_user_management_permissions():
    """Test 3.2: User management API permissions"""
    # Test create user (admin only)
    admin_session, _ = login(ADMIN_CREDS)
    new_user = {
        "email": f"test_{int(time.time())}@test.com",
        "name": "Test User",
        "password": "testpassword123",
        "role": "ceo"
    }
    response = admin_session.post(f"{BASE_URL}/api/users", json=new_user)
    passed = response.status_code == 200
    print_test("Admin can create users", passed, f"Status: {response.status_code}")
    
    # Founder should NOT be able to create users
    founder_session, _ = login(FOUNDER_CREDS)
    response = founder_session.post(f"{BASE_URL}/api/users", json=new_user)
    passed = response.status_code == 403
    print_test("Founder cannot create users", passed, f"Status: {response.status_code}")

def test_delete_feedback_permissions():
    """Test 3.3: Delete feedback (admin only)"""
    # Admin can delete
    admin_session, _ = login(ADMIN_CREDS)
    response = admin_session.post(f"{BASE_URL}/api/feedback/999/delete")
    # 404 is OK (feedback doesn't exist), 403 would be permission error
    passed = response.status_code in [200, 404]
    print_test("Admin can delete feedback", passed, f"Status: {response.status_code}")
    
    # Founder cannot delete
    founder_session, _ = login(FOUNDER_CREDS)
    response = founder_session.post(f"{BASE_URL}/api/feedback/999/delete")
    passed = response.status_code == 403
    print_test("Founder cannot delete feedback", passed, f"Status: {response.status_code}")

def test_all_roles_can_view_inbox():
    """Test 3.4: All authenticated users can view inbox"""
    for role, creds in [("Admin", ADMIN_CREDS), ("Founder", FOUNDER_CREDS), ("CEO", CEO_CREDS)]:
        session, _ = login(creds)
        response = session.get(f"{BASE_URL}/admin/inbox")
        passed = response.status_code == 200
        print_test(f"{role} can view inbox", passed, f"Status: {response.status_code}")

def test_sql_injection_protection():
    """Test 4: SQL injection protection"""
    print_section("4. SQL Injection Tests")
    
    admin_session, _ = login(ADMIN_CREDS)
    
    # Test bulk status with SQL injection attempt
    malicious_payload = {
        "ids": ["1; DROP TABLE users; --", "2"],
        "status": "read"
    }
    response = admin_session.post(f"{BASE_URL}/api/feedback/bulk-status", json=malicious_payload)
    # Should fail with 400 (invalid ID format) not 500 (SQL error)
    passed = response.status_code == 400
    print_test("Bulk status rejects SQL injection in IDs", passed, f"Status: {response.status_code}")
    
    # Test search with SQL injection attempt
    response = admin_session.get(f"{BASE_URL}/admin/inbox?search=' OR '1'='1")
    # Should return 200 (parameterized query handles it safely)
    passed = response.status_code == 200
    print_test("Search handles SQL injection safely", passed, f"Status: {response.status_code}")

def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}RBAC & Authentication Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Budtender Feedback System{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"\nTesting against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Check if server is running
        response = requests.get(BASE_URL, timeout=5)
        print(f"{Colors.GREEN}✓ Server is running{Colors.END}\n")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Server is not running at {BASE_URL}{Colors.END}")
        print(f"Please start the server with: python run.py\n")
        return
    
    # Run tests
    test_login_valid_credentials()
    test_login_invalid_credentials()
    test_inactive_user_cannot_login()
    
    test_httponly_cookies()
    test_token_expiration()
    test_expired_token_handling()
    
    test_admin_only_routes()
    test_user_management_permissions()
    test_delete_feedback_permissions()
    test_all_roles_can_view_inbox()
    
    test_sql_injection_protection()
    
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Test suite completed{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")

if __name__ == "__main__":
    run_all_tests()
