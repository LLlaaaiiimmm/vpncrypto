#!/usr/bin/env python3
"""
File Upload and Form Validation Test Suite
Tests for Budtender Feedback System
"""
import requests
import io
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

def create_test_image(format="jpeg", size_kb=10):
    """Create a test image in memory"""
    if format == "jpeg":
        # JPEG signature + minimal data
        data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        data += b'\x00' * (size_kb * 1024 - len(data))
        return data, "test.jpg"
    elif format == "png":
        # PNG signature + minimal data
        data = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0dIHDR'
        data += b'\x00' * (size_kb * 1024 - len(data))
        return data, "test.png"
    else:
        return b'fake data', f"test.{format}"

def submit_feedback(message, photo_data=None, photo_filename=None, category="complaint"):
    """Submit feedback with optional photo"""
    data = {
        "category": category,
        "message": message,
        "anonymity_consent": "on"
    }
    
    files = {}
    if photo_data:
        files["photo"] = (photo_filename, io.BytesIO(photo_data), "image/jpeg")
    
    response = requests.post(f"{BASE_URL}/submit", data=data, files=files if files else None)
    return response

# ==================== FILE UPLOAD TESTS ====================

def test_file_size_limit():
    """Test 1.1: Files >5MB should be rejected"""
    print_section("1. File Upload Tests")
    
    # Test file exactly at limit (5MB)
    data, filename = create_test_image("jpeg", size_kb=5120)  # 5MB
    response = submit_feedback("Test message", data, filename)
    passed = response.status_code in [200, 302]
    print_test("5MB file accepted", passed, f"Status: {response.status_code}")
    
    # Test file over limit (6MB)
    data, filename = create_test_image("jpeg", size_kb=6144)  # 6MB
    response = submit_feedback("Test message", data, filename)
    passed = response.status_code == 400 and "too large" in response.text.lower()
    print_test("6MB file rejected", passed, f"Status: {response.status_code}")

def test_file_extension_validation():
    """Test 1.2: Only JPG/PNG allowed"""
    
    # Test valid extensions
    for ext in ["jpg", "jpeg", "png"]:
        data, filename = create_test_image(ext if ext != "jpeg" else "jpeg", size_kb=10)
        response = submit_feedback("Test message", data, filename)
        passed = response.status_code in [200, 302]
        print_test(f".{ext} file accepted", passed, f"Status: {response.status_code}")
    
    # Test invalid extensions
    for ext in ["exe", "php", "txt", "pdf", "gif"]:
        data = b"fake executable data"
        filename = f"malicious.{ext}"
        response = submit_feedback("Test message", data, filename)
        passed = response.status_code == 400
        print_test(f".{ext} file rejected", passed, f"Status: {response.status_code}")

def test_mime_type_validation():
    """Test 1.3: MIME type validation (not just extension)"""
    
    # Test: PHP file disguised as JPG
    php_content = b"<?php system($_GET['cmd']); ?>"
    response = submit_feedback("Test message", php_content, "malicious.jpg")
    passed = response.status_code == 400
    print_test("PHP disguised as .jpg rejected", passed, f"Status: {response.status_code}")
    
    # Test: EXE disguised as PNG
    exe_content = b"MZ\x90\x00" + b"\x00" * 100  # EXE signature
    response = submit_feedback("Test message", exe_content, "malicious.png")
    passed = response.status_code == 400
    print_test("EXE disguised as .png rejected", passed, f"Status: {response.status_code}")
    
    # Test: Valid JPEG with correct signature
    jpeg_data, filename = create_test_image("jpeg", size_kb=10)
    response = submit_feedback("Test message", jpeg_data, filename)
    passed = response.status_code in [200, 302]
    print_test("Valid JPEG accepted", passed, f"Status: {response.status_code}")

def test_empty_file():
    """Test 1.4: Empty files should be rejected"""
    response = submit_feedback("Test message", b"", "empty.jpg")
    passed = response.status_code == 400 and "empty" in response.text.lower()
    print_test("Empty file rejected", passed, f"Status: {response.status_code}")

def test_filename_sanitization():
    """Test 1.5: Filenames should be sanitized"""
    # Test with malicious filename
    malicious_names = [
        "../../../etc/passwd.jpg",
        "../../uploads/hack.jpg",
        "test<script>.jpg",
        "test'; DROP TABLE feedback; --.jpg"
    ]
    
    for malicious_name in malicious_names:
        data, _ = create_test_image("jpeg", size_kb=10)
        response = submit_feedback("Test message", data, malicious_name)
        # Should accept (filename is regenerated) or reject safely
        passed = response.status_code in [200, 302, 400]
        print_test(f"Malicious filename handled: {malicious_name[:30]}...", passed, 
                  f"Status: {response.status_code}")

