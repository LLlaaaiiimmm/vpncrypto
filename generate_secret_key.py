#!/usr/bin/env python3
"""
Generate a cryptographically secure SECRET_KEY for production use.
Usage: python generate_secret_key.py
"""
import secrets
import string

def generate_secret_key(length=64):
    """Generate a cryptographically secure random key."""
    # Use a mix of letters, digits, and punctuation for maximum entropy
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Remove characters that might cause issues in shell/env files
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '').replace('$', '')
    
    # Generate using secrets module (cryptographically secure)
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return key

def main():
    print("=" * 70)
    print("SECRET_KEY Generator for Budtender Feedback System")
    print("=" * 70)
    print()
    
    # Generate hex-based key (recommended)
    hex_key = secrets.token_hex(32)  # 32 bytes = 64 hex characters
    print("Option 1: Hex-based key (recommended)")
    print(f"SECRET_KEY={hex_key}")
    print()
    
    # Generate URL-safe base64 key
    urlsafe_key = secrets.token_urlsafe(48)  # ~64 characters
    print("Option 2: URL-safe base64 key")
    print(f"SECRET_KEY={urlsafe_key}")
    print()
    
    # Generate alphanumeric + punctuation key
    mixed_key = generate_secret_key(64)
    print("Option 3: Mixed alphanumeric + symbols")
    print(f"SECRET_KEY={mixed_key}")
    print()
    
    print("=" * 70)
    print("Instructions:")
    print("1. Copy one of the keys above")
    print("2. Add it to your .env file: SECRET_KEY=<your_key_here>")
    print("3. Keep this key secret and secure!")
    print("4. Never commit .env to version control")
    print("=" * 70)

if __name__ == "__main__":
    main()
