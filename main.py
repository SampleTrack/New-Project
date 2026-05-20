import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from hydrogram import Client
from config import Config

# Configure real-time diagnostic stream saving to a local text file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_errors.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DealBot")

# Global reference mapping containers
bot_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles secure application execution startup and graceful shutdowns context."""
    global bot_app
    logger.info("🚀 Bootstrapping Hydrogram engine within explicit async loop task container...")
    
    try:
        bot_app = Client(
            "automated_deal_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        
        # Import the deal loop routine cleanly out of our separate module file
        from deals_worker import register_handlers, automation_loop
        
        # Register the text listener functions onto our client scope container
        register_handlers(bot_app)
        
        # Start the MTProto connection
        await bot_app.start()
        logger.info("🤖 Hydrogram connected! Scheduling background deal pipeline...")
        
        # Deploy the autonomous deal hunter routine as a non-blocking context background task
        bg_task = asyncio.create_task(automation_loop(bot_app))
        
        yield  # Hand over loop context execution to the core web service runtime layer
        
        # Graceful shutdown process execution cleanup handling lines
        bg_task.cancel()
        await bot_app.stop()
        logger.info("🛑 Background client workers stopped safely.")
        
    except Exception as initialization_fault:
        logger.critical(f"❌ DEADLOCK CRASH ON STARTUP: {str(initialization_fault)}")
        raise initialization_fault

# Mount the server using modern lifespan logic matching FastAPI 2026 standards
app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    """Satisfies Render free tier HTTP live checks."""
    return {"status": "active", "engine": "Hydrogram 0.2.0 + FastAPI Core"}

@app.get("/logs", response_class=PlainTextResponse)
def get_bot_error_logs():
    """Secure public text pipeline tracking diagnostic failure stack records directly."""
    log_path = "bot_errors.txt"
    if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
        return "✨ Log Matrix Clean: Zero framework faults recorded in this cycle."
        
    with open(log_path, "r", encoding="utf-8") as file:
        return file.read()

if __name__ == "__main__":
    server_port = int(os.getenv("PORT", 10000))
    logger.info(f"🌐 Commencing interface binding onto port: {server_port}")
    uvicorn.run(app, host="0.0.0.0", port=server_port)
