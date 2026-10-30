# Hệ thống đặt vé xem phim

Môn Kiến trúc phần mềm - INT3105

- Nguyễn Chí Công - 23021481
- Lê Anh Duy - 23021501
- Đỗ Thành Đạt - 23021517

Ứng dụng web đặt vé xem phim cho một rạp nhiều phòng chiếu: xem phim, lịch chiếu, chọn ghế, giữ ghế và xác nhận vé.

---

## 1. Bài toán và nghiệp vụ

Rạp cần bán vé trực tuyến cho nhiều phòng chiếu. Hệ thống có ba nhóm người dùng:

- **Khách (chưa đăng nhập):** xem phim đang chiếu/sắp chiếu, lịch chiếu, sơ đồ ghế; đăng ký tài khoản.
- **Khách hàng (`CUSTOMER`):** giữ ghế, xác nhận đặt vé (mô phỏng thanh toán), hủy chỗ đang giữ, xem vé của mình.
- **Quản trị viên (`ADMIN`):** quản lý phim, phòng chiếu, suất chiếu, người dùng; tra cứu mọi booking. Không đặt vé.

**Tóm tắt quy tắc cốt lõi:**

- **Đặt vé hai bước:** chọn 1–8 ghế của một suất → hệ thống **giữ ghế 5 phút** (không quá giờ chiếu) → khách xác nhận để
  nhận **mã đặt vé** 8 ký tự. Hết 5 phút chưa xác nhận thì ghế tự trả lại.
- **Một ghế, một chủ:** mỗi ghế trong một suất chỉ thuộc tối đa một booking đang giữ hoặc đã mua. Giữ ghế theo nguyên
  tắc tất cả hoặc không.
- **Giới hạn giữ chỗ:** mỗi khách giữ tối đa 2 booking trên một suất và 5 booking trên toàn hệ thống.
- **Vé đã mua không đổi, không hủy, không hoàn tiền.** Chỗ đang giữ thì hủy được bất kỳ lúc nào.
- **Giá vé:** giá ghế Thường theo suất chiếu (bội số 1.000 đ); ghế VIP thêm 30%, làm tròn xuống 1.000 đ. Giá được chốt
  tại lúc giữ ghế.
- **Lịch chiếu:** giờ kết thúc = giờ bắt đầu + thời lượng phim; hai suất cùng phòng cách nhau ít nhất 15 phút để dọn
  phòng; không xếp suất trước ngày khởi chiếu.
- **Phim** có nhãn phân loại P, K, T13, T16, T18; nhãn hiển thị khi đặt vé, tuổi được kiểm tra tại cửa soát vé.
- **Bảo toàn dữ liệu đã bán:** không xóa phim, suất chiếu, người dùng đã có dữ liệu liên quan; booking là lịch sử, không
  bao giờ bị xóa.

### Các vấn đề dễ thấy và hướng xử lý

| Vấn đề                                                                                     | Hướng xử lý                                                                                                                                                                                                                                  |
|--------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Hai người cùng thấy một ghế trống và cùng bấm giữ                                          | Mỗi cặp suất–ghế có đúng một dòng inventory (khóa chính). Giữ ghế khóa các dòng theo thứ tự `seat_id`, rồi `UPDATE … WHERE ghế còn trống`; số dòng cập nhật quyết định thắng/thua. Bên thua nhận `409 SEAT_UNAVAILABLE`, không bao giờ `500` |
| Hai yêu cầu giữ hai nhóm ghế giao nhau (A1-A2 và A2-A3) bị deadlock hoặc giữ được một phần | Luôn khóa theo cùng một thứ tự; thiếu một ghế thì rollback toàn bộ, không giữ ghế nào                                                                                                                                                        |
| Ghế bị giữ mãi khi khách bỏ dở                                                             | Hạn giữ lưu cùng ghế; ghế quá hạn được coi là trống ngay ở lần giữ tiếp theo, không cần tác vụ nền                                                                                                                                           |
| Bấm xác nhận hai lần, hoặc mạng lỗi rồi gửi lại                                            | Xác nhận lần hai trả lại đúng vé cũ. Giữ ghế không tự gửi lại; khách xem lại danh sách vé                                                                                                                                                    |
| Đồng hồ máy chủ ứng dụng lệch nhau khi chạy nhiều worker                                   | Mọi quyết định về hạn giữ dùng đồng hồ PostgreSQL trong cùng transaction                                                                                                                                                                     |
| Một tài khoản giữ hàng loạt ghế để chặn người khác                                         | Giới hạn 2 booking đang giữ mỗi suất, 5 trên toàn hệ thống                                                                                                                                                                                   |
| Đoán ID để xem vé người khác                                                               | Booking không thuộc người gọi trả `404` như không tồn tại                                                                                                                                                                                    |
| Hai quản trị viên cùng tạo hai suất trùng giờ trong một phòng                              | Khóa dòng phòng chiếu khi tạo/sửa suất, nên các yêu cầu cùng phòng chạy lần lượt                                                                                                                                                             |
| Sơ đồ ghế hiển thị trống nhưng giữ thất bại                                                | Sơ đồ chỉ đúng tại lúc đọc; giao diện báo lỗi và tải lại sơ đồ khi nhận `409`                                                                                                                                                                |

