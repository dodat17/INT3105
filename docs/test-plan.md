# Kế hoạch kiểm thử

Triển khai `T-01` … `T-30` của mục 9.1 [requirements.md](./requirements.md) thành ca kiểm thử cụ thể. Mọi bài kiểm thử bắt buộc phải tồn tại trong CI trước khi Pha 1 được nghiệm thu.

## 1. Tầng kiểm thử

| Tầng | Lệnh | Phạm vi | Hạ tầng |
|---|---|---|---|
| Unit | `uv run pytest -m unit` | Service nghiệp vụ, chuyển trạng thái, tính giá, biên hết hạn | Clock giả, port giả. Không DB |
| Integration | `uv run pytest -m integration` | Transaction, truy vấn, ánh xạ lỗi, hợp đồng HTTP | testcontainers-python + PostgreSQL 16 |
| Concurrency | `uv run pytest -m concurrency` | Tranh chấp ghế, cạnh tranh chuyển trạng thái | Testcontainers + `ThreadPoolExecutor` |
| Architecture | `uv run lint-imports` và `uv run pytest -m architecture` | Ranh giới tầng và chiều phụ thuộc | import-linter |
| Smoke | `scripts/smoke.sh` | Luồng đầu-cuối trên môi trường đã chạy | Docker Compose |

Ba nguyên tắc lấy từ mục 9.1 của đặc tả:

1. **Mock repository không chứng minh được chống double booking.** Mọi bài kiểm thử tranh chấp phải chạy trên PostgreSQL thật, cùng phiên bản với môi trường chạy.
2. **Sau kiểm thử tranh chấp phải kiểm tra dữ liệu trong DB**, không chỉ đếm HTTP status. Mỗi bài kiểm thử đồng thời kết thúc bằng `assertInvariants()` chạy I1–I7 của [data-model.md](data-model.md).
3. **Clock được inject ở unit test** để kiểm tra biên hết hạn mà không phải chờ 5 phút.

## 2. Dữ liệu kiểm thử

Fixture tối thiểu dùng chung, tạo lại trước mỗi lớp kiểm thử:

| Thực thể | Nội dung |
|---|---|
| `movie` | 2 phim |
| `auditorium` | 1 phòng, ghế `A1`–`A10`, `B1`–`B10` |
| `showtime` | `ST_OPEN` bắt đầu sau 2 giờ; `ST_CLOSED` với `isOpenForBooking=false`; `ST_STARTED` đã bắt đầu 10 phút trước |
| `app_user` | `alice`, `bob` |
| `showtime_seat` | Sinh đầy đủ cho cả ba suất |

Kiểm thử hết hạn hạ `HOLD_TTL_SECONDS` xuống 2 giây thay vì giả lập thời gian, vì nguồn thời gian quyết định là đồng hồ DB (ADR-0004) và không giả lập được từ phía ứng dụng.

## 3. Ma trận ca kiểm thử

Cột "Assertion then chốt" là điều kiện làm bài kiểm thử fail nếu hiện thực sai — không phải toàn bộ assertion.

