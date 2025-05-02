"""
MongoDB operations for sentiment analysis bot
"""

import logging
from datetime import datetime
from pymongo import MongoClient
import pymongo
from config import Config

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations"""

    def __init__(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client.get_database()
            logger.info("Connected to MongoDB successfully")
        except (pymongo.errors.PyMongoError, ValueError, KeyError) as e:
            logger.error("Failed to connect to MongoDB: %s", e)
            raise

    def get_message_count(self, since=None, user_id=None):
        """Get count of messages optionally filtered by date and user"""
        query = {}
        if since:
            query["timestamp"] = {"$gte": since}
        if user_id:
            query["user_id"] = user_id
        return self.db.messages.count_documents(query)

    def get_sentiment_count(self, sentiment, since=None, user_id=None):
        """Get count of messages with a specific sentiment"""
        query = {"sentiment": sentiment}
        if since:
            query["timestamp"] = {"$gte": since}
        if user_id:
            query["user_id"] = user_id
        return self.db.messages.count_documents(query)

    def get_active_group_count(self, since=None):
        """Get the count of active groups"""
        pipeline = [
            {"$match": {"is_group": True}},
            {"$group": {"_id": "$chat_id"}},
            {"$count": "count"}
        ]
        if since:
            pipeline[0]["$match"]["timestamp"] = {"$gte": since}
        result = list(self.db.messages.aggregate(pipeline))
        return result[0]["count"] if result else 0

    def log_message(self, message_data):
        """Log a message to the database"""
        try:
            message_data["timestamp"] = datetime.utcnow()
            self.db.messages.insert_one(message_data)
        except (pymongo.errors.PyMongoError, TypeError, ValueError) as e:
            logger.error("Failed to log message: %s", e)

    def get_user_stats(self, user_id):
        """Get sentiment statistics for a user"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
            ]
            results = list(self.db.messages.aggregate(pipeline))

            stats = {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "toxic": 0
            }

            for result in results:
                stats[result["_id"]] = result["count"]
                stats["total"] += result["count"]

            return stats
        except (TypeError, ValueError, KeyError) as e:
            logger.error("Failed to get user stats: %s", e)
            return None

    def get_group_stats(self, group_id):
        """Get sentiment statistics for a group"""
        try:
            pipeline = [
                {"$match": {"chat_id": group_id}},
                {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
            ]
            results = list(self.db.messages.aggregate(pipeline))

            stats = {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "toxic": 0
            }

            for result in results:
                stats[result["_id"]] = result["count"]
                stats["total"] += result["count"]

            return stats
        except (pymongo.errors.PyMongoError, TypeError, ValueError, KeyError) as e:
            logger.error("Failed to get group stats: %s", e)
            return None

    def add_admin_action(self, action_data):
        """Log an admin action to the database"""
        try:
            action_data["timestamp"] = datetime.utcnow()
            self.db.admin_actions.insert_one(action_data)
            return True
        except (pymongo.errors.PyMongoError, TypeError, ValueError) as e:
            logger.error("Failed to log admin action: %s", e)
            return False
