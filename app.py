import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
import pandas as pd
import numpy as np
from sklearn import linear_model
import os
from models import *
from extensions import db
import requests

# Load environment variables
load_dotenv()
folder1 = 'static/files/'

app = Flask(__name__)

# Configuration
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', secrets.token_hex(32)),
    PERMANENT_SESSION_LIFETIME=1800,  # 30 minutes
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

app.config['UPLOAD_FOLDER1'] = folder1
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/flask_auth'

db.init_app(app)

# MySQL configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'flask_auth'),
    'port': os.getenv('DB_PORT', '3306')
}

def get_db_connection():
    """Create and return a new database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        app.logger.error(f"Database connection error: {err}")
        raise

def init_db():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            is_active BOOLEAN DEFAULT TRUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # Create sessions table for better session management
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
        """)
        
        conn.commit()
        app.logger.info("Database initialized successfully")
    except mysql.connector.Error as err:
        app.logger.error(f"Database initialization error: {err}")
        raise
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def login_required(f):
    """Decorator to ensure user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    """Initialize database before first request"""
    init_db()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT id, username, password, is_active FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                if not user['is_active']:
                    flash('Your account is disabled', 'danger')
                else:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    
                    # Update last login
                    cursor.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                        (user['id'],)
                    )
                    
                    # Remember me functionality
                    if remember:
                        session.permanent = True
                    
                    flash('Login successful!', 'success')
                    
                    # Redirect to next URL if provided
                    next_url = request.args.get('next')
                    return redirect(next_url or url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
                
            conn.commit()
        except mysql.connector.Error as err:
            app.logger.error(f"Database error during login: {err}")
            flash('Database error occurred', 'danger')
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if len(username) < 4:
            errors.append('Username must be at least 4 characters')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            hashed_password = generate_password_hash(password)
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password)
                )
                
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.IntegrityError as err:
                if 'username' in str(err):
                    flash('Username already exists', 'danger')
                elif 'email' in str(err):
                    flash('Email already exists', 'danger')
                else:
                    flash('Registration failed', 'danger')
                app.logger.error(f"Integrity error during signup: {err}")
            except mysql.connector.Error as err:
                flash('Registration failed', 'danger')
                app.logger.error(f"Database error during signup: {err}")
            finally:
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
@login_required
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


import requests

@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload_marks():
    sid = session.get('user_id')
    if not sid:
        msg = "User not logged in."
        return render_template('upload.html', msg=msg)

    existing = User_marks.query.filter_by(sid=sid).first()
    grade = request.form.get("grade") or "0"  # Default to "0" if grade is missing
    target_cgpa = request.form.get("marks")  # Target CGPA entered by user
    msg = ""

    if existing:
        # Existing user found, show current CGPA and hours
        capable_cgpa = existing.capable_cgpa
        msg = (
            f"Your capable CGPA is: {capable_cgpa}. "
            f"You should start studying for: {existing.capable_hours} hours daily to reach this CGPA.\n"
            f"Your target CGPA is: {existing.marks}. "
            f"To achieve it, you should study for: {existing.hours} hours daily!"
        )
    else:
        capable_cgpa = None

    if request.method == 'POST':
        if not target_cgpa:
            msg = "Please enter your target CGPA."
        else:
            try:
                target_cgpa = float(target_cgpa)  # Convert CGPA to float

                # Fetch capable CGPA from the database
                if capable_cgpa is None:
                    msg = "Error: Unable to retrieve your capable CGPA from the database."
                    return render_template('upload.html', msg=msg)

                # API call to calculate study hours for the target CGPA (using GET)
                api_url_target = f'http://localhost:5001/predict_cgpa?target_cgpa={target_cgpa}'
                response_target = requests.get(api_url_target)

                # API call to calculate study hours for the capable CGPA (using GET)
                api_url_capable = f'http://localhost:5001/predict_cgpa?target_cgpa={capable_cgpa}'
                response_capable = requests.get(api_url_capable)

                if response_target.status_code == 200 and response_capable.status_code == 200:
                    data_target = response_target.json()
                    data_capable = response_capable.json()

                    # Extract the numeric value from the message (remove extra text and convert to float)
                    required_study_hours_target_str = data_target['message'].split('for ')[1].split(' hours')[0]
                    required_study_hours_target = float(required_study_hours_target_str)  # Convert to float before rounding
                    required_study_hours_target = round(required_study_hours_target, 2)  # Now rounding will work

                    required_study_hours_capable_str = data_capable['message'].split('for ')[1].split(' hours')[0]
                    required_study_hours_capable = float(required_study_hours_capable_str)  # Convert to float before rounding
                    required_study_hours_capable = round(required_study_hours_capable, 2)  # Now rounding will work

                    # Update the record in the database with the target CGPA, capable CGPA, and study hours
                    if existing:
                        existing.marks = target_cgpa
                        existing.hours = required_study_hours_target
                        existing.capable_hours = required_study_hours_capable
                        existing.grade = grade  # Update grade
                    else:
                        student = User_marks(
                            sid=sid,
                            grade=grade,
                            marks=target_cgpa,
                            hours=required_study_hours_target,
                            capable_cgpa=capable_cgpa,
                            capable_hours=required_study_hours_capable
                        )
                        db.session.add(student)

                    db.session.commit()
                    msg = (f"Your target CGPA of {target_cgpa} has been successfully saved! "
                           f"You should study for {required_study_hours_target} hours daily to reach this CGPA.\n"
                           f"Your capable CGPA is: {capable_cgpa}. "
                           f"You should start studying for {required_study_hours_capable} hours daily to reach this CGPA.")

                else:
                    msg = "Error: Unable to get study hours prediction."

            except ValueError as ve:
                msg = f"Invalid input: {ve}"
            except Exception as e:
                msg = f"An error occurred while processing your request: {str(e)}"

    return render_template('upload.html', msg=msg)



@app.route('/questions', methods=['GET', 'POST'])
@login_required
def questions():
    user_id = session.get('user_id')  # Retrieve user ID from the session
    
    # Check if a record already exists in the User_marks table
    user_marks_record = User_marks.query.filter_by(sid=user_id).first()

    if user_marks_record and user_marks_record.capable_cgpa:  # If CGPA already exists
        return redirect(url_for('upload_marks'))

    if request.method == 'POST':
        # Collect form responses
        answers = {
            "productive_time": request.form.get("productive_time"),
            "learning_preference": request.form.get("learning_preference"),
            "focus_span": request.form.get("focus_span"),
            "review_frequency": request.form.get("review_material"),
            "exam_preparation":request.form.get("exam_preparation"),
            "note_taking":request.form.get("note_taking"),
            "question_asking": request.form.get("ask_questions"),
            "concept_handling":request.form.get("handle_difficult_concepts"),
            "organization": request.form.get("study_materials_organization")
        }

        try:
            # API call for prediction
            api_url = 'http://localhost:5001/predict'  # Adjust endpoint as necessary
            response = requests.post(api_url, json=answers)

            if response.status_code == 200:
                data = response.json()
                predicted_cgpa = data.get('predicted_cgpa')

                if not user_marks_record:
                    # If no existing record, create one with initial values
                    user_marks_record = User_marks(
                        sid=user_id,
                        capable_cgpa=predicted_cgpa,
                        grade="0",  # Placeholder grade
                        marks="0",  # Initial marks as 0
                        hours=0,  # Initial study hours as 0
                        capable_hours=0  # Initial capable study hours as 0
                    )
                    db.session.add(user_marks_record)
                else:
                    # If record exists, just update the capable CGPA
                    user_marks_record.capable_cgpa = predicted_cgpa

                db.session.commit()
                flash('Your predicted CGPA has been calculated!', 'success')
                return redirect(url_for('upload_marks'))
            else:
                app.logger.error(f"Prediction API error: {response.text}")
                flash('Error: Unable to get predicted CGPA. Please try again.', 'danger')

        except requests.RequestException as e:
            app.logger.error(f"API call failed: {e}")
            flash('An error occurred while contacting the prediction API.', 'danger')

    return render_template('questions.html')





if __name__ == '__main__':
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the app
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', '5000')),
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )