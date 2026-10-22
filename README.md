# Kiến trúc phần mềm - INT3105
- Nguyễn Chí Công vjp pro - 23021481
- Lê Anh Duy - 23021501
- Đỗ Thành Đạt - 23021517

# Movie Booking

Ứng dụng web đặt vé xem phim cho một rạp chiếu phim. Hệ thống cho phép người dùng có thể xem lịch chiếu, thông tin các bộ phim sắp trình chiếu, đặt vé,...

## Tác nhân và nghiệp vụ

- **Khách chưa đăng ký:** xem danh sách phim, chi tiết phim, lịch chiếu và sơ đồ ghế, đăng ký tài khoản.
- **Khách đã đăng ký:** đăng nhập, đặt vé, hủy vé, xem vé đã đặt.
- **Quản trị viên:** quản lý phim, phòng chiếu và suất chiếu.

## Hướng dẫn chạy dự án

### Yêu cầu

Cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) và bảo đảm Docker đang chạy.

### Khởi động

Mở terminal tại thư mục gốc của dự án và chạy:

```bash
docker compose up --build -d
docker compose run --rm seed
```

Ứng dụng sẽ chạy trên http://localhost:8080. Sử dụng tài khoản quản trị mẫu sau để test các chức năng: 

```yaml
Email: admin@example.test
Mật khẩu: admin12345
```

## Kiến trúc

Dự án tuân theo kiến trúc **modular monolith**:

```text
Browser
   │
   ▼
React frontend
   │ REST API
   ▼
FastAPI
   ├── API             Router, xác thực và HTTP schema
   ├── Domain          Model, service và quy tắc nghiệp vụ
   ├── Infrastructure  PostgreSQL, repository, JWT và bcrypt
   └── Bootstrap       Cấu hình và lắp ráp ứng dụng
          │
          ▼
      PostgreSQL
```

### Cấu trúc thư mục

```text
app/
├── api/              REST API theo từng nghiệp vụ
├── domain/           Nghiệp vụ auth, phim, phòng, lịch chiếu và đặt vé
├── infrastructure/   Persistence, bảo mật và Unit of Work
└── bootstrap/        Cấu hình và khởi tạo ứng dụng
frontend/             Giao diện React
alembic/              Migration cơ sở dữ liệu
scripts/              Tạo tài khoản và dữ liệu mẫu
tests/                Unit test và API test
docs/                 Tài liệu yêu cầu, kiến trúc và kế hoạch
deploy/               Tài nguyên triển khai
```

## Tech stack

| Thành phần | Công nghệ |
| --- | --- |
| Frontend | React 19, TypeScript, Vite 8, React Router 7 |
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic, psycopg |
| Xác thực | JWT, bcrypt |
| Quản lý package | uv, npm |
| Kiểm thử và chất lượng | pytest, Ruff, mypy, ESLint |
| Đóng gói | Docker, Docker Compose |

## Các tài liệu liên quan khác
- Tài liệu đặc tả API: [docs/openapi.yaml](docs\openapi.yaml) hoặc truy cập http://localhost:8080/docs.
- Tài liệu đặc tả chi tiết: [xem tại đây](https://docs.google.com/document/d/1H-eb1KEZKutcO7qscpZdq2fFli6BPP_J_6h0DFnI2Bs/edit?tab=t.0).
