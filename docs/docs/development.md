# Phát triển cục bộ

## Yêu cầu

- Python 3.12 và `uv`.
- Node.js 22 và npm.

## Backend

```bash
uv sync
uv run alembic upgrade head      # tạo/cập nhật schema theo DATABASE_URL
uv run python scripts/seed.py    # tài khoản ADMIN + phim mẫu; chạy lại không tạo trùng
uv run uvicorn app.main:app --reload --port 8080
```

Kiểm tra `http://localhost:8080/health`. Swagger ở `http://localhost:8080/docs`: gọi
`POST /api/v1/auth/login`, sao chép `accessToken` rồi bấm **Authorize**.

Tài khoản ADMIN mặc định của seed (chỉ dùng cho development): `admin@example.test` /
`admin12345`, đổi qua `SEED_ADMIN_EMAIL` và `SEED_ADMIN_PASSWORD`. Không có API nào cấp
quyền ADMIN; tài khoản đăng ký qua `POST /api/v1/auth/register` luôn là `CUSTOMER`.

Mọi route dưới `/api/` mặc định yêu cầu Bearer token. Danh sách route công khai nằm ở
`app/api/common/auth.py`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite chuyển tiếp `/api` và `/health` tới backend ở cổng `8080`.

## Chạy cùng một ứng dụng

```bash
cd frontend
npm run build
cd ..
uv run uvicorn app.main:app --port 8080
```

FastAPI phục vụ nội dung trong `frontend/dist` tại `/`.

## Kiểm tra

```bash
uv run ruff check .
uv run ruff format --check app tests
uv run mypy
uv run lint-imports
uv run pytest
uv run alembic check
cd frontend && npm run lint && npm run typecheck && npm run build
```

`pytest` mặc định dùng SQLite tạm. Đặt `TEST_DATABASE_URL` để chạy trên PostgreSQL như CI;
database đó bị xóa sạch dữ liệu giữa các test, không trỏ vào dữ liệu thật.

Sao chép `.env.example` thành `.env` cho cấu hình cục bộ. Không commit `.env` hoặc secret thật.
