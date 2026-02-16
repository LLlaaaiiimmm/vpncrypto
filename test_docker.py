#!/usr/bin/env python3
"""
Docker Configuration Test Suite
Tests Docker and docker-compose setup
"""

import subprocess
import time
import urllib.request
import urllib.error
import sys
import os
import sqlite3

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

def run_command(cmd, capture=True):
    """Run shell command and return output"""
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=60
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=60)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_docker_installed():
    """Check if Docker is installed"""
    print_test("Docker installation")
    code, stdout, stderr = run_command("docker --version")
    if code == 0:
        print_pass()
        print(f"  Version: {stdout.strip()}")
        return True
    else:
        print_fail("Docker not installed")
        return False

def check_docker_compose_installed():
    """Check if Docker Compose is installed"""
    print_test("Docker Compose installation")
    code, stdout, stderr = run_command("docker compose version")
    if code == 0:
        print_pass()
        print(f"  Version: {stdout.strip()}")
        return True
    else:
        print_fail("Docker Compose not installed")
        return False

def check_dockerfile_exists():
    """Check if Dockerfile exists"""
    print_test("Dockerfile exists")
    if os.path.exists("Dockerfile"):
        print_pass()
        return True
    else:
        print_fail("Dockerfile not found")
        return False

def check_docker_compose_file():
    """Check if docker-compose.yml exists"""
    print_test("docker-compose.yml exists")
    if os.path.exists("docker-compose.yml"):
        print_pass()
        return True
    else:
        print_fail("docker-compose.yml not found")
        return False

def check_env_file():
    """Check if .env file exists"""
    print_test(".env file exists")
    if os.path.exists(".env"):
        print_pass()
        return True
    else:
        print_fail(".env file not found (will use defaults)")
        return True  # Not critical

def build_docker_image():
    """Build Docker image"""
    print_test("Building Docker image")
    print()  # New line for build output
    code, stdout, stderr = run_command("docker compose build", capture=False)
    if code == 0:
        print_pass()
        return True
    else:
        print_fail(f"Build failed: {stderr}")
        return False

def start_container():
    """Start Docker container"""
    print_test("Starting container")
    code, stdout, stderr = run_command("docker compose up -d")
    if code == 0:
        print_pass()
        return True
    else:
        print_fail(f"Failed to start: {stderr}")
        return False

def wait_for_container(max_wait=60):
    """Wait for container to be healthy"""
    print_test(f"Waiting for container to be ready (max {max_wait}s)")
    
    for i in range(max_wait):
        try:
            # Check if container is running
            code, stdout, stderr = run_command("docker compose ps --format json")
            if code == 0 and "running" in stdout.lower():
                # Try to connect to the app
                try:
                    response = urllib.request.urlopen('http://localhost:8000/', timeout=2)
                    if response.status == 200:
                        print_pass()
                        print(f"  Ready after {i+1} seconds")
                        return True
                except (urllib.error.URLError, urllib.error.HTTPError):
                    pass
        except Exception:
            pass
        
        time.sleep(1)
    
    print_fail(f"Container not ready after {max_wait}s")
    return False

def check_container_running():
    """Check if container is running"""
    print_test("Container is running")
    code, stdout, stderr = run_command("docker compose ps")
    if code == 0 and "running" in stdout.lower():
        print_pass()
        return True
    else:
        print_fail("Container not running")
        return False

