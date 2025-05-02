import socket
import urllib3
from urllib3.util.connection import allowed_gai_family

# Force IPv4 for all connections
def _create_connection(address, *args, **kwargs):
    family = allowed_gai_family()
    host, port = address
    return socket.create_connection(
        (host, port),
        timeout=5,
        family=socket.AF_INET
    )

urllib3.util.connection.create_connection = _create_connection
#!/usr/bin/env python3
"""
Sentiment Analysis Telegram Bot
- Analyzes text sentiment (Positive/Neutral/Negative)
- Detects harmful content (offensive/terrorism-related)
- Provides group moderation features
- Includes rate limiting and clean UI
"""

import time
from typing import Dict, List

from loguru import logger
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from sentiment import SentimentAnalyzer
from config import Config


# Initialize analyzer
analyzer = SentimentAnalyzer()

# Configure logging
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    level=Config.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Rate limiting configuration
RATE_LIMIT = 5  # Max requests per minute
user_requests: Dict[int, List[float]] = {}

# Modern UI Keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🔍 Analyze Sentiment"],
        ["ℹ️ Help", "📊 Stats"]
    ],
    resize_keyboard=True,
    input_field_placeholder="Type a message or choose an option..."
)


def format_response(result: Dict) -> str:
    """Creates a clean, formatted response for sentiment analysis."""
    response = (
        "🔍 <b>Analysis Result</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Sentiment</b>: {result['label']}\n"
        f"📊 <b>Scores</b>:\n"
        f"- Positive: {result['scores']['pos']:.2f}\n"
        f"- Neutral: {result['scores']['neu']:.2f}\n"
        f"- Negative: {result['scores']['neg']:.2f}"
    )

    if result["harmful"]["is_offensive"]:
        response += "\n\n⚠️ <b>Warning</b>: Offensive content detected!"

    if result["harmful"]["is_terrorism"]:
        response += "\n\n🚨 <b>ALERT</b>: Terrorism-related content!"

    return response


async def check_rate_limit(user_id: int) -> bool:
    """Check if user is within rate limit."""
    now = time.time()

    # Clear old requests (>1 minute)
    if user_id in user_requests:
        user_requests[user_id] = [
            t for t in user_requests[user_id] if now - t < 60]
    else:
        user_requests[user_id] = []

    if len(user_requests[user_id]) >= RATE_LIMIT:
        return False

    user_requests[user_id].append(now)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with interactive keyboard."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 <b>Hi {user.first_name}!</b> I'm your Sentiment Analysis Bot.\n\n"
        "I can:\n"
        "• Analyze text sentiment\n"
        "• Detect harmful content\n"
        "• Moderate groups\n\n"
        "Try sending a message or use the buttons below!",
        reply_markup=MAIN_KEYBOARD
    )


async def analyze_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sentiment analysis with rate limiting."""
    user_id = update.effective_user.id

    # Check rate limit
    if not await check_rate_limit(user_id):
        await update.message.reply_text(
            "⏳ Too many requests! Please wait 1 minute.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    text = update.message.text
    logger.info(f"Analyzing message from {user_id}: {text}")

    try:
        result = analyzer.analyze(text)
        response = format_response(result)
        await update.message.reply_html(
            response,
            reply_markup=MAIN_KEYBOARD
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await update.message.reply_text(
            "❌ Error processing your request. Please try again.",
            reply_markup=MAIN_KEYBOARD
        )


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-delete harmful content in groups."""
    if update.message.chat.type not in ["group", "supergroup"]:
        return

    try:
        result = analyzer.analyze(update.message.text)

        if result["harmful"]["is_terrorism"]:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=update.message.chat.id,
                text="🚨 <b>ALERT</b>: Removed terrorism-related content.",
                parse_mode=ParseMode.HTML
            )
        elif result["harmful"]["is_offensive"]:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=update.message.chat.id,
                text="⚠️ Removed offensive message. Please be respectful.",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Group moderation error: {e}")


async def post_init(application: Application) -> None:
    """Set bot commands after initialization."""
    commands = [
        ("start", "Start the bot"),
        ("scan", "Analyze text sentiment"),
        ("stats", "View your usage statistics"),
        ("help", "Show help information")
    ]
    await application.bot.set_my_commands(commands)


def main() -> None:
    """Run the bot."""
    # Create Application
    app = Application.builder() \
        .token(Config.TOKEN) \
        .post_init(post_init) \
        .build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, analyze_text))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS, handle_group_message))

    # Start bot
    logger.info("Starting bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
# This is the main entry point for the bot.
