"""
Web Application for Mental Health AI Therapy
This is a Flask web application that provides both API endpoints and web UI
"""
import os
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, render_template, redirect, url_for, flash, session, abort
from flask_cors import CORS
from dotenv import load_dotenv
import redis
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app.ai.personalization import personalization_engine
from base64 import b64encode
from ai_therapy_app.llm_service import get_llm_response, clear_session_history
# Remove the direct import from here to avoid circular imports

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Enable debug mode
app.config['DEBUG'] = True

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'temporarysecretkey123456789')
app.config['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
app.config['REDIS_PORT'] = int(os.getenv('REDIS_PORT', 6379))
app.config['REDIS_PASSWORD'] = os.getenv('REDIS_PASSWORD', '')
app.config['REDIS_SSL'] = os.getenv('REDIS_SSL', 'False').lower() == 'true'
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', "sqlite:///app.db")
app.config['SESSION_TYPE'] = 'filesystem'

logger.info(f"Starting application with Redis host: {app.config['REDIS_HOST']}")

try:
    # Initialize database
    DATABASE_URL = app.config['DATABASE_URL']
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database engine: {str(e)}")
    raise

try:
    # Initialize Redis
    redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        password=app.config['REDIS_PASSWORD'],
        ssl=app.config['REDIS_SSL'],
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )
    # Test Redis connection
    redis_client.ping()
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    # Create a dummy Redis client for development if Redis is not available
    class DummyRedis:
        def __init__(self):
            self.data = {}
        def ping(self):
            return True
        def set(self, key, value):
            self.data[key] = value
            return True
        def get(self, key):
            return self.data.get(key, b'')
        def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True
        def rpush(self, key, value):
            if key not in self.data:
                self.data[key] = []
            self.data[key].append(value)
            return len(self.data[key])
        def lrange(self, key, start, end):
            if key not in self.data:
                return []
            return self.data[key][start:end if end != -1 else None]
        def expire(self, key, seconds):
            return True
    
    redis_client = DummyRedis()
    logger.warning("Using dummy Redis client for development")

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    phone_number = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    bio = Column(Text)
    preferences = Column(JSON, default={})
    data_permissions = Column(JSON, default={})
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    emergency_contact_relation = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    therapy_sessions = relationship("TherapySession", back_populates="user")


