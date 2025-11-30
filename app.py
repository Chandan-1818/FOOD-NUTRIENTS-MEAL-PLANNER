from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import base64
import requests
import json
import re
import math
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)

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

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_bmi(weight, height):
    # Height in meters (convert from cm)
    height_m = height / 100
    bmi = weight / (height_m * height_m)
    return round(bmi, 2)

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def get_smtp_config_for_email(email_address):
    """
    Dynamically determine SMTP configuration based on email provider.
    Returns SMTP server and port for the email domain.
    """
    email_domain = email_address.split('@')[1].lower() if '@' in email_address else ''
    
    # Common email provider SMTP settings
    smtp_configs = {
        'gmail.com': {'server': 'smtp.gmail.com', 'port': 587},
        'outlook.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        'hotmail.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        'live.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
        'yahoo.com': {'server': 'smtp.mail.yahoo.com', 'port': 587},
        'yahoo.co.uk': {'server': 'smtp.mail.yahoo.co.uk', 'port': 587},
        'aol.com': {'server': 'smtp.aol.com', 'port': 587},
        'icloud.com': {'server': 'smtp.mail.me.com', 'port': 587},
        'mail.com': {'server': 'smtp.mail.com', 'port': 587},
    }
    
    # Return config for known provider, or use default Gmail settings
    return smtp_configs.get(email_domain, {'server': 'smtp.gmail.com', 'port': 587})

