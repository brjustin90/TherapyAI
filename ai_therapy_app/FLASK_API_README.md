# Flask API for Mental Health AI Therapy Application

This is a temporary Flask API implementation to provide core functionality until the FastAPI compatibility issues with Python 3.13 are resolved.

## Overview

This minimal Flask API provides the essential endpoints needed for the Mental Health AI Therapy application:

- User authentication (register, login)
- Therapy session management
- Voice chat interaction with Redis-based conversation history
- Health checks and diagnostics

## Getting Started

### Prerequisites

- Python 3.8+
- Redis (we're using Upstash Redis)
- SQLite (can be upgraded to PostgreSQL for production)

### Installation

1. Install dependencies:
   ```
   pip install flask flask-cors redis sqlalchemy python-dotenv
   ```

2. Make sure your `.env` file is configured with:
   ```
   REDIS_HOST=your-redis-host
   REDIS_PORT=6379
   REDIS_PASSWORD=your-redis-password
   REDIS_SSL=True
   SECRET_KEY=your-secret-key
   ```

### Running the API

1. Start the Flask server:
   ```
   python flask_app.py
   ```

2. The API will be available at `http://localhost:8000`

## API Endpoints

### Basic Endpoints

- `GET /` - Welcome message and API info
- `GET /health` - Health check status of components

### User Endpoints

- `POST /api/v1/users/register` - Register a new user
  - Body: `{"email": "user@example.com", "password": "password123", "full_name": "User Name"}`

- `POST /api/v1/users/login` - Login and get token
  - Body: `{"email": "user@example.com", "password": "password123"}`

- `GET /api/v1/users/me` - Get current user info
  - Header: `Authorization: Bearer your_token`

### Session Endpoints

- `POST /api/v1/sessions` - Create a new therapy session
  - Header: `Authorization: Bearer your_token`
  - Body: 
    ```
    {
        "session_type": "VOICE", 
        "therapy_approach": "CBT",
        "scheduled_start": "2025-03-09T12:00:00",
        "scheduled_end": "2025-03-09T13:00:00",
        "title": "Anxiety Session"
    }
    ```

- `GET /api/v1/sessions` - Get all sessions for current user
  - Header: `Authorization: Bearer your_token`

- `GET /api/v1/sessions/{session_id}` - Get a specific session
  - Header: `Authorization: Bearer your_token`

### Voice Chat Endpoint

- `POST /api/v1/voice/chat` - Send a message and get AI response
  - Header: `Authorization: Bearer your_token`
  - Body: `{"user_message": "I'm feeling anxious today", "session_id": 1}`

### Testing Endpoint

- `GET /api/v1/redis-test` - Test Redis connection

## Testing

Run the tests with:
```
python -m unittest tests/test_flask_api.py
```

## Limitations

This is a simplified implementation with some missing features:

1. Password hashing is currently disabled (plaintext for demo)
2. JWT token generation is simplified
3. No actual AI integration - responses are simulated
4. Limited error handling

## Transitioning to FastAPI

Once FastAPI compatibility issues with Python 3.13 are resolved, you should:

1. Migrate endpoints from Flask to FastAPI
2. Implement proper Pydantic schemas
3. Use FastAPI's dependency injection system
4. Update tests to use FastAPI's TestClient

The database models and Redis integration can be kept mostly the same during the transition. 