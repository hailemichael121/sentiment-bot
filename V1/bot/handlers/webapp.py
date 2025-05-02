from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler
import os


async def show_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send web app button with localhost URL"""
    webapp_url = os.getenv("WEB_APP_URL", "http://localhost:3000")

    await update.message.reply_text(
        "Open Team Portal (Local Development):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🌐 Open Local Portal",
                web_app=WebAppInfo(url=webapp_url))
        ]])
    )


def register_webapp_handlers(app):
    """Register webapp handlers"""
    app.add_handler(CommandHandler("portal", show_webapp))
