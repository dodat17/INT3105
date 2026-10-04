# Movie Booking

Ứng dụng đặt vé xem phim cho một rạp, gồm React SPA và FastAPI trong cùng repository.

Frontend hiện sử dụng dữ liệu mock để thử giao diện và luồng đặt vé. REST API, cơ sở dữ liệu
và các quy tắc nghiệp vụ sẽ được kết nối theo đặc tả trong `docs/requirements.md`.

## Chức năng chính

- Xem, tìm kiếm phim và lọc lịch chiếu theo ngày.
- Xem sơ đồ ghế và trạng thái ghế.
- Chọn từ 1 đến 8 ghế, xem giá dự kiến và giữ chỗ.
- Xem hoặc hủy booking của người dùng.
- Quản trị danh mục phim, phòng và suất chiếu.
- Đăng nhập bằng JWT với quyền `CUSTOMER` và `ADMIN`.

Xác nhận booking chỉ là mô phỏng, không bao gồm thanh toán thật.

## Đặc tả nghiệp vụ

- Một rạp có nhiều phòng; mỗi phòng có sơ đồ ghế cố định.
- Một booking chỉ chứa ghế của cùng một suất chiếu.
- Ghế được giữ trong 5 phút, sau đó có thể được người khác đặt lại.
- Mỗi booking có từ 1 đến 8 ghế khác nhau.
- Giá và trạng thái ghế cuối cùng do backend quyết định, không tin dữ liệu từ frontend.
- Tạo, xác nhận và hủy booking phải chạy trong một transaction.
- Một ghế trong một suất chiếu không thể thuộc hai booking còn hiệu lực.
- Người dùng chỉ được xem, xác nhận hoặc hủy booking của chính mình.

Chi tiết đầy đủ:

- [Đặc tả yêu cầu](docs/requirements.md)
- [Kiến trúc](docs/docs/architecture.md)
- [Mô hình dữ liệu](docs/docs/data-model.md)
- [Kế hoạch kiểm thử](docs/docs/test-plan.md)

## Kiến trúc

Dự án sử dụng **modular monolith**. Frontend và backend được phát triển riêng nhưng được
triển khai thành một ứng dụng; FastAPI có thể phục vụ bản build trong `frontend/dist`.

```text
React SPA
    │ REST JSON /api/v1
    ▼
FastAPI API + Middleware
    ▼
Domain services và business rules
    ▼
Repository ports + Unit of Work
    ▼
SQLAlchemy / PostgreSQL
```

Backend được chia thành các tầng:

| Thư mục | Trách nhiệm |
|---|---|
| `app/api` | Router, schema HTTP, middleware và ánh xạ lỗi. |
| `app/domain` | Entity, use case và quy tắc nghiệp vụ thuần Python. |
| `app/infrastructure` | PostgreSQL, SQLAlchemy, JWT, bcrypt và adapter. |
| `app/bootstrap` | Cấu hình và lắp ráp ứng dụng. |
| `frontend/src` | Giao diện React, router, trạng thái client và API client. |
| `tests` | Unit test, integration test và kiểm thử đồng thời. |

Chiều phụ thuộc chính:

```text
bootstrap → api → domain
bootstrap → infrastructure → domain
```

Tầng `domain` không phụ thuộc FastAPI, Pydantic, SQLAlchemy hoặc PostgreSQL.

Các module nghiệp vụ gồm `auth`, `catalog`, `cinema`, `scheduling`, `booking` và `health`.

## Công nghệ

- Python 3.12, FastAPI, Pydantic Settings.
- SQLAlchemy, psycopg và PostgreSQL 16.
- React 19, TypeScript 6, React Router và Vite.
- pytest, Ruff, mypy, ESLint và import-linter.

## Cách chạy

### Yêu cầu

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22.13+
- npm

### Chuẩn bị cấu hình

Sao chép `.env.example` thành `.env` và thay các giá trị phù hợp với môi trường cục bộ.
Không commit `.env` hoặc secret thật.

```bash
cp .env.example .env
```

Trên PowerShell:

```powershell
Copy-Item .env.example .env
```

### Chạy backend

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8080
```

Kiểm tra:

- Ứng dụng: `http://localhost:8080`
- Health check: `http://localhost:8080/health`
- OpenAPI: `http://localhost:8080/docs`

### Chạy frontend để phát triển

Mở terminal khác:

```bash
cd frontend
npm install
npm run dev
```

Mở `http://localhost:5173`. Vite chuyển tiếp `/api` và `/health` tới backend ở cổng `8080`.

### Chạy frontend và backend cùng một cổng

```bash
cd frontend
npm install
npm run build
cd ..
uv run uvicorn app.main:app --port 8080
```

FastAPI sẽ phục vụ nội dung trong `frontend/dist` tại `http://localhost:8080`.

## Kiểm tra mã nguồn

Backend:

```bash
uv run ruff check .
uv run ruff format --check app tests
uv run mypy
uv run lint-imports
uv run pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Cấu trúc repository

```text
INT3105/
├── app/            Backend FastAPI
├── frontend/       React SPA
├── tests/          Kiểm thử backend
├── docs/           Đặc tả và tài liệu kỹ thuật
├── deploy/         Cấu hình triển khai
├── scripts/        Script hỗ trợ
└── .github/        Cấu hình CI
```
