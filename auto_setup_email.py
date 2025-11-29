"""
Automatic Email Setup Script
This will create .env file and test email sending in one go.
"""

import os
import sys
from dotenv import load_dotenv

def create_env_automatically():
    print("="*70)
    print(" AUTOMATIC EMAIL SETUP - OTP Email Configuration")
    print("="*70)
    print("\nThis script will:")
    print("  1. Create .env file automatically")
    print("  2. Configure email settings")
    print("  3. Test email sending")
    print("  4. Send you a test OTP email\n")
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (yes/no): ").strip().lower()
        if overwrite != 'yes':
            print("Keeping existing .env file. Loading configuration...")
            load_dotenv()
            test_existing_config()
            return
        else:
            print("Will create new .env file...\n")
    
    print("="*70)
    print(" STEP 1: Email Provider Selection")
    print("="*70)
    print("\n1. Gmail (Recommended - Most reliable)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Custom SMTP")
    
    provider = input("\nSelect email provider (1-4) [Default: 1]: ").strip() or "1"
    
    if provider == "1":
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
        provider_name = "Gmail"
        print("\n✓ Gmail selected")
        print("\n⚠️  IMPORTANT: You need a Gmail App Password (not your regular password)")
        print("   Get it here: https://myaccount.google.com/apppasswords")
        print("   Steps:")
        print("   1. Enable 2-Step Verification (if not done)")
        print("   2. Go to App Passwords")
        print("   3. Select: Mail > Other > 'Health Food Monitor'")
        print("   4. Copy the 16-character password\n")
        
    elif provider == "2":
        smtp_server = "smtp-mail.outlook.com"
        smtp_port = "587"
        provider_name = "Outlook/Hotmail"
        print("\n✓ Outlook/Hotmail selected")
        
    elif provider == "3":
        smtp_server = "smtp.mail.yahoo.com"
        smtp_port = "587"
        provider_name = "Yahoo"
        print("\n✓ Yahoo selected")
        
    elif provider == "4":
        smtp_server = input("Enter SMTP server: ").strip()
        smtp_port = input("Enter SMTP port [587]: ").strip() or "587"
        provider_name = "Custom"
        print(f"\n✓ Custom SMTP: {smtp_server}:{smtp_port}")
    else:
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
        provider_name = "Gmail"
        print("\n✓ Using Gmail (default)")
    
    print("\n" + "="*70)
    print(" STEP 2: Enter Your Email Credentials")
    print("="*70)
    
    smtp_username = input(f"\nEnter your {provider_name} email address: ").strip()
    if not smtp_username:
        print("❌ Email address is required!")
        return False
    
    print(f"\nEnter your {provider_name} password:")
    if provider_name == "Gmail":
        print("   (Use App Password from https://myaccount.google.com/apppasswords)")
    smtp_password = input("Password: ").strip()
    if not smtp_password:
        print("❌ Password is required!")
        return False
    
    # Remove spaces (common issue with Gmail app passwords)
    smtp_password = smtp_password.replace(' ', '')
    
    # Create .env content
    env_content = f"""# Email Configuration - Auto-generated
# Created automatically by auto_setup_email.py
# DO NOT SHARE THIS FILE - Contains sensitive credentials

SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SMTP_USERNAME={smtp_username}
SMTP_PASSWORD={smtp_password}

# Flask Secret Key
SECRET_KEY=your_secret_key_change_in_production
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"\n✓ .env file created successfully at: {os.path.abspath('.env')}")
    except Exception as e:
        print(f"\n❌ Error creating .env file: {e}")
        return False
    
    # Reload environment variables
    load_dotenv(override=True)
    
    print("\n" + "="*70)
    print(" STEP 3: Testing Email Configuration")
    print("="*70)
    
    # Test email sending
    test_email = input(f"\nEnter an email address to receive test OTP (or press Enter to use {smtp_username}): ").strip()
    if not test_email:
        test_email = smtp_username
    
    print(f"\n📧 Sending test OTP email to: {test_email}")
    
    # Import and test
    try:
        # Add parent directory to path to import app functions
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import send_otp_email, generate_otp
        
        test_otp = generate_otp()
        print(f"Generated test OTP: {test_otp}")
        
        success = send_otp_email(test_email, test_otp, user_name="Test User")
        
        if success:
            print("\n" + "="*70)
            print(" ✅ SUCCESS! Email configuration is working!")
            print("="*70)
            print(f"\n✓ Test OTP email sent to: {test_email}")
            print(f"✓ OTP Code: {test_otp}")
            print("\n📬 Please check your inbox (and spam folder) for the test email.")
            print("\n" + "="*70)
            print(" NEXT STEPS:")
            print("="*70)
            print("1. Check your email inbox for the test OTP")
            print("2. Restart your Flask app: python app.py")
            print("3. Register a new user - OTP will be sent automatically!")
            print("="*70 + "\n")
            return True
        else:
            print("\n" + "="*70)
            print(" ⚠️  Email sending failed")
            print("="*70)
            print("\nPossible issues:")
            print("1. Wrong password (for Gmail: use App Password, not regular password)")
            print("2. 2-Step Verification not enabled (required for Gmail App Passwords)")
            print("3. Firewall/network blocking SMTP connection")
            print("4. Incorrect SMTP server/port settings")
            print("\nThe .env file has been created. You can:")
            print("- Edit it manually and try again")
            print("- Run this script again to reconfigure")
            print("="*70 + "\n")
            return False
            
    except ImportError as e:
        print(f"\n⚠️  Could not import app functions: {e}")
        print("The .env file has been created successfully.")
        print("Restart your Flask app to use the new configuration.")
        return True
    except Exception as e:
        print(f"\n❌ Error testing email: {e}")
        print("The .env file has been created. Please check your settings.")
        return False

def test_existing_config():
    """Test existing .env configuration"""
    print("\n" + "="*70)
    print(" Testing Existing Email Configuration")
    print("="*70)
    
    smtp_username = os.getenv('SMTP_USERNAME', '')
    if not smtp_username:
        print("❌ SMTP_USERNAME not found in .env file")
        return
    
    test_email = input(f"\nEnter email to test (or press Enter for {smtp_username}): ").strip()
    if not test_email:
        test_email = smtp_username
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import send_otp_email, generate_otp
        
        test_otp = generate_otp()
        print(f"\n📧 Sending test OTP to: {test_email}")
        print(f"Generated OTP: {test_otp}")
        
        success = send_otp_email(test_email, test_otp, user_name="Test User")
        
        if success:
            print(f"\n✅ Test email sent! Check {test_email} for OTP: {test_otp}")
        else:
            print("\n❌ Email sending failed. Check console output above for details.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    try:
        create_env_automatically()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

