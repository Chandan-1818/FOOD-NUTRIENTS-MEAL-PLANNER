"""
Quick Email Configuration Checker
Run this to see if your email is configured correctly.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("Email Configuration Check")
print("="*60)

SMTP_SERVER = os.getenv('SMTP_SERVER', '')
SMTP_PORT = os.getenv('SMTP_PORT', '')
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

print(f"\nCurrent Configuration:")
print(f"  SMTP_SERVER: {SMTP_SERVER or 'NOT SET (default: smtp.gmail.com)'}")
print(f"  SMTP_PORT: {SMTP_PORT or 'NOT SET (default: 587)'}")
print(f"  SMTP_USERNAME: {SMTP_USERNAME[:3] + '***@' + SMTP_USERNAME.split('@')[1] if SMTP_USERNAME and '@' in SMTP_USERNAME else 'NOT SET'}")
print(f"  SMTP_PASSWORD: {'***SET***' if SMTP_PASSWORD else 'NOT SET'}")

if not SMTP_USERNAME or not SMTP_PASSWORD:
    print("\n❌ Email is NOT configured!")
    print("\nTo configure email:")
    print("1. Create a file named '.env' in the project root")
    print("2. Add the following lines:")
    print("\n   SMTP_SERVER=smtp.gmail.com")
    print("   SMTP_PORT=587")
    print("   SMTP_USERNAME=your_email@gmail.com")
    print("   SMTP_PASSWORD=your_app_password")
    print("\n3. For Gmail: Get App Password from:")
    print("   https://myaccount.google.com/apppasswords")
    print("\n4. Restart your Flask app after creating .env file")
else:
    print("\n✓ Email appears to be configured!")
    print("\nTo test if it works, run: python test_email.py")

print("\n" + "="*60)

