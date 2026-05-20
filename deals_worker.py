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
    """
    Executes network pipeline parsing queries out to regional deal matrix streams.
    bypass_filters=True allows ANY store to post immediately for testing purposes.
    """
    logger.info(f"🔍 Querying feed networks (Force: {force}, Bypass: {bypass_filters})...")
    feed_url = "https://www.desidime.com/feed/top-deals.atom"
    
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            logger.warning("⚠️ Connected to aggregator node but found no raw elements present.")
            return False

        allowed_platforms = ["amazon", "flipkart", "myntra", "ajio", "nykaa", "tatacliq", "croma", "boat"]
        
        for entry in feed.entries[:20]:  
            deal_id = entry.id
            
            if not force and deal_id in POSTED_DEALS_CACHE:
                continue
                
            title = entry.title
            raw_url = entry.link
            summary_text = entry.summary.lower() if hasattr(entry, 'summary') else ""
            
            matched_platform = "DEAL"
            
            if not bypass_filters:
                # Normal mode: check strict platform rules
                found = False
                for platform in allowed_platforms:
                    if platform in raw_url.lower() or platform in summary_text:
                        matched_platform = platform.upper()
                        found = True
                        break
                if not found:
                    continue  # Skip if it doesn't match a main e-commerce platform
            else:
                # Test mode: try to guess platform name, default to general name if not found
                for platform in allowed_platforms:
                    if platform in raw_url.lower() or platform in summary_text:
                        matched_platform = platform.upper()
                        break

            affiliate_link = convert_to_earnkaro(raw_url)

            premium_caption = (
                f"⚙️ **[SYSTEM TEST] LIVE DEAL CONFIRMATION**\n\n"
                f"📦 **Product:** {title}\n\n"
                f"⚡ *This is an instant system test to verify connection loops are completely active.*"
            )

            inline_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=f"🛒 Try Link via {matched_platform}", url=affiliate_link)]
            ])

            await bot_instance.send_message(
                chat_id=Config.CHANNEL_ID,
                text=premium_caption,
                reply_markup=inline_keyboard
            )
            
            if not force:
                POSTED_DEALS_CACHE.add(deal_id)
                
            logger.info(f"✅ Test deal successfully sent to channel.")
            return True 
            
        return False
            
    except Exception as loop_fault:
        logger.error(f"⚠️ Error encountered during worker sweep: {str(loop_fault)}")
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

    # 1. STANDARDIZED SEARCH (Stricter store checks)
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

    # 2. INSTANT TEST EXPRESS (Bypasses all rules to force a live channel upload)
    @bot_instance.on_message(filters.command("testdeal") & filters.private)
    async def test_deal_command(client, message):
        if message.from_user.id != Config.ADMIN_ID:
            return
        
        status_msg = await message.reply_text("🛠️ **Bypassing store filtering systems...** Fetching the absolute freshest item from the grid immediately...")
        
        # force=True and bypass_filters=True guarantees the newest deal pushes immediately
        did_post = await fetch_and_post_deals(client, force=True, bypass_filters=True)
        
        if did_post:
            await status_msg.edit_text("🚀 **Instant Test Completed!** Check your channel right now. A live formatted test post with an active EarnKaro link has been created.")
        else:
            await status_msg.edit_text("❌ System error reading feed data array. Check web logs.")
