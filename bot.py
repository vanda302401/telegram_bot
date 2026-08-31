import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import img2pdf
from pdf2docx import Converter
import qrcode
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image

import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab import colors

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

# Function បង្កើត PDF Thumbnail
def generate_pdf_thumbnail(pdf_path, output_thumb_path):
    try:
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            page = doc[0]
            zoom = 400 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            temp_png = f"{output_thumb_path}_temp.png"
            pix.save(temp_png)
            doc.close()

            img = Image.open(temp_png)
            img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            img.convert("RGB").save(output_thumb_path, "JPEG", quality=100, optimize=True, subsampling=0)

            if os.path.exists(temp_png):
                os.remove(temp_png)
            return True
    except Exception as e:
        print(f"Thumbnail Generation Error: {e}")
    return False

# --- 3. Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "សូមស្វាគមន៍មកកាន់ Ultimate File Utility & Learning Bot! 🤖📄🇬🇧\n\n"
        "🛠 **មុខងារគ្រប់គ្រង File៖**\n"
        "1. ផ្ញើ **រូបភាព (JPG/PNG)** ➔ បំប្លែងទៅ **PDF**\n"
        "2. ផ្ញើ **File PDF** ➔ បំប្លែងទៅ **Word (.docx)**\n"
        "3. ផ្ញើ **File Excel (.xlsx / .xls)** ➔ បំប្លែងទៅ **PDF**\n"
        "4. ផ្ញើ **File PDF** រួច Reply `/preview` ➔ មើលរូបភាព Preview\n"
        "5. ផ្ញើ **File PDF** រួច Reply `/compress` ➔ កាត់បន្ថយទំហំ PDF\n"
        "6. `/qr <អត្ថបទ/Link>` ➔ បង្កើត QR Code\n\n"
        "📚 **មជ្ឈមណ្ឌលរៀនភាសាអង់គ្លេស (English Learning Center)៖**\n"
        "• `/english` - បើកម៉ឺនុយរៀនភាសាអង់គ្លេស (Interactive Menu)\n"
        "• `/vocab` - រៀនពាក្យគន្លឹះប្រចាំថ្ងៃ\n"
        "• `/grammar` - រៀនទម្រង់វេយ្យាករណ៍\n"
        "• `/idiom` - រៀនពាក្យប្រៀបធៀប (Idioms)\n"
        "• `/quiz` - ធ្វើលំហាត់តេស្តសមត្ថភាព\n"
    )
    await update.message.reply_text(msg)

# --- 🎓 មុខងាររៀន English (Advanced & Interactive) ---

async def english_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📖 Vocabulary", callback_data="eng_vocab"),
            InlineKeyboardButton("✍️ Grammar Tips", callback_data="eng_grammar")
        ],
        [
            InlineKeyboardButton("💡 Idioms", callback_data="eng_idiom"),
            InlineKeyboardButton("❓ Quiz Time", callback_data="eng_quiz")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = (
        "📚 **មជ្ឈមណ្ឌលរៀនភាសាអង់គ្លេស (English Learning Center)** 🇬🇧\n\n"
        "សូមជ្រើសរើសផ្នែកដែលអ្នកចង់សិក្សាខាងក្រោម៖"
    )
    
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)

