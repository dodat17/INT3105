# ADR-0005 — Xác thực JWT

- **Trạng thái:** Accepted
- **Ngày:** 01/10/2026
- **Yêu cầu liên quan:** FR-01, AS-04, AS-05, AS-08, RI-10, `T-01`, `T-02`, `T-13`, `T-23`

## Bối cảnh

FR-01 yêu cầu Bearer JWT với xác thực tập trung, hash mật khẩu chuyên dụng có salt, và thông báo lỗi chung không tiết lộ tài khoản có tồn tại hay không.

Ba ràng buộc từ phạm vi định hình thiết kế này, và cả ba đều là quyết định có chủ đích chứ không phải thiếu sót:

1. **Không có giới hạn tần suất.** Từ đặc tả phiên bản 1.2, mọi biện pháp chống lạm dụng nằm ngoài phạm vi Pha 1.
2. **Không có refresh token và không thu hồi token** (mục 2.2).
3. **Không có TLS trong ứng dụng** (AS-05).

## Quyết định

### 1. Hash mật khẩu

BCrypt qua package `bcrypt`, cost factor **10**. Adapter `BcryptPasswordHasher` cài đặt port `PasswordHasher` của domain.

Cost 10 thay vì giá trị cao hơn là đánh đổi có chủ đích cho môi trường đo: mỗi lần hash tốn khoảng 50–80 ms trên CPU chia sẻ của Kaggle, và cost 12 nhân chi phí đó lên bốn lần. Cost factor là cấu hình và phải giữ **nguyên giá trị** giữa baseline và bản cải tiến. Hệ thống thật nên dùng cost cao hơn hoặc Argon2id; đây là giới hạn có ý thức của môi trường đồ án, ghi lại để không ai đọc số liệu này như số liệu production.

Xác minh mật khẩu phải chạy **kể cả khi email không tồn tại**, đối chiếu với một hash giả cố định, để thời gian phản hồi không tiết lộ tài khoản có tồn tại hay không (FR-01).

### 2. Token

| Thuộc tính | Giá trị |
|---|---|
| Thuật toán | `HS256` |
| Khóa | `JWT_SECRET`, base64, tối thiểu 32 byte entropy; ứng dụng **từ chối khởi động** nếu thiếu hoặc quá ngắn |
| Claim | `sub` = ID người dùng, `iat`, `exp`. Không có dữ liệu cá nhân nào khác |
| TTL | 60 phút, cấu hình qua `JWT_TTL_MINUTES` |
| Dung sai lệch đồng hồ | 60 giây |

Chọn `HS256` thay vì `RS256` vì hệ thống chỉ có một bên vừa phát hành vừa xác minh token; khóa bất đối xứng thêm việc quản lý cặp khóa mà không đổi lấy lợi ích nào ở phạm vi này.

**Từ chối `alg` do token tự khai báo.** Dùng PyJWT với `jwt.decode(token, key, algorithms=["HS256"], leeway=60, options={"require": ["sub", "iat", "exp"]})`. Danh sách thuật toán được cố định phía server. Token khai `alg: none` hoặc thuật toán khác đều bị từ chối với `401`.

### 3. Xác thực tập trung

Một pure ASGI `JwtAuthMiddleware` duy nhất, không tạo session phía server:

```text
/api/v1/auth/login                      permitAll
/api/v1/movies/**, /showtimes/**        permitAll
/health/live, /health/ready             permitAll
/docs, /redoc, /openapi.json            permitAll
/api/v1/bookings/**, /api/v1/me/**      authenticated
mọi đường dẫn còn lại                    authenticated
```

Không router nào tự xác minh `Authorization` header. Middleware đặt `user_id` vào request state; dependency `current_user_id` lấy giá trị đó và truyền cho service. Tầng nghiệp vụ không biết FastAPI request hoặc middleware tồn tại.

Danh sách này bao trùm **cả năm** endpoint booking, không chỉ hai endpoint tối thiểu mà tiêu chí nghiệm thu cũ nêu ra.

### 4. Truy cập tài nguyên của người khác trả `404`, không phải `403`

Booking không thuộc người gọi được xử lý giống hệt booking không tồn tại (FR-09). `403` sẽ xác nhận rằng tài nguyên đó có thật, tức là một oracle liệt kê ID. Đây là lý do bảng lỗi ở mục 6.4 gộp hai trường hợp vào cùng `RESOURCE_NOT_FOUND`.

### 5. Log

Không bao giờ log mật khẩu hay token đầy đủ. Khi cần log token để gỡ lỗi, chỉ ghi 8 ký tự đầu của phần chữ ký. Dòng log mỗi request theo NFR-07 chứa `requestId`, method, route template, status và thời gian xử lý — không chứa header `Authorization`.

## Hệ quả

### Tích cực

- Một điểm xác thực duy nhất, không lặp lại logic trong từng handler (mục 8.2).
- `T-23` phủ được các biến thể tấn công token phổ biến vì thuật toán bị cố định ở phía server.
- Không có trạng thái phiên nên không có thành phần nào phải chia sẻ giữa các instance.

### Tiêu cực và đánh đổi phải chấp nhận

- **`POST /auth/login` hoàn toàn không được bảo vệ trước dò mật khẩu.** Không có giới hạn tần suất, không có lockout, không có backoff. Hệ quả kép:
  - *Bảo mật:* endpoint này mở cho credential stuffing. Chấp nhận được **chỉ** vì AS-08 giả định bên gọi là client có kiểm soát, không phải Internet công cộng. Nếu giả định đó sai, đây là lỗ hổng thật.
  - *Đo lường:* BCrypt cost 10 tốn 50–80 ms CPU cho mỗi lần thử. Ở mức đồng thời 100 trên máy dùng chung (AS-06), riêng đăng nhập có thể chiếm hết CPU và làm sai lệch số liệu của mọi kịch bản khác. Vì vậy **token phải được chuẩn bị trước bài đo nghiệp vụ**, và tải đăng nhập nếu cần thì đo như một kịch bản riêng (RI-10).
- **Không thu hồi được token (AS-04).** Một token vẫn hiệu lực tới 60 phút sau khi tài khoản bị vô hiệu. Chấp nhận được vì tài khoản seed không bị vô hiệu khi đang chạy; nếu giả định đó sai thì cần blacklist hoặc refresh token, vốn nằm ngoài phạm vi.
- **Ứng dụng phục vụ HTTP, không TLS (AS-05).** Bearer token đi qua kênh không mã hóa. Cấu hình này không được triển khai ra môi trường công khai.
- **BCrypt cost 10 thấp hơn khuyến nghị cho production.** Ghi rõ trong README rằng đây là lựa chọn cho môi trường đo.

Ba gạch đầu dòng trên phải xuất hiện trong README dưới dạng giới hạn đã biết. Một hệ thống có lỗ hổng được ghi nhận là một bài tập trung thực; một hệ thống có lỗ hổng được trình bày như đã bảo vệ thì không.

### Cách kiểm chứng

| Kiểm thử | Chứng minh điều gì |
|---|---|
| `T-01` | Đăng nhập đúng/sai; hai trường hợp sai trả cùng `code` và cùng `message` |
| `T-02` | Thiếu, sai, hết hạn token trên endpoint được bảo vệ: `401`, không thay đổi dữ liệu |
| `T-13` | Truy cập booking người khác trả `404`, không phải `403` |
| `T-23` | Token sửa payload, ký sai khóa, khai `alg: none`, thiếu `sub`, hết hạn trong và ngoài dung sai |
