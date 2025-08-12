import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CLIENT_SECRET_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
GOOGLE_API_SCOPES = ['https://www.googleapis.com/auth/calendar']
OAUTH_REDIRECT_PATH = "/oauth2callback"

API_HOST = os.getenv("API_HOST", "0.0.0.0")  # Use 0.0.0.0 by default
API_PORT = int(os.getenv("API_PORT", 8060))  # Use 8060 by default

# LLM Model - configured externally via environment variables
LITELLM_MODEL = os.getenv("LITELLM_MODEL")
if not LITELLM_MODEL:
    raise ValueError("LITELLM_MODEL environment variable must be set")