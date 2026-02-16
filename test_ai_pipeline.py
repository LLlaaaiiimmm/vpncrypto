#!/usr/bin/env python3
"""
AI Pipeline Test Suite
Tests for OpenAI integration and fallback processing
"""
import os
import sys
import time
import sqlite3
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import DATABASE_PATH, OPENAI_API_KEY
from app.ai_pipeline import process_feedback_async, _process_fallback

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

def create_test_feedback(message, category="complaint"):
    """Create a test feedback entry in the database"""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    
    # Generate submission ID
    import random
    import string
    submission_id = f"TEST-{random.randint(100,999)}-{random.randint(10,99)}"
    
    # Insert feedback
    db.execute("""
        INSERT INTO feedback (submission_id, category, message, ip_hash, user_agent, ai_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (submission_id, category, message, "test_hash", "test_agent", "pending"))
    
    db.commit()
    
    # Get feedback ID
    feedback_id = db.execute(
        "SELECT id FROM feedback WHERE submission_id = ?", 
        (submission_id,)
    ).fetchone()[0]
    
    db.close()
    return feedback_id

def get_feedback_status(feedback_id):
    """Get feedback AI status and results"""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    
    row = db.execute(
        "SELECT * FROM feedback WHERE id = ?", 
        (feedback_id,)
    ).fetchone()
    
    db.close()
    return dict(row) if row else None

def wait_for_processing(feedback_id, timeout=10):
    """Wait for AI processing to complete"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        feedback = get_feedback_status(feedback_id)
        if feedback and feedback['ai_status'] in ('done', 'failed'):
            return feedback
        time.sleep(0.5)
    return None

def cleanup_test_feedback(feedback_id):
    """Remove test feedback from database"""
    db = sqlite3.connect(DATABASE_PATH)
    db.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
    db.close()

# ==================== FALLBACK MODE TESTS ====================

def test_fallback_english():
    """Test 1.1: Fallback processing with English text"""
    print_section("1. Fallback Mode Tests (No OpenAI Key)")
    
    # Temporarily disable OpenAI key
    original_key = os.environ.get('OPENAI_API_KEY')
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    
    feedback_id = create_test_feedback("The salary is too low and the manager is not helpful")
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id)
    
    if result:
        passed = (
            result['ai_status'] == 'done' and
            result['detected_language'] == 'en' and
            'Salary' in result['tags'] and
            result['summary'] is not None
        )
        print_test("English text processed", passed, 
                  f"Status: {result['ai_status']}, Lang: {result['detected_language']}, Tags: {result['tags']}")
    else:
        print_test("English text processed", False, "Timeout waiting for processing")
    
    cleanup_test_feedback(feedback_id)
    
    # Restore OpenAI key
    if original_key:
        os.environ['OPENAI_API_KEY'] = original_key

def test_fallback_thai():
    """Test 1.2: Fallback processing with Thai text"""
    feedback_id = create_test_feedback("เงินเดือนต่ำเกินไป และผู้จัดการไม่ช่วยเหลือ")
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id)
    
    if result:
        passed = (
            result['ai_status'] == 'done' and
            result['detected_language'] == 'th' and
            result['tags'] is not None
        )
        print_test("Thai text processed", passed,
                  f"Status: {result['ai_status']}, Lang: {result['detected_language']}, Tags: {result['tags']}")
    else:
        print_test("Thai text processed", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)

def test_fallback_cyrillic():
    """Test 1.3: Fallback processing with Cyrillic text"""
    feedback_id = create_test_feedback("Зарплата слишком низкая и менеджер не помогает")
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id)
    
    if result:
        passed = (
            result['ai_status'] == 'done' and
            result['detected_language'] == 'ru' and
            result['tags'] is not None
        )
        print_test("Cyrillic text processed", passed,
                  f"Status: {result['ai_status']}, Lang: {result['detected_language']}, Tags: {result['tags']}")
    else:
        print_test("Cyrillic text processed", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)

def test_fallback_keyword_tagging():
    """Test 1.4: Keyword-based tagging accuracy"""
    test_cases = [
        ("Need better training and equipment", ["Training", "Equipment"]),
        ("Store is dirty and unsafe", ["Store", "Safety", "Hygiene"]),
        ("Customer complaints about product quality", ["Customer", "Product"]),
        ("Schedule conflicts with manager", ["Schedule", "Management"]),
    ]
    
    for message, expected_tags in test_cases:
        feedback_id = create_test_feedback(message)
        process_feedback_async(feedback_id)
        result = wait_for_processing(feedback_id)
        
        if result:
            result_tags = result['tags'].split(',') if result['tags'] else []
            # Check if at least one expected tag is present
            has_expected = any(tag in result_tags for tag in expected_tags)
            passed = result['ai_status'] == 'done' and has_expected
            print_test(f"Keyword tagging: '{message[:40]}...'", passed,
                      f"Expected: {expected_tags}, Got: {result_tags}")
        else:
            print_test(f"Keyword tagging: '{message[:40]}...'", False, "Timeout")
        
        cleanup_test_feedback(feedback_id)

# ==================== OPENAI MODE TESTS ====================