| Mã | Tầng | Tiền điều kiện | Hành động | Assertion then chốt |
|---|---|---|---|---|
| `T-01` | Integration | `alice` tồn tại | Đăng nhập đúng; đăng nhập sai mật khẩu; đăng nhập email không tồn tại | `200` + token hợp lệ; hai trường hợp sai trả `401` với **cùng** `code` và **cùng** `message`; không log mật khẩu |
| `T-02` | Integration | — | Gọi `GET /me/bookings` và `POST /bookings` với: không token, token rác, token hết hạn | `401` cả ba; `count(booking)` không đổi |
| `T-03` | Integration | Fixture danh mục | Phân trang hợp lệ và sai; lọc `date` đúng và sai định dạng; `movieId` không tồn tại | Timezone đúng theo `CINEMA_TIMEZONE`; `pageSize=101` → `400`; `movieId` lạ → danh sách rỗng, không `404` |
| `T-04` | Integration | `ST_OPEN` | Giữ 1 ghế; giữ 3 ghế | `201`; `expiresAt = min(now+TTL, startsAt)`; `items.length` đúng; `totalAmount = Σ unitPrice`; `unitPrice = ticketPrice` |
| `T-05` | Integration | `ST_OPEN` | `seatIds` rỗng; trùng ghế; 9 ghế; ghế của phòng khác; ghế không tồn tại; body có trường lạ | `400` cả sáu; `count(booking)` không đổi; không dòng inventory nào đổi trạng thái |
| `T-06` | Integration | `A1` đã `BOOKED` | Giữ `[A1, A2, A3]` | `409 SEAT_UNAVAILABLE`; `details.seatIds == ["A1"]`; **`A2` và `A3` vẫn `AVAILABLE`** |
| `T-07` | Concurrency | `A1` trống | 20 request đồng thời giữ `[A1]`. Biến thể a: 20 người dùng khác nhau. Biến thể b: cùng `alice` | Đúng 1 × `201`, 19 × `409 SEAT_UNAVAILABLE`, **0 × `5xx`**; `showtime_seat(A1).booking_id` = booking thắng; đúng 1 booking `HELD` cho `A1` |
| `T-08` | Concurrency | `A1,A2,A3` trống | Đồng thời giữ `[A1,A2]` và `[A2,A3]`. **Lặp 100 vòng** để lộ deadlock | Đúng **một** booking thành công mỗi vòng; ghế của nhóm thua còn `AVAILABLE`; 0 × `5xx` trên toàn bộ 100 vòng |
| `T-09` | Integration | Booking `HELD` còn hạn | Xác nhận; xác nhận lại | `200` cả hai; `bookingCode` **giống nhau**; `count(booking)` không đổi; `confirmedAt` không đổi |
| `T-10` | Integration | `HOLD_TTL_SECONDS=2` | Xác nhận tại `now = expiresAt`; xác nhận sau đó | `409 BOOKING_EXPIRED` cả hai; không sinh `bookingCode`; ghế không chuyển `BOOKED` |
| `T-11` | Integration | Booking `HELD` | Hủy; hủy lại; giữ lại chính ghế đó | `204`, `204`, `201`; booking cũ vẫn tồn tại với `status=CANCELLED`; `booking_item` còn nguyên |
| `T-12` | Integration | Booking `CONFIRMED` | Hủy | `409 INVALID_BOOKING_STATE`; ghế vẫn `BOOKED` |
| `T-13` | Integration | Booking của `alice` | `bob` gọi GET, confirm, DELETE | `404` cả ba (không phải `403`); dữ liệu không đổi |
| `T-14` | Integration | Hold đã hết hạn, không job nào chạy | `GET /showtimes/{id}/seats`; `GET /bookings/{id}`; `bob` giữ lại ghế đó | Ghế trả `AVAILABLE`; booking trả `EXPIRED`; `bob` giữ thành công. **Không assert cột `status` trong DB** — xem ADR-0003 |
| `T-15` | Concurrency | Booking `HELD` của `alice` | `alice` gọi confirm và DELETE đồng thời, lặp 50 vòng | Đúng một chuyển trạng thái thắng; trạng thái cuối là `CONFIRMED` hoặc `CANCELLED`, không bao giờ lẫn lộn; inventory khớp trạng thái cuối |
| `T-16` | Concurrency | Hold sắp hết hạn | Đồng thời: `alice` confirm, `bob` giữ mới cùng ghế | Không kết quả nào ghi đè kết quả kia; nếu `bob` thắng thì confirm của `alice` trả `409`; nếu `alice` thắng thì `bob` nhận `409`. I1–I7 sạch |
| `T-17` | Integration | — | Inject lỗi ở bước ghi `booking_item` | Rollback toàn bộ; không có booking mồ côi; không dòng inventory nào chuyển `HELD` |
| `T-18` | Integration | `ST_CLOSED`, `ST_STARTED` | Giữ ghế; xác nhận một hold cũ; xác nhận lại một booking đã `CONFIRMED` trên `ST_STARTED` | Giữ → `409 SHOWTIME_NOT_BOOKABLE`; xác nhận hold → `409`; xác nhận lại booking đã confirm → **`200`** với dữ liệu cũ |
| `T-19` | Integration | Booking `HELD`, `CONFIRMED` | Khởi động lại ứng dụng, đọc lại | Booking đã commit còn nguyên; `expiresAt` **không** bị đẩy xa hơn |
| `T-20` | Integration | Cùng ghế `A1` ở hai suất | Giữ `A1` ở cả hai | Cả hai `201`; kiểm chứng BR-02 |
| `T-21` | Integration | Booking vừa tạo | Đọc lại và kiểm tra biểu diễn | `createdAt`/`expiresAt` có offset timezone; cột DB là UTC; `currency == "VND"`; `unitPrice == ticketPrice` tại lúc giữ; `totalAmount == Σ unitPrice` |
| `T-22` | Integration | `HOLD_MAX_ACTIVE_PER_SHOWTIME=2`, `HOLD_MAX_ACTIVE_TOTAL=5` | Tạo hold thứ 3 trên cùng suất; tạo hold thứ 6 toàn hệ thống; hủy một hold rồi tạo lại | `409 HOLD_LIMIT_EXCEEDED` hai lần đầu; lần cuối `201` |
| `T-23` | Integration | Token hợp lệ | Sửa payload; ký bằng khóa khác; `alg: none`; thiếu `sub`; hết hạn 30 giây; hết hạn 90 giây | `401` cho mọi trường hợp trừ "hết hạn 30 giây" (nằm trong dung sai 60 giây) → `200` |
| `T-24` | Integration | Mỗi trạng thái một booking, trong đó một hold đã quá hạn | `status=HELD`, `EXPIRED`, `CONFIRMED`, `CANCELLED`, không truyền, `status=FOO`, `status=HELD,CONFIRMED`, `page=999` | `HELD` không chứa booking quá hạn; `EXPIRED` chứa đúng nó; `FOO` và giá trị kép → `400`; `totalItems` khớp số bản ghi thỏa điều kiện; `page=999` → `200` + `items` rỗng |
| `T-25` | Concurrency | Suất chiếu mới, chưa có giao dịch nào | 20 request đồng thời giữ cùng một ghế | Như `T-07`; đặc biệt **0 lỗi vi phạm khóa chính rò ra thành `500`** |
| `T-27` | Integration | — | `Content-Type: text/plain`; body 100 KB; `PUT /api/v1/bookings`; trường lạ trong DTO; `?page=1` trên endpoint sơ đồ ghế | `415`, `413`, `405`, `400`, `400`; không tạo dữ liệu |
| `T-28` | Architecture | — | Chạy `lint-imports` và architecture tests | Fail khi `app.domain` import `fastapi`, `starlette`, `pydantic`, `sqlalchemy`, `psycopg`, `app.api` hoặc `app.infrastructure`; fail khi API import persistence implementation |
| `T-29` | Integration | Phòng 100 ghế | `GET /showtimes/{id}/seats` | Trả đủ 100 phần tử trong một response; thứ tự `rowLabel, seatNumber`; không có trường phân trang |
| `T-30` | Integration (Pha 2) | Phiên bản có cache | Làm cache cũ đi rồi giữ một ghế đã bị chiếm | Quyết định cấp ghế dựa trên DB; cache cũ không cho phép giữ. Bắt buộc **chỉ khi** Pha 2 có cache |

