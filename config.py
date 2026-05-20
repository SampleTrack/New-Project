import os
from dotenv import load_dotenv

# Load local .env file during development staging
load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # <--- Added Admin Identity check validation
    
    # Validation block to prevent boot up if core credentials are blank
    if not API_ID or not API_HASH or not BOT_TOKEN or not CHANNEL_ID:
        raise ValueError("CRITICAL ERROR: Missing vital configuration keys in your environment variables.")

