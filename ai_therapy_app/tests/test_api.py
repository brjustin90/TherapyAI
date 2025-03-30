import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a simple test API
from fastapi import FastAPI, Depends
from app.db.session import get_redis

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Welcome to the Test API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/redis-test")
async def redis_test(redis=Depends(get_redis)):
    test_value = "API Test Value"
    redis.set("api_test_key", test_value)
    retrieved = redis.get("api_test_key")
    return {
        "set_value": test_value, 
        "retrieved_value": retrieved.decode('utf-8') if retrieved else None
    }


class TestAPI(unittest.TestCase):
    """Tests for FastAPI endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Test API"})
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["version"], "1.0.0")
    
    def test_redis_integration(self):
        """Test Redis integration with API"""
        response = self.client.get("/redis-test")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["set_value"], data["retrieved_value"])


if __name__ == "__main__":
    unittest.main() 