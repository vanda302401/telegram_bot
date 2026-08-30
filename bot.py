import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import img2pdf
from pdf2docx import Converter

# --- 1. បង្កើត Web Server តូចមួយសម្រាប់ Render (Port Binding) ---
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
    await update.message.reply_text("សូមស្វាគមន៍មកកាន់ File Converter Bot! 🤖📄\nផ្ញើរូបភាពដើម្បីបំប្លែងទៅ PDF ឬផ្ញើ PDF ដើម្បីបំប្លែងទៅ Word។")

async def convert_image_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ កំពុងបំប្លែងរូបភាពទៅជា PDF...")
    photo_file = await update.message.photo[-1].get_file()
    input_img = f"temp_{update.message.from_user.id}.jpg"
    output_pdf = f"converted_{update.message.from_user.id}.pdf"
    
    await photo_file.download_to_drive(input_img)
    try:
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(input_img))
        await update.message.reply_document(document=open(output_pdf, "rb"), caption="✅ បំប្លែងជោគជ័យ!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_img): os.remove(input_img)
        if os.path.exists(output_pdf): os.remove(output_pdf)

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
        await update.message.reply_document(document=open(output_docx, "rb"), caption="✅ បំប្លែងជោគជ័យ!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_docx): os.remove(output_docx)

def main():
    # រត់ Web Server លើ Thread ផ្សេង
    Thread(target=run_web).start()

    # រត់ Telegram Bot
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, convert_image_to_pdf))
    app.add_handler(MessageHandler(filters.Document.PDF, convert_pdf_to_word))

    print("🤖 Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()