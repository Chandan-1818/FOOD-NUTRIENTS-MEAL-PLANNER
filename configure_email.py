"""
Email Configuration Helper for OTP Verification
This script helps you configure email settings for receiving OTP codes.
"""
import os
from pathlib import Path

def create_env_file():
    """Create or update .env file with email configuration"""
    env_path = Path('.env')
    
    print("="*60)
    print("EMAIL CONFIGURATION FOR OTP VERIFICATION")
    print("="*60)
    print("\nThis script will help you configure email settings.")
    print("You'll need a Gmail account with App Password enabled.\n")
    
    # Check if .env already exists
    existing_config = {}
    if env_path.exists():
        print("⚠️  .env file already exists. Reading current configuration...")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    existing_config[key] = value
        
        print("\nCurrent email configuration:")
        print(f"  SMTP_SERVER: {existing_config.get('SMTP_SERVER', 'Not set')}")
        print(f"  SMTP_PORT: {existing_config.get('SMTP_PORT', 'Not set')}")
        print(f"  SMTP_USERNAME: {existing_config.get('SMTP_USERNAME', 'Not set')}")
        print(f"  SMTP_PASSWORD: {'*' * len(existing_config.get('SMTP_PASSWORD', '')) if existing_config.get('SMTP_PASSWORD') else 'Not set'}")
        
        response = input("\nDo you want to update the email configuration? (y/n): ").strip().lower()
        if response != 'y':
            print("Configuration cancelled.")
            return
    
    print("\n" + "="*60)
    print("STEP 1: Gmail App Password Setup")
    print("="*60)
    print("\nTo use Gmail for sending OTP emails, you need to:")
    print("1. Enable 2-Step Verification on your Google Account")
    print("2. Generate an App Password")
    print("\nDetailed steps:")
    print("  a) Go to: https://myaccount.google.com/security")
    print("  b) Enable '2-Step Verification' if not already enabled")
    print("  c) Go to: https://myaccount.google.com/apppasswords")
    print("  d) Select 'Mail' and 'Other (Custom name)'")
    print("  e) Enter 'Food Insight' as the app name")
    print("  f) Click 'Generate'")
    print("  g) Copy the 16-character password (no spaces)")
    print("\n⚠️  IMPORTANT: Use the App Password, NOT your regular Gmail password!")
    
    input("\nPress Enter when you have your App Password ready...")
    
    print("\n" + "="*60)
    print("STEP 2: Enter Email Configuration")
    print("="*60)
    
    # Get email configuration
    smtp_server = input("\nSMTP Server (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
    smtp_port = input("SMTP Port (default: 587): ").strip() or "587"
    smtp_username = input("Your Gmail address (e.g., yourname@gmail.com): ").strip()
    smtp_password = input("App Password (16 characters, no spaces): ").strip()
    
    if not smtp_username or not smtp_password:
        print("\n❌ Error: Email address and App Password are required!")
        return
    
    # Read existing .env file to preserve other settings
    env_lines = []
    email_keys = ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD']
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                # Skip existing email config lines
                if not any(line.strip().startswith(key + '=') for key in email_keys):
                    env_lines.append(line.rstrip())
    
    # Add email configuration
    env_lines.append(f"\n# Email Configuration for OTP Verification")
    env_lines.append(f"SMTP_SERVER={smtp_server}")
    env_lines.append(f"SMTP_PORT={smtp_port}")
    env_lines.append(f"SMTP_USERNAME={smtp_username}")
    env_lines.append(f"SMTP_PASSWORD={smtp_password}")
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write('\n'.join(env_lines))
        if not env_lines[-1].endswith('\n'):
            f.write('\n')
    
    print("\n✓ Email configuration saved to .env file!")
    print("\n" + "="*60)
    print("STEP 3: Test Email Configuration")
    print("="*60)
    
    test = input("\nDo you want to test the email configuration now? (y/n): ").strip().lower()
    if test == 'y':
        test_email_config(smtp_server, smtp_port, smtp_username, smtp_password)
    else:
        print("\nYou can test email later by running: python test_email.py")
    
    print("\n" + "="*60)
    print("✓ EMAIL CONFIGURATION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart your Flask app if it's running")
    print("2. Register a new account to test OTP email")
    print("3. Check your email inbox for the OTP code")
    print("\n" + "="*60)

def test_email_config(smtp_server, smtp_port, smtp_username, smtp_password):
    """Test email configuration by sending a test email"""
    print("\nTesting email configuration...")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        test_email = input("Enter your email address to receive test OTP: ").strip()
        if not test_email:
            print("❌ No email address provided.")
            return
        
        # Generate test OTP
        import random
        import string
        test_otp = ''.join(random.choices(string.digits, k=6))
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = test_email
        msg['Subject'] = 'Test OTP - Food Insight Email Configuration'
        
        body = f"""
        Hello,
        
        This is a test email from Food Insight.
        
        Your test OTP code is: {test_otp}
        
        If you received this email, your email configuration is working correctly!
        
        Best regards,
        Food Insight Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print(f"\nSending test email to {test_email}...")
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"\n✓ Test email sent successfully!")
        print(f"✓ Test OTP code: {test_otp}")
        print(f"\nPlease check your inbox at: {test_email}")
        print("If you received the email, your configuration is working!")
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication failed!")
        print("Please check:")
        print("  1. Your Gmail address is correct")
        print("  2. You're using an App Password (not your regular password)")
        print("  3. 2-Step Verification is enabled on your Google account")
    except Exception as e:
        print(f"\n❌ Error sending test email: {e}")
        print("\nPlease check:")
        print("  1. Your internet connection")
        print("  2. SMTP server and port settings")
        print("  3. Firewall settings")

if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

