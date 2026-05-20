import asyncio
import re
import sys
import urllib.parse
from hydrogram import Client, filters
from config import Config

# The public channel username you want to source deals from (Example: "dealshub")
# Do not include the '@' symbol in this variable string
SOURCE_CHANNEL = "ubuydeals" 

app = None

def convert_to_earnkaro(target_url: str) -> str:
    """Extracts raw link parameters and nests them safely inside your EarnKaro redirect profile."""
    base_url = target_url.split("?")[0]
    encoded_target = urllib.parse.quote(base_url)
    return f"https://earnkaro.com/connect?url={encoded_target}"

def extract_urls(text: str) -> list:
    """Finds all standard HTTP/HTTPS links hidden inside a raw message string."""
    return re.findall(r'(https?://[^\s]+)', text)

async def main():
    global app
    print("🚀 Booting Autonomous Deal Scraper Loop Engine...")
    
    app = Client(
        "automated_deal_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN
    )

    # Listen specifically for incoming posts from your target source channel
    @app.on_message(filters.chat(SOURCE_CHANNEL))
    async def auto_scraper_handler(client, message):
        # We need text data to process a clean post. If it's a raw image without a caption, skip.
        raw_text = message.text or message.caption
        if not raw_text:
            return

        print(f"📥 New raw candidate deal captured from source channel: {message.id}")

        # Step 1: Link Extraction & Verification
        found_links = extract_urls(raw_text)
        if not found_links:
            return # No destination link means nothing to monetize
            
        source_link = found_links[0]
        
        # Step 2: Convert the external affiliate link to your EarnKaro account link
        my_affiliate_link = convert_to_earnkaro(source_link)

        # Step 3: Strip out the competitor's channel names or custom links
        # This regex cleans up common promotional lines or signature tags
        cleaned_text = re.sub(r'(@\w+|t\.me/\w+)', '', raw_text)
        
        # Step 4: Build your clean presentation layout structure
        final_caption = (
            f"🔥 **AUTOMATED HOT DEAL** 🔥\n\n"
            f"{cleaned_text}\n\n"
            f"👇 **Grab the deal here before it expires:**\n"
            f"🔗 {my_affiliate_link}"
        )

        try:
            # Step 5: Mirror deployment logic. If the source post had an image, forward it with your new caption
            if message.photo:
                await client.send_photo(
                    chat_id=Config.CHANNEL_ID,
                    photo=message.photo.file_id, # Reuses Telegram's file ID for instant caching
                    caption=final_caption
                )
            else:
                await client.send_message(
                    chat_id=Config.CHANNEL_ID,
                    text=final_caption,
                    disable_web_page_preview=False
                )
            print(f"✅ Deal {message.id} successfully auto-converted and broadcasted.")

        except Exception as dispatch_error:
            print(f"⚠️ Non-fatal sync skip: {str(dispatch_error)}", file=sys.stderr)

    await app.start()
    print("🤖 Automation Engine is online. Monitoring target streams 24/7...")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as boot_error:
        print(f"❌ CRITICAL WORKER FAULT: {str(boot_error)}", file=sys.stderr)
        sys.exit(1)
