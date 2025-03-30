# Mental Health AI Therapy Web Application

A therapeutic web application that uses AI to provide mental health support through text, voice, and video interaction.

## Features

- User authentication (register, login, logout)
- Interactive therapy sessions
- Various therapy approaches (CBT, DBT, Mindfulness, etc.)
- Session types (Text, Voice, Video)
- Mood tracking
- Profile management
- Mobile-responsive design

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Redis (for session and message storage)
- SQLite (default database, can be replaced with PostgreSQL)

### Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/ai-therapy-app.git
cd ai-therapy-app
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install requirements
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a .env file in the root directory)
```
SECRET_KEY=your_secret_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
DATABASE_URL=sqlite:///./app.db
```

5. Create database tables
```bash
python create_tables.py
```

### Running the Application

#### Web Application (Flask)

```bash
python web_app.py
```

The web application will be available at http://localhost:8000

#### API Only (FastAPI)

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs

## Development

### Project Structure

- `web_app.py` - Flask web application with both UI and API endpoints
- `main.py` - FastAPI application (API only)
- `templates/` - HTML templates for the web interface
- `static/` - Static files (CSS, JavaScript, images)
- `app/` - Application modules
  - `core/` - Core functionality
  - `models/` - Database models
  - `api/` - API endpoints
  - `services/` - Business logic

### Database Models

- `User` - User account information
- `TherapySession` - Session details (type, approach, scheduling)
- `TherapyMessage` - Individual messages in a therapy session

## Deployment

### Docker

A Dockerfile is provided to containerize the application:

```bash
docker build -t ai-therapy-app .
docker run -p 8000:8000 ai-therapy-app
```

### Production Considerations

- Use a production-ready database (PostgreSQL)
- Configure Redis with password and SSL
- Set up proper logging
- Use a proper web server (Nginx/Apache) with Gunicorn/uWSGI

## Testing

Run tests with pytest:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bootstrap for UI components
- Chart.js for visualization
- FontAwesome for icons 