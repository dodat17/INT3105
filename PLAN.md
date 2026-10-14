# Kế hoạch xây dựng hệ thống đặt vé xem phim

Tài liệu này chuyển nội dung trong `docs/brainstorm001.md` thành các công việc có thể triển khai và kiểm chứng. Phạm vi chỉ gồm các chức năng đã nêu trong brainstorm; không tự bổ sung thanh toán thật, giữ ghế có thời hạn, khuyến mãi, email hoặc refresh token.

## 1. Mục tiêu hoàn thành

Hệ thống được xem là hoàn thành khi:

- Cung cấp REST API JSON bằng FastAPI, có Swagger/OpenAPI.
- Hỗ trợ đăng ký, đăng nhập JWT, xem phim/suất chiếu/ghế, đặt và hủy vé.
- Hỗ trợ quản trị phim, phòng và suất chiếu theo quyền `ADMIN`.
- Tuân thủ luồng API -> nghiệp vụ -> dữ liệu; tầng nghiệp vụ không phụ thuộc framework hoặc CSDL.
- Không bán cùng một ghế hai lần trong cùng một suất, kể cả khi có request đồng thời.
- Chạy được bằng SQLite khi phát triển/test và PostgreSQL khi chạy Docker.
- Có unit test, API test, kiểm tra kiến trúc, CI và kiểm thử tải bằng Locust trên Kaggle.
- Có README đủ để người mới clone repo, chạy ứng dụng, chạy test và demo.

## 2. Nguyên tắc triển khai

1. Chốt entities, lỗi nghiệp vụ và ports trước khi chia việc song song.
2. Viết nghiệp vụ bằng Python thuần, kiểm thử bằng fake repository trước khi nối FastAPI/SQLAlchemy.
3. Mỗi use case là một transaction thông qua `UnitOfWork`.
4. Quy tắc nghiệp vụ nằm trong service; router chỉ nhận/trả HTTP; repository chỉ xử lý lưu trữ.
5. Dùng ràng buộc CSDL làm lớp bảo vệ cuối cùng cho dữ liệu có cạnh tranh đồng thời.
6. Mỗi bước chỉ hoàn thành khi có tiêu chí kiểm chứng tương ứng.
7. Ưu tiên cách làm đơn giản nhất đáp ứng phạm vi; chưa tối ưu nếu chưa có số đo chứng minh cần thiết.

## 3. Cấu trúc thư mục dự kiến

```text
.
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- docs/
|   |-- brainstorm001.md
|   `-- api-examples.md                 # Tùy chọn: ví dụ request/response quan trọng
|-- notebooks/
|   `-- kaggle_load_test.ipynb
|-- scripts/
|   |-- seed.py
|   `-- generate_load_test_data.py
|-- src/
|   `-- cinema_booking/
|       |-- __init__.py
|       |-- domain/                     # Tầng nghiệp vụ, chỉ dùng Python chuẩn
|       |   |-- __init__.py
|       |   |-- entities.py
|       |   |-- enums.py
|       |   |-- errors.py
|       |   |-- ports.py
|       |   `-- services/
|       |       |-- auth_service.py
|       |       |-- movie_service.py
|       |       |-- room_service.py
|       |       |-- showtime_service.py
|       |       `-- booking_service.py
|       |-- infrastructure/             # Cài đặt ports bằng công nghệ cụ thể
|       |   |-- __init__.py
|       |   |-- database/
|       |   |   |-- models.py
|       |   |   |-- mappers.py
|       |   |   |-- repositories.py
|       |   |   |-- session.py
|       |   |   `-- unit_of_work.py
|       |   `-- security/
|       |       |-- password_hasher.py
|       |       `-- jwt_service.py
|       `-- api/                        # FastAPI và composition root
|           |-- __init__.py
|           |-- app.py
|           |-- dependencies.py
|           |-- middleware.py
|           |-- error_handlers.py
|           |-- schemas/
|           |   |-- auth.py
|           |   |-- movie.py
|           |   |-- room.py
|           |   |-- showtime.py
|           |   `-- booking.py
|           `-- routers/
|               |-- auth.py
|               |-- movies.py
|               |-- rooms.py
|               |-- showtimes.py
|               `-- bookings.py
|-- tests/
|   |-- unit/
|   |   |-- fakes.py
|   |   |-- test_auth_service.py
|   |   |-- test_movie_service.py
|   |   |-- test_room_service.py
|   |   |-- test_showtime_service.py
|   |   `-- test_booking_service.py
|   |-- integration/
|   |   |-- test_repositories.py
|   |   `-- test_booking_concurrency.py
|   `-- api/
|       |-- conftest.py
|       |-- test_auth.py
|       |-- test_movies.py
|       |-- test_rooms.py
|       |-- test_showtimes.py
|       `-- test_bookings.py
|-- load_tests/
|   |-- locustfile.py
|   `-- scenarios/
|       |-- browse.py
|       |-- mixed.py
|       |-- seat_contention.py
|       `-- login.py
|-- .env.example
|-- .gitignore
|-- .importlinter
|-- CODING_STANDARDS.md
|-- Dockerfile
|-- PLAN.md
|-- README.md
|-- compose.yml
`-- pyproject.toml
```

