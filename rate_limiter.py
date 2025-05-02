"""
Rate limiting implementation using Redis
"""

import logging
from datetime import timedelta
import redis
from config import Config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Handles rate limiting for bot users"""

    def __init__(self):
        """Initialize Redis connection and rate limit settings"""
        try:
            self.redis = redis.from_url(Config.REDIS_URL)
            self.limit = Config.RATE_LIMIT
            self.window = timedelta(minutes=1)
            logger.info("Rate limiter initialized")
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to initialize rate limiter: %s", e)
            raise

    def check_limit(self, user_id):
        """
        Check if user has exceeded rate limit
        Args:
            user_id: Telegram user ID
        Returns:
            bool: True if within limit, False if exceeded
        """
        try:
            key = f"rate_limit:{user_id}"
            current = self.redis.get(key)

            if current and int(current) >= self.limit:
                return False

            self.redis.incr(key, 1)
            if not current:
                self.redis.expire(key, int(self.window.total_seconds()))

            return True
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Rate limit check failed: %s", e)
            return True  # Fail open to avoid blocking users
