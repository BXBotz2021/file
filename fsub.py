from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, UsernameNotOccupied
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://anushkabot:anushkabot@cluster0.rg84dqj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["youtube_thumb_bot"]
settings_collection = db["settings"]

# Default force sub channel (will be used if no channel is set)
DEFAULT_FSUB_CHANNEL = "-1002693207322"  # Replace with your default channel ID

async def get_force_sub_channel():
    settings = settings_collection.find_one({"type": "fsub"})
    # Return the stored channel ID if exists, otherwise return default channel
    return settings.get("channel_id") if settings and settings.get("channel_id") else DEFAULT_FSUB_CHANNEL

async def set_force_sub_channel(channel_id):
    if channel_id is None:
        # If disabling, set to default channel instead of None
        channel_id = DEFAULT_FSUB_CHANNEL
    
    settings_collection.update_one(
        {"type": "fsub"},
        {"$set": {"channel_id": channel_id}},
        upsert=True
    )

async def force_sub(bot, message):
    try:
        channel_id = await get_force_sub_channel()
        try:
            # Try to get channel information
            chat = await bot.get_chat(channel_id)
            channel_type = chat.type
            channel_username = chat.username
            channel_title = chat.title
            
            # Get user's subscription status
            user = await bot.get_chat_member(channel_id, message.from_user.id)
            if user.status in ["kicked", "left", "banned"]:
                raise UserNotParticipant
                
            return True
            
        except UserNotParticipant:
            # Create channel link based on channel type
            if channel_username:
                channel_link = f"https://t.me/{channel_username}"
            else:
                # For private channels, try to create an invite link
                try:
                    invite_link = await bot.create_chat_invite_link(channel_id)
                    channel_link = invite_link.invite_link
                except ChatAdminRequired:
                    channel_link = "❌ ᴄᴏᴜʟᴅɴ'ᴛ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋ"
            
            buttons = [[
                InlineKeyboardButton("🔔 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link)
            ]]
            
            await message.reply_text(
                text=f"**❗ᴘʟᴇᴀsᴇ ᴊᴏɪɴ @{channel_title} ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ!**\n\n"
                     "ᴅᴜᴇ ᴛᴏ ᴏᴠᴇʀʟᴏᴀᴅ, ᴏɴʟʏ ᴄʜᴀɴɴᴇʟ sᴜʙsᴄʀɪʙᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ʙᴏᴛ!",
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            return False
            
        except (UsernameNotOccupied, Exception) as e:
            print(f"Force Sub Error: {str(e)}")
            # If there's an error with the current channel, switch to default
            if channel_id != DEFAULT_FSUB_CHANNEL:
                await set_force_sub_channel(DEFAULT_FSUB_CHANNEL)
            return True
            
    except Exception as e:
        print(f"Force Sub Error: {str(e)}")
        return True

async def handle_force_sub_command(bot, message):
    """Handle the /fsub command to set or view force subscription channel"""
    try:
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id not in bot.ADMIN_IDS:
            await message.reply_text("⚠️ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ᴏɴʟʏ ғᴏʀ ᴀᴅᴍɪɴs!")
            return

        # If no argument provided, show current channel
        if len(message.command) == 1:
            channel_id = await get_force_sub_channel()
            try:
                chat = await bot.get_chat(channel_id)
                await message.reply_text(
                    f"🔒 ᴄᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ:\n"
                    f"• ID: `{channel_id}`\n"
                    f"• Title: {chat.title}\n"
                    f"• Username: @{chat.username if chat.username else 'Private Channel'}\n"
                    f"• Status: {'Default Channel' if channel_id == DEFAULT_FSUB_CHANNEL else 'Custom Channel'}"
                )
            except Exception as e:
                await message.reply_text(
                    f"🔒 ᴄᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ: `{channel_id}`\n"
                    f"❌ Error: {str(e)}\n"
                    f"Status: {'Default Channel' if channel_id == DEFAULT_FSUB_CHANNEL else 'Custom Channel'}"
                )
            return

        # Get the channel ID/username from command
        channel_input = message.command[1]
        
        # Handle channel removal (will set to default instead of disabling)
        if channel_input.lower() in ['none', 'off', 'disable', 'remove', 'default']:
            await set_force_sub_channel(DEFAULT_FSUB_CHANNEL)
            await message.reply_text("✅ ғᴏʀᴄᴇ sᴜʙ ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ ᴄʜᴀɴɴᴇʟ!")
            return

        # Verify the channel exists and bot has access
        try:
            chat = await bot.get_chat(channel_input)
            # Try to get bot's member status in the channel
            bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
            
            if bot_member.status not in ["administrator", "creator"]:
                await message.reply_text(
                    "❌ ᴛʜᴇ ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ!\n\n"
                    "ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴛʜᴇ ʙᴏᴛ ᴀs ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
                )
                return

            # Save the channel ID
            await set_force_sub_channel(str(chat.id))
            
            await message.reply_text(
                f"✅ ғᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!\n\n"
                f"• Title: {chat.title}\n"
                f"• Chat ID: `{chat.id}`\n"
                f"• Username: @{chat.username if chat.username else 'Private Channel'}\n"
                f"• Status: Custom Channel"
            )
            
        except Exception as e:
            await message.reply_text(f"❌ ᴇʀʀᴏʀ: {str(e)}\n\nᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ:\n1. ᴛʜᴇ ʙᴏᴛ ɪs ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ\n2. ʏᴏᴜ ᴘʀᴏᴠɪᴅᴇᴅ ᴀ ᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ")
    except Exception as e:
        await message.reply_text(f"❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {str(e)}")