Không cần tạo trước mọi file rỗng. Chỉ thêm file khi giai đoạn tương ứng bắt đầu.

## 4. Thứ tự phụ thuộc

```text
Khung dự án
    -> Entities + errors + ports
        -> Services + unit tests
        -> ORM + repositories + UnitOfWork
            -> API + auth middleware + error mapping
                -> API tests + concurrency tests
                    -> Docker + CI
                        -> Load test + tài liệu + demo
```

Sau khi entities và ports ổn định, ba nhánh `services`, `infrastructure` và khung `api` có thể được làm song song. Khi thay đổi một port, người thay đổi phải cập nhật cả fake dùng trong test và adapter SQLAlchemy.

## 5. Kế hoạch từng giai đoạn

### Giai đoạn 0 - Chốt phạm vi và quyết định kỹ thuật

Việc cần làm:

- [ ] Xác nhận chức năng trong phạm vi và ngoài phạm vi theo brainstorm.
- [ ] Chốt Python 3.12, FastAPI, SQLAlchemy 2.x, PostgreSQL 16, pytest, Ruff, import-linter và Locust.
- [ ] Chốt ID dùng một kiểu thống nhất trong toàn hệ thống.
- [ ] Chốt quy ước thời gian: lưu UTC, API trả ISO 8601 có múi giờ.
- [ ] Chốt tiền là số nguyên VND; hệ số VIP được tính không dùng `float` gây sai số.
- [ ] Giải quyết điểm chưa thống nhất trong brainstorm: bảng phạm vi nói admin được xóa phòng nhưng bảng endpoint chưa có `DELETE /rooms/{id}`; ghi quyết định cuối vào đặc tả API trước khi code.
- [ ] Chốt payload và mã lỗi chính trước khi triển khai router.

Đầu ra: một bộ quyết định đủ rõ để entities và ports không phải thay đổi tùy tiện giữa các nhánh.

Tiêu chí hoàn thành: mọi thành viên mô tả giống nhau về phạm vi, luồng phân tầng và cách chống đặt trùng ghế.

### Giai đoạn 1 - Dựng khung dự án và hàng rào chất lượng

Việc cần làm:

- [ ] Tạo `pyproject.toml` với dependency runtime/dev và cấu hình Ruff, pytest.
- [ ] Tạo package theo `src/` layout và các package tầng chính.
- [ ] Tạo FastAPI app tối thiểu và `GET /health`.
- [ ] Thêm `.env.example`; không thêm secret thật.
- [ ] Cấu hình import-linter:
  - `domain` không import FastAPI, Starlette, Pydantic, SQLAlchemy, psycopg, PyJWT hoặc bcrypt.
  - `domain` không import `api` hay `infrastructure`.
  - `infrastructure` không import `api`.
