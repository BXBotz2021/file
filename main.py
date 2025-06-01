# Author: Fayas (https://github.com/FayasNoushad) (@FayasNoushad)

import os
import time
import ytthumb
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pyrogram.errors import FloodWait
from pymongo import MongoClient
import datetime

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

START_TEXT = """👋 ʜᴇʏ  **{}**!
ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʏᴏᴜᴛᴜʙᴇ ᴛʜᴜᴍʙɴᴀɪʟ ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ 🚀

🎯 ɪ'ᴍ ʏᴏᴜʀ ɢᴏ-ᴛᴏ ʙᴏᴛ ғᴏʀ ɢʀᴀʙʙɪɴɢ ʜɪɢʜ-ǫᴜᴀʟɪᴛʏ ᴛʜᴜᴍʙɴᴀɪʟs ɪɴ sᴇᴄᴏɴᴅs.

🔍 ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ:
• ᴅᴏᴡɴʟᴏᴀᴅ ᴛʜᴜᴍʙɴᴀɪʟs ɪɴ sᴅ, ᴍǫ, ʜǫ, ᴍᴀxʀᴇs
• ᴀᴄᴄᴇᴘᴛs ʏᴏᴜᴛᴜʙᴇ ʟɪɴᴋs ᴏʀ ᴠɪᴅᴇᴏ ɪᴅs
• ǫᴜɪᴄᴋ, sɪᴍᴘʟᴇ, ɴᴏ ᴄᴀᴘ

🧠 ᴀᴠᴀɪʟᴀʙʟᴇ ǫᴜᴀʟɪᴛɪᴇs: sd, mq, hq, maxres

ᴛʏᴘᴇ /help ɪғ ʏᴏᴜ ɴᴇᴇᴅ ᴀ ʙᴏᴏsᴛ 💬

ʟᴇᴛ'ꜱ ɢᴇᴛ ᴛʜᴏsᴇ ᴛʜᴜᴍʙɴᴀɪʟs 🔥"""

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
• **Developer:** @BOT_RESURGE
• **Language:** Python
• **Framework:** Pyrogram

📊 **Statistics:**
• Users: {}
• Downloads: {}
"""

STATS_TEXT = """📊 **ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs:**

👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: {}
📥 ᴛᴏᴛᴀʟ ᴅᴏᴡɴʟᴏᴀᴅs: {}
🔄 ʟᴀsᴛ ᴜᴘᴅᴀᴛᴇᴅ: {} UTC

📈 **ᴛᴏᴅᴀʏ's sᴛᴀᴛs:**
• ɴᴇᴡ ᴜsᴇʀs: {}
• ᴅᴏᴡɴʟᴏᴀᴅs: {}"""

# Enhanced buttons with emojis
MAIN_BUTTONS = [
    [
        InlineKeyboardButton("❓ ʜᴇʟᴘ", callback_data="help"),
        InlineKeyboardButton("ℹ️ ᴀʙᴏᴜᴛ", callback_data="about")
    ],
    [
        InlineKeyboardButton("📊 sᴛᴀᴛs", callback_data="stats"),
        InlineKeyboardButton("👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://telegram.me/bot_resurge')
    ]
]

photo_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton('🎨 ᴏᴛʜᴇʀ ǫᴜᴀʟɪᴛɪᴇs', callback_data='qualities')],
    [InlineKeyboardButton("👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://telegram.me/bot_resurge')]
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
    # Update total downloads
    stats_collection.update_one(
        {"type": type},
        {"$inc": {"count": 1}},
        upsert=True
    )
    
    # Update daily downloads
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    stats_collection.update_one(
        {
            "type": "daily_downloads",
            "date": today
        },
        {"$inc": {"count": 1}},
        upsert=True
    )

def get_daily_stats():
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get today's new users
    new_users = users_collection.count_documents({
        "joined_date": {"$gte": today.timestamp()}
    })
    
    # Get today's downloads
    daily_downloads = stats_collection.find_one({
        "type": "daily_downloads",
        "date": today.strftime("%Y-%m-%d")
    })
    
    return new_users, daily_downloads["count"] if daily_downloads else 0

async def get_stats_text():
    total_users = users_collection.count_documents({})
    total_downloads = stats_collection.find_one({"type": "downloads"})
    downloads = total_downloads["count"] if total_downloads else 0
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    daily_users, daily_downloads = get_daily_stats()
    
    return STATS_TEXT.format(
        total_users,
        downloads,
        current_time,
        daily_users,
        daily_downloads
    )

@Bot.on_callback_query()
async def cb_data(_, message):
    data = message.data.lower()
    
    if data == "help":
        await message.edit_message_text(
            HELP_TEXT,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data="start")
            ]])
        )
    
    elif data == "stats":
        stats_text = await get_stats_text()
        await message.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data="start")
            ]])
        )
    
    elif data == "about":
        total_users = users_collection.count_documents({})
        total_downloads = stats_collection.find_one({"type": "downloads"})
        downloads = total_downloads["count"] if total_downloads else 0
        
        await message.edit_message_text(
            ABOUT_TEXT.format(total_users, downloads),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data="start")
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
                    text=ytthumb.qualities()[quality].upper().replace("QUALITY", "ǫᴜᴀʟɪᴛʏ").replace("STANDARD", "sᴛᴀɴᴅᴀʀᴅ").replace("MEDIUM", "ᴍᴇᴅɪᴜᴍ").replace("HIGH", "ʜɪɢʜ").replace("MAXIMUM RESOLUTION", "ᴍᴀxɪᴍᴜᴍ ʀᴇsᴏʟᴜᴛɪᴏɴ"),
                    callback_data=quality
                )
            )
        await message.edit_message_reply_markup(
            InlineKeyboardMarkup([
                [buttons[0], buttons[1]],
                [buttons[2], buttons[3]],
                [InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data="back")]
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

# Add stats command handler
@Bot.on_message(filters.private & filters.command("stats"))
async def stats_command(_, message):
    # Only allow admins to use this command
    if message.from_user.id not in ADMIN_IDS:
        await message.reply_text("⚠️ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ᴏɴʟʏ ғᴏʀ ᴀᴅᴍɪɴs.")
        return
    
    stats_text = await get_stats_text()
    await message.reply_text(
        stats_text,
        quote=True,
        reply_markup=InlineKeyboardMarkup(MAIN_BUTTONS)
    )

Bot.run()
