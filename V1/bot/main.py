import os
import asyncio
from fastapi import FastAPI
from telegram.ext import ApplicationBuilder
from services.database import init_db
from handlers import register_handlers
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Sentiment Analysis Bot API")
bot = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize services and start the bot"""
    await init_db()
    register_handlers(bot)
    await bot.initialize()
    asyncio.create_task(bot.start())


@app.get("/health")
async def health_check():
    """Endpoint for health checks"""
    return {"status": "healthy", "bot": "running"}