- [ ] Tạo workflow CI chạy Ruff, import-linter, pytest và Docker build.

Đầu ra: ứng dụng tối thiểu khởi động được, `/health` trả 200 và CI xanh.

Tiêu chí hoàn thành:

```powershell
ruff check .
lint-imports
pytest
```

đều thành công trên máy local và CI.

### Giai đoạn 2 - Xây dựng lõi nghiệp vụ

#### 2.1. Entities và kiểu dữ liệu

- [ ] Tạo `User`, `Movie`, `Room`, `Seat`, `Showtime`, `Booking`, `Ticket` bằng dataclass.
- [ ] Tạo enum cho role, loại ghế và trạng thái booking.
- [ ] Giữ entities độc lập với ORM/Pydantic.
- [ ] Thêm validation trong service hoặc hàm nghiệp vụ có ý nghĩa; không nhét HTTP validation vào entity.

#### 2.2. Lỗi nghiệp vụ

- [ ] Tạo lỗi nền và các lỗi: `BusinessRuleViolation`, `EmailAlreadyUsed`, `Forbidden`, `NotFound`, `ShowtimeOverlap`, `ShowtimeAlreadyStarted`, `SeatUnavailable`.
- [ ] Lỗi chứa dữ liệu cần để API tạo mã lỗi và `details`, nhưng không chứa status code HTTP.

#### 2.3. Ports

- [ ] Định nghĩa repository interface cho user, movie, room/seat, showtime và booking.
- [ ] Định nghĩa `UnitOfWork` gom các repository và có `commit`/rollback theo context manager.
- [ ] Định nghĩa `PasswordHasher`, `TokenService`, `Clock`.
- [ ] Chỉ thêm method repository khi một use case thực sự cần.

#### 2.4. Services và unit test

- [ ] `AuthService`: đăng ký, đăng nhập, lấy thông tin người dùng.
- [ ] `MovieService`: danh sách/chi tiết, tạo và xóa phim.
- [ ] `RoomService`: danh sách, tạo phòng và sinh ghế.
- [ ] `ShowtimeService`: danh sách, tạo và xóa suất chiếu; tính giờ kết thúc; kiểm tra trùng lịch.
- [ ] `BookingService`: tạo, liệt kê, xem chi tiết và hủy booking.
- [ ] Tạo fake repositories, fake UoW, fake clock, fake hasher/token cho unit test.
- [ ] Viết test cho toàn bộ BR-01 đến BR-12, gồm cả nhánh thành công và thất bại quan trọng.

Đầu ra: nghiệp vụ chạy hoàn toàn bằng fake in-memory, không cần FastAPI hoặc CSDL.

Tiêu chí hoàn thành: toàn bộ BR-01 đến BR-12 có ít nhất một test trực tiếp; test domain chạy nhanh và import-linter vẫn xanh.

### Giai đoạn 3 - Tầng dữ liệu

#### 3.1. ORM và lược đồ

- [ ] Tạo ORM models tương ứng với entities.
- [ ] Thêm các ràng buộc:
  - `users.email` unique.
  - `(room_id, row_label, number)` unique trong `seats`.
  - `(showtime_id, seat_id)` unique trong `tickets`.
- [ ] Thêm index cho truy vấn theo room/time, movie/time và user booking.
- [ ] Tạo mapper hai chiều ORM model <-> domain entity.

#### 3.2. Repository và UnitOfWork

- [ ] Cài đặt tất cả repository ports bằng SQLAlchemy.
- [ ] Không trả ORM model ra khỏi `infrastructure`.
- [ ] Cài đặt SQLAlchemy UnitOfWork: mở session, commit tường minh, rollback mặc định.
- [ ] Trong luồng đặt vé, flush trước commit để bắt vi phạm unique tại repository.
- [ ] Chuyển lỗi unique ghế của SQLAlchemy thành `SeatUnavailable`.

