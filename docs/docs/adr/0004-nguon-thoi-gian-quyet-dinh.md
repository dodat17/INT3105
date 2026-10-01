# ADR-0004 — Nguồn thời gian quyết định

- **Trạng thái:** Accepted
- **Ngày:** 01/10/2026
- **Yêu cầu liên quan:** BR-05, BR-13, FR-05, FR-06, FR-08, mục 5 của [requirements.md](../../requirements.md)

## Bối cảnh

BR-13 yêu cầu chốt **một** nguồn thời gian quyết định duy nhất và cấm trộn đồng hồ ứng dụng với đồng hồ DB trong cùng một luồng quyết định. BR-05 yêu cầu thời gian do server/DB xác định, lưu UTC, trả ISO 8601 có timezone, và không tin thời gian client.

Mục 5 của đặc tả thêm một câu dễ bị bỏ qua nhưng quyết định toàn bộ thiết kế này:

> Thời điểm quyết định được lấy sau khi giành quyền xử lý bản ghi liên quan để tránh xác nhận dựa trên thời gian cũ sau một lần chờ khóa dài.

## Vấn đề cụ thể: `now()` của PostgreSQL là một cái bẫy

Trong PostgreSQL, `now()` và `transaction_timestamp()` trả về **thời điểm bắt đầu transaction** và giữ nguyên giá trị đó suốt transaction. Chỉ `clock_timestamp()` trả về thời gian thực tại thời điểm gọi.

Hệ quả với luồng xác nhận:

```text
T0  transaction bắt đầu          → now() bị đóng băng tại T0
T0  SELECT booking … FOR UPDATE  → phải chờ, vì một transaction khác đang giữ khóa
T0+4s  giành được khóa
        booking.expires_at = T0 + 2s   ← đã hết hạn trong lúc chờ
        nếu so sánh với now() = T0     → tưởng là CÒN HẠN → xác nhận sai
        nếu so sánh với clock_timestamp() = T0+4s → đúng: đã hết hạn → 409
```

Đây không phải tình huống lý thuyết. Nó xảy ra chính xác ở `T-15` và `T-16`, những bài kiểm thử cố tình tạo ra tranh chấp có chờ khóa, và chính là lỗi mà mục 5 cảnh báo.

Đồng hồ của tiến trình ứng dụng (`datetime.now()` trong Python) có một vấn đề khác: nó là một đồng hồ thứ hai, lệch với đồng hồ DB. Trộn hai đồng hồ khiến `expires_at` được ghi bằng đồng hồ này rồi so sánh bằng đồng hồ kia — đúng điều BR-13 cấm.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược | Kết luận |
|---|---|---|---|
| **`clock_timestamp()` của PostgreSQL, đọc sau khi giành khóa** | Một đồng hồ duy nhất; đúng sau khi chờ khóa; thỏa cả BR-13 lẫn mục 5 | Tốn một round trip cho mỗi use case ghi | **Chọn** |
| `now()` / `transaction_timestamp()` | Không tốn round trip riêng | Đóng băng tại lúc mở transaction → xác nhận sai sau chờ khóa dài | Loại vì sai |
| `datetime.now()` trong Python | Rẻ nhất, dễ inject clock giả | Đồng hồ thứ hai, lệch với DB; vi phạm BR-13 | Loại |
| Python process là nguồn chính, DB dùng làm đối chiếu | — | Vẫn là hai đồng hồ; phức tạp hơn mà không đúng hơn | Loại |

## Quyết định

### 1. Nguồn duy nhất

`clock_timestamp()` của PostgreSQL là nguồn thời gian quyết định cho `created_at`, `expires_at`, `confirmed_at`, `cancelled_at` và **mọi** phép so sánh hết hạn. Đồng hồ của tiến trình Python không xuất hiện trong bất kỳ đường quyết định nghiệp vụ nào.

Truy cập qua port `Clock` của tầng `domain`:

```python
# app.domain.port.clock
class Clock(Protocol):
    def now(self) -> datetime: ...

# app.infrastructure.time.postgres_clock
class PostgresClock:
    def __init__(self, session: Session):
        self._session = session

    def now(self) -> datetime:
        return self._session.execute(
            text("SELECT clock_timestamp()")
        ).scalar_one()
```

