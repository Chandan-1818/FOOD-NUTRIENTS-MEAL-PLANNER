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
import string
import io
# Email sending imports removed - email verification module disabled
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

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
        email = request.form.get('email', '').strip()
        number = request.form.get('number', '').strip()
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '').strip()
        password = request.form.get('password', '').strip()
        captcha_input = request.form.get('captcha', '').strip().upper()
        captcha_code = session.get('register_captcha_code', '').upper()
        
        # Verify CAPTCHA
        if not captcha_code or captcha_input != captcha_code:
            flash('Invalid CAPTCHA code. Please try again.')
            # Generate new CAPTCHA
            code, img_base64 = generate_captcha()
            session['register_captcha_code'] = code.upper()
            return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.')
            # Generate new CAPTCHA for retry
            code, img_base64 = generate_captcha()
            session['register_captcha_code'] = code.upper()
            return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')

        # Create user directly (no email verification required)
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email, 
            number=number, 
            name=name, 
            gender=gender, 
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Clear CAPTCHA from session after successful registration
        session.pop('register_captcha_code', None)
        
        flash('Registration successful! You can now login.')
        return redirect(url_for('login'))
    
    # GET request - generate CAPTCHA
    code, img_base64 = generate_captcha()
    session['register_captcha_code'] = code.upper()
    return render_template('register.html', captcha_image=f'data:image/png;base64,{img_base64}')

# Email verification routes removed - OTP verification module disabled

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password_input):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_gender'] = user.gender
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
    return render_template('login.html')

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
        
        required_tables = ['user', 'health_data', 'password_reset']
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
        
        # Email verification removed - no migration needed for 'verified' column
        print("✓ Database schema is up to date.")
            
        # OTP table removed - email verification module disabled
            
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
                required_tables = ['user', 'health_data', 'password_reset']
                
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