# Phát triển cục bộ

## Yêu cầu

- Python 3.12 và `uv`.
- Node.js 22 và npm.

## Backend

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8080
```

Kiểm tra `http://localhost:8080/health`.

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
cd frontend && npm run lint && npm run typecheck && npm run build
```

Sao chép `.env.example` thành `.env` cho cấu hình cục bộ. Không commit `.env` hoặc secret thật.
