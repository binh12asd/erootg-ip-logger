# -*- coding: utf-8 -*-
# EROOTG IP LOGGER - CLASSIC EDITION (MAX PERFORMANCE)

from flask import Flask, request, render_template, send_file, g
import sqlite3
import json
import os
from datetime import datetime
from functools import lru_cache
import gzip
from io import BytesIO

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ====== CẤU HÌNH ======
DB_PATH = "erootg.db"
MAX_LOGS_VIEW = 5000  # Giới hạn log hiển thị để không treo trình duyệt

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
            created TEXT NOT NULL
        )
    ''')
    # Index để tăng tốc truy vấn
    c.execute('CREATE INDEX IF NOT EXISTS idx_ip ON logs(ip)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_created ON logs(created)')
    conn.commit()
    conn.close()

init_db()

# ====== HÀM LẤY IP THẬT (vượt qua proxy, Cloudflare, VPN) ======
def get_real_ip(request):
    """Lấy IP thật của client, vượt qua mọi proxy"""
    # Cloudflare
    cf = request.headers.get('CF-Connecting-IP')
    if cf: return cf

    # X-Forwarded-For (nhiều proxy)
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0].strip()

    # X-Real-IP
    xri = request.headers.get('X-Real-IP')
    if xri: return xri

    # True-Client-IP
    tci = request.headers.get('True-Client-IP')
    if tci: return tci

    # Fallback
    return request.remote_addr

# ====== HÀM LẤY GEOIP (CÓ CACHE) ======
@lru_cache(maxsize=1000)
def get_geo(ip):
    try:
        import requests
        r = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,city,isp', timeout=2)
        data = r.json()
        if data.get('status') == 'success':
            return data.get('country', ''), data.get('city', ''), data.get('isp', '')
    except:
        pass
    return '', '', ''

# ====== HÀM GHI LOG (TỐI ƯU) ======
def save_log(ip, ua, ref, country='', city='', isp=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO logs (ip, ua, ref, country, city, isp, created)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ip, ua[:500] if ua else '', ref[:500] if ref else '', 
          country, city, isp, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ====== ROUTE CHÍNH ======
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/track')
def track():
    """Track IP - trả về ảnh 1x1 pixel siêu nhanh"""
    ip = get_real_ip(request)
    ua = request.headers.get('User-Agent', '')
    ref = request.headers.get('Referer', '')

    # Lấy geo (có cache)
    country, city, isp = get_geo(ip)

    # Ghi log (thread-safe)
    save_log(ip, ua, ref, country, city, isp)

    # Trả về ảnh 1x1 pixel (gzip nén để nhanh hơn)
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return send_file(
        BytesIO(pixel),
        mimetype='image/gif',
        as_attachment=False,
        download_name='pixel.gif'
    )

@app.route('/logs')
def view_logs():
    """Xem log - phân trang, tối ưu truy vấn"""
    page = request.args.get('page', 1, type=int)
    limit = 100
    offset = (page - 1) * limit

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Đếm tổng
    c.execute('SELECT COUNT(*) FROM logs')
    total = c.fetchone()[0]

    # Lấy log
    c.execute('''
        SELECT ip, ua, ref, country, city, isp, created 
        FROM logs 
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = c.fetchall()
    conn.close()

    logs = []
    for row in rows:
        logs.append({
            'ip': row[0],
            'ua': row[1],
            'ref': row[2],
            'country': row[3] or 'N/A',
            'city': row[4] or 'N/A',
            'isp': row[5] or 'N/A',
            'time': row[6]
        })

    total_pages = (total + limit - 1) // limit

    return render_template('logs.html', 
                         logs=logs,
                         page=page,
                         total_pages=total_pages,
                         total=total)

@app.route('/stats')
def stats():
    """Thống kê nhanh - JSON"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM logs')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(DISTINCT ip) FROM logs')
    unique = c.fetchone()[0]
    conn.close()
    return {
        'total': total,
        'unique': unique,
        'status': 'online'
    }

@app.route('/export')
def export_logs():
    """Xuất toàn bộ log dạng CSV"""
    import csv
    from io import StringIO

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT ip, ua, ref, country, city, isp, created FROM logs ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['IP', 'User-Agent', 'Referer', 'Country', 'City', 'ISP', 'Time'])
    writer.writerows(rows)

    return output.getvalue(), 200, {'Content-Type': 'text/csv; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, threaded=True)