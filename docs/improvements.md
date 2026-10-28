# Các vấn đề có thể cải tiến

Tài liệu ghi lại các điểm yếu quan sát được trong mã nguồn Pha 1 và hướng cải tiến đề xuất. Mỗi mục nêu hiện trạng, tác động và hướng xử lý. Các mục ở nhóm 1 là ứng viên cho Pha 2 và cần được đối chiếu với số liệu đo tải trước khi triển khai, theo [requirements.md](./requirements.md) và [benchmark-plan.md](./benchmark-plan.md).

Mức ưu tiên: **Cao**: nên xử lý sớm hoặc có lỗi thực tế. **Trung bình**: cải thiện rõ khi tải tăng. **Thấp**: tiện ích, có thể để sau.

## Tổng hợp

| # | Vấn đề | Nhóm | Ưu tiên |
|---|---|---|---|
| 1.1 | Request tranh cùng ghế phải xếp hàng chờ khóa | Hiệu năng | Cao |
| 1.2 | Luồng xử lý nhiều hơn kết nối DB | Hiệu năng | Trung bình |
| 1.3 | Sơ đồ ghế luôn đọc từ DB | Hiệu năng | Trung bình |
| 1.4 | Hai truy vấn đếm hold riêng lẻ | Hiệu năng | Thấp |
| 1.5 | Chi tiết booking mở thêm Unit of Work và truy vấn lẻ | Hiệu năng | Thấp |
| 2.1 | Mã đặt vé 32 bit có thể trùng, gây lỗi 500 | Đúng đắn | Cao |
| 2.2 | Không có tác vụ dọn hold hết hạn | Đúng đắn | Trung bình |
| 2.3 | `POST /bookings` không idempotent | Đúng đắn | Trung bình |
| 2.4 | Chưa định nghĩa việc sửa/xóa suất chiếu đang có booking | Đúng đắn | Trung bình |
| 3.1 | Đăng nhập không giới hạn tần suất | Bảo mật | Trung bình |
| 3.2 | JWT không thu hồi được | Bảo mật | Thấp |
| 4.1 | Sơ đồ ghế không tự cập nhật | Trải nghiệm | Trung bình |
| 4.2 | Không có đếm ngược thời gian giữ ghế | Trải nghiệm | Thấp |
| 5.1 | Seed lỗi encoding trên Windows | Vận hành | Cao |
| 5.2 | SQLite cục bộ không tái hiện được tranh chấp | Vận hành | Trung bình |
| 5.3 | Cổng 8080 dễ trùng với dịch vụ khác | Vận hành | Thấp |

## 1. Hiệu năng

### 1.1. Request tranh cùng ghế phải xếp hàng chờ khóa

**Hiện trạng.** `InventoryRepository.lock` khóa các dòng `showtime_seats` bằng `SELECT … FOR UPDATE` ([repositories.py](../app/infrastructure/persistence/repositories.py), hàm `lock`). Khi N request cùng giữ một ghế, request đầu giữ khóa đến khi commit, N−1 request còn lại chờ tuần tự rồi mới nhận 409 `SEAT_UNAVAILABLE`.

**Tác động.** Ở kịch bản tranh chấp cao (L-04), độ trễ p95/p99 tăng theo số người tranh. Mỗi request đang chờ vẫn giữ một kết nối DB và một luồng xử lý, nên request ở các suất chiếu khác cũng bị chậm theo.

**Hướng xử lý.**
- Dùng `FOR UPDATE NOWAIT` và ánh xạ lỗi khóa thành 409 `SEAT_UNAVAILABLE`: người thua biết kết quả ngay.
- Hoặc dùng `FOR UPDATE SKIP LOCKED`, rồi so số dòng khóa được với số ghế yêu cầu: thiếu dòng nghĩa là có ghế đang bị người khác xử lý.
- Giữ nguyên `UPDATE` có điều kiện trong `acquire` làm lớp bảo vệ cuối cho BR-01.

**Kiểm chứng.** `test_booking_concurrency.py` vẫn phải đạt 0 vi phạm BR-01. So p95 của L-04 trước và sau thay đổi.

### 1.2. Luồng xử lý nhiều hơn kết nối DB

**Hiện trạng.** Endpoint viết dạng đồng bộ (`def`) nên chạy trong threadpool của AnyIO với `ANYIO_THREAD_TOKENS=40`, trong khi `DB_POOL_SIZE=10` ([settings.py](../app/bootstrap/settings.py)).

**Tác động.** Khi tải cao, tối đa 30 luồng đứng chờ kết nối trong pool. Thời gian chờ không xuất hiện trong log truy vấn nhưng cộng thẳng vào độ trễ phía client, và có thể gây timeout của pool.

