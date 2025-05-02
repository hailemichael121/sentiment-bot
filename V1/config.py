import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")