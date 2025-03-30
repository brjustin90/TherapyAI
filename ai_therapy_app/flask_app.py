"""
Minimal Flask API for Mental Health AI Therapy Application
This is a temporary solution until FastAPI compatibility issues with Python 3.13 are resolved
"""
import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
import redis
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'temporarysecretkey123456789')
app.config['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
app.config['REDIS_PORT'] = int(os.getenv('REDIS_PORT', 6379))
app.config['REDIS_PASSWORD'] = os.getenv('REDIS_PASSWORD', '')
app.config['REDIS_SSL'] = os.getenv('REDIS_SSL', 'False').lower() == 'true'
app.config['DATABASE_URL'] = "sqlite:///./app.db"

# Initialize database
engine = create_engine(app.config['DATABASE_URL'], connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Initialize Redis
redis_client = redis.Redis(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT'],
    password=app.config['REDIS_PASSWORD'],
    ssl=app.config['REDIS_SSL']
)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="therapy_sessions")
    messages = relationship("TherapyMessage", back_populates="session", cascade="all, delete-orphan")


class TherapyMessage(Base):
    __tablename__ = "therapy_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("therapy_sessions.id"), nullable=False)
    is_from_ai = Column(Boolean, default=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    emotion = Column(String)
    intent = Column(String)
    therapy_technique = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = relationship("TherapySession", back_populates="messages")


# Create tables
Base.metadata.create_all(bind=engine)

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

# Authentication decorator (simplified for now)
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        
        # In a real app, validate the token
        # For now, just checking if the header exists
        
        return f(*args, **kwargs)
    return decorated

# Basic routes
@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the Mental Health AI Therapy API",
        "version": "1.0.0"
    })

@app.route('/health')
def health_check():
    # Check database
    db = get_db()
    db_status = "healthy"
    try:
        db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Redis
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    })

# User routes
@app.route('/api/v1/users/register', methods=['POST'])
def register():
    data = request.json
    db = get_db()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == data['email']).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400
    
    # In real app, hash the password
    user = User(
        email=data['email'],
        hashed_password=data['password'],  # In production, hash this!
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
def login():
    data = request.json
    db = get_db()
    
    user = db.query(User).filter(User.email == data['email']).first()
    if not user or user.hashed_password != data['password']:  # In production, verify hash
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
@auth_required
def get_current_user():
    # In a real app, get user from token
    # For now, just return a demo user
    return jsonify({
        "id": 1,
        "email": "demo@example.com",
        "full_name": "Demo User",
        "is_active": True
    })

# Session routes
@app.route('/api/v1/sessions', methods=['POST'])
@auth_required
def create_session():
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

@app.route('/api/v1/sessions', methods=['GET'])
@auth_required
def get_sessions():
    db = get_db()
    
    # Get user from authentication (simplified)
    user_id = 1  # In production, get from token
    
    sessions = db.query(TherapySession).filter(TherapySession.user_id == user_id).all()
    
    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "session_type": session.session_type,
            "therapy_approach": session.therapy_approach,
            "scheduled_start": session.scheduled_start.isoformat(),
            "scheduled_end": session.scheduled_end.isoformat(),
            "status": session.status,
            "title": session.title
        })
    
    return jsonify(result)

@app.route('/api/v1/sessions/<int:session_id>', methods=['GET'])
@auth_required
def get_session(session_id):
    db = get_db()
    
    # Get user from authentication (simplified)
    user_id = 1  # In production, get from token
    
    session = db.query(TherapySession).filter(
        TherapySession.id == session_id,
        TherapySession.user_id == user_id
    ).first()
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "id": session.id,
        "user_id": session.user_id,
        "session_type": session.session_type,
        "therapy_approach": session.therapy_approach,
        "scheduled_start": session.scheduled_start.isoformat(),
        "scheduled_end": session.scheduled_end.isoformat(),
        "status": session.status,
        "title": session.title,
        "description": session.description,
        "goals": session.goals,
        "actual_start": session.actual_start.isoformat() if session.actual_start else None,
        "actual_end": session.actual_end.isoformat() if session.actual_end else None
    })

# Redis test route
@app.route('/api/v1/redis-test', methods=['GET'])
def test_redis():
    key = f"test:{datetime.now().timestamp()}"
    value = "Test from Flask API"
    
    redis_client.set(key, value)
    retrieved = redis_client.get(key)
    redis_client.delete(key)
    
    return jsonify({
        "set_value": value,
        "retrieved_value": retrieved.decode('utf-8') if retrieved else None
    })

# Voice routes (simplified)
@app.route('/api/v1/voice/chat', methods=['POST'])
@auth_required
def voice_chat():
    data = request.json
    user_message = data.get('user_message', '')
    session_id = data.get('session_id')
    
    # Get user from authentication (simplified)
    user_id = 1  # In production, get from token
    
    # Store user message in Redis
    conversation_key = f"conversation:{user_id}:{session_id or 'new'}"
    redis_client.rpush(conversation_key, f"user: {user_message}")
    
    # Simple AI response (in production would call OpenAI or other LLM)
    ai_response = f"This is a simulated AI response to: {user_message}"
    
    # Store AI response
    redis_client.rpush(conversation_key, f"assistant: {ai_response}")
    redis_client.expire(conversation_key, 60 * 60 * 24)  # Expire in 24 hours
    
    return jsonify({
        "response": ai_response,
        "session_id": session_id or "new"
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000) 