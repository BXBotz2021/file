import os
from pdf2docx import Converter
from docx2pdf import convert
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def process_document(bot, message):
    try:
        # Download the document file
        file_path = await message.download()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Create conversion options based on file type
        if file_ext == '.pdf':
            buttons = [
                [
                    InlineKeyboardButton("DOCX ➡️", callback_data="convert_docx"),
                    InlineKeyboardButton("Images ➡️", callback_data="convert_images")
                ],
                [
                    InlineKeyboardButton("🗜️ Compress", callback_data="compress_pdf")
                ]
            ]
        elif file_ext in ['.doc', '.docx']:
            buttons = [
                [
                    InlineKeyboardButton("PDF ➡️", callback_data="convert_pdf")
                ]
            ]
        else:
            await message.reply_text("❌ Unsupported document format! Please send PDF or Word documents.")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        await message.reply_text(
            "**Select the output format:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Store the file path for later use
        bot.temp_files[message.chat.id] = file_path
        
    except Exception as e:
        await message.reply_text(f"❌ Error processing document: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def convert_pdf_to_docx(file_path):
    try:
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}.docx"
        
        # Convert PDF to DOCX
        cv = Converter(file_path)
        cv.convert(output_path)
        cv.close()
        
        return output_path
    except Exception as e:
        raise Exception(f"Error converting PDF to DOCX: {str(e)}")

async def convert_docx_to_pdf(file_path):
    try:
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}.pdf"
        
        # Convert DOCX to PDF
        convert(file_path, output_path)
        
        return output_path
    except Exception as e:
        raise Exception(f"Error converting DOCX to PDF: {str(e)}")

async def convert_pdf_to_images(file_path):
    try:
        # Create output directory
        output_dir = f"{os.path.splitext(file_path)[0]}_images"
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(file_path)
        image_paths = []
        
        for i, image in enumerate(images):
            output_path = os.path.join(output_dir, f"page_{i+1}.jpg")
            image.save(output_path, 'JPEG')
            image_paths.append(output_path)
        
        return image_paths
    except Exception as e:
        raise Exception(f"Error converting PDF to images: {str(e)}")

async def compress_pdf(file_path):
    try:
        # Create output filename
        output_path = f"{os.path.splitext(file_path)[0]}_compressed.pdf"
        
        # Read the PDF
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        # Copy pages with compression
        for page in reader.pages:
            writer.add_page(page)
        
        # Save with compression
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path
    except Exception as e:
        raise Exception(f"Error compressing PDF: {str(e)}") 
