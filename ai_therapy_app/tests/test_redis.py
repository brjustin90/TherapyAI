import os
import sys
import unittest
from dotenv import load_dotenv
import redis

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

class TestRedisConnection(unittest.TestCase):
    """Tests for Redis connection"""
    
    def setUp(self):
        """Set up the Redis client"""
        self.host = os.getenv("REDIS_HOST")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD")
        self.ssl = os.getenv("REDIS_SSL", "False").lower() == "true"
        
        self.redis_client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            ssl=self.ssl
        )
        
        # Clear test key if it exists
        self.redis_client.delete("test_key")
    
    def test_connection(self):
        """Test basic Redis connection"""
        # Test if we can ping Redis
        self.assertTrue(self.redis_client.ping())
        
    def test_set_and_get(self):
        """Test setting and getting a value"""
        # Set a value
        test_value = "Hello from test!"
        self.redis_client.set("test_key", test_value)
        
        # Get the value
        retrieved_value = self.redis_client.get("test_key")
        self.assertEqual(retrieved_value.decode('utf-8'), test_value)
    
    def test_expiration(self):
        """Test key expiration"""
        # Set a value with expiration
        test_value = "This will expire"
        self.redis_client.setex("expiring_key", 1, test_value)
        
        # Value should exist initially
        self.assertIsNotNone(self.redis_client.get("expiring_key"))
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Value should be gone after expiration
        self.assertIsNone(self.redis_client.get("expiring_key"))
    
    def tearDown(self):
        """Clean up after tests"""
        # Delete test keys
        self.redis_client.delete("test_key")
        self.redis_client.delete("expiring_key")


if __name__ == "__main__":
    unittest.main() 