import uvicorn
import httpx
import os
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router
from app.services.telegram import TelegramBotService
from app.config import API_HOST, API_PORT, TELEGRAM_API_TOKEN
from app import __version__

# Set up logging
logger = logging.getLogger(__name__)

# Global Telegram service instance
telegram_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    global telegram_service
    
    # Log version at startup
    print(f"=== CaliBOT Starting ===")
    print(f"Version: {__version__}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Backend URL: {os.getenv('BACKEND_URL', 'http://localhost:8060')}")
    logger.info(f"CaliBOT v{__version__} starting up")
    
    # Startup: Initialize Telegram bot service
    telegram_service = TelegramBotService()
    telegram_service.start()
    print("Telegram bot started...")
    
    # Set up Telegram webhook
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8060")
    WEBHOOK_URL = f"{backend_url}/webhook"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/setWebhook",
            params={"url": WEBHOOK_URL}
        )
        if response.status_code != 200 or not response.json().get("ok"):
            print(f"Error setting webhook: {response.status_code} - {response.text}")
            print("Continuing with polling method...")

    # Send deployment notification
    try:
        from app.services.deployment_monitor import notify_deployment_ready
        await notify_deployment_ready()
    except Exception as e:
        logger.warning(f"Failed to send deployment notification: {e}")

    yield  # Hand control back to FastAPI

    # Shutdown: Clean up Telegram service
    if telegram_service:
        telegram_service.stop()
        print("Telegram bot stopped...")
    
    # Remove webhook on shutdown
    async with httpx.AsyncClient() as client:
        await client.get(f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/deleteWebhook")

app = FastAPI(title="Calendar AI Agent", lifespan=lifespan)
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CaliBOT - AI Calendar Bot is running",
        "version": __version__,
        "status": "operational"
    }

def start():
    """Start the FastAPI application"""
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)

if __name__ == "__main__":
    start()
