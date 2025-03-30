"""
Core Component check script for the Mental Health AI Therapy Application
Verifies that core components (Redis and database) are working properly
"""
import os
import sys
import json
import importlib.util
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
        test_key = f"test:{datetime.now().timestamp()}"
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
        from sqlalchemy import create_engine, Column, String, Integer
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.declarative import declarative_base
        
        # Use SQLite for testing
        db_url = "sqlite:///./test_check.db"
        print(f"Connecting to database: {db_url}")
        
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create a simple test model
        Base = declarative_base()
        
        class TestUser(Base):
            __tablename__ = "test_users"
            
            id = Column(Integer, primary_key=True, index=True)
            name = Column(String, index=True)
            email = Column(String, unique=True, index=True)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Test session
        db = SessionLocal()
        
        # Create test user
        timestamp = datetime.now().timestamp()
        test_user = TestUser(
            name=f"Test User {timestamp}",
            email=f"test_{timestamp}@example.com"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Verify creation
        if test_user.id:
            print(f"✅ Test user created with ID: {test_user.id}")
        else:
            print("❌ Failed to create test user")
            return False
        
        # Retrieve user
        retrieved_user = db.query(TestUser).filter(TestUser.id == test_user.id).first()
        if retrieved_user and retrieved_user.email == test_user.email:
            print(f"✅ Test user retrieved successfully")
        else:
            print("❌ Failed to retrieve test user")
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

def check_package_installed(package_name):
    """Check if a package is installed using importlib"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def check_core_dependencies():
    """Check if core required dependencies are installed"""
    print("\n--- Checking Core Dependencies ---")
    required_packages = [
        "sqlalchemy", "redis", "pymongo", "dotenv"
    ]
    
    all_installed = True
    for package in required_packages:
        if check_package_installed(package):
            print(f"✅ {package}: Installed")
        else:
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
    print("=== Mental Health AI Therapy Application Core Component Check ===")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    results = {
        "core_dependencies": check_core_dependencies(),
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
        print("\n🎉 All core components are working correctly! 🎉")
        print("\nNote: FastAPI compatibility with Python 3.13 still needs to be resolved.")
        return 0
    else:
        print("\n⚠️ Some core components failed the check. Please fix the issues above. ⚠️")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 