#### 3.3. Khởi tạo và seed dữ liệu

- [ ] Cấu hình `DATABASE_URL` cho SQLite/PostgreSQL.
- [ ] Tạo cơ chế tạo bảng phù hợp phạm vi bài tập; chỉ thêm Alembic nếu nhóm quyết định cần migration.
- [ ] Viết script seed admin, phim, phòng, ghế và suất chiếu mẫu.
- [ ] Script chạy lặp lại không tạo dữ liệu rác hoặc phải ghi rõ cách reset dữ liệu.

Đầu ra: cùng một bộ repository test chạy được với SQLite; ứng dụng kết nối được PostgreSQL.

Tiêu chí hoàn thành: integration test xác nhận mapping đúng, rollback đúng và ràng buộc ghế trùng hoạt động.

### Giai đoạn 4 - API và bảo mật

#### 4.1. Schemas và routers

- [ ] Tạo Pydantic request/response schemas tách khỏi domain entities.
- [ ] Triển khai toàn bộ endpoint trong bảng đặc tả của brainstorm.
- [ ] Triển khai hoặc loại khỏi phạm vi `DELETE /rooms/{id}` theo quyết định đã chốt ở giai đoạn 0; không để tài liệu và API mâu thuẫn.
- [ ] Dùng đúng status code: tạo booking 201, hủy 204, lỗi theo bảng mapping.
- [ ] Thêm tìm kiếm/phân trang phim và lọc suất chiếu theo phim/ngày ở mức đơn giản.
- [ ] Router chỉ chuyển schema -> input service và entity -> response schema.

#### 4.2. Xác thực và phân quyền

- [ ] Cài đặt bcrypt adapter và JWT HS256 adapter.
- [ ] JWT chứa `sub`, `role`, `exp`; secret lấy từ môi trường.
- [ ] Tạo AuthMiddleware mặc định yêu cầu token, chỉ bỏ qua danh sách route công khai.
- [ ] Cho phép `OPTIONS`, Swagger, ReDoc và OpenAPI schema đi qua.
- [ ] Gắn actor vào request sau khi xác thực.
- [ ] Kiểm tra quyền `ADMIN` và quyền sở hữu booking trong service, không đặt ở middleware/router.

#### 4.3. Xử lý lỗi và OpenAPI

- [ ] Đăng ký exception handler tập trung cho lỗi nghiệp vụ.
- [ ] Chuẩn hóa response lỗi gồm `code`, `message`, `details`.
- [ ] Chuyển lỗi validation của Pydantic thành `VALIDATION_ERROR`.
- [ ] Khai báo Bearer security scheme để Swagger có nút Authorize.
- [ ] Bổ sung mô tả và response model cho các endpoint quan trọng.

Đầu ra: có thể thao tác đầy đủ đăng ký -> đăng nhập -> xem ghế -> đặt vé -> xem vé -> hủy vé trên Swagger.

Tiêu chí hoàn thành: không có SQLAlchemy model hoặc exception hạ tầng rò rỉ vào response API.

### Giai đoạn 5 - Kiểm thử end-to-end và đồng thời

Việc cần làm:

- [ ] API test luồng đăng ký, đăng nhập, đặt, xem và hủy vé.
- [ ] Test 401 khi thiếu/sai/hết hạn token.
- [ ] Test 403 khi `CUSTOMER` gọi chức năng admin.
- [ ] Test 409 khi email trùng, suất chiếu trùng hoặc ghế đã bán.
- [ ] Test không đặt được suất đã bắt đầu.
- [ ] Test hủy booking rồi ghế có thể được đặt lại.
- [ ] Test không xóa phim/suất chiếu có booking `CONFIRMED`.
- [ ] Integration/concurrency test gửi nhiều yêu cầu đặt cùng một ghế.
- [ ] Sau test đồng thời, truy vấn xác nhận không có cặp `(showtime_id, seat_id)` trùng.