class TherapySession(Base):
    __tablename__ = "therapy_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String, nullable=False)  # VOICE, VIDEO, TEXT, CHECK_IN
    therapy_approach = Column(String, nullable=False)  # CBT, DBT, MINDFULNESS, etc.
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    status = Column(String, default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, MISSED
    title = Column(String)
    description = Column(Text)
    goals = Column(JSON, default=[])
    notes = Column(Text)
    recording_url = Column(String)
    is_recorded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", back_populates="therapy_sessions")
    messages = relationship("TherapyMessage", back_populates="session", cascade="all, delete-orphan")


class TherapyMessage(Base):
    __tablename__ = "therapy_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("therapy_sessions.id"), nullable=False)
    is_from_ai = Column(Boolean, default=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    emotion = Column(String)
    intent = Column(String)
    therapy_technique = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    session = relationship("TherapySession", back_populates="messages")


try:
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {str(e)}")
    raise

# Helper function to get database session
def get_db():
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Authentication helpers
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        db = get_db()
        return db.query(User).filter(User.id == session['user_id']).first()
    return None

# API authentication decorator
def api_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        
        # In a real app, validate the token
        # For now, just checking if the header exists
        
        return f(*args, **kwargs)
    return decorated

# Web Routes
@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        user = db.query(User).filter(User.email == email).first()
        
        if user and check_password_hash(user.hashed_password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        db = get_db()
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            flash('Email already registered', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name
            )
            db.add(user)
            db.commit()
            
            session['user_id'] = user.id
            flash('Registration successful!', 'success')
            return redirect(url_for('welcome_setup'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    db = get_db()
    
    # Get upcoming sessions
    upcoming_sessions = db.query(TherapySession).filter(
        TherapySession.user_id == user.id,
        TherapySession.scheduled_start > datetime.now(),
        TherapySession.status != 'CANCELLED'
    ).order_by(TherapySession.scheduled_start).limit(5).all()
    
    # Get past sessions
    past_sessions = db.query(TherapySession).filter(
        TherapySession.user_id == user.id,
        TherapySession.scheduled_start <= datetime.now()
    ).order_by(TherapySession.scheduled_start.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          user=user, 
                          upcoming_sessions=upcoming_sessions,
                          past_sessions=past_sessions)

@app.route('/sessions')
@login_required
def sessions():
    """List user's therapy sessions"""
    db_session = get_db()
    try:
        user = get_current_user()
        # Get user's therapy sessions
        sessions = db_session.query(TherapySession).filter_by(user_id=user.id).order_by(TherapySession.scheduled_start).all()
        
        # Add the current datetime to the template context
        now = datetime.now()
        
        return render_template('sessions.html', user=user, sessions=sessions, now=now)
    finally:
        db_session.close()

@app.route('/sessions/new', methods=['GET', 'POST'])
@login_required
def new_session():
    """Create a new therapy session"""
    if request.method == 'POST':
        db_session = get_db()
        try:
            user = get_current_user()
            
            # Get form data
            session_type = request.form.get('session_type')
            therapy_approach = request.form.get('therapy_approach')
            scheduled_date = request.form.get('scheduled_date')
            scheduled_time = request.form.get('scheduled_time')
            duration = int(request.form.get('duration', 60))
            title = request.form.get('title')
            description = request.form.get('description', '')
            
            # Parse date and time
            scheduled_start = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            scheduled_end = scheduled_start + timedelta(minutes=duration)
            
            # Create new session
            new_therapy_session = TherapySession(
                user_id=user.id,
                session_type=session_type,
                therapy_approach=therapy_approach,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                title=title,
                description=description,
                status="SCHEDULED"
            )
            
            db_session.add(new_therapy_session)
            db_session.commit()
            
            flash('Therapy session scheduled successfully!', 'success')
            return redirect(url_for('sessions'))
        except Exception as e:
            db_session.rollback()
            flash(f'Error scheduling session: {str(e)}', 'danger')
        finally:
            db_session.close()
    
    return render_template('new_session.html', user=get_current_user())

@app.route('/sessions/<int:session_id>')
@login_required
def view_session(session_id):
    """View details of a specific therapy session"""
    db_session = get_db()
    try:
        user = get_current_user()
        
        # Get the therapy session
        session = db_session.query(TherapySession).filter_by(id=session_id, user_id=user.id).first()
        if session is None:
            abort(404)  # Return 404 if session not found
        
        # Get session messages
        messages = db_session.query(TherapyMessage).filter_by(session_id=session_id).order_by(TherapyMessage.timestamp).all()
        
        # Get current datetime for template
        now = datetime.now()
        
        return render_template('view_session.html', user=user, session=session, messages=messages, now=now)
    finally:
        db_session.close()

@app.route('/sessions/<int:session_id>/chat', methods=['GET', 'POST'])
@login_required
def session_chat(session_id):
    """Chat interface for a therapy session"""
    db_session = get_db()
    try:
        user = get_current_user()
        
        # Get the therapy session
        session = db_session.query(TherapySession).filter_by(id=session_id, user_id=user.id).first()
        if session is None:
            abort(404)  # Return 404 if session not found
        
        if request.method == 'POST':
            message_content = request.form.get('message', '')
            if message_content:
                # Save user message
                user_message = TherapyMessage(
                    session_id=session_id,
                    content=message_content,
                    is_from_ai=False,
                    timestamp=datetime.now()
                )
                db_session.add(user_message)
                
                # Get personalization context for the user
                personalization_context = personalization_engine.generate_personalization_context(user.id)
                
                # Generate AI response using LLM service
                ai_text_response, ai_audio_data = get_llm_response(
                    message_content, 
                    str(session_id), 
                    str(user.id), 
                    personalization_context
                )
                
                # Save AI response (using text part)
                if ai_text_response:
                    ai_message = TherapyMessage(
                        session_id=session_id,
                        content=ai_text_response, # Use the text response
                        is_from_ai=True,
                        timestamp=datetime.now()
                    )
                    db_session.add(ai_message)
                
                    # Log the topics discussed in this interaction
                    session_data = {
                        'session_id': session_id,
                        'message_pair': {
                            'user': message_content,
                            'ai': ai_text_response
                        }
                    }
                    
                    # Update the personalization engine with this interaction
                    personalization_engine.update_profile_from_session(user.id, session_data)
                    
                    db_session.commit()
                
                    # --- Updated to include audio data (base64 encoded) --- 
                    audio_base64 = None
                    if ai_audio_data:
                        audio_base64 = b64encode(ai_audio_data).decode('utf-8')

                    return jsonify({
                        'success': True,
                        'response': ai_text_response,
                        'audio': audio_base64,
                        'audio_format': 'wav',
                        'session_id': session_id
                    })
                    # ------------------------------------------------------
                else:
                    # Handle case where LLM failed
                    logger.error(f"LLM failed to generate text response for session {session_id}")
                    db_session.rollback() # Rollback the user message save if AI fails?
                    return jsonify({
                        'success': False,
                        'message': 'AI failed to generate a response.',
                        'session_id': session_id
                    }), 500
            
            # Get session messages
            messages = db_session.query(TherapyMessage).filter_by(session_id=session_id).order_by(TherapyMessage.timestamp).all()
            
            # Get current datetime for template
            now = datetime.now()
            
            return render_template('session_chat.html', user=user, session=session, messages=messages, now=now)
    finally:
        db_session.close()

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    return render_template('profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.phone_number = request.form.get('phone_number')
        user.bio = request.form.get('bio')
        user.emergency_contact_name = request.form.get('emergency_contact_name')
        user.emergency_contact_phone = request.form.get('emergency_contact_phone')
        user.emergency_contact_relation = request.form.get('emergency_contact_relation')
        
        db.add(user)
        db.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/profile/therapist_preferences', methods=['GET', 'POST'])
@login_required
def therapist_preferences():
    """Allow user to select their preferred therapist avatar"""
    db_session = get_db()
    try:
        user = get_current_user()
        
        # Initialize preferences if they don't exist
        if not user.preferences:
            user.preferences = {}
        
        if 'therapist' not in user.preferences:
            user.preferences['therapist'] = {
                'gender': 'female',  # Default to female
                'ethnicity': 'caucasian',  # Default
                'avatar_id': '1'  # Default avatar ID
            }
        
        if request.method == 'POST':
            # Update preferences based on form data
            gender = request.form.get('gender')
            ethnicity = request.form.get('ethnicity')
            avatar_id = request.form.get('avatar_id')
            
            if gender and ethnicity and avatar_id:
                user.preferences['therapist'] = {
                    'gender': gender,
                    'ethnicity': ethnicity,
                    'avatar_id': avatar_id
                }
                
                # Save to database
                db_session.commit()
                
                flash('Therapist preferences updated successfully!', 'success')
                return redirect(url_for('profile'))
        
        # Get available avatars
        available_avatars = {
            'male': {
                'caucasian': [
                    {'id': '1', 'name': 'Michael', 'image': 'male/male_caucasian_1.jpg'},
                    {'id': '2', 'name': 'James', 'image': 'male/male_caucasian_2.jpg'},
                ],
                'african_american': [
                    {'id': '3', 'name': 'David', 'image': 'male/male_african_american_1.jpg'},
                    {'id': '4', 'name': 'William', 'image': 'male/male_african_american_2.jpg'},
                ],
                'asian': [
                    {'id': '5', 'name': 'Robert', 'image': 'male/male_asian_1.jpg'},
                    {'id': '6', 'name': 'John', 'image': 'male/male_asian_2.jpg'},
                ],
                'hispanic': [
                    {'id': '7', 'name': 'Carlos', 'image': 'male/male_hispanic_1.jpg'},
                    {'id': '8', 'name': 'Miguel', 'image': 'male/male_hispanic_2.jpg'},
                ],
                'middle_eastern': [
                    {'id': '9', 'name': 'Ahmed', 'image': 'male/male_middle_eastern_1.jpg'},
                    {'id': '10', 'name': 'Ali', 'image': 'male/male_middle_eastern_2.jpg'},
                ],
                'south_asian': [
                    {'id': '11', 'name': 'Raj', 'image': 'male/male_south_asian_1.jpg'},
                    {'id': '12', 'name': 'Vikram', 'image': 'male/male_south_asian_2.jpg'},
                ]
            },
            'female': {
                'caucasian': [
                    {'id': '13', 'name': 'Emily', 'image': 'female/female_caucasian_1.jpg'},
                    {'id': '14', 'name': 'Sarah', 'image': 'female/female_caucasian_2.jpg'},
                ],
                'african_american': [
                    {'id': '15', 'name': 'Zoe', 'image': 'female/female_african_american_1.jpg'},
                    {'id': '16', 'name': 'Maya', 'image': 'female/female_african_american_2.jpg'},
                ],
                'asian': [
                    {'id': '17', 'name': 'Lucy', 'image': 'female/female_asian_1.jpg'},
                    {'id': '18', 'name': 'Michelle', 'image': 'female/female_asian_2.jpg'},
                ],
                'hispanic': [
                    {'id': '19', 'name': 'Sofia', 'image': 'female/female_hispanic_1.jpg'},
                    {'id': '20', 'name': 'Isabella', 'image': 'female/female_hispanic_2.jpg'},
                ],
                'middle_eastern': [
                    {'id': '21', 'name': 'Yasmin', 'image': 'female/female_middle_eastern_1.jpg'},
                    {'id': '22', 'name': 'Fatima', 'image': 'female/female_middle_eastern_2.jpg'},
                ],
                'south_asian': [
                    {'id': '23', 'name': 'Priya', 'image': 'female/female_south_asian_1.jpg'},
                    {'id': '24', 'name': 'Deepa', 'image': 'female/female_south_asian_2.jpg'},
                ]
            }
        }
        
        return render_template(
            'therapist_preferences.html', 
            user=user, 
            therapist_prefs=user.preferences.get('therapist', {}),
            available_avatars=available_avatars
        )
    finally:
        db_session.close()

@app.route('/video_session/<session_id>')
@login_required
def video_session(session_id):
    """Page for a video therapy session with the AI avatar"""
    db_session = get_db()
    try:
        user = get_current_user()
        
        # Add debug logging
        app.logger.debug(f"Accessing video session {session_id} for user {user.id}")
        
        # Get the therapy session
        therapy_session = db_session.query(TherapySession).filter_by(id=session_id, user_id=user.id).first()
        if therapy_session is None:
            app.logger.error(f"Session {session_id} not found for user {user.id}")
            abort(404)  # Return 404 if session not found
        
        # Check if session is valid for video
        if therapy_session.session_type != 'VIDEO':
            app.logger.error(f"Session {session_id} type is {therapy_session.session_type}, not VIDEO")
            flash('This session does not support video.', 'warning')
            return redirect(url_for('view_session', session_id=session_id))
        
        try:
            # Get session messages
            messages = db_session.query(TherapyMessage).filter_by(session_id=session_id).order_by(TherapyMessage.timestamp).all()
            
            # Get current datetime for template
            now = datetime.now()
            
            # Get therapist preferences for the avatar
            therapist_prefs = user.preferences.get('therapist', {})
            app.logger.debug(f"Therapist preferences: {therapist_prefs}")
            
            if not therapist_prefs:
                # Default preferences if not set
                therapist_prefs = {
                    'gender': 'female',
                    'ethnicity': 'caucasian',
                    'avatar_id': '13'  # Default to first female avatar
                }
            
            # Find the selected avatar
            selected_avatar = None
            selected_gender = therapist_prefs.get('gender', 'female')
            selected_ethnicity = therapist_prefs.get('ethnicity', 'caucasian')
            selected_id = therapist_prefs.get('avatar_id', '13')
            
            app.logger.debug(f"Selected avatar details - Gender: {selected_gender}, Ethnicity: {selected_ethnicity}, ID: {selected_id}")
            
            # Get available avatars (reuse the same dictionary from earlier)
            available_avatars = {
                'male': {
                    'caucasian': [
                        {'id': '1', 'name': 'Michael', 'image': 'male/male_caucasian_1.jpg'},
                        {'id': '2', 'name': 'James', 'image': 'male/male_caucasian_2.jpg'},
                    ],
                    'african_american': [
                        {'id': '3', 'name': 'David', 'image': 'male/male_african_american_1.jpg'},
                        {'id': '4', 'name': 'William', 'image': 'male/male_african_american_2.jpg'},
                    ],
                    'asian': [
                        {'id': '5', 'name': 'Robert', 'image': 'male/male_asian_1.jpg'},
                        {'id': '6', 'name': 'John', 'image': 'male/male_asian_2.jpg'},
                    ],
                    'hispanic': [
                        {'id': '7', 'name': 'Carlos', 'image': 'male/male_hispanic_1.jpg'},
                        {'id': '8', 'name': 'Miguel', 'image': 'male/male_hispanic_2.jpg'},
                    ],
                    'middle_eastern': [
                        {'id': '9', 'name': 'Ahmed', 'image': 'male/male_middle_eastern_1.jpg'},
                        {'id': '10', 'name': 'Ali', 'image': 'male/male_middle_eastern_2.jpg'},
                    ],
                    'south_asian': [
                        {'id': '11', 'name': 'Raj', 'image': 'male/male_south_asian_1.jpg'},
                        {'id': '12', 'name': 'Vikram', 'image': 'male/male_south_asian_2.jpg'},
                    ]
                },
                'female': {
                    'caucasian': [
                        {'id': '13', 'name': 'Emily', 'image': 'female/female_caucasian_1.jpg'},
                        {'id': '14', 'name': 'Sarah', 'image': 'female/female_caucasian_2.jpg'},
                    ],
                    'african_american': [
                        {'id': '15', 'name': 'Zoe', 'image': 'female/female_african_american_1.jpg'},
                        {'id': '16', 'name': 'Maya', 'image': 'female/female_african_american_2.jpg'},
                    ],
                    'asian': [
                        {'id': '17', 'name': 'Lucy', 'image': 'female/female_asian_1.jpg'},
                        {'id': '18', 'name': 'Michelle', 'image': 'female/female_asian_2.jpg'},
                    ],
                    'hispanic': [
                        {'id': '19', 'name': 'Sofia', 'image': 'female/female_hispanic_1.jpg'},
                        {'id': '20', 'name': 'Isabella', 'image': 'female/female_hispanic_2.jpg'},
                    ],
                    'middle_eastern': [
                        {'id': '21', 'name': 'Yasmin', 'image': 'female/female_middle_eastern_1.jpg'},
                        {'id': '22', 'name': 'Fatima', 'image': 'female/female_middle_eastern_2.jpg'},
                    ],
                    'south_asian': [
                        {'id': '23', 'name': 'Priya', 'image': 'female/female_south_asian_1.jpg'},
                        {'id': '24', 'name': 'Deepa', 'image': 'female/female_south_asian_2.jpg'},
                    ]
                }
            }
            
            if selected_gender in available_avatars and selected_ethnicity in available_avatars[selected_gender]:
                avatars_list = available_avatars[selected_gender][selected_ethnicity]
                for avatar in avatars_list:
                    if avatar['id'] == selected_id:
                        selected_avatar = avatar
                        break
                
                # If not found, use the first avatar of selected gender and ethnicity
                if not selected_avatar and avatars_list:
                    selected_avatar = avatars_list[0]
            
            # Fallback to default if still not found
            if not selected_avatar:
                app.logger.warning(f"Could not find selected avatar, using default")
                selected_avatar = available_avatars['female']['caucasian'][0]
            
            app.logger.debug(f"Selected avatar: {selected_avatar}")
            
            return render_template('video_session.html', 
                                user=user,
                                session=therapy_session,
                                messages=messages,
                                now=now,
                                therapist_prefs=therapist_prefs,
                                selected_avatar=selected_avatar)
        except Exception as e:
            app.logger.error(f"Error in video session: {str(e)}")
            raise
    finally:
        db_session.close()

@app.route('/sessions/<session_id>/videocall', methods=['POST'])
@login_required
def video_call_api(session_id):
    """Handle actions during a video call session (start, end, message)"""
    db_session = get_db()
    try:
        user = get_current_user()
        therapy_session = db_session.query(TherapySession).filter_by(id=session_id, user_id=user.id).first_or_404()
        
        data = request.json
        action = data.get('action')
        
        logger.info(f"Received action '{action}' for video session {session_id}")

        if action == 'start':
            # Update session status to IN_PROGRESS if it's SCHEDULED
            if therapy_session.status == 'SCHEDULED':
                therapy_session.status = 'IN_PROGRESS'
                therapy_session.actual_start = datetime.now()
                db_session.commit()
            return jsonify({
                'success': True,
                'message': 'Video call started',
                'session_id': session_id,
                'status': therapy_session.status
            })
            
        elif action == 'end':
            # Update session status to COMPLETED
            therapy_session.status = 'COMPLETED'
            therapy_session.actual_end = datetime.now()
            db_session.commit()
            
            # Clear LLM conversation history
            clear_session_history(str(session_id)) # Ensure session_id is string if needed by llm_service
            
            return jsonify({
                'success': True,
                'message': 'Video call ended',
                'session_id': session_id,
                'status': therapy_session.status
            })
            
        elif action == 'message':
            logger.info(f"Processing message in video session {session_id}")
            user_message = data.get('message')
            
            if not user_message:
                return jsonify({
                    'success': False,
                    'message': 'No message provided'
                }), 400
            
            # Save user message first
            new_message = TherapyMessage(
                session_id=session_id,
                content=user_message,
                is_from_ai=False,
                timestamp=datetime.now()
            )
            db_session.add(new_message)
            # Commit the user message immediately so it appears even if AI fails
            db_session.commit() 
            
            # Get personalization context for the user
            personalization_context = personalization_engine.generate_personalization_context(user.id)
            
            # Generate AI response using LLM service
            # --- Updated to handle (text, audio) tuple --- 
            ai_text_response, ai_audio_data = get_llm_response(
                user_message, 
                str(session_id), # Ensure session_id is string
                str(user.id), 
                personalization_context
            )
            # --------------------------------------------
            
            # Save AI response (using text part) if successful
            if ai_text_response:
                ai_message = TherapyMessage(
                    session_id=session_id,
                    content=ai_text_response, # Use the text response
                    is_from_ai=True,
                    timestamp=datetime.now()
                )
                db_session.add(ai_message)
            
                # Log the topics discussed in this interaction
                session_data = {
                    'session_id': session_id,
                    'message_pair': {
                        'user': user_message,
                        'ai': ai_text_response # Use text response here too
                    }
                }
                
                # Update the personalization engine with this interaction
                personalization_engine.update_profile_from_session(user.id, session_data)
                
                # Commit the AI message and personalization update
                db_session.commit()
            
                # --- Prepare JSON response including audio --- 
                audio_base64 = None
                if ai_audio_data:
                    audio_base64 = b64encode(ai_audio_data).decode('utf-8')

                return jsonify({
                    'success': True,
                    'response': ai_text_response,
                    'audio': audio_base64,
                    'audio_format': 'wav',
                    'session_id': session_id
                })
                # ---------------------------------------------
            else:
                # Handle case where LLM failed to generate text
                logger.error(f"LLM failed to generate text response for video session {session_id}")
                # User message is already saved, so just return error
                return jsonify({
                    'success': False,
                    'message': 'AI failed to generate a response.',
                    'session_id': session_id
                }), 500 # Indicate server error
            
        else:
            logger.error(f"Unknown action: {action}")
            return jsonify({
                'success': False,
                'message': f'Unknown action: {action}'
            }), 400
    except Exception as e:
        logger.error(f"Error in video_call_api: {str(e)}")
        # Rollback potentially partially committed changes (though less likely with separate commits)
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500
    finally:
        db_session.close()

@app.route('/sessions/<session_id>/transcript', methods=['POST'])
@login_required
def save_transcript(session_id):
    """Save transcript from a therapy session"""
    db_session = get_db()
    try:
        therapy_session = db_session.query(TherapySession).filter_by(id=session_id, user_id=get_current_user().id).first_or_404()
        
        data = request.json
        transcript = data.get('transcript', [])
        
        # In a production app, we would process and store the transcript properly
        # For this demo, we'll just acknowledge the receipt
        
        # Add a note to the session
        therapy_session.notes = therapy_session.notes or ""
        therapy_session.notes += f"\n\nTranscript saved on {datetime.now().strftime('%Y-%m-%d %H:%M')} with {len(transcript)} exchanges."
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transcript saved successfully'
        })
    finally:
        db_session.close()

@app.route('/ai_preferences')
@login_required
def ai_preferences():
    """Page for managing AI learning preferences"""
    # Get user profile from personalization engine
    user_profile = personalization_engine.get_user_profile(get_current_user().id)
    
    return render_template('ai_preferences.html', user_profile=user_profile)

@app.route('/update_ai_preferences', methods=['POST'])
@login_required
def update_ai_preferences():
    """Update AI learning preferences"""
    # Get consent information from form
    data_collection_consent = 'data_collection_consent' in request.form
    data_retention_preference = request.form.get('data_retention_preference', 'session')
    
    # Get sharing permissions
    sharing_permissions = {
        'anonymized_research': 'share_anonymized_research' in request.form,
        'therapist_oversight': 'share_therapist_oversight' in request.form
    }
    
    # Get user profile
    user_profile = personalization_engine.get_user_profile(get_current_user().id)
    
    # Update permissions
    user_profile.update_data_permissions({
        'data_collection_consent': data_collection_consent,
        'data_retention_preference': data_retention_preference,
        'data_sharing_permissions': sharing_permissions
    })
    
    # Save changes
    user_profile.save()
    
    # Update consent in personalization engine
    personalization_engine.handle_consent_update(get_current_user().id, data_collection_consent)
    
    flash('AI learning preferences updated successfully.', 'success')
    return redirect(url_for('ai_preferences'))

@app.route('/update_ai_personalization', methods=['POST'])
@login_required
def update_ai_personalization():
    """Update AI personalization settings"""
    # Get user profile
    user_profile = personalization_engine.get_user_profile(get_current_user().id)
    
    # Only proceed if user has consented to data collection
    if not user_profile.data_collection_consent:
        flash('You must enable AI learning before updating personalization settings.', 'warning')
        return redirect(url_for('ai_preferences'))
    
    # Update communication style
    formality_level = request.form.get('formality_level', 'balanced')
    verbosity = request.form.get('verbosity', 'balanced')
    
    user_profile.update_communication_style({
        'formality_level': formality_level,
        'verbosity': verbosity
    })
    
    # Update therapy approaches
    therapy_approaches = {}
    for approach in ['cbt', 'mindfulness', 'psychodynamic', 'solution_focused', 'humanistic', 'dbt']:
        rating_key = f'therapy_approaches[{approach}]'
        if rating_key in request.form:
            try:
                rating = int(request.form[rating_key])
                if 1 <= rating <= 10:
                    therapy_approaches[approach] = rating
            except ValueError:
                pass
    
    user_profile.therapy_approaches = therapy_approaches
    
    # Update topics of interest
    interests = request.form.get('interests', '')
    if interests:
        user_profile.topic_interests = {}
        for topic in [t.strip() for t in interests.split(',')]:
            if topic:
                user_profile.update_topic_interest(topic, 0.8)
    
    # Update trigger topics
    triggers = request.form.get('triggers', '')
    if triggers:
        user_profile.trigger_topics = []
        for topic in [t.strip() for t in triggers.split(',')]:
            if topic:
                user_profile.add_trigger_topic(topic, 8)
    
    # Save changes
    user_profile.save()
    
    flash('Personalization settings updated successfully.', 'success')
    return redirect(url_for('ai_preferences'))

@app.route('/delete_ai_data', methods=['POST'])
@login_required
def delete_ai_data():
    """Delete all AI learning data for the current user"""
    # Handle session end which will delete data if consent is not given
    personalization_engine.handle_session_end(get_current_user().id)
    
    # Additionally, force delete any profile data
    secure_id = personalization_engine.get_user_profile(get_current_user().id).secure_id
    
    # Remove from memory
    if get_current_user().id in personalization_engine.profiles:
        del personalization_engine.profiles[get_current_user().id]
    
    # Delete file if it exists
    file_path = f"user_profiles/{secure_id}.json"
    if os.path.exists(file_path):
        os.remove(file_path)
    
    flash('All AI learning data has been deleted successfully.', 'success')
    return redirect(url_for('ai_preferences'))

@app.route('/welcome/setup', methods=['GET', 'POST'])
@login_required
def welcome_setup():
    """Post-registration setup for selecting therapist avatar"""
    db_session = get_db()
    try:
        user = get_current_user()
        
        # Initialize preferences if they don't exist
        if not user.preferences:
            user.preferences = {}
        
        if 'therapist' not in user.preferences:
            user.preferences['therapist'] = {
                'gender': 'female',  # Default to female
                'ethnicity': 'caucasian',  # Default
                'avatar_id': '13'  # Default avatar ID
            }
        
        # Get therapist preferences
        therapist_prefs = user.preferences.get('therapist', {})
        
        if request.method == 'POST':
            # Update preferences based on form data
            gender = request.form.get('gender')
            ethnicity = request.form.get('ethnicity')
            avatar_id = request.form.get('avatar_id')
            
            if gender and ethnicity and avatar_id:
                user.preferences['therapist'] = {
                    'gender': gender,
                    'ethnicity': ethnicity,
                    'avatar_id': avatar_id
                }
                
                # Save to database
                db_session.commit()
                
                flash('Therapist preferences saved successfully!', 'success')
                return redirect(url_for('dashboard'))
        
        # Get available avatars
        available_avatars = {
            'male': {
                'caucasian': [
                    {'id': '1', 'name': 'Michael', 'image': 'male/male_caucasian_1.jpg'},
                    {'id': '2', 'name': 'James', 'image': 'male/male_caucasian_2.jpg'},
                ],
                'african_american': [
                    {'id': '3', 'name': 'David', 'image': 'male/male_african_american_1.jpg'},
                    {'id': '4', 'name': 'William', 'image': 'male/male_african_american_2.jpg'},
                ],
                'asian': [
                    {'id': '5', 'name': 'Robert', 'image': 'male/male_asian_1.jpg'},
                    {'id': '6', 'name': 'John', 'image': 'male/male_asian_2.jpg'},
                ],
                'hispanic': [
                    {'id': '7', 'name': 'Carlos', 'image': 'male/male_hispanic_1.jpg'},
                    {'id': '8', 'name': 'Miguel', 'image': 'male/male_hispanic_2.jpg'},
                ],
                'middle_eastern': [
                    {'id': '9', 'name': 'Ahmed', 'image': 'male/male_middle_eastern_1.jpg'},
                    {'id': '10', 'name': 'Ali', 'image': 'male/male_middle_eastern_2.jpg'},
                ],
                'south_asian': [
                    {'id': '11', 'name': 'Raj', 'image': 'male/male_south_asian_1.jpg'},
                    {'id': '12', 'name': 'Vikram', 'image': 'male/male_south_asian_2.jpg'},
                ]
            },
            'female': {
                'caucasian': [
                    {'id': '13', 'name': 'Emily', 'image': 'female/female_caucasian_1.jpg'},
                    {'id': '14', 'name': 'Sarah', 'image': 'female/female_caucasian_2.jpg'},
                ],
                'african_american': [
                    {'id': '15', 'name': 'Zoe', 'image': 'female/female_african_american_1.jpg'},
                    {'id': '16', 'name': 'Maya', 'image': 'female/female_african_american_2.jpg'},
                ],
                'asian': [
                    {'id': '17', 'name': 'Lucy', 'image': 'female/female_asian_1.jpg'},
                    {'id': '18', 'name': 'Michelle', 'image': 'female/female_asian_2.jpg'},
                ],
                'hispanic': [
                    {'id': '19', 'name': 'Sofia', 'image': 'female/female_hispanic_1.jpg'},
                    {'id': '20', 'name': 'Isabella', 'image': 'female/female_hispanic_2.jpg'},
                ],
                'middle_eastern': [
                    {'id': '21', 'name': 'Yasmin', 'image': 'female/female_middle_eastern_1.jpg'},
                    {'id': '22', 'name': 'Fatima', 'image': 'female/female_middle_eastern_2.jpg'},
                ],
                'south_asian': [
                    {'id': '23', 'name': 'Priya', 'image': 'female/female_south_asian_1.jpg'},
                    {'id': '24', 'name': 'Deepa', 'image': 'female/female_south_asian_2.jpg'},
                ]
            }
        }
        
        return render_template(
            'welcome_setup.html', 
            user=user, 
            therapist_prefs=therapist_prefs,
            available_avatars=available_avatars
        )
    finally:
        db_session.close()

# API Routes
@app.route('/api/health')
def health_check():
    # Check database
    db_status = "healthy"
    try:
        db = get_db()
        db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check Redis
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"
        logger.error(f"Redis health check failed: {str(e)}")
    
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/users/register', methods=['POST'])
def api_register():
    data = request.json
    db = get_db()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == data['email']).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400
    
    # Hash the password
    hashed_password = generate_password_hash(data['password'])
    
    user = User(
        email=data['email'],
        hashed_password=hashed_password,
        full_name=data.get('full_name', ''),
        phone_number=data.get('phone_number', '')
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Don't return the password
    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "created_at": user.created_at.isoformat()
    })

@app.route('/api/v1/users/login', methods=['POST'])
def api_login():
    data = request.json
    db = get_db()
    
    user = db.query(User).filter(User.email == data['email']).first()
    if not user or not check_password_hash(user.hashed_password, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # In real app, generate a proper JWT token
    token = {
        "user_id": user.id,
        "exp": (datetime.now() + timedelta(days=7)).timestamp()
    }
    
    return jsonify({
        "access_token": json.dumps(token),  # In production, use JWT
        "token_type": "bearer"
    })

@app.route('/api/v1/users/me', methods=['GET'])
@api_auth_required
def api_get_current_user():
    # In a real app, get user from token
    # For now, just return a demo user
    return jsonify({
        "id": 1,
        "email": "demo@example.com",
        "full_name": "Demo User",
        "is_active": True
    })

@app.route('/api/v1/sessions', methods=['POST'])
@api_auth_required
def api_create_session():
    data = request.json
    db = get_db()
    
    # Get user from authentication (simplified)
    user_id = 1  # In production, get from token
    
    session = TherapySession(
        user_id=user_id,
        session_type=data['session_type'],
        therapy_approach=data['therapy_approach'],
        scheduled_start=datetime.fromisoformat(data['scheduled_start']),
        scheduled_end=datetime.fromisoformat(data['scheduled_end']),
        title=data.get('title', ''),
        description=data.get('description', ''),
        goals=data.get('goals', []),
        is_recorded=data.get('is_recorded', False)
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return jsonify({
        "id": session.id,
        "user_id": session.user_id,
        "session_type": session.session_type,
        "therapy_approach": session.therapy_approach,
        "scheduled_start": session.scheduled_start.isoformat(),
        "scheduled_end": session.scheduled_end.isoformat(),
        "status": session.status,
        "title": session.title,
        "created_at": session.created_at.isoformat()
    })

@app.route('/api/v1/voice/chat', methods=['POST'])
@api_auth_required
def api_voice_chat():
    """
    API endpoint for voice chat with the AI therapist
    This is for mobile apps to enable voice-based therapy sessions
    """
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id')
    
    if not user_message:
        return jsonify({
            'success': False,
            'message': 'No message provided'
        }), 400
    
    # Get user ID from session (in a real app, from token)
    # Simulating a user for demo purposes
    user_id = data.get('user_id', '1')  
    
    # Get personalization context for the user
    personalization_context = personalization_engine.generate_personalization_context(user_id)
    
    # Generate AI response using LLM service
    # --- Updated to handle (text, audio) tuple --- 
    ai_text_response, ai_audio_data = get_llm_response(
        user_message, 
        session_id or 'api-session', # Use provided session_id or a default
        user_id, 
        personalization_context
    )
    # --------------------------------------------
    
    # In a real app, record this in the database (TherapyMessage)
    # TODO: Decide if/how to link 'api-session' messages to users/sessions
    # For now, we just return the response
    
    # --- Prepare JSON response including audio --- 
    if ai_text_response:
        audio_base64 = None
        if ai_audio_data:
            # Ensure base64 is imported (should be at top of file)
            audio_base64 = b64encode(ai_audio_data).decode('utf-8')

        return jsonify({
            'success': True,
            'response': ai_text_response,
            'audio': audio_base64,
            'audio_format': 'wav' # Assuming WAV format from llm_service
        })
    else:
        # Handle case where LLM failed to generate text
        logger.error(f"LLM failed to generate text response for API voice chat (session: {session_id or 'api-session'})")
        return jsonify({
            'success': False,
            'message': 'AI failed to generate a response.'
        }), 500 # Indicate server error
    # --------------------------------------------

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Create database tables if they don't exist
    init_db()
    
    # Create .env file for OpenAI API key if it doesn't exist
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_file_path):
        with open(env_file_path, "w") as f:
            f.write("# Add your OpenAI API key here for LLM-powered therapy conversations\n")
            f.write("# Sign up at https://platform.openai.com to get an API key\n")
            f.write("OPENAI_API_KEY=\n")
        print(f"Created .env file at {env_file_path}. Please add your OpenAI API key.")
    
    # Run Flask app
    app.run(debug=True, host="localhost", port=8000) 