*Chi tiết quy tắc nghiệp vụ và yêu cầu: xem tại [docs/requirements.md](docs/requirements.md)*

---

## 2. API

Prefix `/api/v1`, JSON, xác thực Bearer JWT. Lỗi có dạng `{"error": {"code", "message", "requestId", "details?"}}`.

| Nhóm     | Phương thức                    | Endpoint                                                                 | Quyền truy cập |
|----------|--------------------------------|--------------------------------------------------------------------------|----------------|
| Xác thực | `POST`                         | `/auth/register`, `/auth/login`                                          | Công khai      |
|          | `GET`                          | `/auth/me`                                                               | Đã đăng nhập   |
| Danh mục | `GET`                          | `/movies`, `/movies/{movieId}`                                           | Công khai      |
|          | `GET`                          | `/showtimes`, `/showtimes/{showtimeId}`, `/showtimes/{showtimeId}/seats` | Công khai      |
| Đặt vé   | `POST`                         | `/bookings`                                                              | `CUSTOMER`     |
|          | `GET`                          | `/me/bookings`                                                           | `CUSTOMER`     |
|          | `GET`, `DELETE`                | `/bookings/{bookingId}`                                                  | Chủ booking    |
|          | `POST`                         | `/bookings/{bookingId}/confirm`                                          | Chủ booking    |
| Quản trị | `GET`, `POST`, `PUT`, `DELETE` | `/admin/movies`                                                          | `ADMIN`        |
|          | `GET`, `POST`, `PUT`           | `/admin/auditoriums`                                                     | `ADMIN`        |
|          | `POST`, `PUT`, `DELETE`        | `/admin/showtimes`                                                       | `ADMIN`        |
|          | `GET`, `PUT`, `DELETE`         | `/admin/users`                                                           | `ADMIN`        |
|          | `GET`                          | `/admin/bookings`                                                        | `ADMIN`        |
| Vận hành | `GET`                          | `/health/live`, `/health/ready` (ngoài prefix)                           | Công khai      |

*Chi tiết: xem Swagger UI hoặc [docs/openapi.yaml](docs/openapi.yaml)*

---

## 3. Công nghệ và yêu cầu kỹ thuật

- **Backend:** Python 3.12, FastAPI, Uvicorn, Pydantic, SQLAlchemy 2, Alembic, psycopg 3, PyJWT (HS256), bcrypt.
- **Frontend:** React 19, TypeScript, React Router 7, Vite 8.
- **Database:** PostgreSQL 16.
- **Đóng gói:** Docker multi-stage, Docker Compose; uv và npm với lockfile.

---

## 4. Kiến trúc và tổ chức mã nguồn

Hệ thống là **modular monolith** theo kiểu **ports and adapters**: một ứng dụng, một database, chia thành các module
nghiệp vụ; mỗi module đi qua đủ các tầng, và mọi phụ thuộc hướng vào tầng nghiệp vụ.

