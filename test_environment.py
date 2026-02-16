#!/usr/bin/env python3
"""
Environment Configuration Test Suite
Tests environment variables and configuration
"""

import os
import sys

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

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")


def test_env_file_exists():
    """Test that .env file exists"""
    print_test(".env file exists")
    
    if os.path.exists(".env"):
        print_pass()
        return True
    else:
        print_fail(".env file not found")
        print_warning("Run: cp .env.example .env")
        return False


def test_env_file_permissions():
    """Test that .env has secure permissions"""
    print_test(".env file permissions")
    
    if not os.path.exists(".env"):
        print_fail(".env file not found")
        return False
    
    # Get file permissions
    stat_info = os.stat(".env")
    permissions = oct(stat_info.st_mode)[-3:]
    
    if permissions == "600":
        print_pass()
        return True
    else:
        print_fail(f"Permissions are {permissions}, should be 600")
        print_warning("Run: chmod 600 .env")
        return False


def test_gitignore_has_env():
    """Test that .env is in .gitignore"""
    print_test(".env in .gitignore")
    
    if not os.path.exists(".gitignore"):
        print_fail(".gitignore not found")
        return False
    
    with open(".gitignore", "r") as f:
        content = f.read()
    
    if ".env" in content:
        print_pass()
        return True
    else:
        print_fail(".env not in .gitignore")
        print_warning("Add '.env' to .gitignore")
        return False


def test_config_loads():
    """Test that config module loads without errors"""
    print_test("Config module loads")
    
    try:
        from app import config
        print_pass()
        return True
    except Exception as e:
        print_fail(str(e))
        return False


