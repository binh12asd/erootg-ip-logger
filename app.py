from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
import sqlite3
import json
import os
from datetime import datetime
from functools import lru_cache
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'erootg_secret_key_2025'

# ====== CẤU HÌNH ======
DB_PATH = "erootg.db"
ADMIN_PASSWORD = "EROTG1234"

# === THAY URL NÀY BẰNG WEBHOOK CỦA BẠN ===
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."  # 👈 PASTE LINK CỦA BẠN VÀO ĐÂY

# Danh sách bot User-Agent
BOT_USER_AGENTS = [
    'Googlebot', 'Bingbot', 'Slurp', 'DuckDuckBot', 'Baiduspider',
    'YandexBot', 'Sogou', 'Exabot', 'facebot', 'facebookexternalhit',
    'Twitterbot', 'WhatsApp', 'TelegramBot', 'Discordbot',
    'UptimeRobot', 'Pingdom', 'NewRelicPinger', 'StatusCake',
    'curl', 'wget', 'python-requests', 'Go-http-client'
]

# ====== KHỞI TẠO DATABASE ======
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            ua TEXT,
            ref TEXT,
            country TEXT,
            city TEXT,
            isp TEXT,
            is_bot BOOLEAN DEFAULT 0,
            created TEXT NOT NULL
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_ip ON logs(ip)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_created ON logs(created)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_bot ON logs(is_bot)')
    conn.commit()
    conn.close()

init_db()

# ====== KIỂM TRA ĐĂNG NHẬP ======
def is_logged_in():
    return session.get('logged_in', False)

# ====== LẤY IP THẬT ======
def get_real_ip(request):
    cf = request.headers.get('CF-Connecting-IP')
    if cf: return cf
    xff = request.headers.get('X-Forwarded-For')
    if xff: return xff.split(',')[0].strip()
    xri = request.headers.get('X-Real-IP')
    if xri: return xri
    return request.remote_addr

# ====== GEOIP CÓ CACHE ======
@lru_cache(maxsize=1000)
def get_geo(ip):
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,city,isp', timeout=2)
        data = r.json()
        if data.get('status') == 'success':
            return data.get('country', ''), data.get('city', ''), data.get('isp', '')
    except:
        pass
    return '', '', ''

# ====== KIỂM TRA BOT ======
def is_bot(ua):
    ua_lower = ua.lower() if ua else ''
    for bot in BOT_USER_AGENTS:
        if bot.lower() in ua_lower:
            return True
    return False

# ====== GỬI THÔNG BÁO DISCORD ======
def send_discord_alert(ip, ua, country, city, isp):
    if not DISCORD_WEBHOOK:
        return
    try:
        message = (
            f"🆕 **IP Mới Được Track!**\n"
            f"📌 IP: `{ip}`\n"
            f"🌍 Quốc gia: {country}\n"
            f"🏙️ Thành phố: {city}\n"
            f"📡 ISP: {isp}\n"
            f"📱 UA: `{ua[:80]}`\n"
            f"🕒 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=2)
    except Exception as e:
        print(f"Lỗi gửi Discord: {e}")

# ====== GHI LOG ======
def save_log(ip, ua, ref, country='', city='', isp='', is_bot=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO logs (ip, ua, ref, country, city, isp, is_bot, created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ip, ua[:500] if ua else '', ref[:500] if ref else '',
          country, city, isp, 1 if is_bot else 0, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ====== ROUTE ======
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('view_logs'))
        else:
            return render_template('login.html', error='Sai mật khẩu!')
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

@app.route('/track')
def track():
    ip = get_real_ip(request)
    ua = request.headers.get('User-Agent', '')
    ref = request.headers.get('Referer', '')
    country, city, isp = get_geo(ip)
    bot = is_bot(ua)
    save_log(ip, ua, ref, country, city, isp, bot)
    
    # === GỬI THÔNG BÁO DISCORD ===
    send_discord_alert(ip, ua, country, city, isp)
    # =============================
    
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return send_file(BytesIO(pixel), mimetype='image/gif')

@app.route('/logs')
def view_logs():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    
    page = request.args.get('page', 1, type=int)
    limit = 100
    offset = (page - 1) * limit
    show_bot = request.args.get('show_bot', '0') == '1'
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if show_bot:
        c.execute('SELECT COUNT(*) FROM logs')
    else:
        c.execute('SELECT COUNT(*) FROM logs WHERE is_bot = 0')
    total = c.fetchone()[0]
    
    if show_bot:
        c.execute('SELECT ip, ua, ref, country, city, isp, is_bot, created FROM logs ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
    else:
        c.execute('SELECT ip, ua, ref, country, city, isp, is_bot, created FROM logs WHERE is_bot = 0 ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
    rows = c.fetchall()
    conn.close()
    
    logs = []
    for r in rows:
        logs.append({
            'ip': r[0], 'ua': r[1], 'ref': r[2],
            'country': r[3] or 'N/A', 'city': r[4] or 'N/A',
            'isp': r[5] or 'N/A', 'is_bot': r[6],
            'time': r[7]
        })
    
    total_pages = (total + limit - 1) // limit
    return render_template('logs.html', 
                         logs=logs, page=page, total_pages=total_pages,
                         total=total, show_bot=show_bot)

@app.route('/stats')
def stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM logs')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(DISTINCT ip) FROM logs')
    unique = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM logs WHERE is_bot = 1')
    bot_count = c.fetchone()[0]
    conn.close()
    return jsonify({
        'total': total,
        'unique': unique,
        'bot': bot_count,
        'human': total - bot_count,
        'status': 'online'
    })

@app.route('/export')
def export_logs():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    
    import csv
    from io import StringIO
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT ip, ua, ref, country, city, isp, is_bot, created FROM logs ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['IP', 'User-Agent', 'Referer', 'Country', 'City', 'ISP', 'Is_Bot', 'Time'])
    writer.writerows(rows)
    return output.getvalue(), 200, {'Content-Type': 'text/csv; charset=utf-8'}

@app.route('/ping')
def ping():
    return 'pong', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
