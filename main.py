import asyncio
import sys
import urllib.parse
import feedparser
import uvicorn
from fastapi import FastAPI
from hydrogram import Client
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

# Initialize FastAPI Web Server to cheat Render's Free Port Check
web_app = FastAPI()
bot_app = None
POSTED_DEALS_CACHE = set()

@web_app.get("/")
def read_root():
    """Keeps Render happy by returning a 200 OK website status code."""
    return {"status": "online", "message": "Affiliate Deal Bot Running Successfully"}

def convert_to_earnkaro(target_url: str) -> str:
    base_url = target_url.split("?")[0]
    encoded_target = urllib.parse.quote(base_url)
    return f"https://earnkaro.com/connect?url={encoded_target}"

async def fetch_and_post_deals():
    """Scans aggregator streams for trending price drops and posts them."""
    global bot_app
    print("🔍 Scanning live data feeds for top Amazon, Flipkart & Myntra deals...")
    feed_url = "https://www.desidime.com/feed/top-deals.atom"
    
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:
            deal_id = entry.id
            if deal_id in POSTED_DEALS_CACHE:
                continue
                
            title = entry.title
            raw_url = entry.link
            
            # Filter specifically for your chosen e-commerce platforms
            if not any(p in raw_url.lower() for p in ["amazon", "flipkart", "myntra"]):
                continue

            affiliate_link = convert_to_earnkaro(raw_url)

            premium_caption = (
                f"🔥 **🔥 TOP TRENDING DEAL ALERT 🔥**\n\n"
                f"📦 **Product:** {title}\n\n"
                f"⚡ *Price drop detected! Grab it at its lowest price before stock runs out.*"
            )

            inline_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🛒 Grab Deal Now", url=affiliate_link)]
            ])

            await bot_app.send_message(
                chat_id=Config.CHANNEL_ID,
                text=premium_caption,
                reply_markup=inline_keyboard
            )
            
            POSTED_DEALS_CACHE.add(deal_id)
            print(f"✅ Auto-posted: {title[:30]}...")
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"⚠️ Error while parsing deal feeds: {str(e)}", file=sys.stderr)

async def automation_loop():
    """Continuous loop running in the background every 30 minutes."""
    while True:
        await fetch_and_post_deals()
        print("😴 Scan completed. Sleeping for 30 minutes...")
        await asyncio.sleep(1800)

@web_app.on_event("startup")
async def start_bot():
    """Triggers instantly when the FastAPI web server starts up."""
    global bot_app
    print("🚀 Initializing Hydrogram Bot Client Engine...")
    bot_app = Client(
        "automated_deal_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN
    )
    await bot_app.start()
    print("🤖 Bot is connected! Starting background auto-finder task...")
    
    # Run the deal finder loop as an independent background task inside the server
    asyncio.create_task(automation_loop())

if __name__ == "__main__":
    import os
    # Read the dynamic port Render provides us on the Free plan, default to 10000 locally
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Spinning up Web Server on port {port}...")
    uvicorn.run(web_app, host="0.0.0.0", port=port)
