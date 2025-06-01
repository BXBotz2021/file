# Author: Fayas (https://github.com/FayasNoushad) (@FayasNoushad)

import os
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
from pymongo import MongoClient
from dotenv import load_dotenv
from handlers.image_handler import process_image
from handlers.document_handler import process_document
from handlers.audio_handler import process_audio
from handlers.video_handler import process_video

load_dotenv()

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://EVOKINDIA:evokindia@evokindia.0cap9.mongodb.net/?retryWrites=true&w=majority&appName=EvokIndia")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["file_converter_bot"]
users_collection = db["users"]
stats_collection = db["stats"]

# Bot initialization
Bot = Client(
    "File-Converter-Bot",
    bot_token=os.environ.get("BOT_TOKEN"),
    api_id=int(os.environ.get("API_ID")),
    api_hash=os.environ.get("API_HASH")
)

# Initialize temp_files dictionary for storing temporary file paths
Bot.temp_files = {}

ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "").split(",") if id]

# Bot messages
START_TEXT = """👋 Hello **{}**!
Welcome to **File Converter Bot** 🔄

I can help you convert various file formats:

📸 **Images:**
 • JPG ↔️ PNG
 • Image → Sticker
 • Image → PDF
 • Resize/Compress Images

📄 **Documents:**
 • PDF → Word
 • Word → PDF
 • PDF → Images
 • PDF Compress

🎵 **Audio:**
 • MP3 ↔️ WAV
 • OGG ↔️ MP3
 • Audio Compress
 • Extract Audio from Video

🎬 **Video:**
 • MP4 → GIF
 • Video Compress
 • Extract Frames
 • Change Format

Send me any file to get started!"""

HELP_TEXT = """🔍 **How to Use File Converter Bot:**

1️⃣ **Converting Files:**
• Simply send me any supported file
• Select the desired output format
• Wait for the conversion to complete

2️⃣ **Supported Formats:**
• Images: JPG, PNG, WEBP, STICKER
• Documents: PDF, DOCX, TXT
• Audio: MP3, WAV, OGG, M4A
• Video: MP4, AVI, MKV, GIF

3️⃣ **File Size Limits:**
• Images: Up to 5MB
• Documents: Up to 20MB
• Audio: Up to 20MB
• Video: Up to 50MB

4️⃣ **Tips:**
• For best quality, send files in original format
• Some conversions may take time
• Premium users get higher limits

❓ Need help? Contact support using button below."""

# Keyboard markups
START_BUTTONS = [
    [
        InlineKeyboardButton("❓ Help", callback_data="help"),
        InlineKeyboardButton("📊 Stats", callback_data="stats")
    ],
    [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/bot_resurge")]
]

# Function to add new user
async def add_user(user_id, username):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "joined_date": datetime.now(),
            "files_converted": 0
        })

# Function to update stats
def update_stats(conversion_type):
    stats_collection.update_one(
        {"type": conversion_type},
        {"$inc": {"count": 1}},
        upsert=True
    )

# Command handlers
@Bot.on_message(filters.command(["start", "help"]))
async def start_command(bot, message):
    await add_user(message.from_user.id, message.from_user.username)
    
    if message.command[0].lower() == "help":
        await message.reply_text(
            HELP_TEXT,
            reply_markup=InlineKeyboardMarkup(START_BUTTONS),
            quote=True
        )
    else:
        await message.reply_text(
            START_TEXT.format(message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(START_BUTTONS),
            quote=True
        )

# Stats command
@Bot.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_command(bot, message):
    total_users = users_collection.count_documents({})
    total_conversions = sum(
        stat["count"] for stat in stats_collection.find()
    )
    
    stats_text = f"""📊 **Bot Statistics**

👥 Total Users: {total_users}
🔄 Total Conversions: {total_conversions}

**Conversion Types:**"""
    
    for stat in stats_collection.find():
        stats_text += f"\n• {stat['type']}: {stat['count']}"
    
    await message.reply_text(stats_text)

# Callback query handler
@Bot.on_callback_query()
async def callback_query(bot, callback_query):
    data = callback_query.data
    
    if data == "help":
        await callback_query.message.edit_text(
            HELP_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="start")]
            ])
        )
    elif data == "start":
        await callback_query.message.edit_text(
            START_TEXT.format(callback_query.from_user.mention),
            reply_markup=InlineKeyboardMarkup(START_BUTTONS)
        )
    elif data == "stats":
        if callback_query.from_user.id in ADMIN_IDS:
            total_users = users_collection.count_documents({})
            total_conversions = sum(
                stat["count"] for stat in stats_collection.find()
            )
            
            stats_text = f"""📊 **Bot Statistics**

👥 Total Users: {total_users}
🔄 Total Conversions: {total_conversions}

**Conversion Types:**"""
            
            for stat in stats_collection.find():
                stats_text += f"\n• {stat['type']}: {stat['count']}"
            
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Back", callback_data="start")]
                ])
            )
        else:
            await callback_query.answer("⚠️ Only admins can view statistics!", show_alert=True)

# File handlers
@Bot.on_message(filters.private & filters.media)
async def media_handler(bot, message):
    try:
        # Check file size
        if message.document:
            file_size = message.document.file_size
        elif message.photo:
            file_size = message.photo.file_size
        elif message.audio:
            file_size = message.audio.file_size
        elif message.video:
            file_size = message.video.file_size
        else:
            await message.reply_text("❌ Unsupported file type!")
            return

        # Size limits (in bytes)
        LIMITS = {
            "photo": 5242880,    # 5MB
            "document": 20971520, # 20MB
            "audio": 20971520,   # 20MB
            "video": 52428800    # 50MB
        }

        # Check file size limits
        if message.photo and file_size > LIMITS["photo"]:
            await message.reply_text("❌ Image file size should be less than 5MB!")
            return
        elif message.document and file_size > LIMITS["document"]:
            await message.reply_text("❌ Document file size should be less than 20MB!")
            return
        elif message.audio and file_size > LIMITS["audio"]:
            await message.reply_text("❌ Audio file size should be less than 20MB!")
            return
        elif message.video and file_size > LIMITS["video"]:
            await message.reply_text("❌ Video file size should be less than 50MB!")
            return

        # Process different types of files
        if message.photo or (message.document and message.document.mime_type.startswith('image')):
            await process_image(bot, message)
        elif message.document:
            await process_document(bot, message)
        elif message.audio:
            await process_audio(bot, message)
        elif message.video:
            await process_video(bot, message)
        else:
            await message.reply_text("❌ Unsupported file type!")

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

Bot.run()
