"""
Configuration settings for sentiment analysis bot
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class"""

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    MONGODB_URI = os.getenv("MONGODB_URI")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    REDIS_URL = os.getenv("REDIS_URL")
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))
    WEBAPP_BASE_URL = os.getenv("WEBAPP_BASE_URL")
    BOT_USERNAME = os.getenv("SENTIMENT_BOT_USERNAME")
