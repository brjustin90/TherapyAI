import os
import sys
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a test database
TEST_DB_URL = "sqlite:///./test_models.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models after setting up test database
from app.models.base import BaseModel
from app.models.user import User
from app.models.therapy import (
    TherapySession,
    TherapyMessage,
    SessionType,
    SessionStatus,
    TherapyApproach
)

# Create tables
Base = declarative_base()
Base.metadata.create_all(bind=engine)


class TestModels(unittest.TestCase):
    """Tests for SQLAlchemy models"""
    
    def setUp(self):
        """Set up test database session"""
        # Create tables for each test
        BaseModel.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
    
    def test_user_model(self):
        """Test User model"""
        # Create test user
        user = User(
            email="test@example.com",
            hashed_password="hashedpassword",
            full_name="Test User",
            is_active=True
        )
        
        # Add to session and commit
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Retrieve user and check
        retrieved_user = self.db.query(User).filter(User.email == "test@example.com").first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.full_name, "Test User")
        self.assertTrue(retrieved_user.is_active)
        self.assertIsNotNone(retrieved_user.created_at)
    
    def test_therapy_session_model(self):
        """Test TherapySession model"""
        # Create test user first
        user = User(
            email="therapy_test@example.com",
            hashed_password="hashedpassword",
            full_name="Therapy Test User"
        )
        self.db.add(user)
        self.db.commit()
        
        # Create therapy session
        now = datetime.utcnow()
        session = TherapySession(
            user_id=user.id,
            session_type=SessionType.VOICE,
            therapy_approach=TherapyApproach.CBT,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            status=SessionStatus.SCHEDULED,
            title="Test Therapy Session"
        )
        
        # Add to session and commit
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Retrieve session and check
        retrieved_session = self.db.query(TherapySession).filter(
            TherapySession.user_id == user.id
        ).first()
        
        self.assertIsNotNone(retrieved_session)
        self.assertEqual(retrieved_session.title, "Test Therapy Session")
        self.assertEqual(retrieved_session.session_type, SessionType.VOICE)
        self.assertEqual(retrieved_session.status, SessionStatus.SCHEDULED)
    
    def test_therapy_message_model(self):
        """Test TherapyMessage model"""
        # Create test user first
        user = User(
            email="message_test@example.com",
            hashed_password="hashedpassword"
        )
        self.db.add(user)
        self.db.commit()
        
        # Create therapy session
        now = datetime.utcnow()
        session = TherapySession(
            user_id=user.id,
            session_type=SessionType.TEXT,
            therapy_approach=TherapyApproach.CBT,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            status=SessionStatus.IN_PROGRESS
        )
        self.db.add(session)
        self.db.commit()
        
        # Create therapy message
        message = TherapyMessage(
            session_id=session.id,
            is_from_ai=False,
            content="Hello, I need help with anxiety."
        )
        
        # Add to session and commit
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Retrieve message and check
        retrieved_message = self.db.query(TherapyMessage).filter(
            TherapyMessage.session_id == session.id
        ).first()
        
        self.assertIsNotNone(retrieved_message)
        self.assertEqual(retrieved_message.content, "Hello, I need help with anxiety.")
        self.assertFalse(retrieved_message.is_from_ai)
    
    def test_relationships(self):
        """Test relationships between models"""
        # Create test user first
        user = User(
            email="relationship_test@example.com",
            hashed_password="hashedpassword"
        )
        self.db.add(user)
        self.db.commit()
        
        # Create therapy session
        now = datetime.utcnow()
        session = TherapySession(
            user_id=user.id,
            session_type=SessionType.VIDEO,
            therapy_approach=TherapyApproach.DBT,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            status=SessionStatus.IN_PROGRESS
        )
        self.db.add(session)
        self.db.commit()
        
        # Create therapy messages
        message1 = TherapyMessage(
            session_id=session.id,
            is_from_ai=False,
            content="User message"
        )
        message2 = TherapyMessage(
            session_id=session.id,
            is_from_ai=True,
            content="AI response"
        )
        
        self.db.add(message1)
        self.db.add(message2)
        self.db.commit()
        
        # Test user-session relationship
        user_sessions = self.db.query(User).filter(
            User.id == user.id
        ).first().therapy_sessions
        
        self.assertEqual(len(user_sessions), 1)
        self.assertEqual(user_sessions[0].session_type, SessionType.VIDEO)
        
        # Test session-message relationship
        session_messages = self.db.query(TherapySession).filter(
            TherapySession.id == session.id
        ).first().messages
        
        self.assertEqual(len(session_messages), 2)
        self.assertFalse(session_messages[0].is_from_ai)
        self.assertTrue(session_messages[1].is_from_ai)
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear data but keep tables
        self.db.query(TherapyMessage).delete()
        self.db.query(TherapySession).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()


if __name__ == "__main__":
    unittest.main() 