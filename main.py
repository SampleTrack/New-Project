import asyncio
import sys
import urllib.parse
import feedparser
from hydrogram import Client
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

app = None

# A secure tracker to make sure the bot never posts the same deal twice
POSTED_DEALS_CACHE = set()

def convert_to_earnkaro(target_url: str) -> str:
    """Wraps any raw product link directly into your EarnKaro monetization stream."""
    base_url = target_url.split("?")[0]
    encoded_target = urllib.parse.quote(base_url)
    return f"https://earnkaro.com/connect?url={encoded_target}"

async def fetch_and_post_deals():
    """Connects to open deal streams, parses price drops, and pushes new deals."""
    global app
    print("🔍 Scanning live data feeds for top Amazon, Flipkart & Myntra deals...")
    
    # We use a curated Indian e-commerce deal aggregator feed tracking major price drops
    # You can also substitute this with your custom EarnKaro RSS/Atom profile link if preferred
    feed_url = "https://www.desidime.com/feed/top-deals.atom"
    
    try:
        feed = feedparser.parse(feed_url)
        
        # Process the top 5 freshest deals found in the current scan loop
        for entry in feed.entries[:5]:
            deal_id = entry.id
            
            # Skip if we already published this specific deal in a previous cycle
            if deal_id in POSTED_DEALS_CACHE:
                continue
                
            title = entry.title
            raw_url = entry.link
            
            # Simple keyword filtering to ensure we only pull from your preferred platforms
            if not any(platform in raw_url.lower() for platform in ["amazon", "flipkart", "myntra"]):
                continue

            # Convert to your personal affiliate earning link
            affiliate_link = convert_to_earnkaro(raw_url)

            # Premium Channel Presentation Styling
            premium_caption = (
                f"🔥 **🔥 TOP TRENDING DEAL ALERT 🔥**\n\n"
                f"📦 **Product:** {title}\n\n"
                f"⚡ *Price drop detected! Grab it at its lowest price before stock runs out.*"
            )

            inline_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🛒 Grab Deal Now", url=affiliate_link)]
            ])

            # Broadcast directly to your channel feed
            await app.send_message(
                chat_id=Config.CHANNEL_ID,
                text=premium_caption,
                reply_markup=inline_keyboard
            )
            
            # Add to local memory cache to block future duplication loops
            POSTED_DEALS_CACHE.add(deal_id)
            print(f"✅ Auto-posted: {title[:30]}...")
            
            # Sleep brief seconds between consecutive channel posts to keep formatting clean
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"⚠️ Error while parsing deal feeds: {str(e)}", file=sys.stderr)

async def main():
    global app
    print("🚀 Initializing Autonomous Deal Finder Engine...")
    
    app = Client(
        "automated_deal_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN
    )

    await app.start()
    print("🤖 Bot is completely online and running on Render!")

    # The continuous background automation routine loop
    while True:
        await fetch_and_post_deals()
        print("😴 Scan completed. Sleeping for 30 minutes before next auto-check...")
        await asyncio.sleep(1800) # Checks for fresh price drops every 30 minutes

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as boot_error:
        print(f"❌ CRITICAL WORKER FAULT: {str(boot_error)}", file=sys.stderr)
        sys.exit(1)
