# ADR-0002 — Kiểm soát đồng thời cho inventory ghế

- **Trạng thái:** Accepted
- **Ngày:** 01/10/2026
- **Yêu cầu liên quan:** BR-01, BR-03, BR-04, BR-08, FR-05, FR-06, FR-07, NFR-01, `T-07`, `T-08`, `T-15`, `T-16`, `T-25`

## Bối cảnh

Đây là quyết định trung tâm của đồ án. BR-01 yêu cầu một ghế trong một suất chiếu chỉ có tối đa một quyền chiếm chỗ có hiệu lực. BR-04 nói rõ rằng "kiểm tra rồi ghi" ở tầng ứng dụng **không đủ**: phải có bảo vệ ở transaction hoặc constraint trong DB. BR-08 thêm một ràng buộc tinh tế hơn: khi xác nhận, hết hạn và giữ mới cạnh tranh nhau, một thao tác đến muộn của booking cũ không được phép giải phóng quyền giữ mà booking khác vừa giành được.

Đồng thời, tranh chấp ghế là tình huống nghiệp vụ **bình thường**, không phải sự cố. Mục 6.4 cấm biến nó thành `500`. Vì vậy cơ chế được chọn phải cho ra mã lỗi `409` xác định, không phải một exception hạ tầng rò lên tầng API.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược | Kết luận |
|---|---|---|---|
| **Một dòng inventory cho mỗi cặp `(showtime_id, seat_id)`, tạo sẵn từ seed; cấp ghế bằng `SELECT … FOR UPDATE` theo thứ tự `seat_id` rồi `UPDATE … WHERE` có điều kiện; xét `rowcount`** | BR-01 trở thành hệ quả của khóa chính, không phải của logic; xung đột lộ ra dưới dạng `rowcount` nên ánh xạ thẳng sang `409`; chạy ở READ COMMITTED, không cần retry | Cần kỷ luật sắp xếp `seat_id` trước khi khóa; phải dùng SQLAlchemy Core/SQL tường minh thay vì ORM state tracking | **Chọn** |
| Isolation `SERIALIZABLE` | Lập luận đúng đắn đơn giản nhất | Sinh `serialization_failure` phải retry; retry làm nhiễu chính chỉ số ta muốn đo ở L-04; thông lượng giảm mạnh trên CPU dùng chung | Loại; giữ làm ứng viên Pha 2 |
| Khóa lạc quan bằng version column trên dòng inventory | Không giữ khóa lâu | Sinh xung đột ORM cho một tình huống hoàn toàn bình thường; phải retry mới dùng được; không đơn giản hơn phương án đã chọn | Loại |
| Khóa bi quan trên bản ghi `showtime` (một khóa cho cả suất chiếu) | Rất dễ lập luận | Tuần tự hóa toàn bộ suất chiếu; L-03 "ít tranh chấp" sẽ tự tạo ra tranh chấp giả, làm hỏng ý nghĩa của kịch bản | Loại |
| Unique index bộ phận trên bảng hold riêng | Ràng buộc do DB bảo đảm | Cần thêm bảng và đường dọn dữ liệu; một dòng cho mỗi cặp đã cho cùng bảo đảm mà đơn giản hơn | Loại |
| Khóa phân tán/Redis | — | Thêm thành phần vận hành; BR-10 nói DB là nguồn quyết định; vi phạm tinh thần Pha 1 | Loại |

## Quyết định

### 1. Cấu trúc

Bảng `showtime_seat` với `PRIMARY KEY (showtime_id, seat_id)`. Toàn bộ dòng được tạo sẵn trong cùng transaction với việc tạo suất chiếu. Mỗi dòng mang `state ∈ {AVAILABLE, HELD, BOOKED}`, `booking_id` và `hold_expires_at`, ràng buộc chéo bằng `CHECK`.

Vì mỗi cặp chỉ có một dòng và một dòng chỉ mang được một `booking_id`, **BR-01 không thể bị vi phạm mà không vi phạm khóa chính**.

### 2. Isolation

`READ COMMITTED` (mặc định của PostgreSQL) cộng với khóa dòng tường minh. Trong READ COMMITTED, khi một `UPDATE` phải chờ khóa, PostgreSQL đánh giá lại mệnh đề `WHERE` trên phiên bản dòng mới nhất sau khi chờ xong. Đó chính là hành vi ta cần: kẻ thua cuộc thấy `state` đã đổi và không khớp điều kiện.

### 3. Thứ tự khóa

`seatIds` **phải được sắp xếp tăng dần** trước khi khóa:

```sql
SELECT … FROM showtime_seat
 WHERE showtime_id = :showtimeId AND seat_id = ANY(:seatIds)
 ORDER BY seat_id FOR UPDATE;
```

Không có bước này, hai yêu cầu đồng thời với tập ghế giao nhau — chính xác là kịch bản `T-08`, A1/A2 và A2/A3 — có thể khóa theo hai thứ tự ngược nhau và deadlock. Deadlock ở đây sẽ biểu hiện thành `500` cho một tranh chấp hợp lệ, vi phạm mục 6.4. Sắp xếp cho một thứ tự khóa toàn cục nên chu trình chờ không thể hình thành.

### 4. Ghi có điều kiện

