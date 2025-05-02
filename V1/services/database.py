import os
from pymongo import MongoClient
from loguru import logger


class Database:
    """MongoDB connection handler"""
    _client = None

    @classmethod
    async def init_db(cls):
        """Initialize database connection"""
        try:
            cls._client = MongoClient(os.getenv("MONGO_URI"))
            logger.success("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    @classmethod
    def get_db(cls):
        """Get database instance"""
        if not cls._client:
            raise RuntimeError("Database not initialized")
        return cls._client.sentiment_bot
