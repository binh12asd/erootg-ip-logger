from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
import os
from datetime import datetime, timedelta
from functools import lru_cache
import requests
from io import BytesIO
import csv
import json
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'EROTG123'

# === CẤU HÌNH ===
ADMIN_PASSWORD = "EROTG123"
LOG_DIR = "logs"
MAX_LINES_PER_FILE = 100
DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK', '')
LOG_RETENTION_DAYS = 30  # Tự động xóa log cũ hơn 30 ngày

# Tạo thư mục logs nếu chưa có
os.makedirs(LOG_DIR, exist_ok=True)

# === HÀM LẤY FILE LOG HIỆN TẠI ===
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
    log_entry = f"""==================================================
🆕 IP Mới Được Track!
📌 IP: {ip}
🌍 Quốc gia: {country}
🏙️ Thành phố: {city}
📡 ISP: {isp}
📂 Nguồn: {source}
📱 UA: {ua[:100]}
🕒 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==================================================
"""
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    print(f"✅ Đã ghi log: {ip} -> {file_path}")

# === HÀM ĐỌC LOG (CÓ LỌC) ===
def read_all_logs(filter_country=None, filter_isp=None, filter_source=None, days=None):
    all_logs = []
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("logs_") and f.endswith(".txt")]
    files.sort()
    
    cutoff_date = None
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
    
    for file in files:
        with open(os.path.join(LOG_DIR, file), 'r', encoding='utf-8') as f:
            content = f.read()
            entries = content.split('==================================================')
            for entry in entries:
                if not entry.strip():
                    continue
                lines = entry.strip().split('\n')
                log_data = {}
                for line in lines:
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        log_data[key.strip()] = value.strip()
                
                if filter_country and log_data.get('🌍 Quốc gia', '') != filter_country:
                    continue
                if filter_isp and log_data.get('📡 ISP', '') != filter_isp:
                    continue
                if filter_source and log_data.get('📂 Nguồn', '') != filter_source:
                    continue
                if cutoff_date:
                    try:
                        log_time = datetime.strptime(log_data.get('🕒 Thời gian', ''), '%Y-%m-%d %H:%M:%S')
                        if log_time < cutoff_date:
                            continue
                    except:
                        pass
                
                all_logs.append(log_data)
    
    return all_logs

# === HÀM XÓA LOG CŨ ===
def delete_old_logs():
    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    deleted = 0
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("logs_") and f.endswith(".txt")]
    for file in files:
        file_path = os.path.join(LOG_DIR, file)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mtime < cutoff_date:
            os.remove(file_path)
            deleted += 1
            print(f"🗑️ Đã xóa file log cũ: {file}")
    return deleted

# === CÁC HÀM TIỆN ÍCH ===
def get_real_ip(request):
    cf = request.headers.get('CF-Connecting-IP')
    if cf: return cf
    xff = request.headers.get('X-Forwarded-For')
    if xff: return xff.split(',')[0].strip()
    xri = request.headers.get('X-Real-IP')
    if xri: return xri
    return request.remote_addr

@lru_cache(maxsize=2000)
def get_geo(ip):
    # Dữ liệu mẫu cho localhost và IP nội bộ
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
        return 'Local', 'Local', 'Local'
    
    # Danh sách API dự phòng
    apis = [
        f'http://ip-api.com/json/{ip}?fields=status,country,city,isp',
        f'https://ipinfo.io/{ip}/json',
        f'https://ipapi.co/{ip}/json/'
    ]
    
    for url in apis:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code != 200:
                continue
            
            data = r.json()
            
            # Xử lý ip-api.com
            if 'status' in data and data.get('status') == 'success':
                return data.get('country', ''), data.get('city', ''), data.get('isp', '')
            
            # Xử lý ipinfo.io
            if 'country' in data:
                country = data.get('country', '')
                city = data.get('city', '')
                isp = data.get('org', '').split(' ')[0] if data.get('org') else ''
                return country, city, isp
            
            # Xử lý ipapi.co
            if 'country_name' in data:
                return data.get('country_name', ''), data.get('city', ''), data.get('org', '')
                
        except:
            continue
    
    # Nếu tất cả API đều thất bại
    return 'Unknown', 'Unknown', 'Unknown'

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

