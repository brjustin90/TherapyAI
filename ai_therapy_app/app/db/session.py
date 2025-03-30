from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
import redis
import os

from app.core.config import settings

# Use SQLite instead of PostgreSQL for local development
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB Client
mongo_client = MongoClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB]

# Redis Client - Updated for Upstash Redis
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    ssl=settings.REDIS_SSL
)

# SQLAlchemy Base Model
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# MongoDB Dependency
def get_mongo_db():
    try:
        yield mongo_db
    finally:
        pass  # MongoDB connection is managed by the client


# Redis Dependency
def get_redis():
    try:
        yield redis_client
    finally:
        pass  # Redis connection is managed by the client 