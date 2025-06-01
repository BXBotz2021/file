# Author: Fayas (https://github.com/FayasNoushad) (@FayasNoushad)

import os
import time
import asyncio
from datetime import datetime
from pyrogram import Client, filters, utils
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import FloodWait
from pymongo import MongoClient
from dotenv import load_dotenv
from handlers.image_handler import process_image, convert_image, compress_image
from handlers.document_handler import process_document, convert_pdf_to_docx, convert_docx_to_pdf, compress_pdf
from handlers.audio_handler import process_audio, convert_audio, compress_audio, extract_audio
from handlers.video_handler import process_video, convert_to_gif, convert_video, extract_frames, compress_video

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
Bot.loading_messages = {}  # Store loading message references

ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "").split(",") if id]

# Loading animation frames
LOADING_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Progress bar settings
PROGRESS_BAR_LENGTH = 20
PROGRESS_CHARS = ["▱", "▰"]

async def show_loading_message(message: Message, text: str = "Processing your file") -> Message:
    """Show a loading message with animation"""
    loading_msg = await message.reply_text(f"{LOADING_FRAMES[0]} {text}...")
    Bot.loading_messages[message.chat.id] = {
        "message": loading_msg,
        "frame_index": 0,
        "is_active": True
    }
    return loading_msg

async def update_loading_animation():
    """Update all active loading animations"""
    while True:
        try:
            for chat_id, data in Bot.loading_messages.copy().items():
                if data["is_active"]:
                    msg = data["message"]
                    frame_index = data["frame_index"]
                    new_frame = LOADING_FRAMES[(frame_index + 1) % len(LOADING_FRAMES)]
                    current_text = msg.text.split("...")[-1]
                    try:
                        await msg.edit_text(f"{new_frame} {current_text}...")
                        Bot.loading_messages[chat_id]["frame_index"] = (frame_index + 1) % len(LOADING_FRAMES)
                    except:
                        # Remove message if we can't edit it
                        Bot.loading_messages.pop(chat_id, None)
        except:
            pass
        await asyncio.sleep(0.5)

async def stop_loading_message(chat_id: int, final_text: str = None):
    """Stop the loading animation and optionally update the message"""
    if chat_id in Bot.loading_messages:
        try:
            msg = Bot.loading_messages[chat_id]["message"]
            if final_text:
                await msg.edit_text(final_text)
            else:
                await msg.delete()
        except:
            pass
        Bot.loading_messages.pop(chat_id, None)

async def progress_bar(current, total):
    """Create a progress bar string"""
    percentage = current * 100 / total
    progress = int(percentage / 100 * PROGRESS_BAR_LENGTH)
    bar = PROGRESS_CHARS[1] * progress + PROGRESS_CHARS[0] * (PROGRESS_BAR_LENGTH - progress)
    percentage_str = f"{percentage:.1f}%"
    return f"[{bar}] {percentage_str}"

async def progress_callback(current, total, message, operation):
    """Callback for tracking file operations progress"""
    try:
        if total:
            now = time.time()
            # Update progress every 0.5 seconds
            if message.temp.get('last_update', 0) + 0.5 < now:
                bar = await progress_bar(current, total)
                size_text = f"{utils.humanbytes(current)} / {utils.humanbytes(total)}"
                
                if operation == "download":
                    text = f"📥 **Downloading Video...**\n{bar}\n{size_text}"
                else:  # upload
                    text = f"📤 **Uploading Video...**\n{bar}\n{size_text}"
                
                await message.edit_text(text)
                message.temp['last_update'] = now
    except Exception as e:
        pass

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
 • PDF Compress

🎵 **Audio:**
 • MP3 ↔️ WAV
 • OGG ↔️ MP3
 • Audio Compress
 • Extract Audio from Video

🎬 **Video:**
 • MP4 → GIF
 • Video Compress
 • Extract 10 Random Frames
 • Extract Audio
 • Supports videos up to 2GB

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
• Video: Up to 2GB