```text
Trình duyệt ──► React SPA ──REST/JSON, Bearer JWT──► FastAPI (Uvicorn) ──SQL──► PostgreSQL 16

FastAPI
 ├── api              Middleware (requestId, giới hạn body, xác thực JWT), router,
 │      │             DTO Pydantic, đổi lỗi nghiệp vụ thành HTTP
 │      ▼ gọi
 ├── domain           Service, model, quy tắc nghiệp vụ; khai báo port (Protocol)
 │      ▲ hiện thực port
 ├── infrastructure   Repository SQLAlchemy, Unit of Work, đồng hồ DB, JWT, bcrypt
 └── bootstrap        Đọc cấu hình, lắp ráp các thành phần, phục vụ file SPA
```

| Module       | Sở hữu dữ liệu                                | Chức năng                                          |
|--------------|-----------------------------------------------|----------------------------------------------------|
| `auth`       | `users`                                       | Đăng ký, đăng nhập, JWT, quản lý người dùng        |
| `catalog`    | `movies`                                      | Phim, đang chiếu/sắp chiếu                         |
| `cinema`     | `rooms`, `seats`                              | Phòng chiếu và lưới ghế                            |
| `scheduling` | `showtimes`                                   | Lịch chiếu, giá ghế, mở/ngừng bán                  |
| `booking`    | `bookings`, `booking_items`, `showtime_seats` | Giữ ghế, xác nhận, hủy, sơ đồ ghế, tra cứu booking |

```text
app/
├── api/                  # Tầng giao tiếp HTTP
│   ├── <module>/         # router.py: endpoint công khai và endpoint /admin của module
│   ├── common/           # Middleware xác thực, requestId, giới hạn body, header bảo mật; hợp đồng lỗi
│   └── router.py         # Gom router các module dưới /api/v1
├── domain/               # Nghiệp vụ, Python thuần
│   ├── <module>/         # model.py, service.py, ports.py (Protocol module cần)
│   ├── ports.py          # Shared kernel: Page, Clock, UnitOfWork
│   └── errors.py         # Lỗi nghiệp vụ dùng chung
├── infrastructure/       # Adapter
│   ├── persistence/      # Model ORM, repository, Unit of Work, readiness check
│   ├── security/         # JWT, bcrypt
│   └── clock.py          # Đồng hồ PostgreSQL
├── bootstrap/            # settings.py, application.py (lắp ráp ứng dụng)
└── main.py               # Điểm vào ASGI
frontend/src/
├── pages/                # Trang chủ, chi tiết phim, đăng nhập, vé, quản trị
├── components/           # Sơ đồ ghế, tóm tắt booking, form quản trị
└── lib/apiClient.ts      # Lớp gọi API duy nhất
alembic/versions/         # Migration schema
scripts/                  # seed.py, export_openapi.py
tests/
├── unit/                 # Kiểm thử service với repository giả
└── api/                  # Kiểm thử API, gồm kiểm thử đồng thời trên PostgreSQL
docs/                     # Yêu cầu, kiến trúc, mô hình dữ liệu, OpenAPI, kế hoạch kiểm thử và đo tải
```

*Quy ước: `<module>` là `auth`, `catalog`, `cinema`, `scheduling`, `booking`. Chi tiết luồng dữ liệu và sơ đồ C4: xem
tại [docs/architecture.md](docs/architecture.md)*

---

## 5. Hướng dẫn chạy (Docker)

### 5.1. Khởi động hệ thống

Cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) và bảo đảm Docker đang chạy. Tại thư mục gốc của
dự án:

```bash
docker compose up --build -d      # db → migrate (alembic upgrade head) → app
docker compose run --rm seed      # tạo ADMIN, phim, phòng, suất chiếu mẫu; chạy lại không tạo trùng
```

> *Lưu ý: `app` chỉ khởi động sau khi `migrate` chạy thành công. Seed chỉ dùng cho môi trường phát triển.*

### 5.2. Truy cập và tài khoản thử nghiệm