```sql
UPDATE showtime_seat
   SET state = 'HELD', booking_id = :bookingId, hold_expires_at = :expiresAt
 WHERE showtime_id = :showtimeId
   AND seat_id = ANY(:seatIds)
   AND (state = 'AVAILABLE'
        OR (state = 'HELD' AND hold_expires_at <= :decisionInstant));
```

`result.rowcount != len(seat_ids)` → rollback toàn bộ transaction → `409 SEAT_UNAVAILABLE`, kèm `details.seatIds` liệt kê **tất cả** ghế gây lỗi (mục 6.4). Đây là điều kiện toàn-bộ-hoặc-không-ghế-nào của FR-05, và nó được thực thi bởi DB chứ không bởi một chuỗi `if` trong ứng dụng.

Mệnh đề `OR (state = 'HELD' AND hold_expires_at <= :decisionInstant)` đồng thời là toàn bộ cơ chế thu hồi hold hết hạn của Pha 1 — xem ADR-0003.

### 5. Phạm vi của mọi thao tác chuyển trạng thái

Tất cả lệnh ghi inventory sau bước cấp ghế đều mang điều kiện `booking_id = :bookingId`:

```sql
-- xác nhận
UPDATE showtime_seat SET state='BOOKED', hold_expires_at=NULL
 WHERE booking_id = :bookingId AND state='HELD' AND hold_expires_at > :decisionInstant;

-- hủy
UPDATE showtime_seat SET state='AVAILABLE', booking_id=NULL, hold_expires_at=NULL
 WHERE booking_id = :bookingId AND state='HELD';
```

Đây là cơ chế thực thi BR-08. Nếu hold của booking A hết hạn và ghế đã được booking B giành lấy, dòng inventory giờ mang `booking_id = B`. Lệnh hủy đến muộn của A không khớp dòng nào và không thể giải phóng ghế của B.

### 6. Ánh xạ lỗi hạ tầng

Trong `app.infrastructure.persistence`, repository bắt `sqlalchemy.exc.IntegrityError` và `sqlalchemy.exc.OperationalError`. Với các SQLSTATE PostgreSQL đã biết như deadlock, lock conflict hoặc serialization failure, repository rollback Session và ném lại `SeatUnavailableError` **trước khi** thoát khỏi infrastructure. Tầng API không bao giờ nhìn thấy exception của SQLAlchemy/psycopg.

## Hệ quả

### Tích cực

- Bất biến quan trọng nhất của hệ thống do schema bảo đảm, không do logic ứng dụng.
- Không cần retry, nên kết quả đo của L-04 phản ánh tranh chấp thật chứ không phản ánh chính sách retry.
- Xung đột có mã lỗi xác định, viết được assertion chắc chắn trong `T-07`, `T-08`, `T-25`.
- Baseline không bị "ăn gian dễ": không có constraint nào bị bỏ để lấy hiệu năng (mục 11.2).

### Tiêu cực và đánh đổi phải chấp nhận

- **Giữ khóa dòng trong suốt transaction ghi.** Với các nhóm ghế giao nhau, các yêu cầu bị tuần tự hóa. Đây chính là điểm nghẽn mà L-04 sẽ đo, và là ứng viên cải tiến rõ ràng nhất cho Pha 2.
- **Lệnh ghi đi vòng qua ORM state tracking.** Dùng SQLAlchemy Core/`text()`, kiểm tra `result.rowcount` và gọi `Session.expire_all()` nếu transaction cần đọc lại entity. Lập trình viên phải nhớ rằng ORM instance đang giữ có thể cũ sau bulk update.
- **Quy tắc sắp xếp `seat_id` là ngầm định và dễ mất.** Phải được viết thành một bài kiểm thử riêng, không chỉ là một dòng bình luận. `T-08` chạy lặp nhiều vòng chính là bài kiểm thử đó.
- Tạo sẵn inventory làm seed nặng hơn: 18.000 dòng cho profile chuẩn. Thời gian seed phải đo và tách khỏi thời gian đo tải (mục 10.3).

### Cách kiểm chứng

| Kiểm thử | Chứng minh điều gì |
|---|---|
| `T-07` | 20 yêu cầu tranh một ghế: đúng 1 thắng, 19 nhận `409`, không có `5xx`; chạy cả biến thể cùng một người dùng |
| `T-08` | Tập ghế giao nhau: đúng một booking thành công, ghế chỉ thuộc nhóm thua vẫn `AVAILABLE`; lặp nhiều vòng để lộ deadlock nếu quy tắc sắp xếp bị bỏ |
| `T-15`, `T-16` | Xác nhận, hết hạn và giữ mới cạnh tranh: không thao tác nào giải phóng quyền chiếm ghế mới |
| `T-17` | Lỗi giữa chừng: rollback sạch, không có booking hay ghế bị ghi một phần |
| `T-25` | Tranh chấp trên suất chiếu chưa từng có giao dịch: không có `500` do vi phạm khóa chính |
| `scripts/check-invariants.sql` | I1–I7 trả về 0 dòng sau mọi bài đo (`NFR-01`) |

Integration test phải chạy trên PostgreSQL thật qua `testcontainers.postgres.PostgresContainer`. Mock repository không chứng minh được bất kỳ điều nào ở trên (mục 9.1).
