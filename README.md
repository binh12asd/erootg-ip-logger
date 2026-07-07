# EROOTG IP Logger - Classic Max Performance

Hệ thống track IP mạnh mẽ, giao diện Classic, tối ưu tốc độ tối đa. Dành cho EROOTG Grey Hat Team.

## Đặc điểm nổi bật
- **Track IP siêu tốc**: Trả về ảnh 1x1 pixel, hỗ trợ GZIP.
- **Xuyên proxy / Cloudflare / VPN**: Tự động lấy IP thật từ nhiều Header khác nhau (`CF-Connecting-IP`, `X-Forwarded-For`, ...).
- **Cơ sở dữ liệu SQLite**: Nhanh hơn JSON hàng trăm lần, có Index tối ưu truy vấn.
- **Cache GeoIP**: Lưu thông tin vị trí (Quốc gia, Thành phố, ISP) để tránh gọi API liên tục.
- **Giao diện Classic**: Phong cách Retro, tối giản, tải siêu nhanh.
- **Phân trang & Export**: Xem log dễ dàng, xuất dữ liệu dạng CSV.

## Cấu trúc thư mục
Source code được thiết kế tối giản, chỉ gồm 1 file server duy nhất:
erootg-ip-logger/
├── app.py # Server chính (Flask) - Chứa toàn bộ logic
├── requirements.txt # Thư viện cần cài đặt
├── Procfile # Cấu hình cho Render
└── templates/ # Giao diện Classic
├── index.html # Trang chủ
└── logs.html # Trang xem log


## Hướng dẫn deploy (lên Render)
1. **Tạo file:** Copy 4 file `app.py`, `requirements.txt`, `Procfile` và thư mục `templates` với 2 file HTML vào máy tính.
2. **Push lên GitHub:** Tạo repository và push code lên.
3. **Tạo Web Service trên Render:** Kết nối với repo GitHub, chọn gói Free.
4. **Build & Run:** Render sẽ tự động cài đặt và chạy server.

## Cách sử dụng
| Đường dẫn | Chức năng |
| :--- | :--- |
| `/` | Trang chủ (Dashboard) |
| `/track` | **Endpoint quan trọng nhất** - Dùng để ghi nhận IP của người truy cập (trả về ảnh 1x1) |
| `/logs` | Xem danh sách IP đã track (có phân trang) |
| `/stats` | Xem thống kê (Tổng số IP, số IP duy nhất) dạng JSON |
| `/export` | Tải toàn bộ log về dưới dạng file CSV |

## Lưu ý
- Server sẽ tự tạo file cơ sở dữ liệu `erootg.db` khi chạy lần đầu.
- Để giữ server không bị ngủ (Free Tier Render), bạn nên dùng [UptimeRobot](https://uptimerobot.com/) ping vào link `/` mỗi 5 phút.

---

**EROTG Grey Hat Team - Classic Edition**