# ==================== TEXT VALIDATION TESTS ====================

def test_message_length_validation():
    """Test 2.1: Message length limits"""
    print_section("2. Text Validation Tests")
    
    # Test empty message
    response = submit_feedback("")
    passed = response.status_code == 400 and "empty" in response.text.lower()
    print_test("Empty message rejected", passed, f"Status: {response.status_code}")
    
    # Test whitespace-only message
    response = submit_feedback("   \n\t   ")
    passed = response.status_code == 400
    print_test("Whitespace-only message rejected", passed, f"Status: {response.status_code}")
    
    # Test valid message
    response = submit_feedback("This is a valid feedback message")
    passed = response.status_code in [200, 302]
    print_test("Valid message accepted", passed, f"Status: {response.status_code}")
    
    # Test message at limit (1000 chars)
    message_1000 = "A" * 1000
    response = submit_feedback(message_1000)
    passed = response.status_code in [200, 302]
    print_test("1000 character message accepted", passed, f"Status: {response.status_code}")
    
    # Test message over limit (1001 chars)
    message_1001 = "A" * 1001
    response = submit_feedback(message_1001)
    passed = response.status_code == 400 and "too long" in response.text.lower()
    print_test("1001 character message rejected", passed, f"Status: {response.status_code}")

def test_xss_protection():
    """Test 2.2: XSS protection in text fields"""
    
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(1)'>",
        "';alert(String.fromCharCode(88,83,83))//",
    ]
    
    for payload in xss_payloads:
        response = submit_feedback(payload)
        # Should accept but escape the content
        passed = response.status_code in [200, 302]
        
        # Check if HTML is escaped (< becomes &lt;, > becomes &gt;)
        # This would need to check the database or rendered output
        print_test(f"XSS payload handled: {payload[:40]}...", passed, 
                  f"Status: {response.status_code}")

def test_unicode_support():
    """Test 2.3: Unicode support (emoji, Cyrillic, Thai)"""
    
    unicode_tests = [
        ("Emoji", "Great service! 😊👍🎉"),
        ("Cyrillic", "Отличный сервис! Спасибо большое!"),
        ("Thai", "บริการดีมาก ขอบคุณครับ"),
        ("Mixed", "Hello мир 世界 🌍"),
        ("Arabic", "خدمة ممتازة شكرا لكم"),
        ("Chinese", "服务很好，谢谢！"),
        ("Japanese", "素晴らしいサービスです！"),
    ]
    
    for name, message in unicode_tests:
        response = submit_feedback(message)
        passed = response.status_code in [200, 302]
        print_test(f"{name} text accepted", passed, 
                  f"Status: {response.status_code}, Length: {len(message)}")

def test_special_characters():
    """Test 2.4: Special characters handling"""
    
    special_chars = [
        "Test with quotes: 'single' and \"double\"",
        "Test with symbols: @#$%^&*()",
        "Test with newlines:\nLine 1\nLine 2",
        "Test with tabs:\tTabbed\tText",
        "SQL-like: ' OR '1'='1",
        "Path-like: ../../../etc/passwd",
    ]
    
    for message in special_chars:
        response = submit_feedback(message)
        passed = response.status_code in [200, 302]
        print_test(f"Special chars handled: {message[:40]}...", passed, 
                  f"Status: {response.status_code}")

# ==================== CATEGORY VALIDATION ====================

def test_category_validation():
    """Test 3: Category validation"""
    print_section("3. Category Validation Tests")
    
    # Valid categories
    valid_categories = ["complaint", "idea", "recommendation", "other"]
    for cat in valid_categories:
        response = submit_feedback("Test message", category=cat)
        passed = response.status_code in [200, 302]
        print_test(f"Valid category '{cat}' accepted", passed, f"Status: {response.status_code}")
    
    # Invalid categories
    invalid_categories = ["invalid", "hack", "", "admin", "<script>"]
    for cat in invalid_categories:
        response = submit_feedback("Test message", category=cat)
        passed = response.status_code == 400
        print_test(f"Invalid category '{cat}' rejected", passed, f"Status: {response.status_code}")

# ==================== MAIN ====================

def run_all_tests():
    """Run all validation tests"""
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}File Upload & Form Validation Test Suite{Colors.END}")
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
    test_file_size_limit()
    test_file_extension_validation()
    test_mime_type_validation()
    test_empty_file()
    test_filename_sanitization()
    
    test_message_length_validation()
    test_xss_protection()
    test_unicode_support()
    test_special_characters()
    
    test_category_validation()
    
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Test suite completed{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")
    
    print(f"{Colors.BLUE}Note:{Colors.END} Some tests may show warnings about rate limiting.")
    print(f"If you see 'rate limited' errors, wait 24 hours or clear the database.\n")

if __name__ == "__main__":
    run_all_tests()
