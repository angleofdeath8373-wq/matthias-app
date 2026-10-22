import os
import re
import json
import threading
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8642920714:AAHQlTd2KDtx3riU8qkp1C5ElPU_igVdUO0")
DATA_FILE = "./matthias_database.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

def add_to_db(new_data):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except:
        db = []
    
    existing = next((item for item in db if item["title"].lower() == new_data["title"].lower()), None)
    if not existing:
        db.append(new_data)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/manhwas', methods=['GET'])
def get_manhwas():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    caption = msg.caption or msg.text or "مجموعه تلگرامی"
    
    clean_title = re.sub(r'(?:چپتر|قسمت|فصل|ch|chapter).*', '', caption, flags=re.IGNORECASE).strip() or "مانهوای جدید"
    ch_match = re.search(r'(\d+)', caption)
    chapter_num = int(ch_match.group(1)) if ch_match else 1

    cover_url = "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500"
    if msg.photo:
        file = await msg.photo[-1].get_file()
        cover_url = file.file_path

    manhwa_item = {
        "id": int(msg.message_id),
        "title": clean_title,
        "genre": "تلگرام",
        "chapters": chapter_num,
        "price": 0,
        "cover": cover_url,
        "desc": caption
    }
    add_to_db(manhwa_item)
    await msg.reply_text(f"✅ مانهوای `{clean_title}` (چپتر {chapter_num}) به سایت ماتیاس اضافه شد!")

def run_telegram_bot():
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    telegram_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    threading.Thread(target=run_telegram_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