Đầu ra: bộ test bảo vệ các luồng chính và lỗi rủi ro cao.

Tiêu chí hoàn thành: chỉ một request cạnh tranh đặt ghế thành công; các request còn lại nhận 409, không có lỗi 500 hoặc dữ liệu trùng.

### Giai đoạn 6 - Docker và vận hành local

Việc cần làm:

- [ ] Viết Dockerfile multi-stage từ `python:3.12-slim`.
- [ ] Chạy container bằng user không phải root.
- [ ] Cho phép cấu hình số worker qua `WEB_WORKERS`.
- [ ] Tạo `compose.yml` gồm `api` và `postgres:16-alpine`.
- [ ] Thêm PostgreSQL healthcheck và dependency theo trạng thái healthy.
- [ ] Dùng volume cho dữ liệu Postgres.
- [ ] Kiểm tra `.env.example` có đủ biến, `.env` bị ignore.
- [ ] Ghi rõ lệnh seed và URL Swagger.

Đầu ra: một lệnh Docker Compose khởi động toàn bộ hệ thống.

Tiêu chí hoàn thành: trên máy sạch, làm theo README có thể khởi động, seed, đăng nhập và đặt vé thành công.

### Giai đoạn 7 - Kiểm thử tải trên Kaggle

Việc cần làm:

- [ ] Viết Locust scenario L1 duyệt dữ liệu.
- [ ] Viết L2 hỗn hợp 60% duyệt, 20% xem vé, 15% đặt, 5% hủy.
- [ ] Viết L3 nhiều user tranh cùng nhóm ghế; coi 409 hợp lệ là kết quả nghiệp vụ đúng.
- [ ] Viết L4 chỉ đăng nhập để đo chi phí bcrypt.
- [ ] Sinh khoảng 2.000 user, 50 suất chiếu và token sẵn cho L1-L3.
- [ ] Tạo notebook Kaggle cài dependency, PostgreSQL, seed và chạy API/Locust.
- [ ] Chạy 10, 50, 100, 200 user ảo; mỗi mức 2 phút.
- [ ] So sánh 1, 2 và 4 worker nếu tài nguyên cho phép.
- [ ] Thu RPS, p50, p95, p99, tỷ lệ 5xx và CPU/RAM.
- [ ] Sau L3, chạy truy vấn kiểm tra dữ liệu ghế trùng phải trả 0 dòng.
- [ ] Vẽ biểu đồ RPS và p95; ghi rõ giới hạn do API và Locust dùng chung CPU.

Đầu ra: notebook tái chạy được, CSV kết quả và biểu đồ dùng trong báo cáo.

Tiêu chí hoàn thành: có kết luận dựa trên số đo, phân biệt rõ lỗi hệ thống với 409 dự kiến của nghiệp vụ.

### Giai đoạn 8 - Hoàn thiện và bàn giao

Việc cần làm:

- [ ] Cập nhật README: bài toán, kiến trúc, ERD, endpoint, xác thực, chạy local/Docker, test, load test và phân công.
- [ ] Kiểm tra toàn bộ lệnh trong README trên môi trường sạch.
- [ ] Xóa code/debug data do nhóm tự tạo nhưng không còn dùng; không refactor ngoài phạm vi sát ngày nộp.
- [ ] Kiểm tra không có secret, token hoặc dữ liệu nhạy cảm trong Git.
- [ ] Chạy toàn bộ CI và Docker build lần cuối.
- [ ] Chuẩn bị kịch bản demo ngắn: admin tạo dữ liệu -> customer đặt vé -> tranh ghế -> hủy và đặt lại.

Đầu ra: repository có thể nộp và demo.

Tiêu chí hoàn thành: CI xanh trên commit cuối, demo chạy theo đúng README và không cần sửa tay mã nguồn.

## 6. Ma trận quy tắc nghiệp vụ và kiểm thử

