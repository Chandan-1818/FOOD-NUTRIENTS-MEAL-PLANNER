"""
Quick .env File Creator
This will create a .env file with your email credentials.
"""

import os

print("="*70)
print(" CREATE .env FILE FOR EMAIL CONFIGURATION")
print("="*70)
print("\nThis will create a .env file in your project directory.")
print("You'll need your email credentials ready.\n")

# Get email provider
print("Select your email provider:")
print("1. Gmail (Recommended)")
print("2. Outlook/Hotmail") 
print("3. Yahoo")
print("4. Other")

choice = input("\nEnter choice (1-4): ").strip() or "1"

if choice == "1":
    smtp_server = "smtp.gmail.com"
    smtp_port = "587"
    print("\n✓ Gmail selected")
    print("\n⚠️  For Gmail, you need an App Password:")
    print("   Get it from: https://myaccount.google.com/apppasswords")
elif choice == "2":
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = "587"
    print("\n✓ Outlook/Hotmail selected")
elif choice == "3":
    smtp_server = "smtp.mail.yahoo.com"
    smtp_port = "587"
    print("\n✓ Yahoo selected")
else:
    smtp_server = input("Enter SMTP server: ").strip() or "smtp.gmail.com"
    smtp_port = input("Enter SMTP port [587]: ").strip() or "587"

# Get credentials
print("\n" + "="*70)
email = input("Enter your email address: ").strip()
if not email:
    print("❌ Email is required!")
    exit(1)

password = input("Enter your password (App Password for Gmail): ").strip()
if not password:
    print("❌ Password is required!")
    exit(1)

# Remove spaces from password
password = password.replace(' ', '')

# Create .env content
env_content = f"""SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SMTP_USERNAME={email}
SMTP_PASSWORD={password}
"""

# Write file
try:
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n" + "="*70)
    print("✅ SUCCESS! .env file created!")
    print("="*70)
    print(f"\nFile created at: {os.path.abspath('.env')}")
    print(f"\nConfiguration:")
    print(f"  Server: {smtp_server}")
    print(f"  Port: {smtp_port}")
    print(f"  Email: {email}")
    print(f"  Password: {'*' * len(password)}")
    
    print("\n" + "="*70)
    print(" NEXT STEPS:")
    print("="*70)
    print("1. Restart your Flask app (if running)")
    print("2. Test email: python test_email.py")
    print("3. Register a user - OTP will be sent!")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error creating .env file: {e}")
    print("\nPlease create .env file manually with this content:")
    print("\n" + "="*70)
    print(env_content)
    print("="*70)

