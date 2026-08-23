# Event Management API - IT215 FastAPI Project

Dự án API Quản lý Sự kiện được phát triển bằng FastAPI, tuân thủ kiến trúc 3 tầng và các tiêu chuẩn giáo trình.

## Yêu cầu môi trường
- Python 3.11+
- MySQL Server

## Cài đặt và Chạy thử
1. Clone dự án và truy cập thư mục gốc.
2. Tạo virtual environment và kích hoạt:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
4. Cấu hình CSDL:
   Tạo file `.env` từ `.env.example` và điều chỉnh `DATABASE_URL` cho phù hợp.

5. Tạo dữ liệu mẫu (Seeding):
   ```bash
   python seed.py
   ```

6. Chạy server (do chúng ta dùng thư mục hiện tại làm root):
   ```bash
   uvicorn main:app --reload
   ```

7. Truy cập Swagger UI:
   Mở trình duyệt và vào: `http://127.0.0.1:8000/docs`