**Hướng xử lý.** Đo trước rồi chỉnh:
- Cân đối số luồng với pool, cộng `max_overflow` của SQLAlchemy.
- Tăng `WEB_WORKERS` thay vì tăng số luồng trong một worker, trong giới hạn `max_connections` của PostgreSQL.
- Ghi lại thời gian chờ lấy kết nối (sự kiện `checkout` của pool) để có số liệu.

### 1.3. Sơ đồ ghế luôn đọc từ DB

**Hiện trạng.** `GET /showtimes/{id}/seats` truy vấn DB ở mọi lần gọi. Đây là endpoint đọc nhiều nhất trong luồng đặt vé.

**Hướng xử lý.** Cache ngắn hạn (1–2 giây) theo `showtimeId`, xóa cache khi có hold, confirm hoặc cancel trên suất đó. Theo BR-10, cache chỉ phục vụ hiển thị; quyết định cấp ghế vẫn đi qua `lock`/`acquire` trên DB. Phải bổ sung T-30.

### 1.4. Hai truy vấn đếm hold riêng lẻ

**Hiện trạng.** `BookingService.create` gọi `count_effective_holds` hai lần: một lần theo suất, một lần toàn hệ thống ([service.py](../app/domain/booking/service.py)).

**Hướng xử lý.** Gộp thành một truy vấn trả về cả hai số đếm, ví dụ `COUNT(*) FILTER (WHERE showtime_id = :id)` cùng `COUNT(*)`. Giảm một vòng gọi DB trên đường ghi đang giữ khóa.

### 1.5. Chi tiết booking mở thêm Unit of Work và truy vấn lẻ

**Hiện trạng.** `get` đọc booking trong một Unit of Work. Sau đó `_details` mở Unit of Work thứ hai và đọc suất chiếu, phim, phòng bằng ba truy vấn riêng.

**Tác động.** Tốn thêm một lần lấy kết nối và bốn vòng gọi DB. Hai lần đọc không cùng một snapshot.

**Hướng xử lý.** Đọc tất cả trong cùng Unit of Work, hoặc thêm một phương thức repository dùng join.

## 2. Đúng đắn và độ bền

### 2.1. Mã đặt vé 32 bit có thể trùng, gây lỗi 500

**Hiện trạng.** `confirm` sinh mã bằng `token_hex(4).upper()`, tức 8 ký tự hex (32 bit). Cột `bookings.booking_code` có ràng buộc `unique` ([models.py](../app/infrastructure/persistence/models.py)).

**Tác động.** Khi trùng mã, `IntegrityError` không được bắt, người dùng nhận 500 dù booking hợp lệ. Theo bài toán ngày sinh, xác suất trùng đạt khoảng 1% sau ~9.300 vé và 50% sau ~77.000 vé.

**Hướng xử lý.** Chọn một trong hai:
- Tăng độ dài mã, ví dụ `token_hex(6)` (48 bit) hoặc mã base32 10 ký tự.
- Bắt lỗi trùng trên `booking_code` và sinh lại mã (tối đa vài lần) trong cùng transaction, dùng savepoint.

**Kiểm chứng.** Unit test thay bộ sinh mã bằng hàm trả mã trùng ở lần đầu, kiểm tra confirm vẫn thành công.

### 2.2. Không có tác vụ dọn hold hết hạn

**Hiện trạng.** FR-08 cho phép không cần tác vụ nền: trạng thái hiệu lực được tính theo `expires_at`, nên kết quả vẫn đúng. Tuy nhiên bản ghi `bookings` và `showtime_seats` vẫn mang `HELD` sau khi hết hạn, và chỉ được dọn khi có thao tác liên quan.

**Tác động.** Mọi truy vấn lọc theo trạng thái phải kèm điều kiện thời gian. Số dòng `HELD` "chết" tăng dần, làm chỉ mục kém chọn lọc và truy vấn đếm chậm hơn.

**Hướng xử lý.** Tác vụ định kỳ (ví dụ mỗi phút) chuyển hold hết hạn sang `EXPIRED` và trả ghế về `AVAILABLE` theo lô nhỏ. Điều kiện `UPDATE` phải kiểm tra lại `expires_at <= now()` và `booking_id` để không giải phóng nhầm hold mới (BR-08). Tính đúng đắn tiếp tục không phụ thuộc tác vụ này.

### 2.3. `POST /bookings` không idempotent

**Hiện trạng.** Pha 1 đã ghi rõ không bảo đảm idempotency (FR-05). Client phải tự kiểm tra danh sách booking khi không rõ kết quả.

**Tác động.** Mạng chập chờn hoặc người dùng bấm hai lần có thể tạo hai booking và tiêu hao hạn mức BR-11.

