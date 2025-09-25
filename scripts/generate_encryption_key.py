#!/usr/bin/env python3
"""
Generate encryption keys for DigitalBoda Django application.

This script generates secure encryption keys that are compatible with
the Fernet encryption used by the application.
"""

import secrets
import string
from cryptography.fernet import Fernet


def generate_django_secret_key(length=50):
    """Generate a Django SECRET_KEY."""
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_fernet_key():
    """Generate a Fernet encryption key."""
    return Fernet.generate_key().decode()


def generate_salt(length=32):
    """Generate a random salt for hashing."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def main():
    print("🔐 DigitalBoda Encryption Key Generator")
    print("=" * 50)
    
    print("\n📋 Copy these values to your .env file:")
    print("-" * 40)
    
    django_key = generate_django_secret_key()
    fernet_key = generate_fernet_key()
    salt = generate_salt()
    
    print(f"SECRET_KEY={django_key}")
    print(f"ID_ENCRYPTION_KEY={fernet_key}")
    print(f"ID_HASH_SALT={salt}")
    
    print("\n" + "=" * 50)
    print("✅ Keys generated successfully!")
    print("\n🔒 Security Notes:")
    print("• Keep these keys secret and secure")
    print("• Use different keys for staging and production")
    print("• Never commit these keys to version control")
    print("• Back up your keys securely")


if __name__ == "__main__":
    main()
