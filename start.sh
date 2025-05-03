#!/bin/bash
# Start both FastAPI and Telegram bot
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &
python3 -m bot &
wait -n