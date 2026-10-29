# Đặc tả yêu cầu phần mềm — Hệ thống đặt vé xem phim

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Người dùng và use case](#2-người-dùng-và-use-case)
3. [Quy tắc nghiệp vụ và yêu cầu chức năng](#3-quy-tắc-nghiệp-vụ-và-yêu-cầu-chức-năng)
4. [Yêu cầu phi chức năng](#4-yêu-cầu-phi-chức-năng)
5. [Ràng buộc, giả định, phụ thuộc và rủi ro](#5-ràng-buộc-giả-định-phụ-thuộc-và-rủi-ro)
6. [Kiểm chứng và nghiệm thu](#6-kiểm-chứng-và-nghiệm-thu)
7. [Phụ lục](#7-phụ-lục)

---

## 1. Giới thiệu

### 1.1. Giới thiệu

Ứng dụng web đặt vé xem phim cho một rạp chiếu phim. Hệ thống cho phép người dùng có thể xem lịch chiếu, thông tin các
bộ phim sắp trình chiếu, đặt vé,...

### 1.2. Phạm vi hệ thống

- Một rạp, nhiều phòng chiếu; mỗi phòng có sơ đồ ghế dạng lưới, hai loại ghế Thường và VIP.
- Danh mục phim có ngày khởi chiếu và nhãn phân loại độ tuổi; phim chia thành "Đang chiếu" và "Sắp chiếu".
- Lịch chiếu có thời gian dọn phòng giữa các suất; giá vé theo suất chiếu, ghế VIP phụ thu cố định.
- Đăng ký tài khoản khách hàng, đăng nhập, xem thông tin tài khoản.
- Giữ một hoặc nhiều ghế thuộc cùng một suất chiếu trong 5 phút.
- Xác nhận đặt vé **mô phỏng thanh toán**, không xử lý tiền thật; khách nhận mã đặt vé.
- Hủy chỗ đang giữ; ghế hết hạn giữ tự trả lại mà không cần tác vụ nền.
- Xem danh sách và chi tiết vé của chính mình.
- Quản trị: thêm/sửa/xóa phim, thêm/sửa phòng chiếu, thêm/sửa/xóa suất chiếu, quản lý người dùng, tra cứu booking.
- Giao diện web cho khách và quản trị viên.
- Kiểm thử chức năng, tích hợp, tranh chấp đồng thời; kiểm thử tải trên Kaggle Notebook CPU.

### 1.3. Ngoài phạm vi

Các mục dưới đây là quyết định có chủ đích, không phải thiếu sót. Không mở rộng phạm vi trước khi hoàn tất tiêu chí
nghiệm thu Pha 1.

- Cổng thanh toán, hoàn tiền, hóa đơn tài chính, gửi email/SMS, quét vé tại rạp.
- Đổi ghế, đổi suất, hủy vé đã mua.
- Giá theo ngày/giờ (cuối tuần, ngày lễ, giờ vàng), giá theo đối tượng (học sinh – sinh viên, trẻ em, người cao tuổi),
  khuyến mãi, thẻ thành viên, combo bắp nước.
- Xác minh độ tuổi khi đặt vé trực tuyến; việc kiểm tra giấy tờ diễn ra tại cửa soát vé.
- Ngày ngừng chiếu của phim, định dạng chiếu (2D/3D/IMAX), phụ đề/lồng tiếng.
- Quản lý chuỗi rạp, đề xuất phim, tìm kiếm nâng cao.
- Quy tắc chọn ghế nâng cao: bắt buộc ghế liền kề, chống bỏ trống ghế lẻ, ghế đôi, ghế dành cho người khuyết tật.
- Xóa phòng chiếu; hủy hoặc dời suất chiếu đã có booking cùng luồng đền bù (`AS-03`).
- Thu hồi token tức thời, refresh token, vô hiệu hóa tài khoản (`AS-04`).
- Giới hạn tần suất, chống credential stuffing và các biện pháp chống lạm dụng khác (`AS-07`, `RI-10`).

---

## 2. Người dùng và use case

### 2.1. Tác nhân

| Tác nhân                | Quyền chính                                                                     |
|-------------------------|---------------------------------------------------------------------------------|
| Khách (chưa đăng nhập)  | Xem phim, suất chiếu, sơ đồ ghế; đăng ký; đăng nhập.                            |
| Khách hàng (`CUSTOMER`) | Mọi quyền của khách; giữ ghế, xác nhận, hủy, xem vé của mình.                   |
| Quản trị viên (`ADMIN`) | Quản lý phim, phòng, suất chiếu, người dùng; tra cứu mọi booking. Không đặt vé. |

### 2.2. Thuật ngữ

| Thuật ngữ           | Định nghĩa                                                                           |
|---------------------|--------------------------------------------------------------------------------------|
| Suất chiếu          | Một lần chiếu của một phim trong một phòng tại một thời điểm                         |
| Ngày khởi chiếu     | Ngày đầu tiên phim được phép chiếu tại rạp                                           |
| Nhãn phân loại      | Mức độ tuổi được phép xem phim theo quy định Việt Nam: P, K, T13, T16, T18           |
| Booking             | Một lần đặt chỗ cho một hoặc nhiều ghế trong cùng suất chiếu                         |
| Giữ ghế (hold)      | Quyền giữ ghế tạm thời của một booking đang chờ xác nhận                             |
| Mã đặt vé           | Mã khách đưa ra tại quầy để nhận vé, chỉ có sau khi xác nhận                         |
| Booking item        | Một ghế và đơn giá tương ứng trong booking; là lịch sử, không bị xóa                 |
| Inventory ghế       | Bản ghi cho một cặp suất chiếu–ghế; nơi **duy nhất** quyết định ghế đang thuộc về ai |
| Trạng thái hiệu lực | Trạng thái booking sau khi xét thời hạn thực tế; có thể khác giá trị đang lưu        |

### 2.3. Danh sách use case

| Mã    | Use case                           | Tác nhân                  | Yêu cầu chính |
|-------|------------------------------------|---------------------------|---------------|
| UC-01 | Đăng ký tài khoản                  | Khách                     | FR-10         |
| UC-02 | Đăng nhập, xem thông tin tài khoản | Khách hàng, Quản trị viên | FR-01, FR-11  |
| UC-03 | Xem phim đang chiếu, sắp chiếu     | Mọi người dùng            | FR-02         |
| UC-04 | Xem lịch chiếu theo phim và ngày   | Mọi người dùng            | FR-03         |
| UC-05 | Xem sơ đồ ghế của suất chiếu       | Mọi người dùng            | FR-04         |
| UC-06 | Giữ ghế                            | Khách hàng                | FR-05         |
| UC-07 | Xác nhận đặt vé                    | Khách hàng                | FR-06         |
| UC-08 | Hủy chỗ đang giữ                   | Khách hàng                | FR-07         |
| UC-09 | Xem vé của tôi                     | Khách hàng                | FR-08, FR-09  |
| UC-10 | Quản lý phim                       | Quản trị viên             | FR-12         |
| UC-11 | Quản lý phòng chiếu                | Quản trị viên             | FR-13         |
| UC-12 | Quản lý suất chiếu                 | Quản trị viên             | FR-14         |
| UC-13 | Quản lý người dùng                 | Quản trị viên             | FR-15         |
| UC-14 | Tra cứu booking                    | Quản trị viên             | FR-16         |

### 2.4. Use case trọng tâm: đặt vé (UC-06, UC-07)

**Tiền điều kiện:** khách hàng đã đăng nhập; suất chiếu đang mở bán và chưa bắt đầu.

**Luồng chính**

1. Khách hàng chọn phim, chọn suất chiếu và mở sơ đồ ghế.
2. Khách hàng chọn 1–8 ghế và gửi yêu cầu giữ ghế.
3. Hệ thống giữ toàn bộ ghế trong 5 phút và trả booking "Đang giữ" kèm hạn giữ và tổng tiền.
4. Khách hàng xem lại phim, nhãn phân loại, suất, ghế, tổng tiền rồi xác nhận trước khi hết hạn.
5. Hệ thống chuyển booking sang "Đã xác nhận", ghế sang "Đã bán", cấp mã đặt vé.

**Luồng thay thế và ngoại lệ**

| Bước | Tình huống                                      | Kết quả                                                             |
|------|-------------------------------------------------|---------------------------------------------------------------------|
| 3    | Một trong các ghế vừa bị người khác giữ         | Không giữ ghế nào; báo ghế không còn trống và tải lại sơ đồ         |
| 3    | Khách đã giữ quá số booking cho phép (`BR-18`)  | Từ chối, yêu cầu hoàn tất hoặc hủy booking đang giữ                 |
| 3    | Ghế trùng, không tồn tại, khác phòng, quá 8 ghế | Từ chối do dữ liệu không hợp lệ                                     |
| 4    | Khách hàng hủy thay vì xác nhận                 | Booking "Đã hủy", ghế trả lại ngay                                  |
| 4    | Quá hạn giữ                                     | Không xác nhận được; ghế đã trở lại trạng thái trống với người khác |
| 4    | Bấm xác nhận lần nữa sau khi đã thành công      | Trả lại đúng vé đã xác nhận, không tạo vé mới                       |

**Hậu điều kiện:** mỗi ghế trong suất chiếu có tối đa một chủ (`BR-15`); không có booking hoặc ghế bị ghi một phần
(`CON-04`).

### 2.5. Vòng đời booking

```text
                 xác nhận trước hạn
  ĐANG GIỮ (HELD) ----------------> ĐÃ XÁC NHẬN (CONFIRMED)
        |
        +---- khách hủy ----------> ĐÃ HỦY (CANCELLED)
        |
        +---- hết thời hạn giữ ---> HẾT HẠN (EXPIRED)
```

Trạng thái chỉ đi một chiều (`BR-23`).

---

## 3. Quy tắc nghiệp vụ và yêu cầu chức năng

### 3.1. Quy ước chung của API

Áp dụng cho mọi FR có endpoint.

- Prefix `/api/v1`. Request và response có body dùng `application/json`; `204` không có body.
- ID là UUID dạng chuỗi.
- Thời gian trả theo ISO 8601 có múi giờ. Tiền là số nguyên VND, kèm `currency = "VND"` trong response có tiền.
- Mọi route dưới `/api/` yêu cầu header `Authorization: Bearer <token>`, trừ danh sách công khai ở phụ lục 7.A. Route
  mới mặc định được bảo vệ.
- Endpoint dưới `/api/v1/admin/` yêu cầu vai trò `ADMIN`; vai trò khác nhận `403 FORBIDDEN`.
- **Phân trang:** `page` mặc định 1, `pageSize` mặc định 20, tối đa 100; giá trị không hợp lệ trả `400`. Trang vượt quá
  số trang hiện có trả `200` với `items` rỗng và `totalItems` đúng. Response gồm `items`, `page`, `pageSize`,
  `totalItems`.
- **Thứ tự ổn định:** phim theo ngày khởi chiếu mới nhất trước, rồi tên; suất chiếu theo giờ bắt đầu; booking mới nhất
  trước; ghế theo hàng rồi số ghế.
- DTO từ chối trường ngoài hợp đồng, ở cả body và query parameter.
- `error.message` bằng tiếng Việt và có thể thay đổi; bên gọi xử lý theo `error.code`.

**Hợp đồng lỗi**

```json
{
  "error": {
    "code": "SEAT_UNAVAILABLE",
    "message": "Một hoặc nhiều ghế không còn trống.",
    "details": {
      "seatIds": [
        "…"
      ]
    },
    "requestId": "…"
  }
}
```

| HTTP | Mã lỗi                                                                   | Trường hợp                                                                                                                   |
|------|--------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| 400  | `VALIDATION_ERROR`                                                       | JSON lỗi, thiếu trường, trường ngoài hợp đồng, sai kiểu hoặc sai miền giá trị, ghế trùng/không tồn tại/khác phòng, quá 8 ghế |
| 400  | `BUSINESS_RULE_VIOLATION`                                                | Dữ liệu hợp lệ về hình thức nhưng vi phạm quy tắc nghiệp vụ ở mục 3.2                                                        |
| 401  | `INVALID_CREDENTIALS`, `UNAUTHENTICATED`                                 | Đăng nhập sai; thiếu, sai hoặc hết hạn token                                                                                 |
| 403  | `FORBIDDEN`                                                              | Sai vai trò cho thao tác                                                                                                     |
| 404  | `RESOURCE_NOT_FOUND`                                                     | Không có tài nguyên, hoặc booking không thuộc người gọi                                                                      |
| 405  | `METHOD_NOT_ALLOWED`                                                     | Method không được hỗ trợ trên route đã tồn tại                                                                               |
| 409  | `SEAT_UNAVAILABLE`                                                       | Ghế đang được người khác giữ hoặc đã bán                                                                                     |
| 409  | `BOOKING_EXPIRED`, `INVALID_BOOKING_STATE`, `SHOWTIME_NOT_BOOKABLE`      | Xung đột trạng thái booking hoặc suất chiếu                                                                                  |
| 409  | `HOLD_LIMIT_EXCEEDED`                                                    | Vượt số booking được giữ cùng lúc (`BR-18`)                                                                                  |
| 409  | `EMAIL_ALREADY_USED`, `AUDITORIUM_NAME_ALREADY_USED`, `SHOWTIME_OVERLAP` | Trùng dữ liệu duy nhất hoặc trùng lịch phòng                                                                                 |
| 413  | `PAYLOAD_TOO_LARGE`                                                      | Body vượt 64 KB                                                                                                              |
| 415  | `UNSUPPORTED_MEDIA_TYPE`                                                 | Content-Type không phải `application/json`                                                                                   |
| 500  | `INTERNAL_ERROR`                                                         | Lỗi ngoài dự kiến; không lộ stack trace hoặc SQL                                                                             |
| 503  | `SERVICE_UNAVAILABLE`                                                    | Dịch vụ hoặc DB chưa sẵn sàng                                                                                                |

### 3.2. Quy tắc nghiệp vụ

**Phim**

| Mã    | Quy tắc                                                                                                                                                                                                            |
|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BR-01 | Mỗi phim có tên, thời lượng (1–600 phút), ngày khởi chiếu và đúng một nhãn phân loại: **P** (mọi lứa tuổi), **K** (dưới 13 tuổi xem cùng cha mẹ/người giám hộ), **T13**, **T16**, **T18** (từ đủ 13, 16, 18 tuổi). |
| BR-02 | Phim là "Sắp chiếu" khi ngày khởi chiếu sau ngày hôm nay (theo giờ Việt Nam), ngược lại là "Đang chiếu".                                                                                                           |
| BR-03 | Nhãn phân loại phải được hiển thị ở trang phim và ở bước xác nhận đặt vé. Hệ thống không xác minh tuổi khi bán trực tuyến.                                                                                         |

**Phòng và ghế**

| Mã    | Quy tắc                                                                                                 |
|-------|---------------------------------------------------------------------------------------------------------|
| BR-04 | Mỗi phòng có tên duy nhất và sơ đồ ghế dạng lưới: hàng ký hiệu A–Z. Ghế được đánh số A1, A2… theo lưới. |
| BR-05 | Ghế có hai loại: **Thường** và **VIP**, khai báo theo hàng.                                             |

**Lịch chiếu**

| Mã    | Quy tắc                                                                                                                                            |
|-------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| BR-06 | Giờ kết thúc suất chiếu = giờ bắt đầu + thời lượng phim, do hệ thống tính.                                                                         |
| BR-07 | Hai suất chiếu trong cùng phòng phải cách nhau ít nhất **15 phút** để dọn phòng: suất sau bắt đầu không sớm hơn giờ kết thúc suất trước + 15 phút. |
| BR-08 | Không xếp suất chiếu có giờ bắt đầu trong quá khứ, hoặc trước ngày khởi chiếu của phim.                                                            |
| BR-09 | Ngày của một suất chiếu là ngày của giờ bắt đầu theo giờ Việt Nam (`Asia/Ho_Chi_Minh`), kể cả khi suất kết thúc sau nửa đêm.                       |

**Giá vé**

| Mã    | Quy tắc                                                                                                                                                                                         |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BR-10 | Mỗi suất chiếu có một giá vé ghế Thường, là bội số của 1.000 đ và lớn hơn 0. Giá ghế VIP = giá ghế Thường × 130%, làm tròn xuống tới 1.000 đ. Ví dụ: 90.000 đ → 117.000 đ; 75.000 đ → 97.000 đ. |
| BR-11 | Giá của từng ghế được chốt tại thời điểm giữ ghế. Đổi giá suất chiếu sau đó chỉ áp dụng cho các lần giữ ghế mới.                                                                                |
| BR-12 | Tiền tệ duy nhất là VND, số nguyên. Tổng tiền booking = tổng giá các ghế; khách hàng không tự đặt giá.                                                                                          |

**Đặt vé**

| Mã    | Quy tắc                                                                                                                                                                                                |
|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BR-13 | Chỉ tài khoản khách hàng đã đăng nhập mới được đặt vé, và chỉ đặt cho chính mình. Quản trị viên không đặt vé.                                                                                          |
| BR-14 | Mỗi booking gồm **1–8 ghế** khác nhau, thuộc cùng một suất chiếu. Muốn nhiều hơn 8 ghế thì tạo booking khác.                                                                                           |
| BR-15 | Mỗi ghế trong một suất chiếu chỉ có tối đa **một** chủ tại một thời điểm: một booking đang giữ còn hạn hoặc một booking đã xác nhận. Cùng ghế đó ở suất chiếu khác là độc lập.                         |
| BR-16 | Giữ ghế theo nguyên tắc **tất cả hoặc không**: nếu một ghế không giữ được thì không ghế nào được giữ.                                                                                                  |
| BR-17 | Ghế được giữ trong **5 phút** kể từ khi giữ, nhưng không quá giờ bắt đầu suất chiếu. Hết thời hạn mà chưa xác nhận thì booking hết hạn và ghế tự trả lại.                                              |
| BR-18 | Mỗi khách hàng được có tối đa **2** booking đang giữ trên cùng một suất chiếu và tối đa **5** booking đang giữ trên toàn hệ thống.                                                                     |
| BR-19 | Chỉ bán vé cho suất chiếu đang mở bán và chưa bắt đầu. Quản trị viên có thể tạm ngừng bán một suất; vé đã bán vẫn có hiệu lực.                                                                         |
| BR-20 | Xác nhận (thanh toán mô phỏng) chỉ thành công khi booking còn hạn giữ. Khi thành công, khách nhận **mã đặt vé** gồm 8 ký tự chữ in hoa và chữ số, duy nhất, không đoán được, dùng để nhận vé tại quầy. |
| BR-21 | Vé đã xác nhận **không đổi, không hủy, không hoàn tiền**. Booking đang giữ thì khách hủy được bất kỳ lúc nào; ghế trả lại ngay.                                                                        |
| BR-22 | Khách hàng chỉ thấy và thao tác được booking của chính mình; booking của người khác được coi như không tồn tại.                                                                                        |
| BR-23 | Trạng thái booking chỉ đi một chiều: Đang giữ → Đã xác nhận, Đã hủy hoặc Hết hạn. Không có chuyển trạng thái nào khác.                                                                                 |

**Tài khoản**

| Mã    | Quy tắc                                                                                                                            |
|-------|------------------------------------------------------------------------------------------------------------------------------------|
| BR-24 | Mỗi email chỉ đăng ký được một tài khoản, không phân biệt chữ hoa thường và khoảng trắng đầu cuối. Mật khẩu tối thiểu **8** ký tự. |
| BR-25 | Tài khoản tự đăng ký luôn là khách hàng. Quyền quản trị chỉ có từ lúc khởi tạo hệ thống hoặc do một quản trị viên khác cấp.        |
| BR-26 | Quản trị viên không được tự hạ quyền hoặc tự xóa tài khoản của chính mình.                                                         |

**Bảo toàn dữ liệu đã bán**

| Mã    | Quy tắc                                                                                                                                  |
|-------|------------------------------------------------------------------------------------------------------------------------------------------|
| BR-27 | Phim đã có suất chiếu thì không được xóa và không được đổi thời lượng; các thông tin khác vẫn sửa được.                                  |
| BR-28 | Phòng đã có suất chiếu thì không được sửa. Không xóa phòng.                                                                              |
| BR-29 | Suất chiếu đã có booking thì không được xóa và không được đổi phim, phòng hoặc giờ chiếu; chỉ được đổi giá (theo BR-11) và mở/ngừng bán. |
| BR-30 | Người dùng đã có booking thì không được xóa. Booking là lịch sử, không bao giờ bị xóa.                                                   |

### 3.3. Danh sách yêu cầu chức năng

| Mã    | Tên                     | Ưu tiên | Tác nhân       |
|-------|-------------------------|---------|----------------|
| FR-01 | Đăng nhập               | Must    | Mọi tài khoản  |
| FR-02 | Xem phim                | Must    | Mọi người dùng |
| FR-03 | Xem suất chiếu          | Must    | Mọi người dùng |
| FR-04 | Xem sơ đồ ghế           | Must    | Mọi người dùng |
| FR-05 | Giữ ghế                 | Must    | Khách hàng     |
| FR-06 | Xác nhận đặt vé         | Must    | Khách hàng     |
| FR-07 | Hủy chỗ đang giữ        | Must    | Khách hàng     |
| FR-08 | Xử lý hết hạn giữ ghế   | Must    | Hệ thống       |
| FR-09 | Xem vé của tôi          | Must    | Khách hàng     |
| FR-10 | Đăng ký tài khoản       | Should  | Khách          |
| FR-11 | Xem thông tin tài khoản | Should  | Mọi tài khoản  |
| FR-12 | Quản lý phim            | Must    | Quản trị viên  |
| FR-13 | Quản lý phòng chiếu     | Must    | Quản trị viên  |
| FR-14 | Quản lý suất chiếu      | Must    | Quản trị viên  |
| FR-15 | Quản lý người dùng      | Must    | Quản trị viên  |
| FR-16 | Tra cứu booking         | Should  | Quản trị viên  |
| FR-17 | Giao diện web           | Must    | Mọi người dùng |

### 3.4. Xác thực và tài khoản

**FR-01 — Đăng nhập** · `POST /auth/login`

- Nhận email và mật khẩu; trả `accessToken`, `tokenType = "Bearer"`, `expiresIn` (giây).
- Email được chuẩn hóa (bỏ khoảng trắng đầu cuối, chữ thường) trước khi so khớp; mật khẩu giữ nguyên.
- Sai email hoặc sai mật khẩu trả **cùng** thông báo và tốn thời gian xử lý tương đương, để không lộ tài khoản có tồn
  tại hay không.
- Token chứa ID người dùng, vai trò, thời điểm cấp và hết hạn; không chứa dữ liệu cá nhân khác. Yêu cầu bảo mật ở
  `NFR-08`.

**FR-10 — Đăng ký tài khoản** · `POST /auth/register`

- Nhận `email`, `password`, `fullName`; trả `201` với thông tin tài khoản, không kèm mật khẩu.
- Áp dụng `BR-24`, `BR-25`.

**FR-11 — Xem thông tin tài khoản** · `GET /auth/me`

### 3.5. Danh mục và lịch chiếu

**FR-02 — Xem phim** · `GET /movies`, `GET /movies/{movieId}`

- Không cần đăng nhập. Danh sách có phân trang, tìm theo một phần tên phim (không phân biệt hoa thường, tối đa 100 ký
  tự) và lọc theo `status` = `NOW_SHOWING` hoặc `COMING_SOON` (`BR-02`).
- Mỗi phim gồm: `id`, `title`, `description`, `durationMinutes`, `genre`, `ageRating`, `releaseDate`, `status`.

**FR-03 — Xem suất chiếu** · `GET /showtimes`, `GET /showtimes/{showtimeId}`

- Không cần đăng nhập. Danh sách có phân trang; lọc tùy chọn theo `movieId` và `date` (`YYYY-MM-DD`, theo `BR-09`).
- Mỗi suất gồm: mã suất, phim, phòng, `startsAt`, `endsAt`, `basePrice`, `currency`, `isOpenForBooking`, và `bookable`
  cho biết hiện có đặt được không (`BR-19`).

**FR-04 — Xem sơ đồ ghế** · `GET /showtimes/{showtimeId}/seats`

- Không cần đăng nhập. Trả **toàn bộ** ghế của phòng (không phân trang) với hàng, số, loại ghế, giá ghế (`BR-10`) và
  trạng thái `AVAILABLE`, `HELD` hoặc `BOOKED`.
- Không tiết lộ ai đang giữ hoặc đã mua ghế.
- Sơ đồ chỉ phản ánh thời điểm đọc; ghế đang trống không bảo đảm lần giữ ghế tiếp theo thành công.

### 3.6. Đặt vé

**FR-05 — Giữ ghế** · `POST /bookings`

- Nhận `showtimeId` và `seatIds`. Áp dụng `BR-13` … `BR-19`.
- Thành công trả `201` kèm header `Location`; booking ở trạng thái `HELD` với `createdAt`, `expiresAt`, đơn giá từng ghế
  và `totalAmount`.
- Client không được chỉ định chủ booking, trạng thái, giá, tổng tiền hay thời hạn giữ.
- `POST /bookings` không idempotent: client không tự động gửi lại khi chưa biết kết quả mà phải xem lại danh sách vé.

**FR-06 — Xác nhận đặt vé** · `POST /bookings/{bookingId}/confirm`

- Không có body. Áp dụng `BR-20`. Đây là xác nhận mô phỏng; không được mô tả là "thanh toán thành công" ở API, giao diện
  hay README.
- Thứ tự kiểm tra: quyền sở hữu → trạng thái → thời hạn → suất chiếu còn bán. Booking đã `CONFIRMED` trả lại kết quả cũ
  trước mọi kiểm tra còn lại.

**FR-07 — Hủy chỗ đang giữ** · `DELETE /bookings/{bookingId}`

- Áp dụng `BR-21`. Hủy là đổi trạng thái, không xóa booking.

**FR-08 — Xử lý hết hạn giữ ghế**

- Booking `HELD` có trạng thái hiệu lực `EXPIRED` khi thời điểm hiện tại ≥ `expiresAt` (`BR-17`).
- Mọi thao tác xem, giữ, xác nhận, hủy đều xét thời hạn thực tế, không chỉ dựa vào trạng thái đang lưu. Không bắt buộc
  tác vụ nền; tính đúng đắn không phụ thuộc vào việc có tác vụ dọn hay không.

**FR-09 — Xem vé của tôi** · `GET /me/bookings`, `GET /bookings/{bookingId}`

- Danh sách có phân trang, mới nhất trước; lọc tùy chọn theo đúng một `status` trong `HELD`, `CONFIRMED`, `CANCELLED`,
  `EXPIRED`, áp dụng trên **trạng thái hiệu lực**.
- Lọc, sắp xếp, phân trang và `totalItems` phải nhất quán với nhau (giải quyết trong cùng một truy vấn).
- Chi tiết gồm phim (kèm nhãn phân loại), suất chiếu, phòng, ghế, đơn giá, tổng tiền, trạng thái, mã đặt vé và các mốc
  thời gian.

### 3.7. Quản trị

Mọi FR trong mục này chỉ dành cho quản trị viên: khách chưa đăng nhập nhận `401`, khách hàng nhận `403`, dữ liệu không
đổi.

**FR-12 — Quản lý phim** · `/admin/movies`

- Liệt kê có tìm kiếm và phân trang; tạo, sửa, xóa phim. Áp dụng `BR-01`, `BR-27`.

**FR-13 — Quản lý phòng chiếu** · `/admin/auditoriums`

- Liệt kê, xem chi tiết, tạo và sửa phòng; không có thao tác xóa. Phòng khai báo số hàng, số ghế mỗi hàng và các hàng
  VIP; hệ thống tự sinh ghế. Áp dụng `BR-04`, `BR-05`, `BR-28`.

**FR-14 — Quản lý suất chiếu** · `/admin/showtimes`

- Tạo, sửa, xóa suất chiếu; mở hoặc ngừng bán. Áp dụng `BR-06` … `BR-11`, `BR-19`, `BR-29`.
- Khi tạo suất, hệ thống tạo sẵn trạng thái `AVAILABLE` cho mọi ghế của phòng trong cùng thao tác.
- Quy tắc cách 15 phút (`BR-07`) phải đúng cả khi hai yêu cầu tạo/sửa trong cùng phòng đến đồng thời.

**FR-15 — Quản lý người dùng** · `/admin/users`

- Liệt kê có tìm theo email/họ tên, lọc theo vai trò, phân trang; xem chi tiết; sửa họ tên và vai trò; xóa. Áp dụng
  `BR-25`, `BR-26`, `BR-30`.
- Đổi vai trò có hiệu lực từ lần đăng nhập kế tiếp của người đó (`AS-04`).

**FR-16 — Tra cứu booking** · `/admin/bookings`

- Liệt kê mọi booking, lọc theo trạng thái hiệu lực, người dùng, suất chiếu, có phân trang; xem chi tiết một booking bất
  kỳ.
- Chỉ đọc: quản trị viên không xác nhận hay hủy booking thay khách hàng.

### 3.8. Giao diện web

**FR-17 — Giao diện web**

- SPA chỉ dùng REST API ở mục 3; không truy cập dữ liệu bằng đường khác.
- Trang cho khách: phim đang chiếu/sắp chiếu, chi tiết phim kèm lịch chiếu, sơ đồ ghế, đăng ký/đăng nhập, danh sách vé,
  chi tiết vé.
- Trang quản trị chỉ dành cho quản trị viên: quản lý phim, phòng, suất chiếu.
- Toàn bộ văn bản tiếng Việt; tiền hiển thị dạng `117.000 đ`; giờ hiển thị theo giờ Việt Nam.
- Có thể được backend phục vụ chung cổng với API.

---

## 4. Yêu cầu phi chức năng

| Mã     | Nhóm              | Yêu cầu                              | Chỉ số và ngưỡng                                                                                                                                                       | Kiểm chứng                                                    |
|--------|-------------------|--------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| NFR-01 | Tính đúng đắn     | Đúng dưới tải đồng thời              | Ghế có hai chủ, inventory lệch booking, ghi một phần: **= 0** ở mọi mức đồng thời đo (1–100)                                                                           | T-07, T-08, T-15, T-16, T-17; kiểm tra dữ liệu sau mỗi lần đo |
| NFR-02 | Độ tin cậy        | Ngân sách lỗi                        | `5xx` + timeout **< 1%** tổng request ở L-01, L-02, L-03, L-05, L-06                                                                                                   | Kết quả k6                                                    |
| NFR-03 | Hiệu năng         | Độ trễ và thông lượng                | Thu p50/p95/p99 theo endpoint và kịch bản; Pha 2 đạt mục tiêu chính chốt sau pilot (mặc định p95 **giảm ≥ 20%** hoặc throughput hữu ích **tăng ≥ 20%** ở cùng mức tải) | Mục 6.2.5, 6.2.6                                              |
| NFR-04 | Sẵn sàng          | Khởi động                            | Từ container khởi động tới `/health/ready` = 200: **≤ 120 giây** (không tính build và seed)                                                                            | Smoke test                                                    |
| NFR-05 | Bảo vệ đầu vào    | Giới hạn request                     | Body **≤ 64 KB** (vượt: 413); sai Content-Type: 415; sai method: 405; `pageSize ≤ 100`; chuỗi văn bản có độ dài tối đa                                                 | T-05, T-26                                                    |
| NFR-06 | Khả năng quan sát | Log có thể truy vết                  | **1** dòng log/request; `requestId` trong body lỗi trùng `requestId` trong log                                                                                         | Smoke test                                                    |
| NFR-07 | Tái lập           | Dữ liệu và số liệu tái lập được      | Cùng commit + seed + cấu hình → cùng dữ liệu; mọi số liệu gắn commit SHA                                                                                               | Mục 6.2.2, 5.2                                                |
| NFR-08 | Bảo mật           | Xác thực và bảo vệ dữ liệu           | bcrypt cost **≥ 12**; khóa HS256 **≥ 32 byte**; token hết hạn sau **3600 giây**; dung sai đồng hồ **≤ 60 giây**; **0** secret thật trong lịch sử Git                   | T-01, T-02, T-13, T-23, T-30, T-31                            |
| NFR-09 | Khả năng mở rộng  | Mở rộng ngang trên một DB            | Backend stateless; số worker tăng bằng cấu hình, không sửa mã; `WEB_WORKERS × (DB_POOL_SIZE + 10) < max_connections` của PostgreSQL                                    | Mục 4.2                                                       |
| NFR-10 | Khả năng bảo trì  | Ranh giới kiến trúc và chất lượng mã | **0** vi phạm import-linter, mypy strict, ruff; CI xanh cho mọi PR; mỗi tiêu chí `AC-xx.y` có kiểm thử tự động hoặc bước kiểm tra thủ công được ghi lại                | T-27                                                          |

---

## 5. Ràng buộc, giả định, phụ thuộc và rủi ro

### 5.1. Ràng buộc kỹ thuật

| Mã     | Ràng buộc                                                                                                                                                                                                                                                                                      |
|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CON-01 | Stack: Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL 16, PyJWT, bcrypt; React 19 + TypeScript + Vite cho frontend. Giữ cùng loại và phiên bản DB trong hai pha đo.                                                                                                         |
| CON-02 | Kiến trúc monolith phân tầng (modular monolith): API → Domain service → cổng Repository/Unit of Work ← Infrastructure. Tầng nghiệp vụ không import framework web, thư viện DB hay ORM; API không truy vấn DB trực tiếp.                                                                        |
| CON-03 | Truy cập dữ liệu qua ORM/data mapper; schema quản lý bằng migration có phiên bản.                                                                                                                                                                                                              |
| CON-04 | Giữ ghế, xác nhận và hủy đều nguyên tử: một transaction bao trùm toàn bộ thao tác; lỗi giữa chừng thì rollback toàn bộ.                                                                                                                                                                        |
| CON-05 | Chống bán trùng ghế phải được bảo vệ ở DB, không chỉ "đọc rồi ghi": inventory của mọi ghế được tạo sẵn khi tạo suất chiếu; giữ ghế là một câu lệnh cập nhật có điều kiện, số dòng bị ảnh hưởng quyết định thành công. Thao tác của booking cũ không được giải phóng ghế đã thuộc booking khác. |
| CON-06 | Một nguồn thời gian duy nhất cho mọi quyết định về hạn giữ và mốc thời gian booking: đồng hồ PostgreSQL, lấy trong cùng transaction. Thời gian lưu ở UTC. Tầng nghiệp vụ truy cập thời gian qua cổng `Clock` để unit test kiểm tra được biên hết hạn.                                          |
| CON-07 | Cache, nếu có, không phải nguồn quyết định cấp ghế; DB là nguồn quyết định.                                                                                                                                                                                                                    |
| CON-08 | Đóng gói bằng Dockerfile và Docker Compose (backend + DB); cấu hình qua biến môi trường: DB URL, khóa và thuật toán JWT, thời hạn token, thời hạn giữ ghế, giới hạn giữ ghế (`BR-18`), pool size, số worker, cổng HTTP, múi giờ rạp.                                                           |
| CON-09 | Kiểm thử tải chạy trên Kaggle Notebook CPU, không dùng GPU/TPU; không giả định có Docker daemon, nên phải có script/notebook chạy trực tiếp backend, DB và load generator với cùng phiên bản phần mềm và cấu hình.                                                                             |
| CON-10 | Không tăng phần cứng để tạo ra cải thiện; thành phần bổ sung (Redis, worker nền) được tính vào cùng ngân sách CPU/RAM.                                                                                                                                                                         |

Kiến trúc chi tiết: [architecture.md](./architecture.md). Mô hình dữ liệu: [data-model.md](./data-model.md).

---

## 6. Kiểm chứng và nghiệm thu

### 6.1. Kiểm thử bắt buộc

| Mã   | Kịch bản                                                                                                 | Kết quả kỳ vọng                                                                                      |
|------|----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| T-01 | Đăng nhập đúng/sai                                                                                       | Token hợp lệ hoặc 401; không lộ thông tin nhạy cảm                                                   |
| T-02 | Gọi GET cá nhân và POST booking thiếu/sai/hết hạn token                                                  | 401, không thay đổi dữ liệu                                                                          |
| T-03 | Xem danh mục, phân trang, lọc theo trạng thái phim, theo phim và ngày                                    | Dữ liệu và múi giờ đúng; đầu vào lỗi trả 400                                                         |
| T-04 | Giữ 1 ghế và nhiều ghế hợp lệ                                                                            | 201, đúng hạn giữ, giá và số item                                                                    |
| T-05 | Giữ ghế trùng, rỗng, quá 8 ghế, khác phòng                                                               | 400, không tạo dữ liệu một phần                                                                      |
| T-06 | Một trong nhiều ghế đã bị chiếm                                                                          | 409, các ghế còn lại không bị giữ                                                                    |
| T-07 | ≥ 20 yêu cầu đồng thời tranh một ghế trống; hai biến thể: 20 người dùng khác nhau và cùng một người dùng | Đúng 1 request 201, còn lại 409 `SEAT_UNAVAILABLE`, không có 5xx; inventory trỏ đúng booking thắng   |
| T-08 | Hai yêu cầu đồng thời với nhóm ghế giao nhau (A1/A2 và A2/A3)                                            | Đúng một booking thành công; ghế chỉ thuộc nhóm thua (A3) vẫn trống; không có hold một phần          |
| T-09 | Xác nhận trước hạn và xác nhận lại                                                                       | `CONFIRMED`, mã vé ổn định, không sinh bản ghi trùng                                                 |
| T-10 | Xác nhận đúng thời điểm hết hạn và sau hạn                                                               | 409 `BOOKING_EXPIRED`, không tạo vé                                                                  |
| T-11 | Hủy, hủy lại, giữ lại ghế vừa hủy                                                                        | 204, 204, giữ mới thành công                                                                         |
| T-12 | Hủy vé đã xác nhận                                                                                       | 409, ghế vẫn `BOOKED`                                                                                |
| T-13 | Đọc/xác nhận/hủy booking của người khác                                                                  | 404, không thay đổi dữ liệu                                                                          |
| T-14 | Hold hết hạn khi không có tác vụ nền                                                                     | Xem trả trạng thái hiệu lực đúng; người khác giữ lại được                                            |
| T-15 | Xác nhận đồng thời với hủy                                                                               | Chỉ một chuyển trạng thái thắng; inventory khớp booking cuối                                         |
| T-16 | Xác nhận, hết hạn và giữ mới cạnh tranh                                                                  | Không ghi đè hoặc giải phóng ghế đã thuộc booking mới (`BR-15`, `CON-05`)                            |
| T-17 | Lỗi giữa thao tác ghi nhiều bảng                                                                         | Rollback; không có booking hoặc ghế bị ghi một phần (`CON-04`)                                       |
| T-18 | Suất đã bắt đầu hoặc ngừng bán                                                                           | Không giữ/xác nhận mới; xác nhận lặp vé đã thành công vẫn trả kết quả cũ                             |
| T-19 | Khởi động lại backend                                                                                    | Booking đã commit còn nguyên; hạn giữ không bị kéo dài                                               |
| T-20 | Đặt cùng ghế vật lý ở hai suất khác nhau                                                                 | Cả hai thành công (`BR-15`)                                                                          |
| T-21 | Đọc lại booking vừa tạo, gồm ghế VIP                                                                     | Thời gian ISO 8601 có múi giờ; currency VND; giá VIP đúng `BR-10`; tổng bằng tổng item (`BR-12`)     |
| T-22 | Vượt giới hạn giữ trên một suất và toàn hệ thống                                                         | 409 `HOLD_LIMIT_EXCEEDED`; hủy một booking thì giữ được (`BR-18`)                                    |
| T-23 | Token bị sửa, khác khóa, `alg: none`, thiếu thông tin, quá hạn trong và ngoài dung sai                   | 401 cho mọi trường hợp trừ quá hạn trong dung sai; không thay đổi dữ liệu                            |
| T-24 | `GET /me/bookings` với status hợp lệ, sai, nhiều giá trị, bỏ trống; trang vượt quá                       | Lọc theo trạng thái hiệu lực đúng; status sai trả 400; `totalItems` đúng; trang vượt trả 200 rỗng    |
| T-25 | Nhiều yêu cầu đồng thời giữ ghế của suất chưa từng có giao dịch                                          | Như T-07; không có 500 do vi phạm unique                                                             |
| T-26 | Content-Type sai, body > 64 KB, method sai, trường ngoài hợp đồng, query lạ trên sơ đồ ghế               | Lần lượt 415, 413, 405, 400, 400; không tạo dữ liệu                                                  |
| T-27 | Kiểm thử phụ thuộc kiến trúc trong CI                                                                    | Build fail khi tầng nghiệp vụ import framework web hoặc thư viện DB/ORM, hoặc API import persistence |
| T-28 | Sơ đồ ghế của phòng 100 ghế                                                                              | Đủ 100 ghế trong một response, đúng thứ tự, không phân trang                                         |
| T-29 | Chỉ cho phiên bản Pha 2 có cache: đọc sơ đồ cũ rồi giữ ghế đã bị chiếm                                   | Quyết định cấp ghế dựa trên DB (`CON-07`)                                                            |
| T-30 | Đăng ký: hợp lệ, email trùng khác hoa thường, mật khẩu ngắn, gửi kèm vai trò                             | 201, 409, 400, 400; tài khoản mới là `CUSTOMER`                                                      |
| T-31 | Khách và khách hàng gọi mọi endpoint `/admin/`                                                           | 401 cho khách, 403 cho khách hàng; không thay đổi dữ liệu                                            |
| T-32 | Quản trị phim theo AC-12.x                                                                               | Như các AC                                                                                           |
| T-33 | Quản trị phòng theo AC-13.x                                                                              | Như các AC                                                                                           |
| T-34 | Quản trị suất chiếu theo AC-14.x, gồm tạo đồng thời hai suất chồng giờ                                   | Như các AC; chỉ một suất chồng giờ được tạo                                                          |
| T-35 | Quản trị người dùng theo AC-15.x                                                                         | Như các AC                                                                                           |
| T-36 | Tra cứu booking theo AC-16.x                                                                             | Như các AC                                                                                           |

Chi tiết ca kiểm thử: [test-plan.md](./test-plan.md).

### 6.2. Kiểm thử tải trên Kaggle CPU

Quy trình thực hiện chi tiết: [benchmark-plan.md](./benchmark-plan.md).

### 6.3. Pha 2 — cải tiến kiến trúc

**Phương pháp**

1. Phân tích baseline để xác định điểm nghẽn thực tế.
2. Viết giả thuyết: thay đổi gì, tác động chỉ số nào, vì sao, đánh đổi gì.
3. Chọn ít nhất một cải tiến kiến trúc có phạm vi rõ.
4. Ghi ADR kèm sơ đồ trước/sau và cách giữ tính đúng đắn.
5. Đo trên cùng kịch bản, dữ liệu và phần cứng; nếu kết hợp nhiều thay đổi thì đo từng thay đổi khi khả thi.

**Hướng ứng viên**

| Hướng                                       | Khi nào xem xét                                 | Đánh đổi                                                 |
|---------------------------------------------|-------------------------------------------------|----------------------------------------------------------|
| Cache-aside cho phim/suất chiếu             | Truy vấn đọc lặp lại chiếm tài nguyên đáng kể   | TTL, vô hiệu hóa, RAM, xử lý khi cache lỗi               |
| Cache sơ đồ ghế, tách dữ liệu tĩnh/động     | L-02 là điểm nghẽn                              | Ghế hiển thị có thể cũ; ghi vẫn kiểm tra DB; fallback DB |
| Điều chỉnh chiến lược đồng thời/transaction | Chờ khóa hoặc transaction dài hạn chế L-03/L-04 | Retry có giới hạn, deadlock, starvation                  |
| Worker thu hồi hold hết hạn                 | Thu hồi trong request làm tăng độ trễ           | Thêm thành phần vận hành; job idempotent                 |
| Tối ưu đường đọc và truy vấn                | N+1 hoặc query plan kém                         | Chi phí index/ghi; phân biệt với thay đổi kiến trúc      |

- Phiên bản có cache phải chạy thêm T-29.
- Không cố tình bỏ constraint hoặc viết baseline sai để tạo cải thiện. Chỉ thêm index có thể chưa đủ được coi là cải
  tiến kiến trúc.
- Theo dõi hồi quy ở các kịch bản khác; nếu không đạt mục tiêu thì báo cáo trung thực kết quả, nguyên nhân và giới hạn.

### 6.4. Tiêu chí nghiệm thu

**Pha 1**

1. Mọi tiêu chí `AC-01.1` … `AC-17.6` ở mục 3 đạt; mọi quy tắc `BR-01` … `BR-30` được tuân thủ.
2. Toàn bộ kiểm thử bắt buộc ở mục 6.1 đạt trong CI; NFR-01 ghi nhận 0 vi phạm.
3. REST API JSON có GET, POST, PUT, DELETE và tài liệu OpenAPI/Swagger khớp hành vi thực tế; Swagger UI cho nhập token
   và thử endpoint được bảo vệ.
4. Mọi endpoint cần đăng nhập được bảo vệ bởi cùng một cơ chế xác thực tập trung.
5. Phân tầng đúng `CON-02`; T-27 chạy trong CI.
6. Build và chạy được bằng Docker theo README trên môi trường sạch; đạt NFR-04.
7. Có kết quả baseline thực sự chạy trên Kaggle CPU kèm dữ liệu thô và metadata môi trường; NFR-02 đạt.
8. README đủ các mục ở 5.2; repository công khai; có commit ở các mốc M1–M4; không chứa secret.

**Pha 2**

1. Có vấn đề và số liệu baseline làm căn cứ; có ADR mô tả trước/sau, giả thuyết và đánh đổi.
2. Có ít nhất một cải tiến được triển khai và kiểm thử; mọi tiêu chí Pha 1 vẫn đạt; NFR-01 = 0 vi phạm ở mọi mức tải đã
   đo.
3. So sánh trên cùng cấu hình Kaggle CPU, cùng tải, dữ liệu và ngân sách tài nguyên.
4. Có kết quả thô, bảng/biểu đồ so sánh và hướng dẫn tái lập.
5. Kết luận nêu rõ cải thiện, hồi quy hoặc không đạt, kèm cả số tuyệt đối lẫn phần trăm.

---

## 7. Phụ lục

### 7.A. Danh sách endpoint

Đường dẫn ghép với `/api/v1`, trừ health. Đặc tả đầy đủ: [openapi.yaml](./openapi.yaml) hoặc `/docs` khi chạy ứng dụng.

| Method           | Endpoint                                                      | Xác thực      | Thành công                  | FR     |
|------------------|---------------------------------------------------------------|---------------|-----------------------------|--------|
| GET              | `/health/live`, `/health/ready`                               | Không         | 200 (503 khi chưa sẵn sàng) | NFR-04 |
| POST             | `/auth/register`                                              | Không         | 201                         | FR-10  |
| POST             | `/auth/login`                                                 | Không         | 200                         | FR-01  |
| GET              | `/auth/me`                                                    | Có            | 200                         | FR-11  |
| GET              | `/movies?q=&status=&page=&pageSize=`                          | Không         | 200                         | FR-02  |
| GET              | `/movies/{movieId}`                                           | Không         | 200                         | FR-02  |
| GET              | `/showtimes?movieId=&date=&page=&pageSize=`                   | Không         | 200                         | FR-03  |
| GET              | `/showtimes/{showtimeId}`                                     | Không         | 200                         | FR-03  |
| GET              | `/showtimes/{showtimeId}/seats`                               | Không         | 200                         | FR-04  |
| POST             | `/bookings`                                                   | Khách hàng    | 201 + `Location`            | FR-05  |
| GET              | `/me/bookings?status=&page=&pageSize=`                        | Khách hàng    | 200                         | FR-09  |
| GET              | `/bookings/{bookingId}`                                       | Chủ booking   | 200                         | FR-09  |
| POST             | `/bookings/{bookingId}/confirm`                               | Chủ booking   | 200                         | FR-06  |
| DELETE           | `/bookings/{bookingId}`                                       | Chủ booking   | 204                         | FR-07  |
| GET, POST        | `/admin/movies`                                               | Quản trị viên | 200, 201                    | FR-12  |
| PUT, DELETE      | `/admin/movies/{movieId}`                                     | Quản trị viên | 200, 204                    | FR-12  |
| GET, POST        | `/admin/auditoriums`                                          | Quản trị viên | 200, 201                    | FR-13  |
| GET, PUT         | `/admin/auditoriums/{auditoriumId}`                           | Quản trị viên | 200                         | FR-13  |
| POST             | `/admin/showtimes`                                            | Quản trị viên | 201                         | FR-14  |
| PUT, DELETE      | `/admin/showtimes/{showtimeId}`                               | Quản trị viên | 200, 204                    | FR-14  |
| GET              | `/admin/users?q=&role=&page=&pageSize=`                       | Quản trị viên | 200                         | FR-15  |
| GET, PUT, DELETE | `/admin/users/{userId}`                                       | Quản trị viên | 200, 204                    | FR-15  |
| GET              | `/admin/bookings?status=&userId=&showtimeId=&page=&pageSize=` | Quản trị viên | 200                         | FR-16  |
| GET              | `/admin/bookings/{bookingId}`                                 | Quản trị viên | 200                         | FR-16  |
