from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text
import os
import uuid
import base64
import requests
import json
import re
import math
import random
import string
import io
import socket
# Email sending imports for verification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Load environment variables from .env file
load_dotenv()

# Admin credentials (hardcoded - cannot be changed or deleted)
ADMIN_USERNAME = "CHANDAN"
ADMIN_PASSWORD = "chandan...$$$"

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_change_in_production')  # Use environment variable or default

# Database configuration - supports both SQLite (local) and PostgreSQL (production)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Production: Use PostgreSQL from DATABASE_URL (Render provides this)
    # Render's DATABASE_URL format: postgresql://user:pass@host:port/dbname
    # SQLAlchemy needs 'postgresql://' but Render gives 'postgres://', so fix it
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    number = db.Column(db.String(15), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    health_data = db.relationship('HealthData', backref='user', lazy=True)

class HealthData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    food_image = db.Column(db.String(255), nullable=True)
    food_name = db.Column(db.String(100), nullable=True)
    nutrition_info = db.Column(db.Text, nullable=True)
    assessment = db.Column(db.Text, nullable=True)
    diet_plan = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

class EmailVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    otp = db.Column(db.String(6), nullable=False)  # 6-digit OTP code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_bmi(weight, height):
    # Height in meters (convert from cm)
    height_m = height / 100
    bmi = weight / (height_m * height_m)
    return round(bmi, 2)

# CAPTCHA generation function
def generate_captcha():
    """Generate a simple CAPTCHA image and return the code and image data"""
    # Generate random 5-character code (letters and numbers)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    
    # Create image
    width, height = 150, 50
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # Draw text with some noise
    for i, char in enumerate(code):
        x = 20 + i * 25 + random.randint(-5, 5)
        y = 10 + random.randint(-5, 5)
        draw.text((x, y), char, fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)), font=font)
    
    # Add some noise lines
    for _ in range(5):
        draw.line([(random.randint(0, width), random.randint(0, height)),
                   (random.randint(0, width), random.randint(0, height))],
                  fill=(200, 200, 200), width=1)
    
    # Convert to base64 string
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return code, img_base64

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_verification_token():
    """Generate a secure random token for email verification (legacy - not used)"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_otp():
    """Generate a 6-digit OTP code for email verification"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, otp_code):
    """Send verification email with OTP code (with timeout to prevent worker timeout)"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        # If email not configured, return False with detailed error
        if not smtp_username or not smtp_password:
            print(f"⚠️  Email not configured. Cannot send OTP to {email}")
            print(f"   SMTP_USERNAME: {'SET' if smtp_username else 'NOT SET'}")
            print(f"   SMTP_PASSWORD: {'SET' if smtp_password else 'NOT SET'}")
            print(f"   SMTP_SERVER: {smtp_server}")
            print(f"   SMTP_PORT: {smtp_port}")
            print(f"   Environment: {'PRODUCTION (Render)' if os.getenv('DATABASE_URL') else 'LOCAL'}")
            print(f"   Please configure SMTP settings in Render Environment Variables:")
            print(f"   - Go to Render Dashboard → Your Service → Environment tab")
            print(f"   - Add: SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD")
            return False
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = 'Verify Your Email - Food Insight'
        
        body = f"""
        Hello,
        
        Thank you for registering with Food Insight!
        
        Your email verification code is: {otp_code}
        
        Please enter this code on the verification page to verify your email address.
        
        This code will expire in 10 minutes.
        
        If you did not create this account, please ignore this email.
        
        Best regards,
        Food Insight Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Set socket timeout to prevent hanging (10 seconds total timeout)
        socket.setdefaulttimeout(10)
        
        # Send email with timeout protection
        # Try SSL (port 465) if TLS (port 587) fails due to network restrictions
        try:
            # Try TLS first (port 587)
            if smtp_port == 587:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()
                print(f"✓ Verification OTP sent to {email} (via TLS)")
                return True
            # Try SSL (port 465)
            elif smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()
                print(f"✓ Verification OTP sent to {email} (via SSL)")
                return True
            else:
                # Fallback to TLS for other ports
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()
                print(f"✓ Verification OTP sent to {email}")
                return True
        except socket.timeout:
            print(f"❌ SMTP connection timeout for {email}")
            print(f"   Email server took too long to respond")
            return False
        except socket.error as e:
            error_code = str(e)
            print(f"❌ Socket error sending email to {email}: {e}")
            if "Network is unreachable" in error_code or "101" in error_code:
                print(f"   ⚠️  Network unreachable - Render may be blocking SMTP connections")
                print(f"   💡 SOLUTION: Try using port 465 with SSL instead of 587 with TLS")
                print(f"   - In Render, change SMTP_PORT from 587 to 465")
                print(f"   - This uses SSL instead of STARTTLS and may work better on Render")
            return False
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Email authentication failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Environment: {'PRODUCTION (Render)' if os.getenv('DATABASE_URL') else 'LOCAL'}")
        print(f"   SMTP_USERNAME: {smtp_username}")
        print(f"   SMTP_SERVER: {smtp_server}:{smtp_port}")
        print(f"   Please check SMTP_USERNAME and SMTP_PASSWORD in Render Environment Variables")
        print(f"   For Gmail: Make sure you're using an App Password, not your regular password")
        print(f"   Generate App Password at: https://myaccount.google.com/apppasswords")
        import traceback
        traceback.print_exc()
        return False
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"Recipient email rejected: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except smtplib.SMTPServerDisconnected as e:
        error_msg = f"Server disconnected: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Check SMTP server and port settings")
        import traceback
        traceback.print_exc()
        return False
    except socket.timeout:
        error_msg = "SMTP connection timeout"
        print(f"❌ {error_msg}")
        print(f"   Email server took too long to respond (>10 seconds)")
        return False
    except socket.error as e:
        error_msg = f"Socket error: {str(e)}"
        print(f"❌ {error_msg}")
        error_code = str(e)
        if "Network is unreachable" in error_code or "101" in error_code:
            print(f"   ⚠️  Network unreachable - Render may be blocking SMTP connections")
            print(f"   💡 SOLUTION: Try using port 465 with SSL instead of 587 with TLS")
            print(f"   - In Render Environment Variables, change SMTP_PORT from 587 to 465")
            print(f"   - This uses SSL instead of STARTTLS and may work better on Render")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def analyze_food_with_gemini(image_path, user_data):
    """
    Analyze food image using Google's Gemini API
    """
    try:
        # Google Gemini API settings
        API_KEY = "AIzaSyAOr1fscByIEIHVs6Gav-90_wV9hVE8IE4"  # Your Gemini API key
        API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        # Read the image file and convert to base64
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Extract user data for context
        age = user_data['age']
        weight = user_data['weight']
        height = user_data['height']
        gender = user_data['gender']
        bmi = calculate_bmi(weight, height)
        
        # Create prompt for the API with user context
        prompt = f"""
        Analyze this food image in detail:
        1. Identify what food item(s) are in the image
        2. Provide detailed nutritional information (calories, protein, carbs, fat, vitamins, etc.)
        3. Assess if this food is suitable for a person with these health metrics:
           - Age: {age} years
           - Gender: {gender}
           - Height: {height} cm
           - Weight: {weight} kg
           - BMI: {bmi}
        4. Suggest a personalized diet plan related to this food
        5. Provide a specific recommendation for improving nutrition
        
        Format your response in JSON with these keys:
        {{"food_name": "Name of food", 
         "nutrition": "Detailed HTML formatted nutritional breakdown with <ul> and <li> tags", 
         "good_for_user": "Assessment of suitability for this user", 
         "diet_plan": "Personalized diet plan", 
         "recommendation": "Specific recommendation"}}
        """
        
        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generation_config": {
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 40
            }
        }
        
        # Make the API request
        response = requests.post(
            f"{API_URL}?key={API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        # Check if request was successful
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract the text response
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                text_response = response_data['candidates'][0]['content']['parts'][0]['text']
                
                # Try to parse JSON from the response
                try:
                    # Find JSON in the response (in case there's additional text)
                    import re
                    json_match = re.search(r'({.*})', text_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        result = json.loads(json_str)
                        
                        # Ensure all required keys are present
                        required_keys = ['food_name', 'nutrition', 'good_for_user', 'diet_plan', 'recommendation']
                        for key in required_keys:
                            if key not in result:
                                result[key] = "Information not available"
                        
                        return result
                except json.JSONDecodeError:
                    # If JSON parsing fails, extract information using regex
                    patterns = {
                        'food_name': r'food_name"?\s*:\s*"([^"]+)"',
                        'nutrition': r'nutrition"?\s*:\s*"(.*?)"(?=,\s*"good_for_user"|,\s*"diet_plan"|,\s*"recommendation"|}})',
                        'good_for_user': r'good_for_user"?\s*:\s*"([^"]+)"',
                        'diet_plan': r'diet_plan"?\s*:\s*"([^"]+)"',
                        'recommendation': r'recommendation"?\s*:\s*"([^"]+)"'
                    }
                    
                    result = {}
                    for key, pattern in patterns.items():
                        match = re.search(pattern, text_response, re.DOTALL)
                        result[key] = match.group(1) if match else "Information not available"
                    
                    # Format nutrition as HTML if it's not already
                    if "<ul>" not in result['nutrition']:
                        nutrition_text = result['nutrition']
                        nutrition_html = "<ul>"
                        for line in nutrition_text.split('\n'):
                            if line.strip():
                                nutrition_html += f"<li>{line.strip()}</li>"
                        nutrition_html += "</ul>"
                        result['nutrition'] = nutrition_html
                    
                    return result
        
        # Fall back to a default response if API call fails or parsing fails
        return {
            'food_name': "Could not analyze food properly",
            'nutrition': "<ul><li>Nutritional information unavailable</li></ul>",
            'good_for_user': "Unable to assess with the current image",
            'diet_plan': "Please consult a nutritionist for personalized advice",
            'recommendation': "Try uploading a clearer image of your food"
        }
    
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return {
            'food_name': "Could not identify food",
            'nutrition': "<ul><li>Nutritional information unavailable</li></ul>",
            'good_for_user': "Unable to assess",
            'diet_plan': "Please consult a nutritionist for personalized advice",
            'recommendation': "Try uploading a clearer image of your food"
        }

# Global error handler for 500 errors (catches unhandled exceptions)
@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Errors"""
    try:
        db.session.rollback()
    except:
        pass
    
    error_msg = str(error) if error else "Unknown error"
    print(f"❌ 500 Internal Server Error: {error_msg}")
    import traceback
    print("Full traceback:")
    traceback.print_exc()
    
    # Try to flash a message and redirect
    try:
        flash('An internal server error occurred. Please try again later.')
        return redirect(url_for('login')), 500
    except:
        # If redirect fails, return a simple error page
        return '<h1>500 Internal Server Error</h1><p>An error occurred. Please try again later.</p>', 500

# Flask routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            number = request.form.get('number', '').strip()
            name = request.form.get('name', '').strip()
            gender = request.form.get('gender', '').strip()
            password = request.form.get('password', '').strip()
            captcha_input = request.form.get('captcha', '').strip().upper()
            captcha_code = session.get('register_captcha_code', '').upper()
            
            # Validate required fields
            if not all([email, number, name, gender, password]):
                flash('Please fill in all required fields.')
                code, img_base64 = generate_captcha()
                session['register_captcha_code'] = code.upper()
                return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')
            
            # Verify CAPTCHA
            if not captcha_code or captcha_input != captcha_code:
                flash('Invalid CAPTCHA code. Please try again.')
                # Generate new CAPTCHA
                code, img_base64 = generate_captcha()
                session['register_captcha_code'] = code.upper()
                return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')

            # Prevent registration with admin username
            if email.upper() == ADMIN_USERNAME:
                flash('This username is reserved. Please use a different email address.')
                code, img_base64 = generate_captcha()
                session['register_captcha_code'] = code.upper()
                return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')
            
            # Check if database tables exist
            try:
                # Test database connection
                db.session.execute(text('SELECT 1'))
            except Exception as db_test_error:
                print(f"❌ Database connection test failed: {db_test_error}")
                raise Exception(f"Database connection failed: {str(db_test_error)}")
            
            # Check if email is already registered (check both existing users and pending registrations)
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered.')
                # Generate new CAPTCHA for retry
                code, img_base64 = generate_captcha()
                session['register_captcha_code'] = code.upper()
                return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')
            
            # Check if there's already a pending registration for this email
            pending_verification = EmailVerification.query.filter_by(email=email, used=False).first()
            if pending_verification:
                # Check if OTP is still valid
                if datetime.utcnow() <= pending_verification.expires_at:
                    flash('An OTP has already been sent to this email. Please check your email or wait for it to expire.')
                    session['verification_email'] = email
                    return redirect(url_for('verify_otp'))
                else:
                    # Expired OTP, delete it
                    db.session.delete(pending_verification)
                    db.session.commit()
            
            # Store registration data in session (don't create user yet)
            # Account will only be created after OTP verification
            session['pending_registration'] = {
                'email': email,
                'number': number,
                'name': name,
                'gender': gender,
                'password': password  # Store plain password temporarily, will hash when creating account
            }
            
            # Generate OTP code
            otp_code = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
            
            # Delete old verification OTPs for this email
            EmailVerification.query.filter_by(email=email).delete()
            
            # Create new verification OTP (store in database for verification)
            verification = EmailVerification(
                email=email,
                otp=otp_code,
                expires_at=expires_at
            )
            db.session.add(verification)
            
            # Commit only the OTP verification record (not the user account)
            try:
                db.session.commit()
                print(f"✓ OTP generated for {email} (account not created yet)")
            except Exception as db_error:
                db.session.rollback()
                error_type = type(db_error).__name__
                print(f"❌ Database commit error [{error_type}]: {str(db_error)}")
                raise  # Re-raise to be caught by outer exception handler
            
            # Clear CAPTCHA from session
            session.pop('register_captcha_code', None)
            
            # Store email in session for OTP verification page
            session['verification_email'] = email
            
            # Send verification email with OTP (non-blocking - don't wait if it times out)
            # This prevents worker timeout if email server is slow
            try:
                email_sent = send_verification_email(email, otp_code)
                if email_sent:
                    flash('Please check your email for the OTP code to complete registration. If you don\'t see it, check your spam folder.')
                else:
                    flash('OTP code sent! However, email sending failed. Please check your email configuration or contact support.')
                    # Log OTP to console for debugging (not shown to user)
                    print(f"⚠️  OTP for {email} (email failed): {otp_code}")
            except Exception as email_error:
                # If email sending causes any error, don't fail registration
                print(f"⚠️  Email sending error (non-fatal): {email_error}")
                flash('OTP code generated! However, email sending encountered an error. Please check your email configuration or contact support.')
                print(f"⚠️  OTP for {email} (email error): {otp_code}")
            
            return redirect(url_for('verify_otp'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Registration failed: {str(e)}"
            error_type = type(e).__name__
            print(f"❌ Registration error [{error_type}]: {error_msg}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            
            # Log additional context
            print(f"   Email: {email if 'email' in locals() else 'N/A'}")
            print(f"   Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:50]}...")
            
            flash(f'Registration error: {error_type}. Please try again or contact support.')
            # Generate new CAPTCHA for retry
            try:
                code, img_base64 = generate_captcha()
                session['register_captcha_code'] = code.upper()
                return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')
            except Exception as captcha_error:
                print(f"❌ Error generating CAPTCHA: {captcha_error}")
                flash('Error loading registration page. Please refresh.')
                return redirect(url_for('register'))
    
    # GET request - generate CAPTCHA
    try:
        code, img_base64 = generate_captcha()
        session['register_captcha_code'] = code.upper()
        return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')
    except Exception as e:
        print(f"❌ Error in GET register: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading registration page. Please try again.')
        # Try to generate a simple fallback CAPTCHA
        try:
            code, img_base64 = generate_captcha()
            session['register_captcha_code'] = code.upper()
            return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')
        except:
            # Last resort: redirect to login if CAPTCHA generation completely fails
            flash('Unable to load registration page. Please contact support.')
            return redirect(url_for('login'))

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify user email with OTP code and create account only after verification"""
    # Get email from session or form
    email = session.get('verification_email') or request.form.get('email', '').strip()
    
    if not email:
        flash('Please register first or enter your email address.')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        
        if not otp_input or len(otp_input) != 6:
            flash('Please enter a valid 6-digit OTP code.')
            return render_template('verify_otp.html', email=email)
        
        # Find verification record
        verification = EmailVerification.query.filter_by(
            email=email, 
            otp=otp_input, 
            used=False
        ).first()
        
        if not verification:
            flash('Invalid OTP code. Please try again.')
            return render_template('verify_otp.html', email=email)
        
        # Check if OTP has expired
        if datetime.utcnow() > verification.expires_at:
            flash('OTP code has expired. Please request a new one.')
            db.session.delete(verification)
            db.session.commit()
            # Clear pending registration if OTP expired
            session.pop('pending_registration', None)
            return render_template('verify_otp.html', email=email)
        
        # Get pending registration data from session
        pending_reg = session.get('pending_registration')
        
        if not pending_reg or pending_reg.get('email') != email:
            flash('Registration session expired. Please register again.')
            session.pop('pending_registration', None)
            session.pop('verification_email', None)
            return redirect(url_for('register'))
        
        # OTP is valid - NOW create the user account
        try:
            hashed_password = generate_password_hash(pending_reg['password'])
            new_user = User(
                email=pending_reg['email'],
                number=pending_reg['number'],
                name=pending_reg['name'],
                gender=pending_reg['gender'],
                password=hashed_password,
                verified=True  # Mark as verified since OTP is confirmed
            )
            db.session.add(new_user)
            
            # Mark OTP as used
            verification.used = True
            
            # Commit user creation and OTP update
            db.session.commit()
            print(f"✓ User {email} created successfully after OTP verification")
            
            # Clear session data
            session.pop('pending_registration', None)
            session.pop('verification_email', None)
            
            flash('Email verified successfully! Your account has been created. You can now login.')
            return redirect(url_for('login'))
            
        except Exception as create_error:
            db.session.rollback()
            error_type = type(create_error).__name__
            print(f"❌ Error creating user after OTP verification [{error_type}]: {str(create_error)}")
            import traceback
            traceback.print_exc()
            flash('Error creating account. Please try registering again.')
            session.pop('pending_registration', None)
            return redirect(url_for('register'))
    
    # GET request - show OTP verification page
    return render_template('verify_otp.html', email=email)

@app.route('/resend_otp', methods=['GET', 'POST'])
def resend_otp():
    """Resend verification OTP for pending registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        # Check if user already exists and is verified
        user = User.query.filter_by(email=email).first()
        if user:
            if user.verified:
                flash('This email is already verified. You can login.')
                return redirect(url_for('login'))
            else:
                # This shouldn't happen with new flow, but handle it
                flash('Account exists but not verified. Please contact support.')
                return redirect(url_for('login'))
        
        # Check if there's a pending registration for this email
        pending_reg = session.get('pending_registration')
        if not pending_reg or pending_reg.get('email') != email:
            # Check if there's a valid OTP in database
            existing_verification = EmailVerification.query.filter_by(email=email, used=False).first()
            if not existing_verification or datetime.utcnow() > existing_verification.expires_at:
                flash('No pending registration found. Please register again.')
                return redirect(url_for('register'))
        
        # Generate new OTP code
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
        
        # Delete old verification OTPs for this email
        EmailVerification.query.filter_by(email=email).delete()
        
        # Create new verification OTP
        verification = EmailVerification(
            email=email,
            otp=otp_code,
            expires_at=expires_at
        )
        db.session.add(verification)
        db.session.commit()
        
        # Send verification email with OTP
        try:
            email_sent = send_verification_email(email, otp_code)
            
            # Store email in session for OTP verification page
            session['verification_email'] = email
            
            if email_sent:
                flash('Verification OTP sent! Please check your email. If you don\'t see it, check your spam folder.')
            else:
                flash('OTP sending failed. Please check your email configuration or contact support.')
                # Log OTP to console for debugging (not shown to user)
                print(f"⚠️  OTP for {email} (email failed): {otp_code}")
        except Exception as email_error:
            print(f"⚠️  Email sending error (non-fatal): {email_error}")
            flash('OTP generated but email sending encountered an error. Please check your email configuration.')
            print(f"⚠️  OTP for {email} (email error): {otp_code}")
        
        return redirect(url_for('verify_otp'))
    
    return render_template('resend_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password_input = request.form.get('password', '').strip()
        
        # Debug logging
        print(f"🔍 Login attempt - Email: '{email}', Password length: {len(password_input)}")
        print(f"   Admin username check: '{email.upper()}' == '{ADMIN_USERNAME}' = {email.upper() == ADMIN_USERNAME}")
        
        # Exception: If email matches admin username, only check admin credentials (skip database query)
        if email.upper() == ADMIN_USERNAME:
            # Admin login attempt - check admin password
            print(f"   Admin login detected - Checking password...")
            if password_input == ADMIN_PASSWORD:
                session['admin'] = True
                session['admin_username'] = ADMIN_USERNAME
                print(f"✓ Admin login successful!")
                flash('Admin login successful!')
                return redirect(url_for('admin_dashboard'))
            else:
                print(f"❌ Admin password incorrect. Expected: '{ADMIN_PASSWORD}', Got: '{password_input}'")
                flash('Invalid admin password.')
                return render_template('login.html')
        
        # Regular user login (only if email is not admin username)
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password_input):
            # Check if email is verified
            if not user.verified:
                session['verification_email'] = email
                flash('Please verify your email before logging in. Check your inbox for OTP or <a href="' + url_for('resend_otp') + '">resend OTP</a>.')
                return redirect(url_for('verify_otp'))
            
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_gender'] = user.gender
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard to view and manage all users"""
    # Check if user is admin
    if not session.get('admin'):
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('login'))
    
    # Get all users
    users = User.query.order_by(User.id.desc()).all()
    
    # Get user statistics
    total_users = len(users)
    verified_users = len([u for u in users if u.verified])
    unverified_users = total_users - verified_users
    
    # Get pending OTPs (for troubleshooting email issues)
    pending_otps = EmailVerification.query.filter_by(used=False).order_by(EmailVerification.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         total_users=total_users,
                         verified_users=verified_users,
                         unverified_users=unverified_users,
                         pending_otps=pending_otps,
                         now=datetime.utcnow)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user account (admin only) - Admin account is protected and cannot be deleted"""
    # Check if user is admin
    if not session.get('admin'):
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('login'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        # STRICT PROTECTION: Prevent deletion of admin account
        # Multiple checks to ensure admin account cannot be deleted
        if (user.email.upper() == ADMIN_USERNAME or 
            user.email.upper() == ADMIN_USERNAME.upper() or
            user.name.upper() == ADMIN_USERNAME or
            str(user_id) == "0"):  # Additional safety check
            flash('❌ ERROR: Admin account is protected and cannot be deleted!')
            print(f"⚠️  Attempted deletion of protected admin account: {user.email}")
            return redirect(url_for('admin_dashboard'))
        
        # Additional check: Prevent deletion if email contains admin username
        if ADMIN_USERNAME.upper() in user.email.upper():
            flash('❌ ERROR: This account is protected and cannot be deleted!')
            print(f"⚠️  Attempted deletion of protected account: {user.email}")
            return redirect(url_for('admin_dashboard'))
        
        # Delete associated health data
        deleted_health = HealthData.query.filter_by(user_id=user_id).delete()
        
        # Delete associated email verifications
        deleted_verifications = EmailVerification.query.filter_by(email=user.email).delete()
        
        # Delete password reset tokens
        deleted_resets = PasswordReset.query.filter_by(email=user.email).delete()
        
        # Store email for logging before deletion
        user_email = user.email
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'✓ User {user_email} has been deleted successfully.')
        print(f"✓ Admin deleted user: {user_email} (Health data: {deleted_health}, Verifications: {deleted_verifications}, Resets: {deleted_resets})")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting user: {e}")
        import traceback
        traceback.print_exc()
        flash('Error deleting user. Please try again.')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/test_email')
def admin_test_email():
    """Test email configuration (admin only)"""
    # Check if user is admin
    if not session.get('admin'):
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('login'))
    
    # Get configuration
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.getenv('SMTP_PORT', '587')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    results = {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'smtp_username': smtp_username if smtp_username else '❌ NOT SET',
        'smtp_password': '✅ SET' if smtp_password else '❌ NOT SET',
        'tests': []
    }
    
    # Test 1: Check if credentials are set
    if not smtp_username or not smtp_password:
        results['tests'].append({
            'name': 'Credentials Check',
            'status': '❌ FAIL',
            'message': 'SMTP_USERNAME or SMTP_PASSWORD not set in environment variables'
        })
        return render_template('admin_test_email.html', results=results)
    else:
        results['tests'].append({
            'name': 'Credentials Check',
            'status': '✅ PASS',
            'message': 'Both SMTP_USERNAME and SMTP_PASSWORD are set'
        })
    
    # Test 2: Test SMTP connection (support both TLS and SSL)
    server = None
    try:
        socket.setdefaulttimeout(10)
        if int(smtp_port) == 465:
            # Use SSL for port 465
            server = smtplib.SMTP_SSL(smtp_server, int(smtp_port), timeout=10)
            results['tests'].append({
                'name': 'SMTP Connection (SSL)',
                'status': '✅ PASS',
                'message': f'Successfully connected to {smtp_server}:{smtp_port} using SSL'
            })
        else:
            # Use TLS for port 587 or other ports
            server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
            results['tests'].append({
                'name': 'SMTP Connection',
                'status': '✅ PASS',
                'message': f'Successfully connected to {smtp_server}:{smtp_port}'
            })
    except socket.error as e:
        error_msg = str(e)
        if "Network is unreachable" in error_msg or "101" in error_msg:
            results['tests'].append({
                'name': 'SMTP Connection',
                'status': '❌ FAIL',
                'message': f'Network unreachable: {str(e)}. Try changing SMTP_PORT to 465 (SSL) instead of 587 (TLS)'
            })
        else:
            results['tests'].append({
                'name': 'SMTP Connection',
                'status': '❌ FAIL',
                'message': f'Connection failed: {str(e)}'
            })
        return render_template('admin_test_email.html', results=results)
    except Exception as e:
        results['tests'].append({
            'name': 'SMTP Connection',
            'status': '❌ FAIL',
            'message': f'Connection failed: {str(e)}'
        })
        return render_template('admin_test_email.html', results=results)
    
    # Test 3: Test TLS (only for non-SSL connections)
    if int(smtp_port) != 465:
        try:
            server.starttls()
            results['tests'].append({
                'name': 'TLS Encryption',
                'status': '✅ PASS',
                'message': 'TLS encryption enabled successfully'
            })
        except Exception as e:
            results['tests'].append({
                'name': 'TLS Encryption',
                'status': '❌ FAIL',
                'message': f'TLS failed: {str(e)}'
            })
            server.quit()
            return render_template('admin_test_email.html', results=results)
    else:
        results['tests'].append({
            'name': 'SSL Encryption',
            'status': '✅ PASS',
            'message': 'SSL encryption enabled (port 465)'
        })
    
    # Test 4: Test authentication
    try:
        server.login(smtp_username, smtp_password)
        results['tests'].append({
            'name': 'Authentication',
            'status': '✅ PASS',
            'message': 'Authentication successful'
        })
    except smtplib.SMTPAuthenticationError as e:
        results['tests'].append({
            'name': 'Authentication',
            'status': '❌ FAIL',
            'message': f'Authentication failed: {str(e)}. Make sure you\'re using an App Password (Gmail) or correct password.'
        })
        server.quit()
        return render_template('admin_test_email.html', results=results)
    except Exception as e:
        results['tests'].append({
            'name': 'Authentication',
            'status': '❌ FAIL',
            'message': f'Authentication error: {str(e)}'
        })
        server.quit()
        return render_template('admin_test_email.html', results=results)
    
    server.quit()
    results['tests'].append({
        'name': 'All Tests',
        'status': '✅ PASS',
        'message': 'Email configuration is working correctly!'
    })
    
    return render_template('admin_test_email.html', results=results)

@app.route('/admin/logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully.')
    return redirect(url_for('login'))

@app.route('/captcha')
def captcha():
    """Generate and return CAPTCHA image for forgot password"""
    code, img_base64 = generate_captcha()
    session['captcha_code'] = code.upper()  # Store in session (case-insensitive comparison)
    return f'data:image/png;base64,{img_base64}'

@app.route('/captcha/register')
def captcha_register():
    """Generate and return CAPTCHA image for registration"""
    code, img_base64 = generate_captcha()
    session['register_captcha_code'] = code.upper()  # Store in session (case-insensitive comparison)
    return f'data:image/png;base64,{img_base64}'

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page with CAPTCHA verification"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        captcha_input = request.form.get('captcha', '').strip().upper()
        captcha_code = session.get('captcha_code', '').upper()
        
        # Verify CAPTCHA
        if not captcha_code or captcha_input != captcha_code:
            flash('Invalid CAPTCHA code. Please try again.')
            # Generate new CAPTCHA
            code, img_base64 = generate_captcha()
            session['captcha_code'] = code.upper()
            return render_template('forgot_password.html', captcha_image=f'data:image/png;base64,{img_base64}')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('If an account with that email exists, a password reset link has been sent.')
            # Don't reveal if email exists or not (security best practice)
            code, img_base64 = generate_captcha()
            session['captcha_code'] = code.upper()
            return render_template('forgot_password.html', captcha_image=f'data:image/png;base64,{img_base64}')
        
        # Generate reset token
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        
        # Delete old reset tokens for this email
        PasswordReset.query.filter_by(email=email).delete()
        
        # Create new reset token
        reset_token = PasswordReset(
            email=email,
            token=token,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        
        # Clear CAPTCHA from session
        session.pop('captcha_code', None)
        
        flash(f'Password reset link has been generated. Please use this link to reset your password: {url_for("reset_password", token=token, _external=True)}')
        return redirect(url_for('login'))
    
    # GET request - generate CAPTCHA
    code, img_base64 = generate_captcha()
    session['captcha_code'] = code.upper()
    return render_template('forgot_password.html', captcha_image=f'data:image/png;base64,{img_base64}')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page"""
    # Find valid reset token
    reset_record = PasswordReset.query.filter_by(token=token, used=False).first()
    
    if not reset_record:
        flash('Invalid or expired reset token.')
        return redirect(url_for('login'))
    
    # Check if token has expired
    if datetime.utcnow() > reset_record.expires_at:
        flash('Reset token has expired. Please request a new one.')
        db.session.delete(reset_record)
        db.session.commit()
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate passwords
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long.')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.')
            return render_template('reset_password.html', token=token)
        
        # Update user password
        user = User.query.filter_by(email=reset_record.email).first()
        if user:
            user.password = generate_password_hash(new_password)
            reset_record.used = True
            db.session.commit()
            flash('Password reset successful! You can now login with your new password.')
            return redirect(url_for('login'))
        else:
            flash('User not found.')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Extract form data
        age = int(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        
        # Handle file upload
        file = request.files['food_image']
        filename = None
        if file and allowed_file(file.filename):
            # Create unique filename to avoid conflicts
            unique_filename = str(uuid.uuid4()) + secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Analyze food image using Gemini API
            user_data = {
                'age': age,
                'height': height,
                'weight': weight,
                'gender': session['user_gender']
            }
            
            analysis_result = analyze_food_with_gemini(filepath, user_data)
            
            # Save the data to the database
            health_data = HealthData(
                user_id=session['user_id'],
                age=age,
                height=height,
                weight=weight,
                food_image=unique_filename,
                food_name=analysis_result['food_name'],
                nutrition_info=analysis_result['nutrition'],
                assessment=analysis_result['good_for_user'],
                diet_plan=analysis_result['diet_plan'],
                recommendation=analysis_result['recommendation']
            )
            db.session.add(health_data)
            db.session.commit()
            
            # Calculate BMI
            bmi = calculate_bmi(weight, height)
            
            # Prepare the food image path for display
            food_image_path = url_for('uploaded_file', filename=unique_filename)
            
            return render_template('result.html', 
                                  name=session['user_name'], 
                                  gender=session['user_gender'],
                                  age=age, 
                                  height=height, 
                                  weight=weight,
                                  bmi=bmi,
                                  food_name=analysis_result['food_name'],
                                  nutrition=analysis_result['nutrition'],
                                  good_for_user=analysis_result['good_for_user'],
                                  diet_plan=analysis_result['diet_plan'],
                                  recommendation=analysis_result['recommendation'],
                                  food_image_path=food_image_path)
        else:
            flash("Please upload a valid image file (png, jpg, jpeg).")

    return render_template('dashboard.html', name=session['user_name'], gender=session['user_gender'])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout') 
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

# Function to create DB tables and migrate schema
def create_tables():
    """Create all database tables if they don't exist"""
    try:
        # Create all tables (this is idempotent - won't recreate if they exist)
        db.create_all()
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = ['user', 'health_data', 'password_reset', 'email_verification']
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")
            print("Attempting to create missing tables...")
            db.create_all()
            # Verify again
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            if all(t in existing_tables for t in required_tables):
                print("✓ All required tables created successfully.")
            else:
                print("⚠️  Some tables still missing. You may need to restart the app.")
        else:
            print("✓ All database tables verified.")
        
        # Now migrate if needed (add new columns to existing tables)
        migrate_database()
        
    except Exception as e:
        print(f"⚠️  Error creating tables: {e}")
        # If tables don't exist, try to create them
        if "no such table" in str(e).lower():
            try:
                print("Attempting to create tables...")
                db.create_all()
                print("✓ Tables created.")
            except Exception as e2:
                print(f"❌ Error creating tables: {e2}")
                print("Please stop the Flask app, delete instance/users.db, and restart.")

def migrate_database():
    """
    Migrate existing database to add new columns and tables.
    This handles the case where the database already exists but is missing new fields.
    """
    try:
        # Check if user table exists first
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'user' not in tables:
            print("User table doesn't exist. It should have been created by db.create_all()")
            return
        
        # Check if 'verified' column exists in user table
        try:
            columns = [col['name'] for col in inspector.get_columns('user')]
            if 'verified' not in columns:
                print("Adding 'verified' column to user table...")
                # For SQLite, we need to use ALTER TABLE
                if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                    with db.engine.begin() as conn:
                        conn.execute(text('ALTER TABLE user ADD COLUMN verified BOOLEAN DEFAULT 0'))
                        # Mark all existing users as verified
                        conn.execute(text('UPDATE user SET verified = 1 WHERE verified IS NULL'))
                    print("✓ 'verified' column added to user table.")
                else:
                    # For PostgreSQL, use ALTER TABLE
                    with db.engine.begin() as conn:
                        conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE'))
                        conn.execute(text('UPDATE "user" SET verified = TRUE WHERE verified IS NULL'))
                    print("✓ 'verified' column added to user table.")
        except Exception as e:
            print(f"Note: Could not check/add 'verified' column: {e}")
            print("This is okay if the column already exists.")
        
        # Check if email_verification table needs migration (token -> otp)
        if 'email_verification' in tables:
            try:
                columns = [col['name'] for col in inspector.get_columns('email_verification')]
                if 'token' in columns and 'otp' not in columns:
                    print("Migrating email_verification table: token -> otp...")
                    # For SQLite, we need to recreate the table
                    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                        # SQLite doesn't support DROP COLUMN, so we'll recreate the table
                        with db.engine.begin() as conn:
                            # Create new table with otp column
                            conn.execute(text('''
                                CREATE TABLE email_verification_new (
                                    id INTEGER PRIMARY KEY,
                                    email VARCHAR(150) NOT NULL,
                                    otp VARCHAR(6) NOT NULL,
                                    created_at DATETIME,
                                    expires_at DATETIME NOT NULL,
                                    used BOOLEAN NOT NULL DEFAULT 0
                                )
                            '''))
                            # Copy data (if any) - we'll just drop old tokens
                            conn.execute(text('DROP TABLE email_verification'))
                            conn.execute(text('ALTER TABLE email_verification_new RENAME TO email_verification'))
                        print("✓ email_verification table migrated to use OTP.")
                    else:
                        # For PostgreSQL, we can add the column and migrate data
                        with db.engine.begin() as conn:
                            conn.execute(text('ALTER TABLE email_verification ADD COLUMN IF NOT EXISTS otp VARCHAR(6)'))
                            # Drop old token column (if safe)
                            # Note: We'll keep both columns for safety, old data will be ignored
                        print("✓ email_verification table updated (otp column added).")
            except Exception as e:
                print(f"Note: Could not migrate email_verification table: {e}")
                print("This is okay if the table is already using OTP.")
        
        print("✓ Database schema is up to date.")
            
    except Exception as e:
        # If inspector fails, try a different approach
        if "no such table" in str(e).lower():
            print("Tables don't exist. Creating all tables...")
            db.create_all()
            print("✓ All tables created.")
        else:
            print(f"Database check error: {e}")

# Initialize database tables when app starts (works for both development and production)
# This ensures tables are created on Render when gunicorn starts the app
def init_database():
    """Initialize database tables - called when app starts"""
    with app.app_context():
        try:
            print("="*60)
            print("Initializing database...")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            print("="*60)
            
            # Try to create all tables (idempotent - won't recreate if they exist)
            db.create_all()
            
            # Verify tables exist
            try:
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                required_tables = ['user', 'health_data', 'password_reset', 'email_verification']
                
                missing_tables = [t for t in required_tables if t not in tables]
                if missing_tables:
                    print(f"⚠️  Missing tables: {missing_tables}. Creating...")
                    db.create_all()
                    print("✓ All tables created.")
                else:
                    print(f"✓ Database tables verified: {tables}")
                
                # Run migration if needed
                migrate_database()
                print("="*60)
                
            except Exception as inspect_error:
                print(f"⚠️  Could not inspect tables: {inspect_error}")
                print("Creating all tables...")
                db.create_all()
                print("✓ Tables created.")
            
        except Exception as e:
            print(f"⚠️  Database initialization error: {e}")
            import traceback
            traceback.print_exc()
            # Try to create tables anyway
            try:
                db.create_all()
                print("✓ Tables created after error recovery.")
            except Exception as e2:
                print(f"❌ Critical database error: {e2}")
                print("Please check DATABASE_URL in environment variables.")
                print("="*60)

# Initialize database when module is imported
init_database()

if __name__ == '__main__':
    # Only run with debug=True in development
    # In production, Render will use gunicorn to run the app
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))