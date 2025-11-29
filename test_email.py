"""
Test Email Configuration
Run this script to test if your email configuration is working.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_config():
    print("="*60)
    print("Email Configuration Test")
    print("="*60)
    
    # Get configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    print(f"\nConfiguration:")
    print(f"  SMTP_SERVER: {SMTP_SERVER}")
    print(f"  SMTP_PORT: {SMTP_PORT}")
    print(f"  SMTP_USERNAME: {SMTP_USERNAME[:3] + '***' if SMTP_USERNAME else 'NOT SET'}")
    print(f"  SMTP_PASSWORD: {'***' if SMTP_PASSWORD else 'NOT SET'}")
    
    # Check if configured
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("\n❌ Email not configured!")
        print("\nPlease create a .env file with:")
        print("  SMTP_SERVER=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USERNAME=your_email@gmail.com")
        print("  SMTP_PASSWORD=your_app_password")
        return False
    
    # Test recipient
    test_email = input("\nEnter your email address to receive test email: ").strip()
    if not test_email:
        print("No email provided. Exiting.")
        return False
    
    try:
        print(f"\n{'='*60}")
        print("Testing email connection...")
        print(f"{'='*60}")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = test_email
        msg['Subject'] = 'Test Email - Health Food Monitor'
        
        body = """
        <html>
            <body>
                <h2>Test Email</h2>
                <p>If you received this email, your SMTP configuration is working correctly!</p>
                <p>You can now receive OTP verification codes.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect and send
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        print("✓ Connected")
        
        print("Starting TLS...")
        server.starttls()
        print("✓ TLS started")
        
        print("Authenticating...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✓ Authenticated")
        
        print(f"Sending test email to {test_email}...")
        server.send_message(msg)
        print("✓ Email sent")
        
        server.quit()
        
        print(f"\n{'='*60}")
        print("✓ SUCCESS! Test email sent successfully!")
        print(f"{'='*60}")
        print(f"\nPlease check your inbox (and spam folder) at: {test_email}")
        print("If you received the email, your configuration is correct.")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication Failed!")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. For Gmail: Use App Password (not regular password)")
        print("   - Go to: https://myaccount.google.com/apppasswords")
        print("   - Generate app password for 'Mail'")
        print("2. Make sure 2-Step Verification is enabled")
        print("3. Remove spaces from app password in .env file")
        return False
        
    except smtplib.SMTPServerDisconnected as e:
        print(f"\n❌ Connection Failed!")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify SMTP_SERVER is correct")
        print("3. Check firewall/antivirus settings")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Error Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_email_config()