4️⃣ **Tips:**
• For best quality, send files in original format
• Some conversions may take time
• For long videos, use the "10 Random Frames" option to extract sample frames
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
async def callback_query(bot, callback_query: CallbackQuery):
    try:
        # Get the stored message and file type
        chat_id = callback_query.message.chat.id
        if chat_id not in Bot.temp_files:
            await callback_query.answer("❌ Please send your file again.", show_alert=True)
            return
        
        stored_data = Bot.temp_files[chat_id]
        original_message = stored_data["original_message"]
        file_type = stored_data["file_type"]
        
        # Show processing message
        await callback_query.message.edit_text("🔄 Processing your request...")
        
        # Handle different conversion types
        if callback_query.data.startswith("convert_"):
            format_type = callback_query.data.replace("convert_", "")
            
            if file_type == "photo":
                result = await convert_image(bot, original_message, format_type)
            elif file_type == "audio":
                result = await convert_audio(bot, original_message, format_type)
            elif file_type == "video" and format_type == "gif":
                result = await convert_to_gif(bot, original_message)
            
        elif callback_query.data == "pdf_to_docx":
            result = await convert_pdf_to_docx(bot, original_message)
            
        elif callback_query.data == "docx_to_pdf":
            result = await convert_docx_to_pdf(bot, original_message)
            
        elif callback_query.data.startswith("compress_"):
            media_type = callback_query.data.replace("compress_", "")
            
            if media_type == "image":
                result = await compress_image(bot, original_message)
            elif media_type == "pdf":
                result = await compress_pdf(bot, original_message)
            elif media_type == "audio":
                result = await compress_audio(bot, original_message)
            elif media_type == "video":
                result = await compress_video(bot, original_message)
                
        elif callback_query.data == "extract_frames":
            result = await extract_frames(bot, original_message)
            
        elif callback_query.data == "extract_audio" or callback_query.data == "extract_audio_from_video":
            result = await extract_audio(bot, original_message)
            
        else:
            await callback_query.message.edit_text("❌ Invalid conversion option.")
            return
        
        # Clean up stored data
        Bot.temp_files.pop(chat_id, None)
        
        # Update user's conversion count
        users_collection.update_one(
            {"user_id": callback_query.from_user.id},
            {"$inc": {"files_converted": 1}}
        )
        
        # Update conversion stats
        update_stats(callback_query.data)
        
    except Exception as e:
        await callback_query.message.edit_text(f"❌ An error occurred: {str(e)}")
        print(f"Error in callback_query: {str(e)}")

# File handlers
@Bot.on_message(filters.private & filters.media)
async def media_handler(bot, message):
    try:
        # Add user to database
        await add_user(message.from_user.id, message.from_user.username)
        
        # Show initial loading message
        loading_msg = await show_loading_message(message, "Analyzing your file")
        
        # Determine file type and show appropriate conversion options
        if message.photo:
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("PNG ➡️ JPG", callback_data="convert_jpg"),
                    InlineKeyboardButton("JPG ➡️ PNG", callback_data="convert_png")
                ],
                [
                    InlineKeyboardButton("Image ➡️ Sticker", callback_data="convert_sticker"),
                    InlineKeyboardButton("Image ➡️ PDF", callback_data="convert_pdf")
                ],
                [InlineKeyboardButton("Compress Image", callback_data="compress_image")]
            ])
            await process_image(bot, message, loading_msg)
            
        elif message.document:
            file_name = message.document.file_name.lower()
            if file_name.endswith(('.pdf', '.docx', '.doc')):
                markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("PDF ➡️ Word", callback_data="pdf_to_docx"),
                        InlineKeyboardButton("Word ➡️ PDF", callback_data="docx_to_pdf")
                    ],
                    [InlineKeyboardButton("Compress PDF", callback_data="compress_pdf")]
                ])
                await process_document(bot, message, loading_msg)
                
        elif message.audio or message.voice:
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("MP3 ➡️ WAV", callback_data="convert_wav"),
                    InlineKeyboardButton("WAV ➡️ MP3", callback_data="convert_mp3")
                ],
                [
                    InlineKeyboardButton("Extract Audio", callback_data="extract_audio"),
                    InlineKeyboardButton("Compress Audio", callback_data="compress_audio")
                ]
            ])
            await process_audio(bot, message, loading_msg)
            
        elif message.video:
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Video ➡️ GIF", callback_data="convert_gif"),
                    InlineKeyboardButton("Compress Video", callback_data="compress_video")
                ],
                [
                    InlineKeyboardButton("Extract Frames", callback_data="extract_frames"),
                    InlineKeyboardButton("Extract Audio", callback_data="extract_audio_from_video")
                ]
            ])
            await process_video(bot, message, loading_msg)
        
        else:
            await stop_loading_message(message.chat.id, "❌ Unsupported file type. Please send an image, document, audio, or video file.")
            return
        
        # Store the original message reference for later use
        Bot.temp_files[message.chat.id] = {
            "original_message": message,
            "file_type": "photo" if message.photo else "document" if message.document else "audio" if message.audio else "video"
        }
        
        await loading_msg.edit_text(
            "Please select your desired conversion option:",
            reply_markup=markup
        )
        
    except Exception as e:
        await stop_loading_message(message.chat.id, f"❌ An error occurred: {str(e)}")
        print(f"Error in media_handler: {str(e)}")

# Start the loading animation task
@Bot.on_start()
async def start_loading_animation():
    asyncio.create_task(update_loading_animation())

Bot.run()