def test_openai_processing():
    """Test 2.1: OpenAI processing (if key available)"""
    print_section("2. OpenAI Mode Tests")
    
    if not OPENAI_API_KEY:
        print(f"{Colors.YELLOW}⚠ SKIP - No OpenAI API key configured{Colors.END}")
        print("      Set OPENAI_API_KEY in .env to test OpenAI integration")
        return
    
    feedback_id = create_test_feedback("The salary is too low and the manager is not helpful")
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id, timeout=30)
    
    if result:
        passed = (
            result['ai_status'] == 'done' and
            result['translation_en'] is not None and
            result['translation_ru'] is not None and
            result['summary'] is not None and
            result['tags'] is not None
        )
        print_test("OpenAI processing completed", passed,
                  f"Status: {result['ai_status']}, Summary: {result['summary'][:50]}...")
    else:
        print_test("OpenAI processing completed", False, "Timeout (30s)")
    
    cleanup_test_feedback(feedback_id)

def test_openai_invalid_key():
    """Test 2.2: Fallback on invalid API key"""
    if not OPENAI_API_KEY:
        print(f"{Colors.YELLOW}⚠ SKIP - No OpenAI API key to test{Colors.END}")
        return
    
    # Temporarily set invalid key
    original_key = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_KEY'] = 'sk-invalid-key-for-testing'
    
    # Reload config
    import importlib
    import app.config
    importlib.reload(app.config)
    
    feedback_id = create_test_feedback("Test message for invalid key")
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id, timeout=15)
    
    if result:
        # Should fallback to keyword-based processing
        passed = result['ai_status'] == 'done'
        print_test("Fallback on invalid API key", passed,
                  f"Status: {result['ai_status']} (should fallback, not fail)")
    else:
        print_test("Fallback on invalid API key", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)
    
    # Restore original key
    if original_key:
        os.environ['OPENAI_API_KEY'] = original_key
    importlib.reload(app.config)

# ==================== ERROR HANDLING TESTS ====================

def test_empty_message():
    """Test 3.1: Empty message handling"""
    print_section("3. Error Handling Tests")
    
    feedback_id = create_test_feedback("")
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id)
    
    if result:
        passed = result['ai_status'] == 'done' and result['detected_language'] == 'unknown'
        print_test("Empty message handled", passed,
                  f"Status: {result['ai_status']}, Lang: {result['detected_language']}")
    else:
        print_test("Empty message handled", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)

def test_very_long_message():
    """Test 3.2: Very long message handling"""
    long_message = "This is a test message. " * 200  # ~5000 characters
    
    feedback_id = create_test_feedback(long_message)
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id, timeout=30)
    
    if result:
        passed = result['ai_status'] in ('done', 'failed')
        summary_length = len(result['summary']) if result['summary'] else 0
        print_test("Long message handled", passed,
                  f"Status: {result['ai_status']}, Summary length: {summary_length}")
    else:
        print_test("Long message handled", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)

def test_special_characters():
    """Test 3.3: Special characters handling"""
    special_message = "Test with <script>alert('xss')</script> and SQL'; DROP TABLE--"
    
    feedback_id = create_test_feedback(special_message)
    process_feedback_async(feedback_id)
    
    result = wait_for_processing(feedback_id)
    
    if result:
        passed = result['ai_status'] == 'done'
        print_test("Special characters handled", passed,
                  f"Status: {result['ai_status']}")
    else:
        print_test("Special characters handled", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)

# ==================== STATUS TESTS ====================

def test_status_transitions():
    """Test 4: AI status transitions"""
    print_section("4. Status Transition Tests")
    
    feedback_id = create_test_feedback("Test status transitions")
    
    # Check initial status
    initial = get_feedback_status(feedback_id)
    print_test("Initial status is 'pending'", initial['ai_status'] == 'pending',
              f"Status: {initial['ai_status']}")
    
    # Start processing
    process_feedback_async(feedback_id)
    time.sleep(0.5)
    
    # Check processing status
    processing = get_feedback_status(feedback_id)
    print_test("Status changes to 'processing'", processing['ai_status'] == 'processing',
              f"Status: {processing['ai_status']}")
    
    # Wait for completion
    final = wait_for_processing(feedback_id)
    if final:
        print_test("Final status is 'done' or 'failed'", 
                  final['ai_status'] in ('done', 'failed'),
                  f"Status: {final['ai_status']}")
    else:
        print_test("Final status is 'done' or 'failed'", False, "Timeout")
    
    cleanup_test_feedback(feedback_id)

# ==================== MAIN ====================

def run_all_tests():
    """Run all AI pipeline tests"""
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}AI Pipeline Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Budtender Feedback System{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    
    # Check database
    if not os.path.exists(DATABASE_PATH):
        print(f"\n{Colors.RED}✗ Database not found: {DATABASE_PATH}{Colors.END}")
        print("Please run the application first to create the database.\n")
        return
    
    print(f"\nDatabase: {DATABASE_PATH}")
    print(f"OpenAI Key: {'✓ Configured' if OPENAI_API_KEY else '✗ Not configured'}\n")
    
    # Run tests
    test_fallback_english()
    test_fallback_thai()
    test_fallback_cyrillic()
    test_fallback_keyword_tagging()
    
    test_openai_processing()
    test_openai_invalid_key()
    
    test_empty_message()
    test_very_long_message()
    test_special_characters()
    
    test_status_transitions()
    
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Test suite completed{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")
    
    print(f"{Colors.BLUE}Note:{Colors.END} Some tests may take 10-30 seconds to complete.")
    print(f"Check logs for detailed error messages if tests fail.\n")

if __name__ == "__main__":
    run_all_tests()