| Quy tắc | Nơi triển khai chính | Kiểm thử tối thiểu |
|---|---|---|
| BR-01 email duy nhất | AuthService + unique DB | đăng ký trùng trả 409 |
| BR-02 mật khẩu >= 8 ký tự | AuthService | mật khẩu ngắn bị từ chối |
| BR-03 quyền admin | Movie/Room/ShowtimeService | customer nhận 403 |
| BR-04 không trùng lịch phòng | ShowtimeService + truy vấn repository | hai suất giao nhau bị từ chối |
| BR-05 không đặt suất đã bắt đầu | BookingService + Clock | thời gian bằng/sau giờ bắt đầu bị từ chối |
| BR-06 đặt 1-8 ghế, không lặp | BookingService | 0, 9 và ID lặp bị từ chối |
| BR-07 ghế đúng phòng | BookingService | ghế phòng khác bị từ chối |
| BR-08 không bán trùng ghế | BookingService + unique DB | request tuần tự và đồng thời trả 409 |
| BR-09 tính giá | BookingService | STANDARD/VIP và tổng tiền đúng |
| BR-10 quyền xem/hủy booking | BookingService | người khác 403, admin được phép |
| BR-11 chỉ hủy trước giờ chiếu | BookingService + Clock | hủy muộn bị từ chối; hủy sớm trả ghế |
| BR-12 không xóa khi có vé | Movie/ShowtimeService | booking confirmed chặn xóa |

## 7. Phân công gợi ý cho nhóm 3-4 người

| Nhóm việc | Trách nhiệm chính | Điểm phối hợp |
|---|---|---|
| Nghiệp vụ | entities, ports, services, fake, unit test | chốt interface trước tiên |
| Dữ liệu | ORM, mapper, repository, UoW, seed | cập nhật theo ports đã chốt |
| API và bảo mật | schemas, routers, middleware, JWT, error handler | không đưa logic nghiệp vụ vào router |
| Nền tảng | CI, Docker, Locust, Kaggle, README | tích hợp liên tục từ sớm |

Nếu nhóm có ba người, gộp nền tảng vào người phụ trách dữ liệu hoặc chia Docker/CI cho API và load test/tài liệu cho nghiệp vụ. Mỗi Pull Request phải có phạm vi nhỏ, test liên quan và ít nhất một người khác review.

## 8. Definition of Done cho mỗi công việc

Một task chỉ được đánh dấu hoàn thành khi:

- Hành vi đúng với brainstorm và không mở rộng phạm vi không cần thiết.
- Code nằm đúng tầng, không phá hợp đồng import-linter.
- Có test cho hành vi mới và các nhánh lỗi quan trọng.
- Ruff, import-linter và pytest đều thành công.
- Không chứa secret, code debug, comment bỏ dở hoặc dependency không dùng.
- Nếu thay đổi API/cấu hình/cách chạy, tài liệu liên quan đã được cập nhật.
- Pull Request đủ nhỏ để reviewer hiểu mục tiêu và kiểm tra được.

## 9. Rủi ro cần xử lý sớm

| Rủi ro | Cách giảm thiểu |
|---|---|
| Hai request cùng đặt một ghế | unique constraint + flush trong transaction + concurrency test |
| Domain phụ thuộc FastAPI/SQLAlchemy | import-linter chạy từ giai đoạn đầu |
| Sai lệch timezone | dùng UTC nội bộ, fake Clock trong test |
| Sai số giá VIP | tiền số nguyên, quy tắc làm tròn được chốt và test |
| Middleware vô tình để route mới thành public | mặc định chặn, public route allowlist |
| Test SQLite che giấu khác biệt PostgreSQL | có integration/concurrency test trên PostgreSQL trước khi nộp |
| Load test chủ yếu đo bcrypt | phát token sẵn; tách login thành L4 |
| Merge khó vì đổi ports liên tục | review/chốt ports trước khi chia nhánh song song |

