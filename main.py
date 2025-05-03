"""
Main application module for the Sentiment Analysis Bot API.

This module sets up the FastAPI application and integrates the Telegram bot.
It handles the web interface, static files, and bot initialization with proper error handling.
"""

import asyncio
import logging

import multiprocessing
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import telegram.error
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sentiment Analysis Bot API")


# Serve static files for a future frontend (like a landing page)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- HTML HOMEPAGE ----------------


@app.get("/", response_class=HTMLResponse)
async def read_root() -> HTMLResponse:
    """Render the homepage with information about the bot.

    Returns:
        HTMLResponse: The rendered homepage HTML
    """
    try:
        bot_username = Config.BOT_USERNAME or "SentimentGuardbot"
        html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Sentiment Analysis Bot</title>
                <meta name="description" content="AI-powered Telegram bot to analyze text sentiment.">
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
                <style>
                    :root {{
                        --bg: #ffffff;
                        --text: #1f1f1f;
                        --card: #f4f4f4;
                    }}
                    body.dark {{
                        --bg: #121212;
                        --text: #ffffff;
                        --card: #1e1e1e;
                    }}
                    body {{
                        font-family: 'Inter', sans-serif;
                        background: var(--bg);
                        color: var(--text);
                        margin: 0;
                        padding: 0;
                        transition: all 0.3s ease;
                    }}
                    header {{
                        background-color: #4a90e2;
                        padding: 3rem 2rem;
                        text-align: center;
                        color: white;
                    }}
                    .toggle {{
                        position: absolute;
                        top: 10px;
                        right: 20px;
                        cursor: pointer;
                        background: #333;
                        color: white;
                        padding: 6px 12px;
                        border-radius: 10px;
                        font-size: 0.85rem;
                    }}
                    main {{
                        max-width: 1000px;
                        margin: 2rem auto;
                        padding: 0 1rem;
                    }}
                    section {{
                        margin-bottom: 3rem;
                        background: var(--card);
                        padding: 2rem;
                        border-radius: 12px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                    }}
                    h1, h2 {{
                        text-align: center;
                    }}
                    ul {{
                        line-height: 1.7;
                    }}
                    .telegram-btn {{
                        display: inline-block;
                        margin-top: 1.5rem;
                        background: #0088cc;
                        color: white;
                        padding: 12px 20px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                    .devs {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                        gap: 1.5rem;
                    }}
                    .card {{
                        background: var(--bg);
                        padding: 1.2rem;
                        border-radius: 12px;
                        text-align: center;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    }}
                    .card img {{
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        object-fit: cover;
                        margin-bottom: 1rem;
                    }}
                    .socials a {{
                        margin: 0 0.3rem;
                        text-decoration: none;
                        color: #4a90e2;
                        font-size: 1.2rem;
                    }}
                    footer {{
                        text-align: center;
                        font-size: 0.9rem;
                        color: #888;
                        margin: 3rem 0 1rem;
                    }}
                </style>
            </head>
            <body>
                <div class="toggle" onclick="toggleDark()">🌗 Toggle Dark Mode</div>
                <header>
                    <h1>🤖 Sentiment Analysis Bot</h1>
                    <p>Understand emotions from text instantly using AI + Telegram</p>
                    <a class="telegram-btn" href="https://t.me/{bot_username}" target="_blank">
                        🔗 Chat with the Bot
                    </a>
                </header>
                <main>
                    <section>
                        <h2>💡 About This Project</h2>
                        <p>This project is a Telegram bot that analyzes the sentiment of messages sent to it using AI and natural language processing techniques. It uses FastAPI for the backend and integrates machine learning for sentiment classification.</p>
                        <ul>
                            <li>🔍 Real-time sentiment detection (positive, neutral, negative)</li>
                            <li>💬 Telegram integration for fast user interaction</li>
                            <li>⚡ FastAPI-powered API backend</li>
                            <li>🧠 Scikit-learn / HuggingFace based AI model</li>
                        </ul>
                    </section>

                    <section>
                        <h2>👥 Developer Team</h2>
                        <div class="devs">
                            <div class="card">
                                <img src="https://via.placeholder.com/100x100.png?text=Selihom" alt="Selihom Demeke">
                                <h3>Selihom Demeke</h3>
                                <p>Ets1159/13</p>
                                <div class="socials">
                                    <a href="#"><i class="fab fa-telegram"></i></a>
                                    <a href="#"><i class="fab fa-github"></i></a>
                                </div>
                            </div>
                            <div class="card">
                                <img src="https://via.placeholder.com/100x100.png?text=Yihuna" alt="Yihun Shikuri">
                                <h3>Yihun Shikuri</h3>
                                <p>Ets1317/13</p>
                                <div class="socials">
                                    <a href="https://t.me/YihunaDeacon"><i class="fab fa-telegram"></i></a>
                                    <a href="https://github.com/yihunash"><i class="fab fa-github"></i></a>
                                </div>
                            </div>
                            <div class="card">
                                <img src="https://via.placeholder.com/100x100.png?text=Yodahe" alt="Yodahe Ketema">
                                <h3>Yodahe Ketema</h3>
                                <p>Ets1328/13</p>
                                <div class="socials">
                                    <a href="#"><i class="fab fa-telegram"></i></a>
                                    <a href="#"><i class="fab fa-github"></i></a>
                                </div>
                            </div>
                            <div class="card">
                                <img src="https://via.placeholder.com/100x100.png?text=YordanosS" alt="Yordanos Seyoum">
                                <h3>Yordanos Seyoum</h3>
                                <p>Ets1371/13</p>
                                <div class="socials">
                                    <a href="#"><i class="fab fa-telegram"></i></a>
                                    <a href="#"><i class="fab fa-github"></i></a>
                                </div>
                            </div>
                            <div class="card">
                                <img src="https://via.placeholder.com/100x100.png?text=YordanosY" alt="Yordanos Yirgu">
                                <h3>Yordanos Yirgu</h3>
                                <p>Ets1374/13</p>
                                <div class="socials">
                                    <a href="#"><i class="fab fa-telegram"></i></a>
                                    <a href="#"><i class="fab fa-github"></i></a>
                                </div>
                            </div>
                        </div>
                    </section>
                </main>
                <footer>
                    © 2025 Sentiment Sensei | Developed by Group-4 of Software Engineering 💻
                </footer>
                <script>
                    function toggleDark() {{
                        document.body.classList.toggle('dark');
                    }}
                </script>
            </body>
            </html>
            """

        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error rendering homepage: %s", e)
        return HTMLResponse(content="<h1>Internal Server Error</h1>", status_code=500)

# ---------------- TELEGRAM BOT RUNNER ----------------


async def run_bot() -> None:
    """Initialize and run the Telegram bot with enhanced error handling."""
    from bot import main  # pylint: disable=import-outside-toplevel

    max_retries = 5
    base_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            logger.info("Attempting to start bot (attempt %d/%d)",
                        attempt + 1, max_retries)
            await main()
            logger.info("Bot started successfully")
            return

        except telegram.error.TimedOut as e:
            wait_time = base_delay * (attempt + 1)
            logger.warning(
                "Bot connection timed out. Retrying in %s seconds... Error: %s",
                wait_time, str(e)
            )
            await asyncio.sleep(wait_time)

        except telegram.error.NetworkError as e:
            logger.error("Network error occurred: %s", str(e))
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay)
            else:
                logger.error("Max network retries reached")
                return  # Don't exit, just stop trying

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Unexpected error in bot: %s", str(e))
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay)
            else:
                logger.error("Max retries reached for unexpected error")
                return

    logger.error("Failed to start bot after %d attempts", max_retries)


@app.get("/webapp", response_class=HTMLResponse)
async def web_app():
    """Serve the web app interface"""
    return FileResponse("static/webapp/index.html")


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler that launches the Telegram bot."""
    asyncio.create_task(run_bot())


# ---------------- GLOBAL ERROR HANDLERS ----------------


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"message": "Not Found"}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )

# ---------------- RUN LOCALLY ----------------


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
