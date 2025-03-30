import logging
from app.db.session import engine
from app.models.base import Base
from app.models.user import User
from app.models.therapy import (
    TherapySession,
    TherapyMessage,
    MentalHealthData,
    UserActivity,
    CheckIn
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables() -> None:
    """
    Create all database tables
    """
    logger.info("Creating tables in database")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully")


if __name__ == "__main__":
    create_tables() 