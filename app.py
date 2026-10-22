import os
import json
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

DATA_FILE = "matthias_database.json"
TOKEN = "8642920714:AAHQlTd2KDtx3riU8qkp1C5ElPU_igVdUO0"

def load_db():
    if not os.path.exists(DATA_FILE):
        initial_data = [
            {
                "id": 1,
                "title": "Solo Leveling",
                "chapters": 179,
                "price": 120000,
                "genre": "اکشن، سیستم، فانتزی",
                "translator": "تیم ماتیاس",
                "status": "کامل شده",
                "rating": 4.9,
                "cover": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500",
                "desc": "داستان جین وو در دنیایی با دروازه‌ها و هیولاها...",
                "files": []
            }
        ]
        save_db(initial_data)
        return initial_data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/manhwas', methods=['GET'])
def get_manhwas():
    db = load_db()
    return jsonify(db)

@app.route('/api/manhwas', methods=['POST'])
def add_manhwa_manual():
    data = request.json
    db = load_db()
    
    title = data.get("title", "بدون عنوان").strip()
    title_lower = title.lower()
    
    existing = next((item for item in db if item["title"].lower() == title_lower), None)
    
    if existing:
        existing["chapters"] = int(data.get("chapters", existing["chapters"]))
        existing["price"] = int(data.get("price", existing["price"]))
        existing["genre"] = data.get("genre", existing["genre"])
        existing["translator"] = data.get("translator", existing["translator"])
        existing["status"] = data.get("status", existing["status"])
        existing["rating"] = float(data.get("rating", existing["rating"]))
        if data.get("cover"):
            existing["cover"] = data.get("cover")
        if data.get("desc"):
            existing["desc"] = data.get("desc")
    else:
        new_item = {
            "id": len(db) + 1,
            "title": title,
            "chapters": int(data.get("chapters", 1)),
            "price": int(data.get("price", 0)),
            "genre": data.get("genre", "نامشخص"),
            "translator": data.get("translator", "ماتیاس"),
            "status": data.get("status", "در حال انتشار"),
            "rating": float(data.get("rating", 5.0)),
            "cover": data.get("cover", "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500"),
            "desc": data.get("desc", ""),
            "files": []
        }
        db.append(new_item)
        
    save_db(db)
    return jsonify({"status": "success", "message": "با موفقیت ذخیره شد"})

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    if not update:
        return "OK", 200
        
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text") or message.get("caption", "مانهوای تلگرامی")
    photo = message.get("photo")
    document = message.get("document")
    
    # استخراج نام و چپتر از متن پیام
    title = text.split("-")[0].strip() if "-" in text else text.strip()
    if len(title) > 35:
        title = "مانهوای آرشیو جدید"
        
    cover_url = None
    file_info = None
    
    if photo:
        file_id = photo[-1].get("file_id")
        file_path_res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()
        if file_path_res.get("ok"):
            f_path = file_path_res["result"]["file_path"]
            cover_url = f"https://api.telegram.org/file/bot{TOKEN}/{f_path}"
            
    if document:
        file_id = document.get("file_id")
        file_name = document.get("file_name", "chapter_file.zip")
        file_path_res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()
        if file_path_res.get("ok"):
            f_path = file_path_res["result"]["file_path"]
            file_info = {
                "name": file_name,
                "url": f"https://api.telegram.org/file/bot{TOKEN}/{f_path}"
            }

    db = load_db()
    title_lower = title.lower()
    existing = next((item for item in db if item["title"].lower() == title_lower), None)
    
    if existing:
        existing["chapters"] += 1
        if cover_url:
            existing["cover"] = cover_url
        if file_info:
            existing.setdefault("files", []).append(file_info)
    else:
        new_item = {
            "id": len(db) + 1,
            "title": title,
            "chapters": 1,
            "price": 50000,
            "genre": "اکشن، فانتزی",
            "translator": "ربات تلگرام",
            "status": "در حال انتشار",
            "rating": 5.0,
            "cover": cover_url if cover_url else "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500",
            "desc": f"ثبت شده از طریق ربات. کپشن: {text}",
            "files": [file_info] if file_info else []
        }
        db.append(new_item)
        
    save_db(db)
    
    if chat_id:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"✅ مانهوای '{title}' با موفقیت به آرشیو ماتیاس اضافه/آپدیت شد!"
        })
        
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