**Hướng xử lý.** Nhận header `Idempotency-Key`, lưu khóa cùng `user_id` và kết quả trong bảng riêng có ràng buộc unique. Gửi lại cùng khóa thì trả kết quả cũ.

### 2.4. Chưa định nghĩa việc sửa/xóa suất chiếu đang có booking

**Hiện trạng.** BR-12 và AS-03 giả định danh mục bất biến trong lúc phục vụ, nhưng hệ thống đã có API admin sửa và xóa suất chiếu.

**Hướng xử lý.** Chốt quy tắc và kiểm tra trong `ShowtimeService`:
- Chặn đổi phòng, đổi giờ hoặc xóa khi có hold hiệu lực hoặc booking đã xác nhận, trả 409.
- Đổi giá chỉ áp dụng cho hold mới. Booking cũ đã chụp giá theo BR-06.
- Thêm thao tác "ngừng bán" thay cho xóa.

## 3. Bảo mật

### 3.1. Đăng nhập không giới hạn tần suất

**Hiện trạng.** `POST /auth/login` không có giới hạn tần suất (AS-08, RI-10). bcrypt làm mỗi lần thử tốn CPU.

**Tác động.** Vừa là bề mặt dò mật khẩu, vừa là cách dễ làm quá tải CPU của server.

**Hướng xử lý.** Giới hạn theo IP và theo email (ví dụ 5 lần/phút), trả 429 kèm `Retry-After`. Với nhiều worker cần bộ đếm dùng chung, ví dụ Redis hoặc bảng trong PostgreSQL.

### 3.2. JWT không thu hồi được

**Hiện trạng.** Access token sống 60 phút, không có refresh token, không có danh sách thu hồi.

**Hướng xử lý.** Rút thời hạn access token (10–15 phút) và thêm refresh token lưu DB để thu hồi được khi đăng xuất, đổi mật khẩu hoặc khi admin khóa tài khoản.

## 4. Trải nghiệm người dùng

### 4.1. Sơ đồ ghế không tự cập nhật

**Hiện trạng.** Frontend tải sơ đồ ghế một lần. Không có polling, SSE hay WebSocket.

**Tác động.** Người dùng chỉ biết ghế đã bị lấy khi bấm giữ và nhận 409.

**Hướng xử lý.** Polling 3–5 giây khi trang sơ đồ đang mở (dừng khi tab ẩn), hoặc SSE nếu cần trễ thấp hơn. Nên làm cùng mục 1.3 để polling không đè tải lên DB.

### 4.2. Không có đếm ngược thời gian giữ ghế

**Hiện trạng.** [MovieShowtimes.tsx](../frontend/src/components/MovieShowtimes.tsx) và [TicketDetailPage.tsx](../frontend/src/pages/TicketDetailPage.tsx) chỉ hiển thị giờ hết hạn cố định. Trạng thái không tự đổi khi hết giờ.

**Hướng xử lý.** Hiển thị đồng hồ đếm ngược theo `expiresAt`. Khi về 0 thì ẩn nút xác nhận và tải lại booking. Thời gian quyết định vẫn là của server (BR-05).

## 5. Vận hành và môi trường phát triển

### 5.1. Seed lỗi encoding trên Windows

**Hiện trạng.** `scripts/seed.py` in thông báo tiếng Việt. Trên console Windows dùng code page cp1252, script dừng với `UnicodeEncodeError` sau khi đã ghi một phần dữ liệu.

**Hướng xử lý.** Thêm `sys.stdout.reconfigure(encoding="utf-8")` ở đầu script. Trước mắt có thể đặt `PYTHONIOENCODING=utf-8` trước khi chạy.

### 5.2. SQLite cục bộ không tái hiện được tranh chấp

**Hiện trạng.** Có thể chạy cục bộ bằng SQLite khi không có Docker, nhưng SQLite bỏ qua `FOR UPDATE` và chỉ cho một tiến trình ghi tại một thời điểm.

**Tác động.** Hành vi tranh chấp khi chạy cục bộ khác với PostgreSQL. Kết quả demo hoặc đo trên SQLite không phản ánh hệ thống thật.

**Hướng xử lý.** Ghi rõ giới hạn này trong [development.md](./development.md). Test đồng thời và đo tải luôn chạy trên PostgreSQL qua `TEST_DATABASE_URL` hoặc Docker Compose.

### 5.3. Cổng 8080 dễ trùng với dịch vụ khác

**Hiện trạng.** README dùng cổng 8080, thường đã bị XAMPP/Apache hoặc Tomcat chiếm. Khi đó uvicorn báo `[Errno 13]` trên Windows, một thông báo khó hiểu.

**Hướng xử lý.** Ghi chú trong README cách đổi cổng (`--port 8000` hoặc biến `APP_PORT`) và cách kiểm tra tiến trình đang giữ cổng.
