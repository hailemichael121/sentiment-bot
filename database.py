"""
MongoDB operations for sentiment analysis bot
"""

import os
import logging
from datetime import datetime
from pymongo import MongoClient, errors as pymongo_errors
from config import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Database:
    """Handles all MongoDB operations for the bot."""

    def __init__(self):
        """Initialize the MongoDB client and database."""
        try:
            self.client = MongoClient(Config.MONGODB_URI)

            # Determine the database name
            db_name = self._extract_db_name(
                Config.MONGODB_URI) or os.getenv("MONGODB_NAME")

            if not db_name:
                raise ValueError(
                    "No MongoDB database name provided in URI/MONGODB_NAME environment variable.")

            self.db = self.client[db_name]
            logger.info("Connected to MongoDB database: %s", db_name)

        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception("Failed to initialize MongoDB: %s", e)
            raise

    @staticmethod
    def _extract_db_name(uri: str) -> str | None:
        """Extract default DB name from Mongo URI, if present."""
        try:
            path = uri.split(".net/", 1)[-1]
            db_name = path.split("?", 1)[0]
            return db_name if db_name else None
        except (pymongo_errors.PyMongoError, ValueError, KeyError):
            return None

    def log_message(self, message_data: dict):
        """Insert a message into the database."""
        try:
            message_data["timestamp"] = datetime.utcnow()
            self.db.messages.insert_one(message_data)
        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception("Failed to log message: %s", e)

    def get_message_count(self, since=None, user_id=None):
        """Count all messages (optionally filtered)."""
        try:
            query = {}
            if since:
                query["timestamp"] = {"$gte": since}
            if user_id:
                query["user_id"] = user_id
            return self.db.messages.count_documents(query)
        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception("Failed to count messages: %s ", e)
            return 0

    def get_sentiment_count(self, sentiment, since=None, user_id=None):
        """Count messages with a specific sentiment."""
        try:
            query = {"sentiment": sentiment}
            if since:
                query["timestamp"] = {"$gte": since}
            if user_id:
                query["user_id"] = user_id
            return self.db.messages.count_documents(query)
        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception(
                "Failed to count sentiment '%s': %s", sentiment, e)
            return 0

    def get_active_group_count(self, since=None):
        """Count unique active group chats."""
        try:
            match_stage = {"is_group": True}
            if since:
                match_stage["timestamp"] = {"$gte": since}

            pipeline = [
                {"$match": match_stage},
                {"$group": {"_id": "$chat_id"}},
                {"$count": "count"}
            ]
            result = list(self.db.messages.aggregate(pipeline))
            return result[0]["count"] if result else 0
        except pymongo_errors.PyMongoError as e:
            logger.exception("Failed to count active groups: %s", e)
            return 0

    def get_user_stats(self, user_id):
        """Get sentiment distribution for a user."""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
            ]
            results = list(self.db.messages.aggregate(pipeline))

            stats = {k: 0 for k in ["positive",
                                    "negative", "neutral", "toxic"]}
            stats["total"] = 0

            for r in results:
                sentiment = r["_id"]
                count = r["count"]
                stats[sentiment] = count
                stats["total"] += count

            return stats
        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception("Failed to get user stats: %s", e)
            return None

    def get_group_stats(self, group_id):
        """Get sentiment distribution for a group."""
        try:
            pipeline = [
                {"$match": {"chat_id": group_id}},
                {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
            ]
            results = list(self.db.messages.aggregate(pipeline))

            stats = {k: 0 for k in ["positive",
                                    "negative", "neutral", "toxic"]}
            stats["total"] = 0

            for r in results:
                sentiment = r["_id"]
                count = r["count"]
                stats[sentiment] = count
                stats["total"] += count

            return stats
        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception("Failed to get group stats: %s", e)
            return None

    def add_admin_action(self, action_data: dict) -> bool:
        """Log an admin action into the database."""
        try:
            action_data["timestamp"] = datetime.utcnow()
            self.db.admin_actions.insert_one(action_data)
            return True
        except (pymongo_errors.PyMongoError, ValueError, KeyError) as e:
            logger.exception("Failed to log admin action: %s", e)
            return False
