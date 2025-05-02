"""
Enhanced Sentiment Analysis Telegram Bot

This bot automatically analyzes text sentiment in private chats without requiring commands.
For groups, it moderates toxic content. Includes rich UI with buttons and visual feedback.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import pytz

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo

)
import telegram
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler

)

from analyzer import TextAnalyzer
from database import Database
from config import Config
from rate_limiter import RateLimiter
from pymongo.errors import PyMongoError


db: Database = Database()

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
db = Database()
analyzer = TextAnalyzer()
rate_limiter = RateLimiter()

# Admin states for conversation handler
ADMIN_AUTH = range(1)

# Sentiment emoji mapping
SENTIMENT_EMOJIS = {
    "positive": "😊",
    "negative": "😞",
    "neutral": "😐",
    "toxic": "⚠️"
}

# Sentiment color mapping (for web interface)
SENTIMENT_COLORS = {
    "positive": "#4CAF50",  # Green
    "negative": "#F44336",  # Red
    "neutral": "#9E9E9E",   # Gray
    "toxic": "#FF9800"      # Orange
}


# In your start command:
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with web app button."""
    try:
        # Ensure the web app URL ends with a slash if needed
        webapp_url = f"{Config.WEBAPP_BASE_URL.rstrip('/')}/webapp"

        keyboard = [
            [InlineKeyboardButton(
                "🌐 Open Portfolio",
                web_app=WebAppInfo(url=webapp_url)
            )],
            [InlineKeyboardButton("📊 My Stats", callback_data="view_stats"),
             InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # For callback queries, we need to edit the message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text="Welcome to Sentiment Guard!",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Welcome to Sentiment Guard!",
                reply_markup=reply_markup
            )
    except telegram.error.BadRequest as e:
        logger.error("Web app URL issue: %s", e)
        error_msg = "Welcome to Sentiment Guard!\n\nWeb app currently unavailable. Please try again later."
        if update.callback_query:
            await update.callback_query.edit_message_text(text=error_msg)
        else:
            await update.message.reply_text(error_msg)


async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically analyze any text message sent to the bot."""
    # Check rate limit
    if not rate_limiter.check_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Please wait a moment before sending more messages.")
        return

    text = update.message.text

    # Skip if the message is a command or too short
    if text.startswith('/') or len(text.strip()) < 3:
        return

    # Show typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Analyze the text
    result = analyzer.analyze(text)
    sentiment = result['sentiment']
    confidence = result['confidence'] * 100

    # Prepare the response
    emoji = SENTIMENT_EMOJIS.get(sentiment, "🤔")
    # color = SENTIMENT_COLORS.get(sentiment, "#9E9E9E")

    if sentiment == "toxic":
        response = (
            f"⚠️ <b>Toxic Content Detected</b> ⚠️\n\n"
            f"🔍 <i>\"{truncate_text(text, 100)}\"</i>\n\n"
            f"🚫 Classification: <b>Toxic content</b>\n"
            f"📈 Confidence: <b>{confidence:.1f}%</b>\n\n"
            f"<i>This type of content may violate community guidelines.</i>"
        )
    else:
        response = (
            f"✨ <b>Sentiment Analysis Result</b> ✨\n\n"
            f"🔍 <i>\"{truncate_text(text, 100)}\"</i>\n\n"
            f"🎭 Sentiment: <b>{sentiment.capitalize()} {emoji}</b>\n"
            f"📈 Confidence: <b>{confidence:.1f}%</b>\n\n"
            f"<i>Keep the conversation positive! {SENTIMENT_EMOJIS['positive']}</i>"
        )

    # Log the message
    log_user_message(update, text, result)

    # Send the response with a custom reply markup
    try:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📊 View My Stats", callback_data="view_stats")],
            [InlineKeyboardButton("🌐 Open Dashboard",
                                  web_app=WebAppInfo(url=Config.WEBAPP_BASE_URL))]
        ])
    except telegram.error.BadRequest as e:
        logger.warning("Web app URL configuration issue: %s", e)
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📊 View My Stats", callback_data="view_stats")]
        ])

    await update.message.reply_text(
        response,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def log_user_message(update: Update, text: str, result: dict) -> None:
    """Log user message to database."""
    user = update.effective_user
    db.log_message({
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "chat_id": update.effective_chat.id,
        "message_id": update.message.message_id,
        "text": text,
        "sentiment": result['sentiment'],
        "confidence": result['confidence'],
        "is_toxic": result.get('is_toxic', False),
        "timestamp": datetime.now(pytz.utc),
        "is_group": update.effective_chat.type != "private"
    })


async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's sentiment statistics."""
    try:
        # Handle both command and callback query
        if update.callback_query:
            chat_id = update.callback_query.message.chat.id
            message_id = update.callback_query.message.message_id
        else:
            chat_id = update.effective_chat.id
            message_id = None

        stats = db.get_user_stats(chat_id)

        if not stats:
            response = "❌ Could not retrieve your stats."
        else:
            response = (
                "📊 <b>Your Sentiment Statistics</b>\n\n"
                f"📝 Total Messages: {stats['total']}\n"
                f"😊 Positive: {stats['positive']}\n"
                f"😞 Negative: {stats['negative']}\n"
                f"😐 Neutral: {stats['neutral']}\n"
                f"⚠️ Flagged: {stats['toxic']}"
            )

        if update.callback_query:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=response,
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=response,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error("Error in user_stats: %s", e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Failed to load statistics. Please try again later."
        )


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle and moderate messages in groups with visual feedback."""
    if not rate_limiter.check_limit(update.effective_user.id):
        return  # Silently ignore rate-limited messages in groups

    text = update.message.text
    if not text or text.startswith('/'):
        return

    result = analyzer.analyze(text)
    log_user_message(update, text, result)

    # Take action if toxic
    if result['sentiment'] == 'toxic':
        try:
            # Delete the toxic message
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )

            # Send a warning with visual feedback
            warning_msg = (
                f"⚠️ <b>Content Moderation Alert</b> ⚠️\n\n"
                f"A message from @{update.effective_user.username or update.effective_user.first_name} "
                f"was removed for violating community guidelines.\n\n"
                f"🔍 <i>\"{truncate_text(text, 100)}\"</i>\n\n"
                f"🚫 Classification: <b>Toxic content</b>\n"
                f"📈 Confidence: <b>{result['confidence']*100:.1f}%</b>\n\n"
                f"<i>Let's keep this conversation positive! {SENTIMENT_EMOJIS['positive']}</i>"
            )

            # Send the warning with a nice design
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=warning_msg,
                parse_mode=ParseMode.HTML
            )

            # Notify admin with more details
            if Config.ADMIN_USERNAME:
                admin_msg = (
                    f"🚨 <b>Toxic Message Deleted</b>\n\n"
                    f"<b>Group:</b> {update.effective_chat.title}\n"
                    f"<b>User:</b> @{update.effective_user.username or update.effective_user.first_name}\n"
                    f"<b>Content:</b> {truncate_text(text, 200)}\n"
                    f"<b>Confidence:</b> {result['confidence']*100:.1f}%\n\n"
                    f"<i>Message was automatically removed by the moderation system.</i>"
                )

                await context.bot.send_message(
                    chat_id=Config.ADMIN_USERNAME,
                    text=admin_msg,
                    parse_mode=ParseMode.HTML
                )
        except telegram.error.TelegramError as e:
            logger.error("Failed to handle toxic message: %s", e)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message with rich formatting."""
    help_text = (
        "🤖 <b>Sentiment Analysis Bot Help</b> 🤖\n\n"
        "I automatically analyze the sentiment of text messages in private chats. "
        "In groups, I moderate toxic content to maintain positive discussions.\n\n"
        "<b>How to use:</b>\n"
        "1. In private chat: Just send me any text message\n"
        "2. In groups: I'll automatically moderate toxic content\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Show welcome message\n"
        "/stats - View your sentiment statistics\n"
        "/help - Show this help message\n\n"
        "<i>No need to use commands for analysis - just send normal messages!</i>"
    )

    # Add a button to open the web dashboard
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Open Web Dashboard",
                              web_app=WebAppInfo(url=Config.WEBAPP_BASE_URL))]
    ])

    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()  # Important: always answer callback queries

    try:
        if query.data == "view_stats":
            await user_stats(update, context)
        elif query.data == "refresh_stats":
            await query.edit_message_text(text="🔄 Refreshing your statistics...")
            await user_stats(update, context)
        elif query.data == "help":
            await help_command(update, context)
    except Exception as e:
        logger.error("Error in button handler: %s", e)
        await query.edit_message_text(text="⚠️ An error occurred. Please try again.")


