import asyncio
import logging
import urllib.parse
import feedparser
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

logger = logging.getLogger("DealBot.Worker")
POSTED_DEALS_CACHE = set()

def convert_to_earnkaro(target_url: str) -> str:
    """Nests any structural product URL safely inside an EarnKaro redirection link."""
    base_url = target_url.split("?")[0]
    encoded_target = urllib.parse.quote(base_url)
    return f"https://earnkaro.com/connect?url={encoded_target}"

async def fetch_and_post_deals(bot_instance: Client):
    """Executes network pipeline parsing queries out to regional deal matrix streams."""
    logger.info("🔍 Querying feed networks for fresh price-drop alerts...")
    feed_url = "https://www.desidime.com/feed/top-deals.atom"
    
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            logger.warning("⚠️ Connected to aggregator node but found no raw elements present.")
            return

        for entry in feed.entries[:5]:
            deal_id = entry.id
            if deal_id in POSTED_DEALS_CACHE:
                continue
                
            title = entry.title
            raw_url = entry.link
            
            # Enforce validation rules protecting your tracking conversion streams
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

            await bot_instance.send_message(
                chat_id=Config.CHANNEL_ID,
                text=premium_caption,
                reply_markup=inline_keyboard
            )
            
            POSTED_DEALS_CACHE.add(deal_id)
            logger.info(f"✅ Deal successfully posted to target channel: {title[:25]}...")
            await asyncio.sleep(5)  # Anti-flood spacing line block
            
    except Exception as loop_fault:
        logger.error(f"⚠️ Error encountered during worker sweep: {str(loop_fault)}")

async def automation_loop(bot_instance: Client):
    """The continuous loop that runs the fetch sequence every 30 minutes."""
    while True:
        await fetch_and_post_deals(bot_instance)
        logger.info("😴 Automation sync pass completed. Sleeping for 30 minutes...")
        await asyncio.sleep(1800)

def register_handlers(bot_instance: Client):
    """Maps custom interactive triggers back onto our instance engine wrapper context."""
    @bot_instance.on_message(filters.command("start") & filters.private)
    async def start_command(client, message):
        await message.reply_text(
            "👋 **Welcome to the Automated Affiliate Deal Finder Engine!**\n\n"
            "The system is currently running in background monitoring mode checking for active price drops."
        )

