#!/usr/bin/env python3
"""
Production Environment Setup Script
Interactive wizard to create production .env file
"""

import os
import sys
import secrets
import shutil
from datetime import datetime

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
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

def print_info(text):
    print(f"{CYAN}ℹ {text}{RESET}")

def generate_secret_key():
    """Generate a cryptographically secure secret key"""
    return secrets.token_hex(32)

def backup_existing_env():
    """Backup existing .env file if it exists"""
    if os.path.exists(".env"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f".env.backup_{timestamp}"
        shutil.copy(".env", backup_path)
        print_success(f"Existing .env backed up to: {backup_path}")
        return backup_path
    return None

def get_input(prompt, default=None, required=False, secret=False):
    """Get user input with optional default and validation"""
    if default:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "
    
    while True:
        if secret:
            import getpass
            value = getpass.getpass(prompt_text)
        else:
            value = input(prompt_text).strip()
        
        if not value and default:
            return default
        
        if not value and required:
            print_error("This field is required!")
            continue
        
        return value

def get_yes_no(prompt, default=True):
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print_error("Please enter 'y' or 'n'")

def main():
    print_header("Production Environment Setup Wizard")
    
    print("This wizard will help you create a production-ready .env file.")
    print("You can press Enter to accept default values shown in [brackets].")
    print()
    
    # Check if .env exists
    if os.path.exists(".env"):
        print_warning(".env file already exists!")
        if not get_yes_no("Do you want to overwrite it?", default=False):
            print("Setup cancelled.")
            return 1
        backup_existing_env()
    
    config = {}
    
    # ===== Environment Configuration =====
    print_header("1. Environment Configuration")
    
    config['ENV'] = 'production'
    print_info("Environment set to: production")
    
    config['DEBUG'] = 'false'
    print_info("Debug mode: false")
    
    config['LOG_LEVEL'] = get_input(
        "Log level (DEBUG/INFO/WARNING/ERROR)",
        default="INFO"
    ).upper()
    
    # ===== Secret Key =====
    print_header("2. Secret Key Configuration")
    
    print("SECRET_KEY is used for JWT tokens and session security.")
    print("It must be at least 32 characters long.")
    print()
    
    if get_yes_no("Generate a new SECRET_KEY automatically?", default=True):
        config['SECRET_KEY'] = generate_secret_key()
        print_success("Generated new SECRET_KEY")
        print_info(f"Key: {config['SECRET_KEY'][:16]}...{config['SECRET_KEY'][-16:]}")
    else:
        while True:
            secret_key = get_input(
                "Enter SECRET_KEY (min 32 chars)",
                required=True,
                secret=True
            )
            if len(secret_key) >= 32:
                config['SECRET_KEY'] = secret_key
                print_success("SECRET_KEY accepted")
                break
            else:
                print_error(f"SECRET_KEY too short ({len(secret_key)} chars, need 32+)")
    
    # ===== OpenAI Configuration =====
    print_header("3. OpenAI Configuration")
    
    print("OpenAI API enables AI-powered features:")
    print("  - Auto-translate feedback to English and Russian")
    print("  - Generate summaries")
    print("  - Auto-tag feedback")
    print()
    print("Without OpenAI, the system uses keyword-based fallback.")
    print()
    
    if get_yes_no("Do you have an OpenAI API key?", default=False):
        config['OPENAI_API_KEY'] = get_input(
            "Enter OpenAI API key",
            required=True,
            secret=True
        )
        print_success("OpenAI API key configured")
        
        config['OPENAI_MODEL'] = get_input(
            "OpenAI model (gpt-4o-mini/gpt-4o/gpt-4-turbo)",
            default="gpt-4o-mini"
        )
        
        config['OPENAI_TIMEOUT'] = get_input(
            "OpenAI timeout (seconds)",
            default="30"
        )
    else:
        print_info("Skipping OpenAI configuration (will use fallback mode)")
    
    # ===== Rate Limiting =====
    print_header("4. Rate Limiting")
    
    print("Rate limiting prevents spam and abuse.")
    print()
    
    config['RATE_LIMIT_MAX'] = get_input(
        "Max submissions per IP",
        default="10"
    )
    
    config['RATE_LIMIT_WINDOW_HOURS'] = get_input(
        "Time window (hours)",
        default="24"
    )
    
    # ===== File Upload =====
    print_header("5. File Upload Configuration")
    
    max_size_mb = get_input(
        "Max file size (MB)",
        default="5"
    )
    config['MAX_FILE_SIZE'] = str(int(max_size_mb) * 1024 * 1024)
    
    config['ALLOWED_EXTENSIONS'] = get_input(
        "Allowed file extensions (comma-separated)",
        default="jpg,jpeg,png"
    )
    
    # ===== Security =====
    print_header("6. Security Configuration")
    
    print("Configure CORS and trusted hosts for your domain.")
    print()
    
    domain = get_input(
        "Your domain (e.g., joyyfeedback.com)",
        required=False
    )
    
    if domain:
        config['CORS_ORIGINS'] = f"https://{domain},https://www.{domain}"
        config['TRUSTED_HOSTS'] = f"{domain},www.{domain}"
        print_success(f"Configured for domain: {domain}")
    else:
        print_warning("Using wildcard (*) - NOT recommended for production!")
        config['CORS_ORIGINS'] = "*"
        config['TRUSTED_HOSTS'] = "*"
    
    # ===== JWT Configuration =====
    print_header("7. JWT Configuration")
    
    config['ACCESS_TOKEN_EXPIRE_MINUTES'] = get_input(
        "JWT token expiration (minutes)",
        default="480"
    )
    
    # ===== Summary =====
    print_header("Configuration Summary")
    
    print(f"Environment: {config['ENV']}")
    print(f"Debug: {config['DEBUG']}")
    print(f"Log Level: {config['LOG_LEVEL']}")
    print(f"SECRET_KEY: {'*' * 32} (hidden)")
    print(f"OpenAI: {'Enabled' if 'OPENAI_API_KEY' in config else 'Disabled (fallback mode)'}")
    print(f"Rate Limit: {config['RATE_LIMIT_MAX']} per {config['RATE_LIMIT_WINDOW_HOURS']}h")
    print(f"Max File Size: {int(config['MAX_FILE_SIZE']) / (1024*1024):.0f}MB")
    print(f"CORS Origins: {config.get('CORS_ORIGINS', 'Not set')}")
    print()
    
    if not get_yes_no("Save this configuration?", default=True):
        print("Setup cancelled.")
        return 1
    
    # ===== Write .env file =====
    print_header("Writing Configuration")
    
    try:
        with open(".env", "w") as f:
            f.write("# ===== Budtender Feedback System - Production Configuration =====\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# DO NOT commit this file to version control!\n\n")
            
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print_success(".env file created successfully")
        
        # Set secure permissions
        os.chmod(".env", 0o600)
        print_success("File permissions set to 600 (owner read/write only)")
        
        # Create backup in secure location
        backup_dir = os.path.expanduser("~/.budtender_backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"env_backup_{timestamp}")
        shutil.copy(".env", backup_path)
        os.chmod(backup_path, 0o600)
        
        print_success(f"Backup created: {backup_path}")
        
    except Exception as e:
        print_error(f"Failed to write .env file: {e}")
        return 1
    
    # ===== Next Steps =====
    print_header("Setup Complete!")
    
    print_success("Production environment configured successfully")
    print()
    print("Next steps:")
    print("  1. Review .env file: cat .env")
    print("  2. Test configuration: python run.py")
    print("  3. Deploy with Docker: docker compose up -d")
    print()
    print_warning("IMPORTANT:")
    print("  - Never commit .env to version control")
    print("  - Keep backup in secure location")
    print("  - Change default admin passwords")
    print("  - Set up SSL/HTTPS before going live")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Setup cancelled by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