`PostgresClock` dùng cùng SQLAlchemy Session với Unit of Work để lệnh đọc thời gian nằm trong đúng transaction đang giữ khóa.

### 2. Thời điểm lấy

Trong các use case ghi, `clock.now()` được gọi **sau** khi đã giành quyền xử lý bản ghi liên quan:

```text
BEGIN
  SELECT … FROM booking WHERE id = :id FOR UPDATE   ← giành quyền trước
  decisionInstant := clock.now()                     ← rồi mới lấy thời điểm
  … mọi so sánh đều dùng decisionInstant …
COMMIT
```

Trong một transaction, `decisionInstant` được lấy **một lần** rồi truyền xuống mọi truy vấn con, để mọi so sánh trong cùng một quyết định đều nhất quán với nhau.

### 3. Lưu trữ và biểu diễn

- Cột kiểu `TIMESTAMPTZ`; PostgreSQL lưu UTC.
- Python process và container đặt `TZ=UTC`; mọi `datetime` đi qua domain phải timezone-aware.
- API trả ISO 8601 có offset, ví dụ `2026-09-10T12:00:00Z` (BR-05).
- Múi giờ rạp (`CINEMA_TIMEZONE`) **chỉ** dùng để diễn giải bộ lọc `date` ở FR-03. Nó không ảnh hưởng tới lưu trữ hay tới bất kỳ so sánh hết hạn nào.

### 4. Kiểm thử

Unit test inject một `Clock` giả để kiểm tra cả ba biên `now < expiresAt`, `now = expiresAt`, `now > expiresAt` mà không phải chờ 5 phút. Integration test dùng `PostgresClock` thật; để kiểm tra hành vi hết hạn, chúng hạ `HOLD_TTL_SECONDS` xuống giá trị nhỏ thay vì giả lập thời gian.

## Hệ quả

### Tích cực

- Xác nhận sau một lần chờ khóa dài cho kết quả đúng (`T-15`, `T-16`).
- Chỉ có một đồng hồ trong toàn hệ thống, nên không có lớp lỗi "lệch đồng hồ giữa app và DB".
- `Clock` là port nên tầng nghiệp vụ vẫn kiểm thử được bằng unit test thuần.

### Tiêu cực và đánh đổi phải chấp nhận

- **Một round trip DB thêm cho mỗi use case ghi.** Ở mức đồng thời cao trên máy dùng chung, chi phí này không phải bằng không. Đo nó trong pilot; nếu số truy vấn mỗi request trở thành điểm nghẽn, gộp `clock_timestamp()` vào chính câu `UPDATE` là một tối ưu hợp lệ cho Pha 2 — nhưng chỉ khi số liệu chứng minh, không phải vì linh cảm.
- **Quy tắc "lấy sau khi khóa" là ngầm định và dễ bị đảo ngược** bởi một lần refactor vô hại. `T-15` và `T-16` là hàng rào duy nhất; chúng phải chạy trong CI, không phải chạy tay.
- Đường đọc cũng gọi `clock.now()` một lần cho mỗi request để suy ra trạng thái hiệu lực, thêm một round trip cho các endpoint đọc. Với L-01 và L-02 đây là chi phí đáng theo dõi.

### Cách kiểm chứng

| Kiểm thử | Chứng minh điều gì |
|---|---|
| `T-09`, `T-10` | Biên hết hạn đúng ở cả ba điểm `<`, `=`, `>` |
| `T-15` | Xác nhận đồng thời với hủy: chỉ một chuyển trạng thái thắng sau khi chờ khóa |
| `T-16` | Xác nhận / thu hồi hết hạn / giữ mới cạnh tranh: không ghi đè lẫn nhau |
| `T-19` | Khởi động lại backend không kéo dài hạn giữ |
| `T-21` | Mốc thời gian trả về là ISO 8601 có timezone và lưu UTC |

Một bài kiểm thử bổ sung nên có: monkeypatch đồng hồ Python hoặc chỉnh đồng hồ hệ điều hành của tiến trình ứng dụng lệch vài phút so với DB rồi chạy lại `T-09` và `T-10`. Nếu kết quả không đổi, quyết định này đã được thực hiện đúng. Nếu đổi, ở đâu đó trong mã vẫn còn `datetime.now()` trên đường quyết định nghiệp vụ.
