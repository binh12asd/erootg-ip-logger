# EROOTG IP Logger - v2.0

Hệ thống track IP mạnh mẽ, giao diện Classic, tích hợp Dashboard, lọc log nâng cao, và nhiều tính năng chuyên nghiệp. Dành cho EROOTG Grey Hat Team.

---

## 🚀 Tính năng

- **Track IP siêu tốc** - Trả về ảnh 1x1 pixel, hỗ trợ GZIP
- **Xuyên proxy / Cloudflare / VPN** - Tự động lấy IP thật từ nhiều Header (`CF-Connecting-IP`, `X-Forwarded-For`, ...)
- **Dashboard thống kê trực quan** - Biểu đồ quốc gia, nguồn track, log theo ngày
- **Bộ lọc log nâng cao** - Lọc theo quốc gia, ISP, nguồn, số ngày gần đây
- **Nhiều link track** - Hỗ trợ theo dõi nguồn: `/track/fb`, `/track/zalo`, `/track/discord`, `/track/email`, ...
- **Export CSV** - Tải toàn bộ log dạng CSV để phân tích
- **Tự động xóa log cũ** - Giữ log 30 ngày (có thể tùy chỉnh)
- **Lưu log dạng file txt** - Mỗi file 100 dòng, tự động tách file mới
- **Discord Alert** - Gửi thông báo real-time khi có IP mới (tùy chọn)
- **Giao diện Classic** - Phong cách Retro, tối giản, tải siêu nhanh
- **Đăng nhập bảo mật** - Trang login với mật khẩu `EROTG123`

---

## 📁 Cấu trúc thư mục
erootg-ip-logger/
├── app.py # Server chính (Flask) - Chạy trên Render
├── requirements.txt # Thư viện cần cài đặt
├── Procfile # Cấu hình cho Render
├── logs/ # Thư mục chứa file log (tự tạo)
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
3. Chạy local (tùy chọn - để nhận log về máy tính)
bash
python local_log_server.py
4. Deploy lên Render
Push code lên GitHub

Tạo Web Service trên Render, kết nối với repo

Thêm biến môi trường (nếu dùng Discord):

DISCORD_WEBHOOK = link webhook Discord

LOCAL_SERVER = link local server (nếu dùng)

🎯 Cách sử dụng
Đường dẫn	Chức năng
/	Trang chủ
/track	Track IP (mặc định, không ghi nguồn)
/track/fb	Track IP - nguồn Facebook
/track/zalo	Track IP - nguồn Zalo
/track/discord	Track IP - nguồn Discord
/track/email	Track IP - nguồn Email
/logs	Xem log (có bộ lọc nâng cao)
/dashboard	Dashboard thống kê trực quan
/stats	Xem thống kê JSON
/export/csv	Tải log dạng CSV
/cleanup	Xóa log cũ (cần đăng nhập)
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
📊 Dashboard
Dashboard cung cấp các thống kê trực quan:

Top quốc gia - Xem quốc gia có nhiều IP nhất

Top nguồn track - Xem nguồn nào hiệu quả nhất

Log theo ngày - Biểu đồ cột log trong 30 ngày gần nhất

Tổng quan - Tổng số log, IP duy nhất, số quốc gia

🔥 Lưu ý
Render Free Tier: File log trên Render có thể bị xóa khi deploy lại. Để lưu trữ vĩnh viễn, hãy chạy local_log_server.py và cấu hình để Render gửi log về máy tính của bạn.

Ngrok: Nếu máy tính không có IP công khai, dùng ngrok http 5000 để tạo tunnel.

Discord: Nếu muốn nhận thông báo qua Discord, thêm biến môi trường DISCORD_WEBHOOK trên Render.

Bảo mật: Đừng chia sẻ link /logs và /dashboard cho người khác nếu không có mật khẩu.
