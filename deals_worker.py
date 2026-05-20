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

async def fetch_and_post_deals(bot_instance: Client, force: bool = False, bypass_filters: bool = False):
    """Executes network pipeline parsing queries out to regional deal matrix streams."""
    logger.info(f"🔍 Querying feed networks (Force: {force}, Bypass: {bypass_filters})...")
    
    # NEW FAIL-SAFE PRODUCTION FEEDS: If feed 1 returns blank, feed 2 acts as an instant backup!
    primary_feed = "https://www.indiafreestuff.in/feed"
    backup_feed = "https://simplecoupon.in/feed/"
    
    selected_feed = primary_feed
    feed = feedparser.parse(selected_feed)
    
    # Fail-over check: If the primary feed is blank or blocked, immediately hit the backup data line
    if not feed.entries:
        logger.warning(f"⚠️ Primary feed blank. Shifting to backup node line...")
        selected_feed = backup_feed
        feed = feedparser.parse(selected_feed)
        
    if not feed.entries:
        logger.critical("❌ CRITICAL: All regional aggregator deal feeds returned empty arrays.")
        return False

    allowed_platforms = ["amazon", "flipkart", "myntra", "ajio", "nykaa", "tatacliq", "croma", "boat"]
    
    for entry in feed.entries[:20]:  
        deal_id = getattr(entry, 'id', entry.link)
        
        if not force and deal_id in POSTED_DEALS_CACHE:
            continue
            
        title = entry.title
        raw_url = entry.link
        summary_text = entry.summary.lower() if hasattr(entry, 'summary') else ""
        
        matched_platform = "DEAL"
        
        if not bypass_filters:
            found = False
            for platform in allowed_platforms:
                if platform in raw_url.lower() or platform in summary_text:
                    matched_platform = platform.upper()
                    found = True
                    break
            if not found:
                continue 
        else:
            for platform in allowed_platforms:
                if platform in raw_url.lower() or platform in summary_text:
                    matched_platform = platform.upper()
                    break

        affiliate_link = convert_to_earnkaro(raw_url)

        premium_caption = (
            f"🛍️ **HOT TRADING DISCOUNTS FOUND**\n\n"
            f"📦 **Product:** {title}\n\n"
            f"⚡ *Price drop tracking active! Secure this price profile before stock scales back down.*"
        )

        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=f"🛒 Buy via {matched_platform}", url=affiliate_link)]
        ])

        await bot_instance.send_message(
            chat_id=Config.CHANNEL_ID,
            text=premium_caption,
            reply_markup=inline_keyboard
        )
        
        if not force:
            POSTED_DEALS_CACHE.add(deal_id)
            
        logger.info(f"✅ Deal successfully sent to channel.")
        return True 
        
    return False

async def automation_loop(bot_instance: Client):
    """The continuous loop that runs the fetch sequence automatically every 30 minutes."""
    while True:
        await fetch_and_post_deals(bot_instance, force=False, bypass_filters=False)
        logger.info("😴 Automation sync pass completed. Sleeping for 30 minutes...")
        await asyncio.sleep(1800)

def register_handlers(bot_instance: Client):
    """Maps custom interactive triggers back onto our instance engine wrapper context."""
    
    @bot_instance.on_message(filters.command("start") & filters.private)
    async def start_command(client, message):
        await message.reply_text(
            "👋 **Welcome to the Automated Affiliate Deal Finder Engine!**\n\n"
            "Bot status: Online 🟢\n"
            "Send `/check` to test normal matching rules.\n"
            "Send `/testdeal` to force-post the newest item instantly regardless of platform."
        )

    @bot_instance.on_message(filters.command("check") & filters.private)
    async def check_command(client, message):
        if message.from_user.id != Config.ADMIN_ID:
            return
        status_msg = await message.reply_text("⚡ Scanning top 20 trending matching platform deals...")
        did_post = await fetch_and_post_deals(client, force=True, bypass_filters=False)
        if did_post:
            await status_msg.edit_text("✅ Success! Matching deal posted.")
        else:
            await status_msg.edit_text("❌ Halt: No active deals matched main platform profiles right now.")

    @bot_instance.on_message(filters.command("testdeal") & filters.private)
    async def test_deal_command(client, message):
        if message.from_user.id != Config.ADMIN_ID:
            return
        
        status_msg = await message.reply_text("🛠️ **Bypassing filtering logic...** Extracting immediate newest stream elements...")
        did_post = await fetch_and_post_deals(client, force=True, bypass_filters=True)
        
        if did_post:
            await status_msg.edit_text("🚀 **Instant Test Completed!** Check your channel right now. A live formatted test post with an active EarnKaro link has been created.")
        else:
            await status_msg.edit_text("❌ Data stream parsing error. See system logs.")