async def send_weekly_report(context: CallbackContext, specific_user: Optional[int] = None) -> None:
    """Send weekly report to admin or specific user."""
    target_user = specific_user or Config.ADMIN_USERNAME
    if not target_user:
        return

    try:
        # Get stats for the past week
        now = datetime.now(pytz.utc)
        week_ago = now - timedelta(days=7)

        # This would query your database for actual stats in a real implementation
        stats = {
            "total_messages": db.get_message_count(since=week_ago, user_id=specific_user),
            "positive_messages": db.get_sentiment_count("positive", since=week_ago, user_id=specific_user),
            "negative_messages": db.get_sentiment_count("negative", since=week_ago, user_id=specific_user),
            "toxic_messages": db.get_sentiment_count("toxic", since=week_ago, user_id=specific_user),
            "groups_active": db.get_active_group_count(since=week_ago)
        }

        if specific_user:
            report = (
                "📅 <b>Your Weekly Sentiment Report</b> 📅\n\n"
                f"📝 <b>Messages analyzed:</b> {stats['total_messages']}\n"
                f"😊 <b>Positive:</b> {stats['positive_messages']}\n"
                f"😞 <b>Negative:</b> {stats['negative_messages']}\n"
                f"⚠️ <b>Flagged:</b> {stats['toxic_messages']}\n\n"
                f"<i>Time period: {week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}</i>"
            )
        else:
            report = (
                "📅 <b>Weekly Moderation Report</b> 📅\n\n"
                f"📝 <b>Total messages analyzed:</b> {stats['total_messages']}\n"
                f"😊 <b>Positive:</b> {stats['positive_messages']}\n"
                f"😞 <b>Negative:</b> {stats['negative_messages']}\n"
                f"⚠️ <b>Toxic messages detected:</b> {stats['toxic_messages']}\n"
                f"👥 <b>Active groups monitored:</b> {stats['groups_active']}\n\n"
                f"<i>Time period: {week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}</i>"
            )

        await context.bot.send_message(
            chat_id=target_user,
            text=report,
            parse_mode=ParseMode.HTML
        )
    except (PyMongoError, telegram.error.TelegramError) as e:
        logger.error("Failed to send weekly report: %s", e)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Properly handle errors with awaited coroutines."""
    logger.error("Update %s caused error %s", update, context.error)

    if isinstance(update, Update) and update.effective_chat:
        text = (
            "⚠️ <b>Oops! Something went wrong</b>\n\n"
            "Our team has been notified about this issue. "
            "Please try again in a few moments.\n\n"
            "<i>If the problem persists, contact support.</i>"
        )

        try:
            # Add await here
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error("Failed to send error message: %s", e)


async def main():
    """Initialize and run the Telegram bot with retries and proper handler setup."""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            application = (
                Application.builder()
                .token(Config.TELEGRAM_TOKEN)
                .read_timeout(30)
                .write_timeout(30)
                .connect_timeout(30)
                .pool_timeout(30)
                .build()
            )

            # 1. Command handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("stats", user_stats))
            application.add_handler(CommandHandler("help", help_command))

            # 2. Callback query handler
            application.add_handler(CallbackQueryHandler(button_handler))

            # 3. Message handlers
            application.add_handler(MessageHandler(
                filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
                analyze_message
            ))
            application.add_handler(MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
                handle_group_message
            ))

            # 4. Error handler
            application.add_error_handler(error_handler)

            # 5. Job queue for weekly reports
            if Config.ADMIN_USERNAME:
                application.job_queue.run_repeating(
                    send_weekly_report,
                    interval=timedelta(weeks=1).total_seconds(),
                    first=0
                )

            # Start the bot
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            logger.info("Bot started successfully ✅")

            # Keep the bot running
            while True:
                await asyncio.sleep(3600)

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                logger.critical("Max retries reached. Exiting...")
                raise
            await asyncio.sleep(5 * (attempt + 1))

if __name__ == '__main__':
    main()