def validate_email(email_address):
    """Validate email address format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email_address) is not None

def send_otp_email(email, otp_code, user_name=None):
    """
    Send OTP to user's email address dynamically.
    Works with any email address - Gmail, Outlook, Yahoo, etc.
    
    IMPORTANT: This function ONLY sends email via SMTP.
    It NEVER returns email content - only returns True/False for success/failure.
    
    Args:
        email: Recipient email address (dynamic - any email)
        otp_code: 6-digit OTP code
        user_name: Optional user name for personalization
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # CRITICAL: Never return email content - only return boolean
    email_body_html = None  # Keep email content local, never return it
    
    try:
        # Validate email format
        if not validate_email(email):
            print(f"❌ Invalid email format: {email}")
            return False
        
        # Get SMTP configuration (can be customized per email provider)
        # For now, we use a single SMTP account to send to all recipients
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
        SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
        
        # Auto-detect SMTP settings based on recipient email (optional feature)
        # Uncomment below to use provider-specific settings
        # provider_config = get_smtp_config_for_email(email)
        # SMTP_SERVER = provider_config['server']
        # SMTP_PORT = provider_config['port']
        
        # Check if email is configured
        if not SMTP_USERNAME or SMTP_USERNAME == 'your_email@gmail.com' or not SMTP_PASSWORD or SMTP_PASSWORD == 'your_app_password':
            print("\n" + "="*60)
            print("⚠️  EMAIL NOT CONFIGURED - OTP will be shown on screen")
            print("="*60)
            print(f"Recipient: {email}")
            print(f"OTP Code: {otp_code}")
            print("\nTo enable email sending, create a .env file with:")
            print("  SMTP_SERVER=smtp.gmail.com")
            print("  SMTP_PORT=587")
            print("  SMTP_USERNAME=your_email@gmail.com")
            print("  SMTP_PASSWORD=your_app_password")
            print("\nFor Gmail: Use App Password (not regular password)")
            print("  Go to: Google Account > Security > 2-Step Verification > App passwords")
            print("="*60 + "\n")
            # CRITICAL: Return False, never return email content
            return False
        
        # Create message object
        msg = MIMEMultipart()
        msg['From'] = f"Health Food Monitor <{SMTP_USERNAME}>"
        msg['To'] = email
        msg['Subject'] = 'Email Verification OTP - Health Food Monitor'
        
        # Personalize greeting
        greeting = f"Hello {user_name}!" if user_name else "Hello!"
        
        # Build email body HTML (stored in local variable, never returned)
        email_body_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #ffffff;">
                    <h2 style="color: #4e73df; margin-top: 0;">Email Verification</h2>
                    <p>{greeting}</p>
                    <p>Thank you for registering with Health Food Monitor!</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0; border: 2px solid #4e73df;">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #666; font-weight: 600;">Your verification code is:</p>
                        <p style="font-size: 36px; font-weight: bold; color: #4e73df; margin: 10px 0; letter-spacing: 8px; font-family: 'Courier New', monospace;">{otp_code}</p>
                    </div>
                    <p style="color: #666; font-size: 14px; margin-bottom: 5px;">⏰ This code will expire in <strong>10 minutes</strong>.</p>
                    <p style="color: #666; font-size: 14px; margin-top: 5px;">If you didn't request this code, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; margin: 0;">This is an automated message from Health Food Monitor.</p>
                </div>
            </body>
        </html>
        """
        
        # Attach HTML body to message (NOT returned to browser)
        msg.attach(MIMEText(email_body_html, 'html'))
        
        # CRITICAL: Clear email_body_html reference after attaching (defensive programming)
        # This ensures it can't accidentally be returned
        email_body_html = None
        
        # Send email
        print(f"\n{'='*60}")
        print(f"📧 Sending OTP Email (Dynamic)")
        print(f"   Recipient: {email}")
        print(f"   Sender: {SMTP_USERNAME}")
        print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
        if user_name:
            print(f"   User: {user_name}")
        print(f"{'='*60}")
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        print("✓ TLS connection established")
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✓ Authentication successful")
        
        server.send_message(msg)
        print("✓ Message sent to server")
        
        server.quit()
        print(f"✓ OTP email sent successfully to {email}")
        print(f"{'='*60}\n")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n{'='*60}")
        print(f"❌ SMTP Authentication Error")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check SMTP_USERNAME in .env file: {SMTP_USERNAME[:3]}***")
        print(f"2. For Gmail: Use App Password (not regular password)")
        print(f"   - Go to: https://myaccount.google.com/apppasswords")
        print(f"   - Generate app password for 'Mail'")
        print(f"3. Make sure 2-Step Verification is enabled on your Google account")
        print(f"4. Remove spaces from app password")
        print(f"\nOTP for {email}: {otp_code}")
        print(f"{'='*60}\n")
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"\n{'='*60}")
        print(f"❌ SMTP Connection Error")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check your internet connection")
        print(f"2. Verify SMTP_SERVER is correct: {SMTP_SERVER}")
        print(f"3. Check firewall/antivirus settings")
        print(f"4. Try different SMTP_PORT (587 or 465)")
        print(f"\nOTP for {email}: {otp_code}")
        print(f"{'='*60}\n")
        return False
    except smtplib.SMTPException as e:
        print(f"\n{'='*60}")
        print(f"❌ SMTP Error")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"Error Type: {type(e).__name__}")
        print(f"\nOTP for {email}: {otp_code}")
        print(f"{'='*60}\n")
        return False
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Unexpected Error")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"Error Type: {type(e).__name__}")
        import traceback
        print(f"\nTraceback:")
        traceback.print_exc()
        print(f"\nOTP for {email}: {otp_code}")
        print(f"{'='*60}\n")
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

# Flask routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        number = request.form['number']
        name = request.form['name']
        gender = request.form['gender']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.verified:
                flash('Email already registered.')
                return redirect(url_for('login'))
            else:
                # User exists but not verified, delete old user and OTPs
                OTP.query.filter_by(email=email).delete()
                db.session.delete(existing_user)
                db.session.commit()

        # Generate OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Delete any existing OTPs for this email
        OTP.query.filter_by(email=email).delete()
        
        # Create new OTP record
        new_otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.session.add(new_otp)
        
        # Create user (unverified)
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email, 
            number=number, 
            name=name, 
            gender=gender, 
            password=hashed_password,
            verified=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Send OTP email to user's email address (dynamic - works with any email)
        email_sent = send_otp_email(email, otp_code, user_name=name)
        if email_sent:
            flash('Registration successful! Please check your email for the OTP verification code.')
        else:
            flash('Registration successful! Email not configured - OTP will be shown on verification page.')
            # Store OTP in session to display on verification page if email fails
            session['display_otp'] = otp_code
        
        # Store email in session for verification
        session['pending_email'] = email
        return redirect(url_for('verify_otp'))
    
    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_email' not in session:
        flash('Please register first.')
        return redirect(url_for('register'))
    
    email = session['pending_email']
    
    # Get OTP to display if email wasn't sent
    display_otp = session.get('display_otp', None)
    email_configured = display_otp is None
    
    if request.method == 'POST':
        entered_otp = request.form['otp']
        
        # Find the most recent unverified OTP for this email
        otp_record = OTP.query.filter_by(
            email=email, 
            verified=False
        ).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('OTP not found. Please register again.')
            session.pop('pending_email', None)
            return redirect(url_for('register'))
        
        # Check if OTP has expired
        if datetime.utcnow() > otp_record.expires_at:
            flash('OTP has expired. Please request a new one.')
            display_otp = session.get('display_otp', None)
            email_configured = display_otp is None
            return render_template('verify_otp.html', email=email, display_otp=display_otp, email_configured=email_configured)
        
        # Verify OTP
        if otp_record.otp_code == entered_otp:
            # Mark OTP as verified
            otp_record.verified = True
            
            # Mark user as verified
            user = User.query.filter_by(email=email).first()
            if user:
                user.verified = True
                db.session.commit()
                
                # Clean up session
                session.pop('pending_email', None)
                session.pop('display_otp', None)
                
                flash('Email verified successfully! You can now login.')
                return redirect(url_for('login'))
            else:
                flash('User not found. Please register again.')
                session.pop('pending_email', None)
                return redirect(url_for('register'))
        else:
            flash('Invalid OTP. Please try again.')
    
    return render_template('verify_otp.html', email=email, display_otp=display_otp, email_configured=email_configured)

@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    if 'pending_email' not in session:
        flash('Please register first.')
        return redirect(url_for('register'))
    
    email = session['pending_email']
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found. Please register again.')
        session.pop('pending_email', None)
        return redirect(url_for('register'))
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Delete old OTPs for this email
    OTP.query.filter_by(email=email).delete()
    
    # Create new OTP record
    new_otp = OTP(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()
    
    # Send OTP email to user's email address (dynamic - works with any email)
    user_name = user.name if user else None
    email_sent = send_otp_email(email, otp_code, user_name=user_name)
    if email_sent:
        flash('New OTP has been sent to your email.')
        session.pop('display_otp', None)  # Remove display OTP if email sent
    else:
        flash('New OTP generated. Email not configured - OTP will be shown on verification page.')
        session['display_otp'] = otp_code  # Store OTP to display
    
    return redirect(url_for('verify_otp'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password_input):
            if not user.verified:
                flash('Please verify your email first. Check your email for the OTP.')
                session['pending_email'] = email
                return redirect(url_for('verify_otp'))
            
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_gender'] = user.gender
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
    return render_template('login.html')

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
        
        required_tables = ['user', 'otp', 'health_data']
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
        
        # Check if 'verified' column exists by trying to query it
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'verified' not in columns:
            print("Migrating database: Adding 'verified' column to User table...")
            try:
                with db.engine.connect() as conn:
                    # SQLite doesn't support adding NOT NULL columns with default easily
                    # So we add it as nullable first, then update
                    conn.execute(db.text("ALTER TABLE user ADD COLUMN verified BOOLEAN"))
                    conn.execute(db.text("UPDATE user SET verified = 1 WHERE verified IS NULL"))
                    conn.commit()
                print("✓ Migration completed: 'verified' column added. Existing users marked as verified.")
            except Exception as e2:
                print(f"Migration error: {e2}")
                print("If migration fails, you may need to delete instance/users.db and restart the app.")
        else:
            print("✓ Database schema is up to date.")
            
        # Check if OTP table exists
        if 'otp' not in tables:
            print("OTP table doesn't exist. Creating it...")
            db.create_all()
            print("✓ OTP table created.")
            
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
                required_tables = ['user', 'otp', 'health_data']
                
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