"""
Interactive .env File Setup Script
This script will help you create and configure your .env file for email sending.
"""

import os

def create_env_file():
    print("="*60)
    print("Email Configuration Setup")
    print("="*60)
    print("\nThis script will help you create a .env file for email configuration.")
    print("You'll need your email credentials to complete this setup.\n")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input(".env file already exists. Overwrite? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Cancelled. Keeping existing .env file.")
            return
    
    print("\n" + "="*60)
    print("Step 1: Choose Your Email Provider")
    print("="*60)
    print("1. Gmail (Recommended)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Other (Custom SMTP)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        smtp_server = 'smtp.gmail.com'
        smtp_port = '587'
        print("\n✓ Gmail selected")
        print("\n⚠️  IMPORTANT: For Gmail, you need an App Password (not your regular password)")
        print("   Get it from: https://myaccount.google.com/apppasswords")
        print("   Steps:")
        print("   1. Enable 2-Step Verification on your Google account")
        print("   2. Go to App Passwords")
        print("   3. Select 'Mail' and 'Other (Custom name)'")
        print("   4. Enter 'Health Food Monitor'")
        print("   5. Copy the 16-character password")
        
    elif choice == '2':
        smtp_server = 'smtp-mail.outlook.com'
        smtp_port = '587'
        print("\n✓ Outlook/Hotmail selected")
        
    elif choice == '3':
        smtp_server = 'smtp.mail.yahoo.com'
        smtp_port = '587'
        print("\n✓ Yahoo selected")
        print("\n⚠️  For Yahoo, you may need to generate an App Password")
        
    elif choice == '4':
        smtp_server = input("Enter SMTP server (e.g., smtp.example.com): ").strip()
        smtp_port = input("Enter SMTP port (usually 587): ").strip() or '587'
        print("\n✓ Custom SMTP configured")
    else:
        print("Invalid choice. Using Gmail defaults.")
        smtp_server = 'smtp.gmail.com'
        smtp_port = '587'
    
    print("\n" + "="*60)
    print("Step 2: Enter Your Email Credentials")
    print("="*60)
    
    smtp_username = input("\nEnter your email address: ").strip()
    if not smtp_username:
        print("❌ Email address is required!")
        return
    
    smtp_password = input("Enter your email password (or App Password for Gmail): ").strip()
    if not smtp_password:
        print("❌ Password is required!")
        return
    
    # Remove spaces from password (common issue with Gmail app passwords)
    smtp_password = smtp_password.replace(' ', '')
    
    # Create .env file content
    env_content = f"""# Email Configuration
# This file contains sensitive information - do not share or commit to git

SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SMTP_USERNAME={smtp_username}
SMTP_PASSWORD={smtp_password}

# Flask Secret Key (optional - for production)
SECRET_KEY=your_secret_key_change_in_production
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n" + "="*60)
        print("✓ .env file created successfully!")
        print("="*60)
        print(f"\nConfiguration saved:")
        print(f"  SMTP Server: {smtp_server}")
        print(f"  SMTP Port: {smtp_port}")
        print(f"  Email: {smtp_username}")
        print(f"  Password: {'*' * len(smtp_password)}")
        
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Restart your Flask application")
        print("2. Test the configuration by running: python test_email.py")
        print("3. Or register a new user to test OTP email sending")
        
        # Ask if user wants to test
        test = input("\nWould you like to test the email configuration now? (yes/no): ").strip().lower()
        if test == 'yes':
            print("\nRunning email test...")
            os.system('python test_email.py')
        
    except Exception as e:
        print(f"\n❌ Error creating .env file: {e}")
        print("\nPlease create the .env file manually with the following content:")
        print("\n" + "="*60)
        print(env_content)
        print("="*60)

if __name__ == '__main__':
    create_env_file()

