import os
from PIL import Image
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def process_image(bot, message):
    try:
        # Download the image
        if message.photo:
            file_path = await message.download()
        else:
            file_path = await message.document.download()
            
        # Create conversion options keyboard
        buttons = [
            [
                InlineKeyboardButton("PNG ➡️", callback_data="convert_png"),
                InlineKeyboardButton("JPG ➡️", callback_data="convert_jpg")
            ],
            [
                InlineKeyboardButton("WEBP ➡️", callback_data="convert_webp"),
                InlineKeyboardButton("STICKER ➡️", callback_data="convert_sticker")
            ],
            [
                InlineKeyboardButton("PDF ➡️", callback_data="convert_pdf"),
                InlineKeyboardButton("🗜️ Compress", callback_data="compress_image")
            ]
        ]
        
        await message.reply_text(
            "**Select the output format:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Store the file path for later use
        bot.temp_files[message.chat.id] = file_path
        
    except Exception as e:
        await message.reply_text(f"❌ Error processing image: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def convert_image(file_path, output_format, quality=95):
    try:
        img = Image.open(file_path)
        
        # Convert image to RGB if necessary
        if output_format.upper() != 'PNG' and img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, 'white')
            background.paste(img, mask=img.split()[-1])
            img = background
            
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}.{output_format.lower()}"
        
        # Save with specific format
        if output_format.upper() == 'PDF':
            img.save(output_path, 'PDF', resolution=100.0, save_all=True)
        else:
            img.save(output_path, output_format.upper(), quality=quality)
            
        return output_path
    except Exception as e:
        raise Exception(f"Error converting image: {str(e)}")
    finally:
        if 'img' in locals():
            img.close()

async def compress_image(file_path, max_size_kb=500):
    try:
        img = Image.open(file_path)
        output_path = f"{os.path.splitext(file_path)[0]}_compressed{os.path.splitext(file_path)[1]}"
        
        # Start with quality 95
        quality = 95
        img.save(output_path, quality=quality, optimize=True)
        
        # Reduce quality until file size is under max_size_kb
        while os.path.getsize(output_path) > max_size_kb * 1024 and quality > 5:
            quality -= 5
            img.save(output_path, quality=quality, optimize=True)
        
        return output_path
    except Exception as e:
        raise Exception(f"Error compressing image: {str(e)}")
    finally:
        if 'img' in locals():
            img.close() 
