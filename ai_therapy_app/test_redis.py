import os
from dotenv import load_dotenv
import redis

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test connection to Redis database"""
    print("Testing Redis connection...")
    
    # Load Redis credentials from .env
    host = os.getenv("REDIS_HOST")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD")
    ssl = os.getenv("REDIS_SSL", "False").lower() == "true"
    
    # Connect to Redis
    try:
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=ssl
        )
        
        # Test setting and getting a value
        r.set('test_key', 'Hello from AI Therapy App!')
        value = r.get('test_key')
        
        if value:
            print(f"Successfully connected to Redis at {host}")
            print(f"Test value retrieved: {value.decode('utf-8')}")
            return True
        else:
            print("Failed to retrieve test value from Redis")
            return False
    
    except Exception as e:
        print(f"Error connecting to Redis: {str(e)}")
        return False

if __name__ == "__main__":
    test_redis_connection() 