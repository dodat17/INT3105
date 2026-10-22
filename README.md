# Movie Booking

Ứng dụng đặt vé xem phim gồm FastAPI, PostgreSQL và React.

## Chạy toàn bộ bằng Docker

### Yêu cầu

- Docker Desktop hoặc Docker Engine có Compose

### Khởi động

Từ thư mục gốc của repository:

```bash
docker compose up --build -d
docker compose run --rm seed
```

Compose sẽ tự động:

- Khởi động PostgreSQL 16.
- Chạy migration bằng Alembic.
- Build frontend và backend.
- Mở ứng dụng tại http://localhost:8080.

Tài khoản quản trị được tạo bởi lệnh seed:

```text
Email: admin@example.test
Mật khẩu: admin12345
```

Người dùng thông thường có thể đăng ký trực tiếp trên giao diện.

### Kiểm tra và dừng

```bash
docker compose ps
docker compose logs -f app
docker compose down
```

Dữ liệu PostgreSQL được giữ trong Docker volume. Chỉ chạy lệnh sau khi muốn xóa toàn bộ dữ liệu cục bộ:

```bash
docker compose down -v
```

### Tùy chỉnh cấu hình

Tạo `.env` trước khi khởi động nếu cần đổi mật khẩu database, JWT, cổng hoặc tài khoản seed.

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Các biến thường dùng: `APP_PORT`, `POSTGRES_PASSWORD`, `JWT_SECRET`, `SEED_ADMIN_EMAIL` và `SEED_ADMIN_PASSWORD`.

## Chạy để phát triển

### Yêu cầu

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22.13+ và npm
- PostgreSQL 16

### 1. Chuẩn bị PostgreSQL

Nếu chưa có PostgreSQL cục bộ, có thể tạo bằng Docker:

```bash
docker run --name movie-booking-db -d -e POSTGRES_USER=movie_booking -e POSTGRES_PASSWORD=movie_booking -e POSTGRES_DB=movie_booking -p 5432:5432 postgres:16-alpine
```

Những lần chạy sau chỉ cần:

```bash
docker start movie-booking-db
```

### 2. Cài đặt backend và tạo dữ liệu

Tạo `.env` theo hướng dẫn ở trên, sau đó chạy:

```bash
uv sync
uv run alembic upgrade head
uv run python scripts/seed.py
```

Lệnh seed an toàn khi chạy lại và không tạo trùng dữ liệu mẫu.

### 3. Chạy backend

```bash
uv run uvicorn app.main:app --reload --port 8080
```

- Health check: http://localhost:8080/health
- Swagger UI: http://localhost:8080/docs

### 4. Chạy frontend

Trong terminal khác:

```bash
cd frontend
npm ci
npm run dev
```

Mở http://localhost:5173. Vite tự chuyển tiếp API đến backend tại cổng `8080`.

## Kiểm tra mã nguồn

Backend:

```bash
uv run ruff check .
uv run ruff format --check app tests
uv run mypy
uv run lint-imports
uv run pytest
uv run alembic check
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Tài liệu yêu cầu chi tiết nằm tại [docs/requirements.md](docs/requirements.md).
