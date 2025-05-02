from transformers import pipeline
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

# Initialize sentiment analyzer
try:
    analyzer = pipeline(
        "text-classification",
        model="finiteautomata/bertweet-base-sentiment-analysis"
    )
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise


async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text analysis requests"""
    text = update.message.text
    try:
        result = analyzer(text)[0]
        await update.message.reply_text(
            f"🧠 Analysis Result:\n"
            f"Label: {result['label']}\n"
            f"Confidence: {result['score']:.2f}"
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        await update.message.reply_text("❌ Analysis failed. Please try again.")


def register_analysis_handlers(app):
    """Register analysis handlers"""
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, analyze_message))
    logger.info("Analysis handlers registered.")
