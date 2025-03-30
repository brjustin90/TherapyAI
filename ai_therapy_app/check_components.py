"""
Component check script for the Mental Health AI Therapy Application
Verifies that all essential components are working properly
"""
import os
import sys
import json
from datetime import datetime

def check_redis():
    """Check Redis connection"""
    print("\n--- Checking Redis Connection ---")
    try:
        import redis
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Connect to Redis
        host = os.getenv("REDIS_HOST")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD")
        ssl = os.getenv("REDIS_SSL", "False").lower() == "true"
        
        print(f"Connecting to Redis at {host}:{port} (SSL: {ssl})")
        
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=ssl
        )
        
        # Test connection
        if r.ping():
            print("✅ Redis ping successful")
        else:
            print("❌ Redis ping failed")
            return False
        
        # Test set/get
        test_key = f"test:{datetime.utcnow().timestamp()}"
        test_value = "Component check test value"
        
        r.set(test_key, test_value)
        retrieved = r.get(test_key)
        
        if retrieved and retrieved.decode('utf-8') == test_value:
            print(f"✅ Redis set/get successful")
        else:
            print(f"❌ Redis set/get failed. Got: {retrieved}")
            return False
        
        # Clean up
        r.delete(test_key)
        print("Redis check completed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Redis check failed with error: {str(e)}")
        return False

def check_database():
    """Check database connection and models"""
    print("\n--- Checking Database ---")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Use SQLite for testing
        db_url = "sqlite:///./test_check.db"
        print(f"Connecting to database: {db_url}")
        
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Import and create models
        from app.models.base import BaseModel
        from app.models.user import User
        
        # Create tables
        BaseModel.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Test session
        db = SessionLocal()
        
        # Create test user
        test_user = User(
            email=f"test_{datetime.utcnow().timestamp()}@example.com",
            hashed_password="testpassword",
            full_name="Test User"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Verify creation
        if test_user.id and test_user.created_at:
            print(f"✅ Test user created with ID: {test_user.id}")
        else:
            print("❌ Failed to create test user")
            return False
        
        # Clean up
        db.delete(test_user)
        db.commit()
        db.close()
        
        print("Database check completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database check failed with error: {str(e)}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n--- Checking Dependencies ---")
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "pydantic", 
        "redis", "python-jose", "passlib", "bcrypt",
        "pymongo", "python-dotenv"
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Not installed")
            all_installed = False
    
    return all_installed

def check_environment():
    """Check if all required environment variables are set"""
    print("\n--- Checking Environment Variables ---")
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    required_vars = [
        "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD",
        "SECRET_KEY"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked_value = value
            if var.endswith("PASSWORD") or var.endswith("KEY") or var.endswith("SECRET"):
                # Mask sensitive values
                if len(value) > 8:
                    masked_value = value[:3] + "****" + value[-3:]
                else:
                    masked_value = "********"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

def main():
    """Run all component checks"""
    print("=== Mental Health AI Therapy Application Component Check ===")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    results = {
        "dependencies": check_dependencies(),
        "environment": check_environment(),
        "redis": check_redis(),
        "database": check_database()
    }
    
    print("\n=== Summary ===")
    all_passed = True
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All components are working correctly! 🎉")
        return 0
    else:
        print("\n⚠️ Some components failed the check. Please fix the issues above. ⚠️")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 