async def english_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vocab_msg = (
        "💡 **Word of the Day (ពាក្យប្រចាំថ្ងៃ)**\n\n"
        "📖 **Word:** Achieve /əˈtʃiːv/\n"
        "🔊 **Type:** Verb (កិរិយាសព្ទ)\n"
        "🇰🇭 **Meaning:** សម្រេចបាន, ទទួលបានជោគជ័យ\n\n"
        "📝 **Example Sentences:**\n"
        "• You can achieve your goals if you work hard.\n"
        "  (អ្នកអាចសម្រេចគោលដៅរបស់អ្នកបាន ប្រសិនបើអ្នកខិតខំប្រឹងប្រែង។)\n"
        "• She achieved high marks in her exams.\n"
        "  (នាងទទួលបានពិន្ទុខ្ពស់ក្នុងការប្រឡង។)"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(vocab_msg)
    else:
        await update.message.reply_text(vocab_msg)

async def english_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grammar_msg = (
        "📖 **Grammar Tip: Present Simple vs Present Continuous**\n\n"
        "1️⃣ **Present Simple** (ទម្លាប់/ការពិតទូទៅ)៖\n"
        "👉 Form: Subject + Verb(s/es)\n"
        "• I play football every Sunday. (ខ្ញុំលេងបាល់រាល់ថ្ងៃអាទិត្យ)\n\n"
        "2️⃣ **Present Continuous** (សកម្មភាពកំពុងធ្វើភ្លាមៗ)៖\n"
        "👉 Form: Subject + am/is/are + V-ing\n"
        "• I am playing football right now. (ខ្ញុំកំពុងតែលេងបាល់ឥឡូវនេះ)"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(grammar_msg)
    else:
        await update.message.reply_text(grammar_msg)

async def english_idiom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idiom_msg = (
        "💡 **Idiom of the Day (សភាសិត/ពាក្យប្រៀបធៀប)**\n\n"
        "🗣 **Idiom:** Piece of cake\n"
        "🇰🇭 **Meaning:** ងាយស្រួលខ្លាំងណាស់ (Very easy)\n\n"
        "📝 **Example:**\n"
        "• Don't worry about the English test, it's a piece of cake!\n"
        "  (កុំបារម្ភអីពីរឿងប្រឡងអង់គ្លេស វាងាយស្រួលខ្លាំងណាស់!)"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(idiom_msg)
    else:
        await update.message.reply_text(idiom_msg)

async def english_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("A) go", callback_data="quiz_wrong"), InlineKeyboardButton("B) goes", callback_data="quiz_correct")],
        [InlineKeyboardButton("C) going", callback_data="quiz_wrong"), InlineKeyboardButton("D) is go", callback_data="quiz_wrong")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    quiz_msg = (
        "❓ **English Quiz Time!**\n\n"
        "ចូរជ្រើសរើសចម្លើយដែលត្រឹមត្រូវ៖\n"
        "\"She _______ to school every day.\""
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(quiz_msg, reply_markup=reply_markup)
    else:
        await update.message.reply_text(quiz_msg, reply_markup=reply_markup)

# Callback Handler សម្រាប់ចម្លើយ Quiz និង Buttons
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "eng_vocab":
        await english_vocab(update, context)
    elif query.data == "eng_grammar":
        await english_grammar(update, context)
    elif query.data == "eng_idiom":
        await english_idiom(update, context)
    elif query.data == "eng_quiz":
        await english_quiz(update, context)
    elif query.data == "quiz_correct":
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ **ត្រឹមត្រូវ! (Correct!)**\n💡 ហេតុផល៖ ព្រោះជាទម្លាប់ប្រចាំថ្ងៃ ប្រើ Present Simple ជាមួយ Subject 'She' (She/He/It + Verb-s/es)។"
        )
    elif query.data == "quiz_wrong":
        await query.edit_message_text(
            f"{query.message.text}\n\n❌ **មិនត្រឹមត្រូវទេ! (Incorrect)**\n💡 ព្យាយាមម្តងទៀត! ចម្លើយដែលត្រូវគឺ **B) goes** (Present Simple ជាមួយ Subject 'She')។"
        )

# --- មុខងារ Utility ដើម ---

async def convert_image_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ កំពុងបំប្លែងរូបភាពទៅជា PDF...")
    photo_file = await update.message.photo[-1].get_file()
    
    user_id = update.message.from_user.id
    input_img = f"temp_{user_id}.jpg"
    output_pdf = f"converted_{user_id}.pdf"
    thumb_path = f"thumb_{user_id}.jpg"
    
    await photo_file.download_to_drive(input_img)
    try:
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(input_img))
        
        has_thumb = generate_pdf_thumbnail(output_pdf, thumb_path)
        
        if has_thumb and os.path.exists(thumb_path):
            with open(output_pdf, "rb") as pdf_file, open(thumb_path, "rb") as thumb_file:
                await update.message.reply_document(
                    document=pdf_file,
                    thumbnail=thumb_file,
                    caption="✅ បំប្លែងទៅជា PDF ជោគជ័យ!"
                )
        else:
            with open(output_pdf, "rb") as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption="✅ បំប្លែងទៅជា PDF ជោគជ័យ!"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_img): os.remove(input_img)
        if os.path.exists(output_pdf): os.remove(output_pdf)
        if os.path.exists(thumb_path): os.remove(thumb_path)

async def convert_pdf_to_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    status_msg = await update.message.reply_text("⏳ កំពុងបំប្លែង PDF ទៅជា Word...")
    pdf_file = await doc.get_file()
    
    user_id = update.message.from_user.id
    input_pdf = f"temp_{user_id}.pdf"
    output_docx = f"converted_{user_id}.docx"
    
    await pdf_file.download_to_drive(input_pdf)
    try:
        cv = Converter(input_pdf)
        cv.convert(output_docx, start=0, end=None)
        cv.close()

        with open(output_docx, "rb") as docx_file:
            await update.message.reply_document(
                document=docx_file,
                caption="✅ បំប្លែងទៅជា Word ជោគជ័យ!"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_docx): os.remove(output_docx)

async def convert_excel_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("⚠️ សូមផ្ញើតែ File Excel (.xlsx) ប៉ុណ្ណោះ!")
        return

    status_msg = await update.message.reply_text("⏳ កំពុងបំប្លែង Excel ទៅជា PDF...")
    excel_file = await doc.get_file()
    
    user_id = update.message.from_user.id
    input_excel = f"excel_{user_id}_{doc.file_name}"
    output_pdf = f"excel_out_{user_id}.pdf"
    thumb_path = f"excel_thumb_{user_id}.jpg"

    await excel_file.download_to_drive(input_excel)
    try:
        wb = openpyxl.load_workbook(input_excel, data_only=True)
        sheet = wb.active
        
        data = []
        for row in sheet.iter_rows(values_only=True):
            row_data = [str(cell) if cell is not None else "" for cell in row]
            if any(row_data):
                data.append(row_data)

        if not data:
            await update.message.reply_text("❌ File Excel នេះគ្មានទិន្នន័យទេ!")
            return

        doc_pdf = SimpleDocTemplate(output_pdf, pagesize=letter)
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        doc_pdf.build([table])

        has_thumb = generate_pdf_thumbnail(output_pdf, thumb_path)
        if has_thumb and os.path.exists(thumb_path):
            with open(output_pdf, "rb") as pdf_file, open(thumb_path, "rb") as thumb_file:
                await update.message.reply_document(
                    document=pdf_file,
                    thumbnail=thumb_file,
                    caption="✅ បំប្លែង Excel ទៅជា PDF ជោគជ័យ!"
                )
        else:
            with open(output_pdf, "rb") as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption="✅ បំប្លែង Excel ទៅជា PDF ជោគជ័យ!"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_excel): os.remove(input_excel)
        if os.path.exists(output_pdf): os.remove(output_pdf)
        if os.path.exists(thumb_path): os.remove(thumb_path)

