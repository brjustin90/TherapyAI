"""
Tests for the Flask API
"""
import os
import sys
import unittest
import json
import tempfile
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app from flask_app
from flask_app import app, Base, engine


class FlaskAPITest(unittest.TestCase):
    """Tests for the Flask API"""
    
    def setUp(self):
        """Set up the test client"""
        app.config['TESTING'] = True
        app.config['DATABASE_URL'] = "sqlite:///:memory:"
        self.app = app.test_client()
        
        # Create all tables in memory
        Base.metadata.create_all(bind=engine)
    
    def test_home_endpoint(self):
        """Test the home endpoint"""
        response = self.app.get('/')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], "Welcome to the Mental Health AI Therapy API")
        self.assertEqual(data['version'], "1.0.0")
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], "healthy")
        self.assertEqual(data['version'], "1.0.0")
        self.assertIn('database', data)
        self.assertIn('redis', data)
        self.assertIn('timestamp', data)
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        response = self.app.post('/api/v1/users/register', 
                                json={
                                    'email': 'test@example.com',
                                    'password': 'password123',
                                    'full_name': 'Test User'
                                })
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_login(self):
        """Test login endpoint"""
        # First register a user
        self.app.post('/api/v1/users/register', 
                    json={
                        'email': 'login_test@example.com',
                        'password': 'password123',
                        'full_name': 'Login Test User'
                    })
        
        # Then try to login
        response = self.app.post('/api/v1/users/login', 
                                json={
                                    'email': 'login_test@example.com',
                                    'password': 'password123'
                                })
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', data)
        self.assertEqual(data['token_type'], 'bearer')
    
    def test_protected_endpoint(self):
        """Test a protected endpoint without authentication"""
        response = self.app.get('/api/v1/users/me')
        
        self.assertEqual(response.status_code, 401)
        
        # Now with authentication header
        response = self.app.get('/api/v1/users/me', 
                               headers={'Authorization': 'Bearer fake_token'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['email'], 'demo@example.com')
    
    def test_redis_test_endpoint(self):
        """Test the Redis test endpoint"""
        response = self.app.get('/api/v1/redis-test')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['set_value'], "Test from Flask API")
        self.assertEqual(data['retrieved_value'], "Test from Flask API")
    
    def tearDown(self):
        """Clean up after tests"""
        pass


if __name__ == '__main__':
    unittest.main() 