#!/usr/bin/env python3
"""
SECRET_KEY Generator for Flask applications.
Generates a cryptographically secure key.
"""
import secrets
import string
import os


def generate_secret_key(length=64):
    """Generate a secure SECRET_KEY."""
    secret_key_urlsafe = secrets.token_urlsafe(length)
    secret_key_hex = secrets.token_hex(length)

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    secret_key_mixed = ''.join(secrets.choice(alphabet) for _ in range(length))

    return {
        'urlsafe': secret_key_urlsafe,
        'hex': secret_key_hex,
        'mixed': secret_key_mixed
    }


def update_env_file(new_secret_key):
    """Update the .env file with the new SECRET_KEY."""
    env_file = '.env'

    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()

        updated_lines = []
        secret_key_found = False

        for line in lines:
            if line.startswith('SECRET_KEY='):
                updated_lines.append(f'SECRET_KEY={new_secret_key}\n')
                secret_key_found = True
                print(f"✅ SECRET_KEY updated in .env")
            else:
                updated_lines.append(line)

        if not secret_key_found:
            updated_lines.append(f'SECRET_KEY={new_secret_key}\n')

        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
    else:
        with open(env_file, 'w') as f:
            f.write(f'SECRET_KEY={new_secret_key}\n')
        print(f"✅ .env file created with SECRET_KEY")


if __name__ == '__main__':
    print("🔐 SECRET_KEY Generator for Flask")
    print("=" * 40)

    keys = generate_secret_key()

    print("\n🔑 Generated SECRET_KEYs:")
    print(f"URL-Safe (recommended): {keys['urlsafe']}")
    print(f"Hexadecimal: {keys['hex']}")
    print(f"Mixed characters: {keys['mixed']}")

    choice = input("\nWhich key would you like to use? (1=URL-Safe, 2=Hex, 3=Mixed) [1]: ").strip()

    if choice == '2':
        selected_key = keys['hex']
    elif choice == '3':
        selected_key = keys['mixed']
    else:
        selected_key = keys['urlsafe']

    update_choice = input(f"\nUpdate .env file with selected key? (y/n) [y]: ").strip().lower()

    if update_choice != 'n':
        update_env_file(selected_key)
        print(f"\n✅ Selected key: {selected_key}")
    else:
        print(f"\n📋 Copy this key to your .env file:")
        print(f"SECRET_KEY={selected_key}")

    print("\n🚨 Security Notes:")
    print("- Never commit the .env file to version control")
    print("- Use different keys for development and production")
    print("- Store production keys securely (environment variables)")
    print("- Regenerate keys regularly for better security")
