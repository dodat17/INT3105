# ADR-0001 — Lựa chọn stack

- **Trạng thái:** Accepted
- **Ngày:** 01/10/2026
- **Yêu cầu liên quan:** Mục 8.1, mục 8.3, mục 14 của [requirements.md](../../requirements.md)

## Bối cảnh

Đặc tả yêu cầu kiến trúc phân tầng có chiều phụ thuộc kiểm chứng được, ORM/data mapper, transaction bao trùm use case ghi, migration có quản lý phiên bản và khả năng chạy lại trên Kaggle CPU với tài nguyên hạn chế.

Backend, PostgreSQL và load generator chạy chung một máy trong môi trường đo. Stack phải đủ nhẹ, cài được trực tiếp khi không có Docker daemon và vẫn cho phép kiểm thử đồng thời trên PostgreSQL thật.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược | Kết luận |
|---|---|---|---|
| Java + Spring Boot + JPA | Hệ sinh thái transaction và kiểm thử kiến trúc mạnh | RAM khởi động cao, cần JDK trên Kaggle, thời gian cài/khởi động lớn | Loại |
| Node.js + NestJS + TypeORM | DI và phân tầng có sẵn | Transaction và data mapper kém tường minh hơn cho use case khóa dòng | Loại |
| **Python 3.12 + FastAPI + SQLAlchemy 2 + PostgreSQL** | Nhẹ trên Kaggle; FastAPI sinh OpenAPI; SQLAlchemy hỗ trợ ORM lẫn SQL tường minh; pytest và Testcontainers đáp ứng kiểm thử | Phải chủ động giữ ranh giới tầng; cần chốt rõ sync/async | **Chọn** |
| Go + GORM | Dấu chân bộ nhớ nhỏ | GORM không phù hợp bằng SQLAlchemy với yêu cầu data mapper và mapping domain riêng | Loại |

## Quyết định

Sử dụng:

- Python 3.12.
- FastAPI và Pydantic 2 cho tầng API.
- Uvicorn làm ASGI server.
- SQLAlchemy 2 synchronous ORM/Core với psycopg 3.
- PostgreSQL 16.
- Alembic cho toàn bộ migration.
- PyJWT cho JWT HS256.
- bcrypt cho hash mật khẩu.
- pytest, pytest-cov, testcontainers-python và import-linter.
- `pyproject.toml` cùng `uv.lock`; chạy lệnh qua `uv run`.
- k6 tiếp tục là load generator độc lập với backend.

### Vì sao chọn SQLAlchemy synchronous

Các use case ghi dựa trên transaction, `SELECT ... FOR UPDATE`, thứ tự khóa và `rowcount`. SQLAlchemy synchronous với psycopg cho mô hình thực thi dễ lập luận và sát SQL nhất.

Các FastAPI route có truy cập DB được khai báo bằng `def`, để FastAPI chạy chúng trong thread pool thay vì chặn event loop. Ba biến sau là biến kiểm soát khi benchmark:

- `WEB_WORKERS`.
- `ANYIO_THREAD_TOKENS`.
- `DB_POOL_SIZE`.

Không trộn `AsyncSession` và `Session` trong Pha 1.

### Migration

Alembic là nguồn sự thật duy nhất của schema:

- Revision nằm trong `alembic/versions/`.
- Khởi tạo hoặc nâng cấp bằng `uv run alembic upgrade head`.
- Không gọi `Base.metadata.create_all()` khi ứng dụng khởi động.
- `GET /health/ready` chỉ trả `200` khi kết nối được DB và revision trong bảng `alembic_version` khớp Alembic head.
- Seed là lệnh riêng và chỉ chạy sau migration.

### Kiểm chứng kiến trúc

`import-linter` chạy trong CI với các hợp đồng:

- `app.domain` không import `fastapi`, `starlette`, `pydantic`, `sqlalchemy`, `psycopg`, `app.api` hoặc `app.infrastructure`.
- `app.api` không import trực tiếp `app.infrastructure.persistence`.
- `app.infrastructure` có thể import port/model của domain để cài đặt.
- Composition root trong `app.bootstrap` là nơi duy nhất biết đầy đủ các tầng.

Một vi phạm làm lệnh `uv run lint-imports` thất bại.

## Hệ quả

### Tích cực

- FastAPI tự sinh OpenAPI và Swagger UI từ Pydantic schema.
- SQLAlchemy cho phép repository trả domain model nhưng vẫn dùng SQL Core tường minh cho inventory nóng.
- Alembic quản lý schema lặp lại được và cung cấp revision để health check.
- Python đã có sẵn trên Kaggle; môi trường nhẹ hơn JVM.
- pytest và Testcontainers chạy được unit, API, transaction và concurrency test.

### Tiêu cực và đánh đổi

- Import-linter không hiểu ngữ nghĩa sâu như ArchUnit; hợp đồng import phải được viết cụ thể và có bài test cố tình vi phạm.
- FastAPI dùng thread pool cho route synchronous. Nếu thread tokens thấp hơn nhu cầu, thread pool có thể thành nút thắt; nếu quá cao so với DB pool, nhiều request chỉ chờ connection. Các giá trị phải được cố định và ghi trong benchmark metadata.
- SQLAlchemy identity map có thể giữ state cũ sau bulk update. Repository inventory phải dùng câu SQL tường minh, kiểm tra `rowcount` và expire/refresh khi cần.
- Python không tự động làm transaction qua annotation; Unit of Work phải bao trùm rõ toàn bộ use case ghi.

## Cách kiểm chứng

- `uv sync --frozen` cài được từ môi trường sạch.
- `uv run lint-imports` fail khi domain import FastAPI hoặc SQLAlchemy.
- `uv run pytest -m integration` chạy trên PostgreSQL 16 qua Testcontainers.
- `uv run alembic upgrade head` tạo schema đầy đủ trên database trống.
- `uv run alembic check` không phát hiện model/schema chưa có migration.
- Metadata benchmark ghi Python, FastAPI, SQLAlchemy, Alembic, psycopg, PostgreSQL và commit SHA.