## 4. Kiểm thử đồng thời: khuôn mẫu

Bốn chi tiết quyết định việc bài kiểm thử có thật sự phát hiện lỗi hay không:

```python
# 1. Barrier buộc mọi worker cùng xuất phát.
barrier = threading.Barrier(threads)

def worker(payload):
    barrier.wait()
    return client.post("/api/v1/bookings", json=payload, headers=auth_headers)

# 2. Số worker lớn hơn DB pool để phủ trường hợp chờ connection.
assert threads > db_pool_size

# 3. Lặp nhiều vòng để lộ race/deadlock hiếm.
for _ in range(rounds):
    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(worker, payloads))

# 4. Kiểm tra bất biến DB, không chỉ HTTP status.
assert_invariants()  # I1–I7 phải trả 0 dòng
```

`T-08` chạy 100 vòng vì nó là bài kiểm thử duy nhất phát hiện việc quy tắc sắp xếp `seatId` trước khi khóa bị bỏ đi (ADR-0002). Quy tắc đó là một dòng mã dễ bị một lần refactor vô hại xóa mất, và hậu quả là deadlock ngẫu nhiên dưới tải.

## 5. Smoke test

`scripts/smoke.sh` chạy trên môi trường đã khởi động, dùng trong `docker compose`, trong CI và như bước kiểm tra trước mỗi lần đo tải (mục 10.5 bước 2):

1. `GET /health/ready` → `200`.
2. Đăng nhập tài khoản demo → lấy token.
3. `GET /showtimes` → chọn một suất còn nhận đặt chỗ.
4. `GET /showtimes/{id}/seats` → chọn 2 ghế `AVAILABLE`.
5. `POST /bookings` → `201`, có header `Location`.
6. `POST /bookings/{id}/confirm` → `200`, có `bookingCode`.
7. `GET /me/bookings?status=CONFIRMED` → chứa booking vừa tạo.
8. Kiểm tra log chứa đúng một dòng cho mỗi request với `requestId`, method, route template, status, thời gian xử lý (`NFR-07`), và `requestId` trong body lỗi khớp với dòng log tương ứng.

Script trả mã thoát khác 0 nếu bất kỳ bước nào sai. Không đo tải khi smoke test chưa xanh.

## 6. Điều kiện xanh của CI

CI phải chạy tối thiểu:

```text
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run lint-imports
uv run alembic upgrade head
uv run alembic check
uv run pytest --cov=app.domain.service --cov-fail-under=80
```

Pipeline fail nếu:

- Bất kỳ bài kiểm thử bắt buộc nào trong bảng ở mục 3 fail.
- `lint-imports` hoặc architecture test phát hiện vi phạm ranh giới tầng.
- `scripts/check-invariants.sql` trả về dòng nào khác 0 sau kiểm thử đồng thời.
- Độ phủ của package `domain.service` dưới 80% dòng lệnh.

`T-30` chỉ chạy trên nhánh Pha 2 có cache.

> Mã `T-26` đã bị thu hồi ở đặc tả phiên bản 1.2 cùng với NFR-05. Số hiệu này không được dùng lại cho nội dung khác, để các mã còn lại giữ nguyên ý nghĩa qua các phiên bản.