def check_app_accessible():
    """Check if app is accessible on port 8000"""
    print_test("App accessible on http://localhost:8000")
    try:
        response = urllib.request.urlopen('http://localhost:8000/', timeout=5)
        if response.status == 200:
            print_pass()
            return True
        else:
            print_fail(f"HTTP {response.status}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def check_database_created():
    """Check if database was created in volume"""
    print_test("Database created in volume")
    if os.path.exists("data/budtender.db"):
        print_pass()
        return True
    else:
        print_fail("Database file not found")
        return False

def check_database_tables():
    """Check if database tables were created"""
    print_test("Database tables created")
    try:
        conn = sqlite3.connect("data/budtender.db")
        cursor = conn.cursor()
        
        # Check for required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['feedback', 'users', 'rate_limits']
        missing = [t for t in required_tables if t not in tables]
        
        conn.close()
        
        if not missing:
            print_pass()
            print(f"  Tables: {', '.join(tables)}")
            return True
        else:
            print_fail(f"Missing tables: {', '.join(missing)}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def check_uploads_directory():
    """Check if uploads directory was created"""
    print_test("Uploads directory created")
    if os.path.exists("data/uploads"):
        print_pass()
        return True
    else:
        print_fail("Uploads directory not found")
        return False

def check_container_logs():
    """Check container logs for errors"""
    print_test("Container logs (checking for errors)")
    code, stdout, stderr = run_command("docker compose logs --tail=50")
    
    if code == 0:
        # Check for common error patterns
        errors = []
        error_patterns = ['error', 'exception', 'failed', 'traceback']
        
        for line in stdout.lower().split('\n'):
            for pattern in error_patterns:
                if pattern in line and 'no error' not in line:
                    errors.append(line.strip())
                    break
        
        if not errors:
            print_pass()
            return True
        else:
            print_fail("Errors found in logs")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  {error}")
            return False
    else:
        print_fail("Could not retrieve logs")
        return False

def check_healthcheck():
    """Check Docker healthcheck status"""
    print_test("Docker healthcheck status")
    code, stdout, stderr = run_command("docker inspect --format='{{.State.Health.Status}}' budtender-feedback-system")
    
    if code == 0:
        status = stdout.strip()
        if status == "healthy":
            print_pass()
            return True
        elif status == "starting":
            print_fail("Still starting (wait a bit longer)")
            return False
        else:
            print_fail(f"Status: {status}")
            return False
    else:
        print_fail("Could not check health status")
        return False

def check_volume_mount():
    """Check if volume is properly mounted"""
    print_test("Volume mount working")
    
    # Create a test file in data directory
    test_file = "data/test_volume.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Check if file is visible in container
        code, stdout, stderr = run_command(
            "docker compose exec -T bfs ls /app/data/test_volume.txt"
        )
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        
        if code == 0:
            print_pass()
            return True
        else:
            print_fail("Volume not properly mounted")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def stop_container():
    """Stop Docker container"""
    print_test("Stopping container")
    code, stdout, stderr = run_command("docker compose down")
    if code == 0:
        print_pass()
        return True
    else:
        print_fail(f"Failed to stop: {stderr}")
        return False

def main():
    print_header("Docker Configuration Test Suite")
    
    results = []
    
    # Pre-flight checks
    print_header("1. Pre-flight Checks")
    results.append(("Docker installed", check_docker_installed()))
    results.append(("Docker Compose installed", check_docker_compose_installed()))
    results.append(("Dockerfile exists", check_dockerfile_exists()))
    results.append(("docker-compose.yml exists", check_docker_compose_file()))
    results.append((".env file", check_env_file()))
    
    # If pre-flight fails, stop here
    if not all([r[1] for r in results[:4]]):
        print(f"\n{RED}Pre-flight checks failed. Fix issues before continuing.{RESET}")
        return False
    
    # Build and start
    print_header("2. Build & Start")
    results.append(("Build image", build_docker_image()))
    results.append(("Start container", start_container()))
    results.append(("Wait for ready", wait_for_container()))
    
    # Runtime checks
    print_header("3. Runtime Checks")
    results.append(("Container running", check_container_running()))
    results.append(("App accessible", check_app_accessible()))
    results.append(("Database created", check_database_created()))
    results.append(("Database tables", check_database_tables()))
    results.append(("Uploads directory", check_uploads_directory()))
    results.append(("Volume mount", check_volume_mount()))
    results.append(("Container logs", check_container_logs()))
    results.append(("Healthcheck", check_healthcheck()))
    
    # Cleanup
    print_header("4. Cleanup")
    results.append(("Stop container", stop_container()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All tests passed!{RESET}")
        print(f"\n{GREEN}Docker setup is ready for deployment.{RESET}")
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
        print(f"\n{YELLOW}Cleaning up...{RESET}")
        run_command("docker compose down")
        sys.exit(1)
