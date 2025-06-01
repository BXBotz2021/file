import os
from pydub import AudioSegment
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def process_audio(bot, message):
    try:
        # Download the audio file
        file_path = await message.audio.download()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Create conversion options
        buttons = [
            [
                InlineKeyboardButton("MP3 ➡️", callback_data="convert_mp3"),
                InlineKeyboardButton("WAV ➡️", callback_data="convert_wav")
            ],
            [
                InlineKeyboardButton("OGG ➡️", callback_data="convert_ogg"),
                InlineKeyboardButton("M4A ➡️", callback_data="convert_m4a")
            ],
            [
                InlineKeyboardButton("🗜️ Compress", callback_data="compress_audio")
            ]
        ]
        
        await message.reply_text(
            "**Select the output format:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Store the file path for later use
        bot.temp_files[message.chat.id] = file_path
        
    except Exception as e:
        await message.reply_text(f"❌ Error processing audio: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def convert_audio(file_path, output_format):
    try:
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}.{output_format.lower()}"
        
        # Export with specific format
        audio.export(output_path, format=output_format.lower())
        
        return output_path
    except Exception as e:
        raise Exception(f"Error converting audio: {str(e)}")

async def compress_audio(file_path, bitrate="128k"):
    try:
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}_compressed{os.path.splitext(file_path)[1]}"
        
        # Export with reduced bitrate
        audio.export(output_path, bitrate=bitrate)
        
        return output_path
    except Exception as e:
        raise Exception(f"Error compressing audio: {str(e)}")

async def extract_audio(video_path):
    try:
        # Load video file
        video = AudioSegment.from_file(video_path)
        
        # Create output filename
        output_path = f"{os.path.splitext(video_path)[0]}_audio.mp3"
        
        # Export audio
        video.export(output_path, format="mp3")
        
        return output_path
    except Exception as e:
        raise Exception(f"Error extracting audio: {str(e)}") 
