from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users, sessions, health_data, check_ins, voice, video

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["therapy sessions"])
api_router.include_router(health_data.router, prefix="/health-data", tags=["health data"])
api_router.include_router(check_ins.router, prefix="/check-ins", tags=["check-ins"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice interface"])
api_router.include_router(video.router, prefix="/video", tags=["video sessions"]) 