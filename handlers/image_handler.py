import os
from PIL import Image
import io
from pyrogram.types import Message

async def process_image(bot, message: Message, loading_msg):
    """Process image and prepare it for conversion"""
    try:
        # Download the image
        if message.photo:
            file = await message.photo.biggest_file_id.download(in_memory=True)
        else:
            file = await message.document.download(in_memory=True)
        
        return file
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

async def convert_image(bot, message: Message, format_type):
    """Convert image to specified format"""
    try:
        # Get the image file
        image_data = await process_image(bot, message, None)
        
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image format
        output = io.BytesIO()
        if format_type == "jpg":
            image = image.convert("RGB")
            image.save(output, format="JPEG")
        elif format_type == "png":
            image.save(output, format="PNG")
        elif format_type == "sticker":
            # Resize for sticker if needed
            if max(image.size) > 512:
                image.thumbnail((512, 512))
            image.save(output, format="WEBP")
        elif format_type == "pdf":
            # Convert to PDF
            image = image.convert("RGB")
            output_path = f"temp_{message.chat.id}.pdf"
            image.save(output_path, "PDF", resolution=100.0)
            # Send PDF
            await message.reply_document(output_path)
            # Cleanup
            os.remove(output_path)
            return
        
        output.seek(0)
        
        # Send the converted file
        if format_type == "sticker":
            await message.reply_sticker(output)
        else:
            file_name = f"converted.{format_type.lower()}"
            await message.reply_document(output, file_name=file_name)
        
        return True
    except Exception as e:
        raise Exception(f"Error converting image: {str(e)}")

async def compress_image(bot, message: Message):
    """Compress image while maintaining reasonable quality"""
    try:
        # Get the image file
        image_data = await process_image(bot, message, None)
        
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Compress image
        output = io.BytesIO()
        image.save(output, 
                  format=image.format if image.format else "JPEG",
                  optimize=True, 
                  quality=85)
        output.seek(0)
        
        # Send compressed image
        await message.reply_document(
            output,
            file_name=f"compressed.{image.format.lower() if image.format else 'jpg'}"
        )
        
        return True
    except Exception as e:
        raise Exception(f"Error compressing image: {str(e)}") 