- **Ứng dụng web và API:** http://localhost:8080
- **Swagger UI:** http://localhost:8080/docs. Gọi `POST /api/v1/auth/login`, sao chép `accessToken`, bấm **Authorize**.
- **Health check:** http://localhost:8080/health/ready

| Vai trò       | Email                      | Mật khẩu     | Ghi chú                                                         |
|---------------|----------------------------|--------------|-----------------------------------------------------------------|
| Quản trị viên | `admin@example.test`       | `admin12345` | Tạo bởi seed; đổi qua `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` |
| Khách hàng    | Tự đăng ký tại `/register` | ≥ 8 ký tự    | Tài khoản đăng ký luôn là `CUSTOMER`                            |

> *Lưu ý: quản trị viên không đặt được vé. Dùng tài khoản khách hàng để thử luồng giữ ghế và xác nhận.*

### 5.3. Thao tác vận hành thường dùng

```bash
docker compose logs -f app        # xem log ứng dụng
docker compose up --build -d app  # build lại sau khi sửa mã
docker compose down -v            # dừng và xóa toàn bộ dữ liệu (reset DB)
```

---

## 6. Tài liệu chi tiết

| Nội dung                                                                                 | Tài liệu                                         |
|------------------------------------------------------------------------------------------|--------------------------------------------------|
| Đặc tả yêu cầu: phạm vi, use case, quy tắc nghiệp vụ, yêu cầu chức năng và phi chức năng | [docs/requirements.md](docs/requirements.md)     |
| Hợp đồng API                                                                             | [docs/openapi.yaml](docs/openapi.yaml)           |
| Kiến trúc: sơ đồ C4, thành phần, luồng dữ liệu, lý do chọn công nghệ                     | [docs/architecture.md](docs/architecture.md)     |
| Mô hình dữ liệu: sơ đồ ER, ràng buộc, index, migration và seed                           | [docs/data-model.md](docs/data-model.md)         |
| Kế hoạch kiểm thử                                                                        | [docs/test-plan.md](docs/test-plan.md)           |
| Kế hoạch đo tải trên Kaggle                                                              | [docs/benchmark-plan.md](docs/benchmark-plan.md) |
| Kế hoạch thực hiện theo mốc                                                              | [docs/project-plan.md](docs/project-plan.md)     |
| Phát triển cục bộ                                                                        | [docs/development.md](docs/development.md)       |

---

## 7. Định hướng Pha 2

| Vấn đề                              | Giải thích                                                                                                                          | Gợi ý giải quyết                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Nhiều người cùng chọn một ghế       | Suất hot mở bán, hàng trăm người cùng bấm ghế A5. Chỉ một người thắng nhưng tất cả phải chờ khóa DB, làm cạn kết nối và tăng độ trễ | Từ chối sớm ghế đã có chủ trước khi vào transaction; rút ngắn thời gian giữ khóa |
| Hết thời gian giữ khi đang xác nhận | Khách bấm xác nhận ở giây cuối nhưng hold đã hết hạn, ghế đã thuộc người khác. Tải cao làm yêu cầu bấm kịp giờ vẫn bị xử lý trễ     | Rút ngắn đường xác nhận; giao diện đếm ngược, nhắc xác nhận trước khi hết giờ    |
| Giữ ghế nhưng không mua             | Khách đóng tab, mất mạng hoặc đổi ý, ghế bị khóa vô ích tới hết 5 phút. Kẻ xấu dùng nhiều tài khoản để giữ hàng loạt ghế            | Worker nền thu hồi hold hết hạn; giới hạn tần suất giữ ghế theo IP               |
| Nhiều người cùng xem sơ đồ ghế      | Khách liên tục tải lại sơ đồ để tìm ghế trống, mỗi lần đọc toàn bộ ghế và tranh tài nguyên DB với đường giữ ghế                     | Cache sơ đồ ghế TTL ngắn; giữ ghế vẫn kiểm tra trên DB                           |
| Đọc danh mục lặp lại                | Phim và lịch chiếu được đọc rất nhiều nhưng hiếm khi thay đổi                                                                       | Cache-aside, xóa cache khi admin sửa danh mục                                    |