def test_secret_key_set():
    """Test that SECRET_KEY is set"""
    print_test("SECRET_KEY is set")
    
    try:
        from app.config import SECRET_KEY
        
        if not SECRET_KEY:
            print_fail("SECRET_KEY is empty")
            return False
        
        if SECRET_KEY == "your-random-secret-key-min-32-chars-here":
            print_fail("SECRET_KEY is still the default value")
            print_warning("Run: python generate_secret_key.py")
            return False
        
        print_pass()
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_secret_key_length():
    """Test that SECRET_KEY is at least 32 characters"""
    print_test("SECRET_KEY length >= 32")
    
    try:
        from app.config import SECRET_KEY
        
        if len(SECRET_KEY) >= 32:
            print_pass()
            print(f"  Length: {len(SECRET_KEY)} characters")
            return True
        else:
            print_fail(f"Length is {len(SECRET_KEY)}, need 32+")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_env_variable():
    """Test ENV variable"""
    print_test("ENV variable")
    
    try:
        from app.config import ENV
        
        if ENV in ['development', 'production']:
            print_pass()
            print(f"  Environment: {ENV}")
            return True
        else:
            print_fail(f"Invalid ENV value: {ENV}")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_debug_setting():
    """Test DEBUG setting"""
    print_test("DEBUG setting")
    
    try:
        from app.config import DEBUG, ENV
        
        print_pass()
        print(f"  Debug: {DEBUG}")
        
        if ENV == "production" and DEBUG:
            print_warning("Debug is enabled in production!")
            return False
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_log_level():
    """Test LOG_LEVEL setting"""
    print_test("LOG_LEVEL setting")
    
    try:
        from app.config import LOG_LEVEL
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if LOG_LEVEL in valid_levels:
            print_pass()
            print(f"  Log level: {LOG_LEVEL}")
            return True
        else:
            print_fail(f"Invalid LOG_LEVEL: {LOG_LEVEL}")
            return False
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_openai_config():
    """Test OpenAI configuration"""
    print_test("OpenAI configuration")
    
    try:
        from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT
        
        if OPENAI_API_KEY:
            print_pass()
            print(f"  API Key: {'*' * 20} (set)")
            print(f"  Model: {OPENAI_MODEL}")
            print(f"  Timeout: {OPENAI_TIMEOUT}s")
        else:
            print_pass()
            print(f"  API Key: Not set (will use fallback mode)")
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_rate_limit_config():
    """Test rate limiting configuration"""
    print_test("Rate limiting configuration")
    
    try:
        from app.config import RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_HOURS
        
        print_pass()
        print(f"  Max: {RATE_LIMIT_MAX} per {RATE_LIMIT_WINDOW_HOURS}h")
        
        if RATE_LIMIT_MAX < 1:
            print_warning("Rate limit is very low!")
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_file_upload_config():
    """Test file upload configuration"""
    print_test("File upload configuration")
    
    try:
        from app.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
        
        print_pass()
        print(f"  Max size: {MAX_FILE_SIZE / (1024*1024):.1f}MB")
        print(f"  Extensions: {', '.join(ALLOWED_EXTENSIONS)}")
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_jwt_config():
    """Test JWT configuration"""
    print_test("JWT configuration")
    
    try:
        from app.config import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
        
        print_pass()
        print(f"  Algorithm: {ALGORITHM}")
        print(f"  Expiration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes ({ACCESS_TOKEN_EXPIRE_MINUTES/60:.1f} hours)")
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_database_paths():
    """Test database paths"""
    print_test("Database paths")
    
    try:
        from app.config import DATABASE_PATH, UPLOAD_DIR
        
        print_pass()
        print(f"  Database: {DATABASE_PATH}")
        print(f"  Uploads: {UPLOAD_DIR}")
        
        # Check if directories exist or can be created
        import os
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_security_config():
    """Test security configuration"""
    print_test("Security configuration")
    
    try:
        from app.config import CORS_ORIGINS, TRUSTED_HOSTS, ENV
        
        print_pass()
        print(f"  CORS Origins: {CORS_ORIGINS}")
        print(f"  Trusted Hosts: {TRUSTED_HOSTS}")
        
        if ENV == "production":
            if "*" in CORS_ORIGINS:
                print_warning("CORS allows all origins in production!")
            if "*" in TRUSTED_HOSTS:
                print_warning("All hosts trusted in production!")
        
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_production_readiness():
    """Test production readiness"""
    print_test("Production readiness")
    
    try:
        from app.config import ENV, DEBUG, SECRET_KEY, LOG_LEVEL
        
        if ENV != "production":
            print_pass()
            print(f"  Environment: {ENV} (not production)")
            return True
        
        issues = []
        
        if DEBUG:
            issues.append("Debug mode enabled")
        
        if SECRET_KEY == "your-random-secret-key-min-32-chars-here":
            issues.append("Default SECRET_KEY")
        
        if LOG_LEVEL == "DEBUG":
            issues.append("Debug log level")
        
        if issues:
            print_fail("Production issues found")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print_pass()
            print(f"  Ready for production")
            return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def main():
    print_header("Environment Configuration Test Suite")
    
    results = []
    
    # File tests
    print_header("1. File Tests")
    results.append((".env exists", test_env_file_exists()))
    results.append((".env permissions", test_env_file_permissions()))
    results.append((".env in .gitignore", test_gitignore_has_env()))
    
    # Config loading
    print_header("2. Configuration Loading")
    results.append(("Config loads", test_config_loads()))
    
    # Secret key tests
    print_header("3. Secret Key Tests")
    results.append(("SECRET_KEY set", test_secret_key_set()))
    results.append(("SECRET_KEY length", test_secret_key_length()))
    
    # Environment tests
    print_header("4. Environment Tests")
    results.append(("ENV variable", test_env_variable()))
    results.append(("DEBUG setting", test_debug_setting()))
    results.append(("LOG_LEVEL", test_log_level()))
    
    # Feature configuration
    print_header("5. Feature Configuration")
    results.append(("OpenAI config", test_openai_config()))
    results.append(("Rate limiting", test_rate_limit_config()))
    results.append(("File upload", test_file_upload_config()))
    results.append(("JWT config", test_jwt_config()))
    
    # Paths and security
    print_header("6. Paths & Security")
    results.append(("Database paths", test_database_paths()))
    results.append(("Security config", test_security_config()))
    
    # Production readiness
    print_header("7. Production Readiness")
    results.append(("Production ready", test_production_readiness()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All tests passed!{RESET}")
        print(f"\n{GREEN}Environment configuration is ready.{RESET}")
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
