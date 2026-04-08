"""
MongoDB connection setup using Motor + Beanie ODM.
"""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.db.models import Campaign, EmailLog, UserToken

_client: AsyncIOMotorClient | None = None

# All Beanie document models to register
ALL_MODELS = [Campaign, EmailLog, UserToken]


async def init_db() -> None:
    """
    Initialise the Motor client and Beanie ODM.

    Called once during application startup via the lifespan context manager.
    """
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=ALL_MODELS,
    )


async def close_db() -> None:
    """Close the Motor client. Called on application shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_client() -> AsyncIOMotorClient | None:
    """Return the current Motor client instance."""
    return _client
