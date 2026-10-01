# ADR-0003 — Thu hồi hold hết hạn ngay trên đường ghi, không dùng tác vụ nền

- **Trạng thái:** Accepted
- **Ngày:** 01/10/2026
- **Yêu cầu liên quan:** FR-04, FR-08, FR-09, BR-07, `T-10`, `T-14`, `T-19`, `T-24`

## Bối cảnh

Hold hết hiệu lực khi `now >= expiresAt`. FR-08 đặt ra một yêu cầu khắt khe: **tính đúng đắn không được phụ thuộc tần suất chạy của bất kỳ tác vụ dọn dữ liệu nào**, và API không được trả `HELD` cho một booking đã hết hạn ngay cả khi bản ghi trong DB vẫn đang mang `status = 'HELD'`.

Nói cách khác, trạng thái vật lý trong DB và trạng thái hiệu lực có thể lệch nhau, và mọi đường đọc lẫn đường ghi phải làm việc với trạng thái hiệu lực.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược | Kết luận |
|---|---|---|---|
| **Thu hồi ngay trên đường ghi + suy ra trạng thái trên đường đọc** | Không có thành phần vận hành thêm; đúng ngay cả khi không có job nào chạy; thỏa FR-08 theo đúng chữ | Mỗi truy vấn đọc phải mang điều kiện thời gian; dòng `HELD` đã chết tồn tại tới khi có người khác cần ghế | **Chọn** |
| Worker nền quét và dọn định kỳ | Dữ liệu sạch; đường đọc đơn giản | Tính đúng đắn phụ thuộc chu kỳ job — vi phạm trực tiếp FR-08; thêm tài nguyên vào ngân sách chung của máy đo | Loại ở Pha 1; là ứng viên Pha 2 (mục 11.2) |
| `UPDATE` ghi lại `status='EXPIRED'` mỗi khi đọc | Trạng thái vật lý luôn đúng | Biến `GET` thành thao tác ghi; phá vỡ L-01/L-02 như kịch bản đọc thuần | Loại |

## Quyết định

### 1. Đường ghi thu hồi cơ hội

Mệnh đề thu hồi được nhúng thẳng vào chính câu lệnh cấp ghế của ADR-0002:

```sql
AND (state = 'AVAILABLE'
     OR (state = 'HELD' AND hold_expires_at <= :decisionInstant))
```

Một hold hết hạn vì thế được thu hồi **bởi chính người cần ghế đó**, trong cùng transaction, dưới cùng khóa dòng. Không có cửa sổ nào để hai người cùng "thu hồi rồi giữ".

### 2. Đường đọc suy ra trạng thái

Không thao tác đọc nào ghi dữ liệu. Trạng thái hiệu lực được tính trong chính câu truy vấn:

```sql
-- sơ đồ ghế (FR-04)
CASE WHEN ss.state = 'BOOKED' THEN 'BOOKED'
     WHEN ss.state = 'HELD' AND ss.hold_expires_at > :now THEN 'HELD'
     ELSE 'AVAILABLE' END
```

Với `GET /me/bookings?status=` (FR-09), bộ lọc được dịch sang điều kiện trên cột thật để dùng được index `ix_booking_user_status_exp`, thay vì tính `CASE` rồi lọc ngoài bộ nhớ:

| `status` yêu cầu | Điều kiện SQL |
|---|---|
| `HELD` | `status = 'HELD' AND expires_at > :now` |
| `EXPIRED` | `status = 'HELD' AND expires_at <= :now` |
| `CONFIRMED` / `CANCELLED` | `status = :status` |

Đây là lý do FR-09 bắt buộc lọc, sắp xếp, phân trang và `totalItems` phải nằm trong cùng một truy vấn: nếu lọc lại trong bộ nhớ sau khi đã phân trang thì `totalItems` sai và ranh giới trang không còn ổn định.

### 3. `status = 'EXPIRED'` gần như không bao giờ được ghi vật lý

Giá trị `EXPIRED` tồn tại trong `CHECK` constraint và trong enum để Pha 2 có thể dùng, nhưng ở Pha 1 hầu như không có đường nào ghi nó. Một booking bị bỏ dở sống mãi trong DB với `status = 'HELD'` và `expires_at` trong quá khứ. Điều đó **không phải lỗi**: nó chính là hình dạng dữ liệu mà FR-08 mô tả.

Hệ quả cho kiểm thử: `T-14` và `T-24` phải kiểm tra **phản hồi của API**, không phải cột `status` trong DB. Một bài kiểm thử khẳng định `booking.status == 'EXPIRED'` trong DB sẽ fail dù hệ thống hoàn toàn đúng.

## Hệ quả

### Tích cực

- Không có thành phần vận hành thêm ở Pha 1; đúng với phạm vi mục 2.1.
- Tính đúng đắn độc lập hoàn toàn với lịch chạy job (`T-14`, `T-19`).
- Việc thu hồi xảy ra dưới khóa dòng đã có sẵn, nên không tạo thêm đường tranh chấp nào.

### Tiêu cực và đánh đổi phải chấp nhận

- **Chi phí thu hồi bị dồn vào request của người dùng.** Đây chính là loại điểm nghẽn mà L-06 được thiết kế để đo, và mục 11.2 đã liệt kê worker thu hồi là một hướng cải tiến Pha 2 hợp lệ — nhưng chỉ khi số liệu chứng minh nó cần thiết.
- **Dòng `HELD` đã chết tích tụ** trong `booking` và `showtime_seat`. Với ghế nóng chúng bị ghi đè ngay; với ghế nguội chúng tồn tại tới hết đợt đo. Không ảnh hưởng tính đúng đắn, có ảnh hưởng kích thước bảng — theo dõi khi đo L-06.
- **Mọi truy vấn đọc booking phải truyền `:now`.** Quên một chỗ là rò rỉ trạng thái sai ra API. Giảm thiểu bằng cách tập trung toàn bộ truy vấn đọc booking vào một repository duy nhất và phủ `T-24` lên mọi nhánh lọc.
- Nếu Pha 2 thêm worker nền, worker đó **phải idempotent** và **không được đụng vào booking đã xác nhận hay hold mới** — tức là vẫn phải mang điều kiện `booking_id` như ADR-0002 (mục 11.2).

### Cách kiểm chứng

| Kiểm thử | Chứng minh điều gì |
|---|---|
| `T-10` | Xác nhận đúng lúc `now = expiresAt` và sau đó: `409 BOOKING_EXPIRED`, không tạo vé |
| `T-14` | Không có tác vụ nền: `GET` trả trạng thái hiệu lực đúng và người khác giữ lại được ghế |
| `T-19` | Khởi động lại backend không kéo dài hạn giữ |
| `T-24` | Lọc `HELD` không trả booking quá hạn; lọc `EXPIRED` trả đúng chúng; `totalItems` khớp |

Unit test dùng clock giả để kiểm tra cả ba biên `now < expiresAt`, `now = expiresAt`, `now > expiresAt` mà không phải chờ 5 phút (mục 9.1).
