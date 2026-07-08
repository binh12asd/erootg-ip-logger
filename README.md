 EROOTG IP Logger

Hệ thống track IP mạnh mẽ, giao diện Classic, tối ưu tốc độ tối đa. Dành cho EROOTG Grey Hat Team.

---

## 🚀 Tính năng

- **Track IP siêu tốc** - Trả về ảnh 1x1 pixel, hỗ trợ GZIP
- **Xuyên proxy / Cloudflare / VPN** - Tự động lấy IP thật từ nhiều Header (`CF-Connecting-IP`, `X-Forwarded-For`, ...)
- **3 hệ thống lưu log song song:**
  - **Render (file txt)** - Lưu trên server, xem qua web `/logs`
  - **Discord Alert** - Gửi thông báo real-time khi có IP mới
  - **Local (máy tính)** - Gửi log về máy tính để lưu trữ vĩnh viễn
- **Giao diện Classic** - Phong cách Retro, tối giản, tải siêu nhanh
- **Phân trang & Export** - Xem log dễ dàng, xuất dữ liệu dạng CSV
- **Đăng nhập bảo mật** - Trang login với mật khẩu `EROTG123`

---

## 📁 Cấu trúc thư mục
erootg-ip-logger/
├── app.py # Server chính (Flask) - Chạy trên Render
├── local_log_server.py # Server local để nhận log (chạy trên máy tính)
├── requirements.txt # Thư viện cần cài đặt
├── Procfile # Cấu hình cho Render
├── logs/ # Thư mục chứa file log trên Render
│ ├── logs_1.txt
│ ├── logs_2.txt
│ └── ...
└── templates/ # Giao diện Classic
├── index.html
├── logs.html
└── login.html

---

## 🔧 Cách cài đặt và chạy

### 1. Clone repository
```bash
git clone https://github.com/binh12asd/erootg-ip-logger
cd erootg-ip-logger
2. Cài thư viện
bash
pip install -r requirements.txt
3. Chạy server local (để nhận log)
bash
python local_log_server.py
→ Server chạy tại http://localhost:5000

4. Cấu hình IP local trong app.py
Mở app.py, sửa dòng:

python
local_server = "http://localhost:5000/log"  # Thay IP nếu dùng ngrok
5. Deploy lên Render
Push code lên GitHub

Tạo Web Service trên Render, kết nối với repo

Thêm biến môi trường (nếu dùng Discord):

DISCORD_WEBHOOK = link webhook Discord

🎯 Cách sử dụng
Đường dẫn	Chức năng
/	Trang chủ
/track	Track IP (gửi cho nạn nhân)
/track/<source>	Track IP kèm nguồn (ví dụ: /track/discord)
/logs	Xem log (yêu cầu đăng nhập)
/stats	Xem thống kê JSON
/login	Trang đăng nhập
/logout	Đăng xuất
Mật khẩu đăng nhập: EROTG123

📂 Định dạng file log
Mỗi file log (logs_1.txt, logs_2.txt, ...) có định dạng:

text
==================================================
🆕 IP Mới Được Track!
📌 IP: 123.45.67.89
🌍 Quốc gia: Vietnam
🏙️ Thành phố: Hanoi
📡 ISP: Viettel
📂 Nguồn: discord
📱 UA: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
🕒 Thời gian: 2026-07-08 14:30:00
==================================================
🔥 Lưu ý
Render Free Tier: File log trên Render có thể bị xóa khi deploy lại. Để lưu trữ vĩnh viễn, hãy chạy local_log_server.py và cấu hình để Render gửi log về máy tính của bạn.

Ngrok: Nếu máy tính không có IP công khai, dùng ngrok http 5000 để tạo tunnel.

Discord: Nếu muốn nhận thông báo qua Discord, thêm biến môi trường DISCORD_WEBHOOK trên Render.

