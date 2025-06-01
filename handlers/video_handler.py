import os
import moviepy.editor as mp
from PIL import Image
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def process_video(bot, message):
    try:
        # Download the video file
        file_path = await message.video.download()
        
        # Create conversion options
        buttons = [
            [
                InlineKeyboardButton("GIF ➡️", callback_data="convert_gif"),
                InlineKeyboardButton("MP4 ➡️", callback_data="convert_mp4")
            ],
            [
                InlineKeyboardButton("Extract Audio ➡️", callback_data="extract_audio"),
                InlineKeyboardButton("Extract Frames ➡️", callback_data="extract_frames")
            ],
            [
                InlineKeyboardButton("🗜️ Compress", callback_data="compress_video")
            ]
        ]
        
        await message.reply_text(
            "**Select the output format:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Store the file path for later use
        bot.temp_files[message.chat.id] = file_path
        
    except Exception as e:
        await message.reply_text(f"❌ Error processing video: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def convert_to_gif(file_path):
    try:
        # Load video file
        video = mp.VideoFileClip(file_path)
        
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}.gif"
        
        # Convert to GIF
        video.write_gif(output_path)
        
        video.close()
        return output_path
    except Exception as e:
        raise Exception(f"Error converting to GIF: {str(e)}")

async def convert_video(file_path, output_format="mp4"):
    try:
        # Load video file
        video = mp.VideoFileClip(file_path)
        
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}.{output_format.lower()}"
        
        # Convert video
        video.write_videofile(output_path)
        
        video.close()
        return output_path
    except Exception as e:
        raise Exception(f"Error converting video: {str(e)}")

async def extract_frames(file_path, frame_rate=1):
    try:
        # Load video file
        video = mp.VideoFileClip(file_path)
        
        # Create output directory
        output_dir = f"{os.path.splitext(file_path)[0]}_frames"
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract frames
        duration = int(video.duration)
        frame_paths = []
        
        for i in range(0, duration, frame_rate):
            frame = video.get_frame(i)
            output_path = os.path.join(output_dir, f"frame_{i}.jpg")
            Image.fromarray(frame).save(output_path)
            frame_paths.append(output_path)
            
        video.close()
        return frame_paths
    except Exception as e:
        raise Exception(f"Error extracting frames: {str(e)}")

async def compress_video(file_path):
    try:
        # Load video file
        video = mp.VideoFileClip(file_path)
        
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}_compressed.mp4"
        
        # Compress video by reducing resolution and bitrate
        video_resized = video.resize(width=480)  # Resize to 480p
        video_resized.write_videofile(output_path, bitrate="1000k")
        
        video.close()
        video_resized.close()
        return output_path
    except Exception as e:
        raise Exception(f"Error compressing video: {str(e)}") 
