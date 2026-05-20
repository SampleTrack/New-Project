import asyncio
import sys
import urllib.parse
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

# Create placeholders for variables that will be assigned inside our async wrapper function
app = None

def convert_to_earnkaro(target_url: str) -> str:
    base_url = target_url.split("?")[0]
    encoded_target = urllib.parse.quote(base_url)
    return f"https://earnkaro.com/connect?url={encoded_target}"

def clean_and_parse_input(text: str):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) < 6:
        return None
    return lines

async def main():
    global app
    print("🚀 Initializing Hydrogram Engine inside an explicit async loop context...")
    
    # Instantiating the Client INSIDE the running loop eliminates the Python 3.14 event loop error entirely
    app = Client(
        "earnkaro_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN
    )

    # Re-register your event handlers explicitly inside our wrapper scope context
    @app.on_message(filters.command("start") & filters.private)
    async def start_command(client, message):
        await message.reply_text(
            "👋 **Welcome to the Affiliate Deal Posting Engine!**\n\n"
            "Send your raw deals inside this private admin panel using the template layout structure."
        )

    @app.on_message(filters.private & ~filters.command(["start"]))
    async def process_deal_post(client, message):
        parsed_lines = clean_and_parse_input(message.text)
        
        if not parsed_lines:
            error_template = (
                "⚠️ **Parsing Aborted: Incorrect Template Structure!**\n\n"
                "Please send the data line-by-line exactly matching this blueprint:\n"
                "```\n"
                "Amazon\n"
                "Noise Pulse 2 Max Smartwatch\n"
                "1199\n"
                "5999\n"
                "80\n"
                "[https://www.amazon.in/dp/B0B6BLG283](https://www.amazon.in/dp/B0B6BLG283)\n"
                "[https://m.media-amazon.com/images/I/61S9aVn9bRL._SL1500_.jpg](https://m.media-amazon.com/images/I/61S9aVn9bRL._SL1500_.jpg)\n")
            await message.reply_text(error_template)
            return

        try:
            platform = parsed_lines[0].upper()
            title = parsed_lines[1]
            deal_price = parsed_lines[2]
            mrp = parsed_lines[3]
            discount = parsed_lines[4]
            product_url = parsed_lines[5]
            image_url = parsed_lines[6]

            affiliate_link = convert_to_earnkaro(product_url)

            premium_caption = (
                f"🛍️ **{title}**\n\n"
                f"⚡ **Deal Price:** ₹{deal_price}\n"
                f"❌ **MRP:** ~~₹{mrp}~~\n"
                f"📉 **Discount:** {discount}% Instant Save!\n\n"
                f"🔥 *Grab it before the price spikes up again!*"
            )

            inline_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=f"🛒 Buy via {platform}", url=affiliate_link)]
            ])

            await client.send_photo(
                chat_id=Config.CHANNEL_ID,
                photo=image_url,
                caption=premium_caption,
                reply_markup=inline_keyboard
            )

            await message.reply_text("✅ **Success:** Post distributed safely to channel feeds!")

        except Exception as e:
            await message.reply_text(f"❌ **Execution Blocked:** System crash: `{str(e)}`")

    # Start the engine asynchronously
    await app.start()
    print("🤖 Bot is completely online and listening for events on Python 3.14!")
    
    # Keep the task loop alive indefinitely 
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        # Use native modern asyncio to handle boot sequencing
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 System shut down by manual kill instruction signal.")
    except Exception as boot_error:
        print(f"❌ CRITICAL BOOT FAILURE: {str(boot_error)}", file=sys.stderr)
        sys.exit(1)
