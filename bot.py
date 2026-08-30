import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import img2pdf
from pdf2docx import Converter
import qrcode
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF សម្រាប់បង្កើត PDF Preview / Thumbnail

# --- 1. Web Server សម្រាប់ Render ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running online 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- 2. Telegram Bot Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "សូមស្វាគមន៍មកកាន់ Ultimate File & Utility Bot! 🤖📄\n\n"
        "🛠 **មុខងារដែលមាន៖**\n"
        "1. ផ្ញើ **រូបភាព (JPG/PNG)** ➔ បំប្លែងទៅ **PDF**\n"
        "2. ផ្ញើ **File PDF** ➔ បំប្លែងទៅ **Word (.docx)**\n"
        "3. ផ្ញើ **File PDF** រួច Reply វាយ `/preview` ➔ បង្កើត **Preview Image (Thumbnail)** នៃទំព័រទី១\n"
        "4. ផ្ញើ **File PDF** រួច Reply វាយ `/compress` ➔ កាត់បន្ថយទំហំ **PDF**\n"
        "5. វាយបញ្ជា `/qr <អត្ថបទ/Link>` ➔ បង្កើត **QR Code**\n"
    )
    await update.message.reply_text(msg)

# មុខងារ 1: Image to PDF
async def convert_image_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ កំពុងបំប្លែងរូបភាពទៅជា PDF...")
    photo_file = await update.message.photo[-1].get_file()
    input_img = f"temp_{update.message.from_user.id}.jpg"
    output_pdf = f"converted_{update.message.from_user.id}.pdf"
    
    await photo_file.download_to_drive(input_img)
    try:
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(input_img))
        await update.message.reply_document(document=open(output_pdf, "rb"), caption="✅ បំប្លែងទៅជា PDF ជោគជ័យ!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_img): os.remove(input_img)
        if os.path.exists(output_pdf): os.remove(output_pdf)

# មុខងារ 2: PDF to Word
async def convert_pdf_to_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.pdf'):
        await update.message.reply_text("⚠️ សូមផ្ញើតែ File PDF ប៉ុណ្ណោះ!")
        return
    status_msg = await update.message.reply_text("⏳ កំពុងបំប្លែង PDF ទៅជា Word...")
    pdf_file = await doc.get_file()
    input_pdf = f"temp_{update.message.from_user.id}.pdf"
    output_docx = f"converted_{update.message.from_user.id}.docx"
    
    await pdf_file.download_to_drive(input_pdf)
    try:
        cv = Converter(input_pdf)
        cv.convert(output_docx, start=0, end=None)
        cv.close()
        await update.message.reply_document(document=open(output_docx, "rb"), caption="✅ បំប្លែងទៅជា Word ជោគជ័យ!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_docx): os.remove(output_docx)

# មុខងារ 3: PDF Preview / Thumbnail Generation (ទាញយករូបភាពទំព័រទី១)
async def preview_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.reply_to_message
    if not reply or not reply.document or not reply.document.file_name.endswith('.pdf'):
        await update.message.reply_text("⚠️ សូម Reply ទៅកាន់ File PDF រួចវាយបញ្ជា `/preview`!")
        return

    status_msg = await update.message.reply_text("⏳ កំពុងបង្កើត Preview Image...")
    pdf_file = await reply.document.get_file()
    input_pdf = f"preview_in_{update.message.from_user.id}.pdf"
    output_img = f"preview_out_{update.message.from_user.id}.png"

    await pdf_file.download_to_drive(input_pdf)
    try:
        # បើក PDF ជាមួយ PyMuPDF
        doc = fitz.open(input_pdf)
        if len(doc) > 0:
            page = doc[0]  # ទាញយកទំព័រទី ១ (Index 0)
            pix = page.get_pixmap(dpi=150)  # Render ជារូបភាព HD
            pix.save(output_img)
            doc.close()

            await update.message.reply_photo(
                photo=open(output_img, "rb"),
                caption=f"🖼 **PDF Preview (ទំព័រទី ១)**\n📄 សរុបមាន៖ {len(doc)} ទំព័រ"
            )
        else:
            await update.message.reply_text("❌ File PDF នេះគ្មានទំព័រឡើយ!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_img): os.remove(output_img)

# មុខងារ 4: Compress PDF
async def compress_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.reply_to_message
    if not reply or not reply.document or not reply.document.file_name.endswith('.pdf'):
        await update.message.reply_text("⚠️ សូម Reply ទៅកាន់ File PDF រួចវាយបញ្ជា `/compress`!")
        return

    status_msg = await update.message.reply_text("⏳ កំពុងកាត់បន្ថយទំហំ PDF...")
    pdf_file = await reply.document.get_file()
    input_pdf = f"compress_in_{update.message.from_user.id}.pdf"
    output_pdf = f"compressed_out_{update.message.from_user.id}.pdf"

    await pdf_file.download_to_drive(input_pdf)
    try:
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        with open(output_pdf, "wb") as f:
            writer.write(f)

        await update.message.reply_document(document=open(output_pdf, "rb"), caption="✅ កាត់បន្ថយទំហំ PDF ជោគជ័យ!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_pdf): os.remove(output_pdf)

# មុខងារ 5: Generate QR Code
async def generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ សូមបញ្ជាក់ Link ឬ អត្ថបទ! ឧទាហរណ៍៖ `/qr https://google.com`")
        return
    
    status_msg = await update.message.reply_text("⏳ កំពុងបង្កើត QR Code...")
    qr_img = f"qr_{update.message.from_user.id}.png"
    
    try:
        img = qrcode.make(text)
        img.save(qr_img)
        await update.message.reply_photo(photo=open(qr_img, "rb"), caption=f"✅ QR Code សម្រាប់៖ {text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(qr_img): os.remove(qr_img)

def main():
    Thread(target=run_web).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("qr", generate_qr))
    app.add_handler(CommandHandler("preview", preview_pdf))
    app.add_handler(CommandHandler("compress", compress_pdf_file))
    app.add_handler(MessageHandler(filters.PHOTO, convert_image_to_pdf))
    app.add_handler(MessageHandler(filters.Document.PDF, convert_pdf_to_word))

    print("🤖 Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