# === GỬI LOG VỀ MÁY TÍNH LOCAL ===
def send_log_to_local(ip, country, city, isp, source, ua):
    try:
        local_server = os.environ.get('LOCAL_SERVER', 'http://localhost:5000/log')
        data = {
            'ip': ip,
            'country': country,
            'city': city,
            'isp': isp,
            'source': source,
            'ua': ua,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        requests.post(local_server, json=data, timeout=2)
    except Exception as e:
        print(f"⚠️ Không gửi được log về local: {e}")

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
    bot = is_bot(ua)
    
    save_log_to_file(ip, ua, ref, country, city, isp, source)
    send_log_to_local(ip, country, city, isp, source, ua)
    send_discord_alert(ip, ua, country, city, isp, source)
    
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return send_file(BytesIO(pixel), mimetype='image/gif')

@app.route('/logs')
def view_logs():
    if not session.get('logged_in', False):
        return redirect(url_for('login_page'))
    
    country = request.args.get('country', '')
    isp = request.args.get('isp', '')
    source = request.args.get('source', '')
    days = request.args.get('days', type=int)
    
    logs = read_all_logs(country if country else None, 
                         isp if isp else None, 
                         source if source else None, 
                         days)
    
    total = len(logs)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>EROOTG - IP Logs</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: #f0f0f0; font-family: 'Courier New', monospace; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: #fff; border: 4px solid #111; padding: 30px; }}
            .header {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; border-bottom: 4px solid #111; padding-bottom: 14px; margin-bottom: 24px; }}
            .header h1 {{ font-size: 24px; font-weight: 700; }}
            .header h1 small {{ font-size: 13px; font-weight: 400; color: #555; }}
            .filter-bar {{ background: #f5f5f5; padding: 14px; border: 2px solid #ccc; margin-bottom: 20px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
            .filter-bar input, .filter-bar select {{ padding: 6px 12px; border: 2px solid #ccc; font-family: 'Courier New', monospace; }}
            .filter-bar button {{ background: #111; color: #fff; padding: 6px 16px; border: 2px solid #111; font-weight: 600; cursor: pointer; font-family: 'Courier New', monospace; }}
            .filter-bar button:hover {{ background: #fff; color: #111; }}
            table {{ width: 100%; border-collapse: collapse; border: 2px solid #111; font-size: 14px; }}
            th {{ background: #111; color: #fff; padding: 10px 12px; text-align: left; border: 1px solid #111; }}
            td {{ padding: 8px 12px; border: 1px solid #ddd; vertical-align: top; font-size: 13px; }}
            tr:nth-child(even) td {{ background: #f9f9f9; }}
            tr:hover td {{ background: #f0f0f0; }}
            .ip {{ font-weight: 700; color: #000; }}
            .back {{ display: inline-block; margin-top: 24px; background: #111; color: #fff; padding: 10px 28px; text-decoration: none; border: 2px solid #111; font-weight: 600; font-family: 'Courier New', monospace; }}
            .back:hover {{ background: #fff; color: #111; }}
            .empty {{ text-align: center; padding: 60px 20px; font-size: 18px; color: #888; border: 2px dashed #ccc; }}
            .stats {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
            .stats .item {{ background: #f5f5f5; padding: 10px 20px; border: 2px solid #ccc; }}
            .stats .item .num {{ font-size: 24px; font-weight: 700; color: #c41a1a; }}
            .footer {{ margin-top: 30px; font-size: 13px; color: #888; border-top: 2px solid #eee; padding-top: 16px; text-align: center; }}
            .footer .team {{ color: #111; font-weight: 700; }}
    """
    
    html += f"""
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1>EROOTG <small>IP Logs</small></h1>
            <span class="count">📋 {total} ban ghi</span>
        </div>
        
        <div class="stats">
            <div class="item"><span class="num">{total}</span> Tổng logs</div>
            <div class="item"><span class="num">{len(set(log.get('📌 IP', '') for log in logs)) if logs else 0}</span> IP duy nhất</div>
            <div class="item"><span class="num">{len(set(log.get('🌍 Quốc gia', '') for log in logs)) if logs else 0}</span> Quốc gia</div>
        </div>
        
        <div class="filter-bar">
            <form method="GET" style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center; width: 100%;">
                <input type="text" name="country" placeholder="Lọc theo quốc gia" value="{country}" style="flex:1; min-width:100px;">
                <input type="text" name="isp" placeholder="Lọc theo ISP" value="{isp}" style="flex:1; min-width:100px;">
                <input type="text" name="source" placeholder="Lọc theo nguồn" value="{source}" style="flex:1; min-width:100px;">
                <input type="number" name="days" placeholder="Số ngày gần đây" value="{days if days else ''}" style="width:120px;">
                <button type="submit">🔍 Lọc</button>
                <a href="/logs" style="background:#ccc; padding:6px 16px; border:2px solid #ccc; color:#111; text-decoration:none; font-weight:600;">Xóa lọc</a>
            </form>
        </div>
    """
    
    if logs:
        html += """
        <table>
            <thead>
                <tr>
                    <th>IP</th>
                    <th>Quốc gia</th>
                    <th>ISP</th>
                    <th>Nguồn</th>
                    <th>Thời gian</th>
                </tr>
            </thead>
            <tbody>
        """
        for log in logs:
            html += f"""
                <tr>
                    <td class="ip">{log.get('📌 IP', 'N/A')}</td>
                    <td>{log.get('🌍 Quốc gia', 'N/A')}</td>
                    <td>{log.get('📡 ISP', 'N/A')}</td>
                    <td>{log.get('📂 Nguồn', 'unknown')}</td>
                    <td>{log.get('🕒 Thời gian', 'N/A')}</td>
                </tr>
            """
        html += """
            </tbody>
        </table>
        """
    else:
        html += '<div class="empty">📭 Không có log nào khớp với bộ lọc</div>'
    
    html += f"""
        <a href="/" class="back">← Trang chủ</a>
        <div class="footer">
            <span class="team">EROTG Grey Hat Team</span> • Classic Edition
        </div>
    </div>
    </body>
    </html>
    """
    
    return html

# === ROUTE DASHBOARD (BIỂU ĐỒ) ===
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in', False):
        return redirect(url_for('login_page'))
    
    logs = read_all_logs()
    
    countries = Counter([log.get('🌍 Quốc gia', 'Unknown') for log in logs])
    sources = Counter([log.get('📂 Nguồn', 'unknown') for log in logs])
    
    daily = defaultdict(int)
    for log in logs:
        try:
            date = datetime.strptime(log.get('🕒 Thời gian', ''), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            daily[date] += 1
        except:
            pass
    dates = sorted(daily.keys())[-30:]
    daily_values = [daily[date] for date in dates]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>EROOTG - Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: #f0f0f0; font-family: 'Courier New', monospace; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: #fff; border: 4px solid #111; padding: 30px; }}
            .header {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; border-bottom: 4px solid #111; padding-bottom: 14px; margin-bottom: 24px; }}
            .header h1 {{ font-size: 24px; font-weight: 700; }}
            .header h1 small {{ font-size: 13px; font-weight: 400; color: #555; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
            .card {{ background: #f5f5f5; border: 2px solid #ccc; padding: 20px; }}
            .card h3 {{ margin-bottom: 12px; font-size: 16px; }}
            .bar {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
            .bar .label {{ width: 120px; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
            .bar .fill {{ height: 20px; background: #c41a1a; border-radius: 2px; }}
            .bar .value {{ font-size: 13px; font-weight: 600; margin-left: 8px; }}
            .back {{ display: inline-block; margin-top: 24px; background: #111; color: #fff; padding: 10px 28px; text-decoration: none; border: 2px solid #111; font-weight: 600; }}
            .back:hover {{ background: #fff; color: #111; }}
            .footer {{ margin-top: 30px; font-size: 13px; color: #888; border-top: 2px solid #eee; padding-top: 16px; text-align: center; }}
            @media (max-width: 700px) {{ .grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1>EROOTG <small>Dashboard</small></h1>
            <span>📊 Thống kê IP</span>
        </div>
        
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
            <div style="background:#f5f5f5; padding:10px 20px; border:2px solid #ccc;">
                <span style="font-size:24px; font-weight:700; color:#c41a1a;">{len(logs)}</span> Tổng logs
            </div>
            <div style="background:#f5f5f5; padding:10px 20px; border:2px solid #ccc;">
                <span style="font-size:24px; font-weight:700; color:#c41a1a;">{len(set([log.get('📌 IP', '') for log in logs]))}</span> IP duy nhất
            </div>
            <div style="background:#f5f5f5; padding:10px 20px; border:2px solid #ccc;">
                <span style="font-size:24px; font-weight:700; color:#c41a1a;">{len(countries)}</span> Quốc gia
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🌍 Top Quốc Gia</h3>
    """
    max_val = max(countries.values()) if countries else 1
    for label, value in sorted(countries.items(), key=lambda x: -x[1])[:10]:
        percent = (value / max_val) * 100 if max_val > 0 else 0
        html += f"""
                <div class="bar">
                    <span class="label">{label[:15]}</span>
                    <div class="fill" style="width:{percent}%;"></div>
                    <span class="value">{value}</span>
                </div>
        """
    
    html += """
            </div>
            <div class="card">
                <h3>📂 Top Nguồn Track</h3>
    """
    max_val = max(sources.values()) if sources else 1
    for label, value in sorted(sources.items(), key=lambda x: -x[1])[:10]:
        percent = (value / max_val) * 100 if max_val > 0 else 0
        html += f"""
                <div class="bar">
                    <span class="label">{label[:15]}</span>
                    <div class="fill" style="width:{percent}%;"></div>
                    <span class="value">{value}</span>
                </div>
        """
    
    html += f"""
            </div>
        </div>
        
        <div class="card" style="margin-top:20px;">
            <h3>📈 Log theo ngày (30 ngày gần nhất)</h3>
            <div style="display: flex; align-items: flex-end; gap: 4px; height: 150px; padding: 10px 0; overflow-x: auto;">
    """
    if daily_values:
        max_daily = max(daily_values) if daily_values else 1
        for i, date in enumerate(dates):
            height = (daily_values[i] / max_daily) * 120 if max_daily > 0 else 0
            html += f"""
                <div style="display:flex; flex-direction:column; align-items:center; min-width:30px;">
                    <div style="height:{height}px; width:20px; background:#c41a1a; border-radius:2px;"></div>
                    <span style="font-size:9px; margin-top:4px; color:#555; transform:rotate(-45deg);">{date[-5:]}</span>
                </div>
            """
    else:
        html += '<div style="padding:20px; color:#888;">Chưa có dữ liệu</div>'
    
    html += """
            </div>
        </div>
        
        <a href="/" class="back">← Trang chủ</a>
        <a href="/logs" class="back" style="margin-left:10px;">📋 Xem Log</a>
        
        <div class="footer">
            <span class="team">EROTG Grey Hat Team</span> • Classic Edition
        </div>
    </div>
    </body>
    </html>
    """
    
    return html

# === CÁC ROUTE KHÁC ===
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
        'unique_ips': len(set([log.get('📌 IP', '') for log in logs])),
        'countries': len(set([log.get('🌍 Quốc gia', '') for log in logs])),
        'status': 'online'
    })

@app.route('/export/csv')
def export_csv():
    if not session.get('logged_in', False):
        return redirect(url_for('login_page'))
    
    logs = read_all_logs()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['IP', 'Quốc gia', 'Thành phố', 'ISP', 'Nguồn', 'User-Agent', 'Thời gian'])
    for log in logs:
        writer.writerow([
            log.get('📌 IP', ''),
            log.get('🌍 Quốc gia', ''),
            log.get('🏙️ Thành phố', ''),
            log.get('📡 ISP', ''),
            log.get('📂 Nguồn', ''),
            log.get('📱 UA', ''),
            log.get('🕒 Thời gian', '')
        ])
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': f'attachment; filename=erootg_logs_{datetime.now().strftime("%Y%m%d")}.csv'
    }

@app.route('/cleanup')
def cleanup():
    if not session.get('logged_in', False):
        return redirect(url_for('login_page'))
    
    deleted = delete_old_logs()
    return f"🗑️ Đã xóa {deleted} file log cũ hơn {LOG_RETENTION_DAYS} ngày. <a href='/logs'>Quay lại</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
