from flask import Flask, request
import os
from datetime import datetime

app = Flask(__name__)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_current_log_file():
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("log_") and f.endswith(".txt")]
    if not files:
        return os.path.join(LOG_DIR, "log_1.txt")
    files.sort()
    last_file = files[-1]
    last_path = os.path.join(LOG_DIR, last_file)
    with open(last_path, 'r', encoding='utf-8') as f:
        line_count = sum(1 for _ in f)
    if line_count >= 100:
        next_num = int(last_file.split('_')[1].split('.')[0]) + 1
        return os.path.join(LOG_DIR, f"log_{next_num}.txt")
    return last_path

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    if not data:
        return "No data", 400
    
    ip = data.get('ip', 'Unknown')
    country = data.get('country', 'Unknown')
    city = data.get('city', 'Unknown')
    isp = data.get('isp', 'Unknown')
    source = data.get('source', 'Unknown')
    ua = data.get('ua', 'Unknown')
    time = data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    log_entry = f"""-----------------------------------------
🆕 IP Mới Được Track!
📌 IP: {ip}
🌍 Quốc gia: {country}
🏙️ Thành phố: {city}
📡 ISP: {isp}
📂 Nguồn: {source}
📱 UA: {ua[:80]}
🕒 Thời gian: {time}
-----------------------------------------
"""
    file_path = get_current_log_file()
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(f"✅ Đã ghi log: {ip} -> {file_path}")
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)