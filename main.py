# Author: Fayas (https://github.com/FayasNoushad) (@FayasNoushad)

import os
import time
import ytthumb
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pyrogram.errors import FloodWait
from pymongo import MongoClient

load_dotenv()

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://anushkabot:anushkabot@cluster0.rg84dqj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["youtube_thumb_bot"]
users_collection = db["users"]
stats_collection = db["stats"]

Bot = Client(
    "YouTube-Thumbnail-Downloader",
    bot_token = os.environ.get("BOT_TOKEN"),
    api_id = int(os.environ.get("API_ID")),
    api_hash = os.environ.get("API_HASH")
)

ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "6974737899").split(",") if id]

START_TEXT = """👋 Hello **{}**!
Welcome to **YouTube Thumbnail Downloader Bot** 🎯

I can help you download thumbnails from YouTube videos in various qualities!

🔹 **Features:**
• Download thumbnails in multiple qualities
• Support for video links and IDs
• Quick and easy to use
• High-quality downloads

📝 Send me any YouTube video link or ID to get started!

💡 **Pro Tip:** You can specify quality like this:
`videoID | quality` (e.g., `dQw4w9WgXcQ | hq`)

Use /help for more detailed instructions."""

HELP_TEXT = """🔍 **How to Use:**

1️⃣ **Simple Download:**
   • Just send a YouTube video link or ID
   • I'll send the thumbnail in standard quality

2️⃣ **Quality Selection:**
   • Format: `videoID | quality`
   • Available qualities:
     - sd (Standard)
     - mq (Medium)
     - hq (High)
     - maxres (Maximum)

3️⃣ **Examples:**
   • `dQw4w9WgXcQ`
   • `dQw4w9WgXcQ | hq`
   • `https://youtube.com/watch?v=dQw4w9WgXcQ`

❓ Need more help? Contact support using the button below."""

ABOUT_TEXT = """🤖 **Bot Information:**

• **Name:** YouTube Thumbnail Downloader
• **Version:** 2.0
• **Developer:** @FayasNoushad
• **Language:** Python
• **Framework:** Pyrogram

📊 **Statistics:**
• Users: {}
• Downloads: {}

🔗 **Useful Links:**
• Support
• Updates
• Source Code"""

# Enhanced buttons with emojis
MAIN_BUTTONS = [
    [
        InlineKeyboardButton("❓ Help", callback_data="help"),
        InlineKeyboardButton("ℹ️ About", callback_data="about")
    ],
    [InlineKeyboardButton("👨‍💻 Developer", url='https://telegram.me/bot_resurge')]
]

photo_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton('🎨 Other Qualities', callback_data='qualities')],
    [InlineKeyboardButton("👨‍💻 Developer", url='https://telegram.me/bot_resurge')]
])

# User tracking function
async def add_user(user_id, username):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "joined_date": time.time()
        })

# Update stats
def update_stats(type="downloads"):
    stats_collection.update_one(
        {"type": type},
        {"$inc": {"count": 1}},
        upsert=True
    )

@Bot.on_callback_query()
async def cb_data(_, message):
    data = message.data.lower()
    
    if data == "help":
        await message.edit_message_text(
            HELP_TEXT,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="start")
            ]])
        )
    
    elif data == "about":
        total_users = users_collection.count_documents({})
        total_downloads = stats_collection.find_one({"type": "downloads"})
        downloads = total_downloads["count"] if total_downloads else 0
        
        await message.edit_message_text(
            ABOUT_TEXT.format(total_users, downloads),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="start")
            ]])
        )
    
    elif data == "start":
        await message.edit_message_text(
            START_TEXT.format(message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(MAIN_BUTTONS)
        )
    
    elif data == "qualities":
        buttons = []
        for quality in ytthumb.qualities():
            buttons.append(
                InlineKeyboardButton(
                    text=ytthumb.qualities()[quality],
                    callback_data=quality
                )
            )
        await message.edit_message_reply_markup(
            InlineKeyboardMarkup([
                [buttons[0], buttons[1]],
                [buttons[2], buttons[3]],
                [InlineKeyboardButton("◀️ Back", callback_data="back")]
            ])
        )
    
    elif data == "back":
        await message.edit_message_reply_markup(photo_buttons)
    
    elif data in ytthumb.qualities():
        try:
            thumbnail = ytthumb.thumbnail(
                video=message.message.reply_to_message.text,
                quality=message.data
            )
            await message.edit_message_media(
                media=InputMediaPhoto(media=thumbnail),
                reply_markup=photo_buttons
            )
            update_stats("downloads")
        except Exception as e:
            await message.answer(f"❌ Error: {str(e)}")

@Bot.on_message(filters.private & filters.command(["start", "help", "about"]))
async def start(_, message):
    command = message.command[0].lower()
    await add_user(message.from_user.id, message.from_user.username)
    
    if command == "help":
        await message.reply_text(
            text=HELP_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(MAIN_BUTTONS),
            quote=True
        )
    elif command == "about":
        total_users = users_collection.count_documents({})
        total_downloads = stats_collection.find_one({"type": "downloads"})
        downloads = total_downloads["count"] if total_downloads else 0
        
        await message.reply_text(
            text=ABOUT_TEXT.format(total_users, downloads),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(MAIN_BUTTONS),
            quote=True
        )
    else:
        await message.reply_text(
            text=START_TEXT.format(message.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(MAIN_BUTTONS),
            quote=True
        )

@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast(_, message):
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a message to broadcast.")
        return
    
    broadcast_msg = message.text.split(None, 1)[1]
    sent = 0
    failed = 0
    status_msg = await message.reply_text("📤 Broadcasting message...")
    
    users = users_collection.find({})
    for user in users:
        try:
            await Bot.send_message(user["user_id"], broadcast_msg)
            sent += 1
            await status_msg.edit_text(f"🔄 Progress: {sent} sent, {failed} failed")
            time.sleep(0.1)  # To prevent flooding
        except FloodWait as e:
            time.sleep(e.value)
        except Exception:
            failed += 1
            continue
    
    await status_msg.edit_text(
        f"✅ Broadcast completed!\n\n"
        f"✓ Successfully sent: {sent}\n"
        f"✗ Failed: {failed}"
    )

@Bot.on_message(filters.private & filters.text)
async def send_thumbnail(bot, update):
    message = await update.reply_text(
        text="🔄 `Analyzing...`",
        disable_web_page_preview=True,
        quote=True
    )
    try:
        if " | " in update.text:
            video = update.text.split(" | ", -1)[0]
            quality = update.text.split(" | ", -1)[1]
        else:
            video = update.text
            quality = "sd"
        
        thumbnail = ytthumb.thumbnail(
            video=video,
            quality=quality
        )
        await update.reply_photo(
            photo=thumbnail,
            reply_markup=photo_buttons,
            quote=True
        )
        update_stats("downloads")
        await message.delete()
    except Exception as error:
        await message.edit_text(
            text=f"❌ Error: {str(error)}",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(MAIN_BUTTONS)
        )

Bot.run()