async def preview_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.reply_to_message
    if not reply or not reply.document or not reply.document.file_name.endswith('.pdf'):
        await update.message.reply_text("⚠️ សូម Reply ទៅកាន់ File PDF រួចវាយបញ្ជា `/preview`!")
        return

    status_msg = await update.message.reply_text("⏳ កំពុងបង្កើត Preview...")
    pdf_file = await reply.document.get_file()
    user_id = update.message.from_user.id
    input_pdf = f"prev_in_{user_id}.pdf"
    output_img = f"prev_out_{user_id}.png"

    await pdf_file.download_to_drive(input_pdf)
    try:
        pdf_doc = fitz.open(input_pdf)
        if len(pdf_doc) > 0:
            page = pdf_doc[0]
            zoom = 400 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(output_img)
            total_pages = len(pdf_doc)
            pdf_doc.close()

            with open(output_img, "rb") as img_file:
                await update.message.reply_photo(
                    photo=img_file,
                    caption=f"🖼 **PDF Preview (ទំព័រទី ១)**\n📄 សរុបមាន៖ {total_pages} ទំព័រ"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_img): os.remove(output_img)

async def compress_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.reply_to_message
    if not reply or not reply.document or not reply.document.file_name.endswith('.pdf'):
        await update.message.reply_text("⚠️ សូម Reply ទៅកាន់ File PDF រួចវាយបញ្ជា `/compress`!")
        return

    status_msg = await update.message.reply_text("⏳ កំពុងកាត់បន្ថយទំហំ PDF...")
    pdf_file = await reply.document.get_file()
    user_id = update.message.from_user.id
    input_pdf = f"comp_in_{user_id}.pdf"
    output_pdf = f"comp_out_{user_id}.pdf"
    thumb_path = f"comp_thumb_{user_id}.jpg"

    await pdf_file.download_to_drive(input_pdf)
    try:
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        with open(output_pdf, "wb") as f:
            writer.write(f)

        has_thumb = generate_pdf_thumbnail(output_pdf, thumb_path)
        
        if has_thumb and os.path.exists(thumb_path):
            with open(output_pdf, "rb") as pdf_file_out, open(thumb_path, "rb") as thumb_file:
                await update.message.reply_document(
                    document=pdf_file_out,
                    thumbnail=thumb_file,
                    caption="✅ កាត់បន្ថយទំហំ PDF ជោគជ័យ!"
                )
        else:
            with open(output_pdf, "rb") as pdf_file_out:
                await update.message.reply_document(
                    document=pdf_file_out,
                    caption="✅ កាត់បន្ថយទំហំ PDF ជោគជ័យ!"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_pdf): os.remove(output_pdf)
        if os.path.exists(thumb_path): os.remove(thumb_path)

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
        with open(qr_img, "rb") as photo_file:
            await update.message.reply_photo(photo=photo_file, caption=f"✅ QR Code សម្រាប់៖ {text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        await status_msg.delete()
        if os.path.exists(qr_img): os.remove(qr_img)

# --- 4. Main Function ---

def main():
    Thread(target=run_web).start()

    app = Application.builder().token(TOKEN).build()
    
    # Utility Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("qr", generate_qr))
    app.add_handler(CommandHandler("preview", preview_pdf))
    app.add_handler(CommandHandler("compress", compress_pdf_file))
    
    # English Learning Commands
    app.add_handler(CommandHandler("english", english_menu))
    app.add_handler(CommandHandler("vocab", english_vocab))
    app.add_handler(CommandHandler("grammar", english_grammar))
    app.add_handler(CommandHandler("idiom", english_idiom))
    app.add_handler(CommandHandler("quiz", english_quiz))
    
    # Button Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    # File Handlers
    app.add_handler(MessageHandler(filters.PHOTO, convert_image_to_pdf))
    app.add_handler(MessageHandler(filters.Document.PDF, convert_pdf_to_word))
    app.add_handler(MessageHandler(filters.Document.FileExtension("xlsx") | filters.Document.FileExtension("xls"), convert_excel_to_pdf))

    print("🤖 Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
