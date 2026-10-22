# Checklist chung của dự án

Checklist này là nơi cả nhóm đánh dấu tiến độ triển khai hệ thống đặt vé xem phim.

## Quy ước

- [ ] Chưa bắt đầu hoặc chưa hoàn thành.
- [x] Đã hoàn thành và được kiểm tra.
- Người phụ trách: `N1` — Backend & dữ liệu, `N2` — Frontend & UX/UI, `N3` — QA & DevOps, `ALL` — cả nhóm.
- Chỉ đánh dấu hoàn thành khi mã nguồn, kiểm thử và tài liệu liên quan đều đã cập nhật.
- Với công việc cần review, ghi đường dẫn pull request hoặc commit bên cạnh mục tương ứng.

## 0. Chốt thiết kế trước khi lập trình

- [x] `ALL` Chốt phạm vi MVP và các chức năng ngoài phạm vi.
- [x] `ALL` Chốt entity: User, Movie, Room, Seat, Showtime, Booking, Ticket.
- [x] `ALL` Chốt enum: Role, SeatType, BookingStatus.
- [x] `ALL` Chốt các quy tắc BR-01 đến BR-12.
- [x] `ALL` Chốt request, response và error code trong API contract.
- [x] `ALL` Chốt múi giờ nghiệp vụ.
- [x] `ALL` Chốt chính sách xóa Movie, Showtime, Booking và Ticket.
- [x] `ALL` Chốt cách lưu lịch sử ghế sau khi hủy booking.
- [x] `ALL` Chốt frontend framework và các thư viện chính.
- [x] `ALL` Chốt Alembic là công cụ migration.
- [x] `ALL` Review toàn bộ tài liệu trong thư mục `docs/`.

**Điều kiện hoàn thành:** ba người có thể giải thích giống nhau về dữ liệu, quyền, endpoint và luồng đặt vé.

---

## 1. Mốc A — Khung dự án

### Repository và quy trình

- [x] `N3` Tạo cấu trúc repository cho backend, frontend, test, deploy và docs.
- [x] `N3` Cấu hình nhánh `main` và quy tắc pull request.
- [x] `N3` Cấu hình Conventional Commits.
- [x] `N3` Tạo file biến môi trường mẫu.
- [x] `N3` Bảo đảm secret không được commit.

### Backend skeleton

- [x] `N1` Tạo cấu trúc tầng `api/business/data/security/bootstrap`.
- [x] `N1` Tạo các module auth, catalog, cinema, scheduling và booking.
- [x] `N1` Tạo cấu hình ứng dụng theo môi trường.
- [x] `N1` Tạo `GET /health`.
- [x] `N1` Tạo error response thống nhất.
- [x] `N1` Tạo request ID middleware.

### Frontend skeleton

- [x] `N2` Khởi tạo SPA TypeScript.
- [x] `N2` Cấu hình router.
- [x] `N2` Tạo app shell và layout cơ bản.
- [x] `N2` Tạo design token ban đầu.
- [x] `N2` Tạo API client cơ bản.
- [x] `N2` Tạo trang lỗi, loading và empty state dùng chung.

### Kiểm tra kiến trúc và CI

- [x] `N3` Cấu hình backend lint/format.
- [x] `N3` Cấu hình frontend lint/type check.
- [x] `N3` Cấu hình `import-linter`.
- [x] `N3` Cấu hình CI chạy lint, test và build.
- [x] `N3` Cấu hình PostgreSQL cho môi trường test.
- [x] `ALL` Xác nhận frontend build được phục vụ bởi FastAPI.

**Nghiệm thu Mốc A**

- [x] `ALL` Ứng dụng monolith khởi động thành công.
- [x] `ALL` `GET /health` trả về `200`.
- [x] `ALL` Trang frontend được mở từ cùng ứng dụng.
- [x] `ALL` CI chạy xanh.
- [x] `ALL` Business layer vượt kiểm tra `import-linter`.

---

## 2. Mốc B — Authentication và Catalog

### Domain và database

- [x] `N1` Tạo User entity và Role enum.
- [x] `N1` Tạo Movie entity.
- [x] `N1` Tạo UserRepository và MovieRepository ports.
- [x] `N1` Tạo ORM models cho users và movies.
- [x] `N1` Tạo migration cho users và movies.
- [x] `N1` Tạo seed tài khoản ADMIN.
- [x] `N1` Tạo seed phim mẫu.

### Authentication backend

- [x] `N1` Implement đăng ký CUSTOMER.
- [x] `N1` Implement đăng nhập.
- [x] `N1` Implement bcrypt PasswordHasher.
- [x] `N1` Implement JWT TokenService.
- [x] `N1` Implement AuthMiddleware mặc định chặn.
- [x] `N1` Implement `POST /auth/register`.
- [x] `N1` Implement `POST /auth/login`.
- [x] `N1` Implement `GET /auth/me`.
- [x] `N1` Cấu hình Bearer security scheme trong OpenAPI.

### Movie backend

- [x] `N1` Implement danh sách phim có tìm kiếm và phân trang.
- [x] `N1` Implement chi tiết phim.
- [x] `N1` Implement ADMIN tạo phim.
- [x] `N1` Implement ADMIN xóa phim.
- [ ] `N1` Áp dụng BR-01, BR-02, BR-03 và phần liên quan của BR-12. — BR-12 (chặn xóa phim đã có vé CONFIRMED) chờ bảng suất chiếu/booking ở Mốc C/D.

### Frontend authentication

- [x] `N2` Tạo trang đăng ký.
- [x] `N2` Tạo trang đăng nhập.
- [x] `N2` Tạo auth state.
- [x] `N2` Lưu JWT theo phương án đã thống nhất.
- [x] `N2` Gọi `/auth/me` khi khởi động ứng dụng.
- [x] `N2` Xử lý JWT sai hoặc hết hạn.
- [x] `N2` Tạo route guard cho CUSTOMER và ADMIN.

### Frontend catalog

- [x] `N2` Tạo trang danh sách phim.
- [x] `N2` Tạo tìm kiếm và phân trang.
- [x] `N2` Tạo trang chi tiết phim.
- [x] `N2` Tạo trang ADMIN quản lý phim.
- [x] `N2` Tạo form thêm phim.
- [x] `N2` Tạo confirm dialog khi xóa phim.

### Kiểm thử

- [x] `N1` Unit test email trùng và mật khẩu không hợp lệ.
- [x] `N1` API test đăng ký, đăng nhập và `/auth/me`.
- [x] `N1` API test CUSTOMER không gọi được API ADMIN.
- [ ] `N2` Test form đăng ký và đăng nhập.
- [ ] `N2` Test route guard.
- [ ] `N3` E2E đăng ký → đăng nhập → xem phim.
- [x] `N3` Security test token thiếu, sai và hết hạn.

**Nghiệm thu Mốc B**

- [ ] `ALL` CUSTOMER đăng ký và đăng nhập thành công.
- [ ] `ALL` ADMIN tạo được phim.
- [ ] `ALL` CUSTOMER không truy cập được chức năng ADMIN.
- [ ] `ALL` Khách chưa đăng nhập xem được danh sách và chi tiết phim.
- [ ] `ALL` Swagger Authorize hoạt động.

---

## 3. Mốc C — Phòng chiếu, ghế và suất chiếu

### Domain và database

- [x] `N1` Tạo Room và Seat entities.
- [x] `N1` Tạo Showtime entity.
- [x] `N1` Tạo SeatType enum.
- [x] `N1` Tạo repository ports tương ứng.
- [x] `N1` Tạo ORM models cho rooms, seats và showtimes.
- [x] `N1` Tạo migration và index.
- [x] `N1` Tạo ràng buộc chống trùng ghế trong một phòng.
- [x] `N1` Tạo cơ chế chống trùng lịch chiếu ở production.

### Room backend

- [x] `N1` Implement ADMIN tạo phòng.
- [x] `N1` Sinh ghế theo số hàng và số cột.
- [x] `N1` Gán đúng hàng VIP.
- [x] `N1` Implement danh sách phòng.
- [ ] `N1` Implement ADMIN cập nhật phòng và sơ đồ ghế khi phòng chưa có suất chiếu.
- [x] `N1` Bảo đảm tạo phòng và ghế trong một transaction.

### Showtime backend

- [x] `N1` Implement danh sách suất chiếu.
- [x] `N1` Implement lọc theo phim và ngày.
- [x] `N1` Implement ADMIN tạo suất chiếu.
- [x] `N1` Tự tính `endsAt` từ thời lượng phim.
- [x] `N1` Implement kiểm tra trùng lịch BR-04.
- [x] `N1` Implement ADMIN xóa suất chiếu.
- [x] `N1` Implement API sơ đồ ghế. — trạng thái BOOKED có khi làm booking ở Mốc D.
- [x] `N1` Tính đúng giá STANDARD và VIP.

### Frontend room và showtime

- [x] `N2` Tạo trang ADMIN danh sách phòng.
- [x] `N2` Tạo form tạo phòng.
- [x] `N2` Tạo preview sơ đồ ghế.
- [ ] `N2` Tạo form chỉnh sửa phòng và sơ đồ ghế.
- [x] `N2` Tạo trang ADMIN quản lý suất chiếu.
- [x] `N2` Tạo form tạo suất chiếu.
- [x] `N2` Hiển thị giờ kết thúc dự kiến.
- [x] `N2` Hiển thị lỗi trùng lịch.
- [x] `N2` Hiển thị suất chiếu trên trang chi tiết phim.

### Kiểm thử

- [x] `N1` Unit test sinh nhãn ghế.
- [x] `N1` Unit test hàng VIP.
- [x] `N1` Unit test showtime overlap.
- [x] `N1` Test hai suất liền nhau không bị coi là trùng.
- [x] `N1` API test quyền ADMIN.
- [ ] `N2` Test form phòng và suất chiếu.
- [ ] `N3` E2E ADMIN tạo phòng và suất chiếu.
- [x] `N3` Test đồng thời khi tạo lịch chiếu cùng phòng.

**Nghiệm thu Mốc C**

- [ ] `ALL` Phòng được tạo với đúng số ghế.
- [ ] `ALL` Ghế VIP có giá đúng.
- [ ] `ALL` Không thể tạo hai suất chiếu trùng phòng và thời gian.
- [ ] `ALL` Khách xem được lịch chiếu và sơ đồ ghế.

---

## 4. Mốc D — Đặt vé

### Domain và database

- [x] `N1` Tạo Booking và BookingItem entities theo mô hình dữ liệu đã chốt.
- [x] `N1` Tạo BookingStatus enum.
- [x] `N1` Tạo BookingRepository port.
- [x] `N1` Tạo ORM models cho bookings, booking items và inventory ghế.
- [x] `N1` Tạo migration.
- [x] `N1` Tạo khóa chính `(showtime_id, seat_id)` cho inventory ghế.
- [x] `N1` Lưu bất biến lịch sử booking item sau khi hủy.

### Booking backend

- [x] `N1` Implement CreateBooking.
- [x] `N1` Kiểm tra mỗi booking có 1–8 ghế.
- [x] `N1` Kiểm tra seat ID không trùng.
- [x] `N1` Kiểm tra ghế thuộc đúng phòng.
- [x] `N1` Kiểm tra suất chiếu chưa bắt đầu.
- [x] `N1` Kiểm tra ghế còn trống.
- [x] `N1` Tính giá từng vé và tổng tiền.
- [x] `N1` Flush booking và booking items trước khi commit transaction.
- [x] `N1` Map tranh chấp inventory thành `SEAT_UNAVAILABLE`.
- [x] `N1` Implement danh sách booking của tôi.
- [x] `N1` Implement chi tiết booking.
- [x] `N1` Implement hủy booking.
- [x] `N1` Chỉ cho chủ booking tra cứu, xác nhận và hủy theo requirements.md.
- [x] `N1` Áp dụng BR-01 đến BR-14 liên quan đến booking theo requirements.md hiện hành.

### Frontend chọn ghế

- [x] `N2` Tạo SeatMap.
- [x] `N2` Hiển thị STANDARD, VIP, BOOKED và SELECTED.
- [x] `N2` Không cho chọn ghế BOOKED.
- [x] `N2` Giới hạn tối đa 8 ghế.
- [x] `N2` Hiển thị giá từng ghế.
- [x] `N2` Hiển thị tổng giá dự kiến.
- [x] `N2` Tạo BookingSummary.
- [x] `N2` Gửi yêu cầu đặt vé.
- [x] `N2` Dùng tổng tiền từ server làm kết quả chính thức.
- [x] `N2` Xử lý `409 SEAT_UNAVAILABLE`.
- [x] `N2` Refresh seat map và bỏ chọn ghế đã bị bán.

### Frontend vé của tôi

- [x] `N2` Tạo danh sách booking.
- [x] `N2` Lọc theo CONFIRMED/CANCELLED.
- [x] `N2` Tạo trang chi tiết booking.
- [x] `N2` Tạo luồng hủy booking.
- [x] `N2` Hiển thị đúng lịch sử ghế sau khi hủy.

### Kiểm thử nghiệp vụ

- [x] `N1` Test 0 ghế và hơn 8 ghế.
- [x] `N1` Test seat ID bị lặp.
- [x] `N1` Test ghế không thuộc phòng.
- [x] `N1` Test suất chiếu đã bắt đầu.
- [x] `N1` Test người khác xem/hủy booking.
- [x] `N1` Test ghế đã bán trả 409.
- [x] `N1` Test hủy vé rồi đặt lại được ghế.
- [x] `N1` Integration test bằng PostgreSQL thật.
- [ ] `N2` Test chọn ghế bằng chuột và bàn phím.
- [ ] `N2` Test xử lý 409.
- [ ] `N3` E2E đặt vé hoàn chỉnh.
- [ ] `N3` E2E hủy vé.
- [x] `N3` Race test hai user đặt cùng ghế.
- [x] `N3` Xác nhận database không có ghế bị bán hai lần.

**Nghiệm thu Mốc D**

- [ ] `ALL` CUSTOMER đặt được 1–8 ghế.
- [ ] `ALL` Chỉ một request thắng khi hai người đặt cùng ghế.
- [ ] `ALL` Booking xuất hiện trong “Vé của tôi”.
- [ ] `ALL` Chỉ chủ booking xem, xác nhận hoặc hủy được.
- [ ] `ALL` Ghế được trả lại đúng sau khi hủy.
- [ ] `ALL` Booking đã hủy vẫn giữ đủ thông tin lịch sử theo thiết kế đã chốt.

---

## 5. Mốc E — Hoàn thiện Frontend

- [x] `N2` Hoàn thiện design system.
- [x] `N2` Hoàn thiện responsive từ 360 px.
- [x] `N2` Hoàn thiện loading state.
- [x] `N2` Hoàn thiện empty state.
- [x] `N2` Hoàn thiện error state.
- [x] `N2` Hoàn thiện success feedback.
- [x] `N2` Hiển thị tiền theo định dạng `vi-VN`.
- [x] `N2` Hiển thị thời gian theo múi giờ đã chốt.
- [x] `N2` Kiểm tra focus và điều hướng bàn phím.
- [x] `N2` Thêm text thay thế cho trạng thái ghế.
- [x] `N2` Không dùng màu làm tín hiệu duy nhất.
- [x] `N2` Cấu hình CSP phù hợp.
- [x] `N2` Kiểm tra không chèn HTML không tin cậy.
- [x] `N2` Tối ưu kích thước bundle.

**Nghiệm thu Frontend**

- [ ] `ALL` Luồng public hoạt động trên mobile và desktop.
- [ ] `ALL` Luồng CUSTOMER hoạt động trên mobile và desktop.
- [ ] `ALL` Luồng ADMIN hoạt động trên mobile và desktop.
- [ ] `ALL` Các thao tác chính sử dụng được bằng bàn phím.

---

## 6. Mốc F — Docker, CI/CD và bảo mật

### Docker

- [x] `N3` Tạo Dockerfile multi-stage.
- [x] `N3` Build frontend trong stage riêng.
- [x] `N3` Cài backend dependency trong stage riêng.
- [x] `N3` Tạo runtime image gọn.
- [x] `N3` Chạy container bằng user không phải root.
- [x] `N3` Tạo Docker Compose cho app và PostgreSQL.
- [x] `N3` Thêm healthcheck cho app và database.
- [x] `N3` Gắn volume cho PostgreSQL.

### Migration và seed

- [x] `N1` Cấu hình Alembic.
- [x] `N1` Tạo migration đầy đủ từ database trống.
- [ ] `N1` Kiểm tra nâng cấp từ phiên bản trước.
- [x] `N3` Chạy migration tự động trong pipeline phù hợp.
- [x] `N3` Chạy seed bằng lệnh riêng, không chạy tự động trên production.

### CI

- [ ] `N3` CI chạy backend lint.
- [ ] `N3` CI chạy frontend lint và type check.
- [ ] `N3` CI chạy import-linter.
- [ ] `N3` CI chạy unit test.
- [ ] `N3` CI chạy PostgreSQL integration test.
- [ ] `N3` CI chạy frontend test.
- [ ] `N3` CI build frontend.
- [ ] `N3` CI build Docker image.
- [ ] `N3` CI quét dependency.
- [ ] `N3` CI quét secret.

### Bảo mật

- [ ] `N3` JWT secret chỉ lấy từ biến môi trường.
- [ ] `N3` Không log mật khẩu hoặc Authorization header.
- [ ] `N3` Route mới mặc định bị AuthMiddleware bảo vệ.
- [ ] `N3` Public route list đã được review.
- [ ] `N3` CORS chỉ cho origin hợp lệ.
- [x] `N3` Bật security headers.
- [x] `N3` Bật CSP cho frontend.
- [ ] `N3` Lỗi production không lộ stack trace.
- [ ] `N3` Kiểm tra CUSTOMER không gọi được API ADMIN.

**Nghiệm thu Mốc F**

- [ ] `ALL` `docker compose up` khởi động được toàn hệ thống.
- [ ] `ALL` Database được tạo bằng migration.
- [ ] `ALL` CI chạy xanh trên pull request.
- [ ] `ALL` Không còn lỗ hổng Critical/High chưa được xử lý hoặc chấp nhận.

---

## 7. Mốc G — End-to-end và kiểm thử tải

### End-to-end

- [ ] `N3` Khách xem phim và sơ đồ ghế.
- [ ] `N3` CUSTOMER đăng ký và đăng nhập.
- [ ] `N3` CUSTOMER đặt hai ghế.
- [ ] `N3` Booking xuất hiện trong danh sách.
- [ ] `N3` Người khác không xem được booking.
- [ ] `N3` CUSTOMER không gọi được API ADMIN.
- [ ] `N3` ADMIN tạo phim, phòng và suất chiếu.
- [ ] `N3` Tạo lịch trùng trả lỗi.
- [ ] `N3` Hai user tranh cùng ghế.
- [ ] `N3` Hủy booking và đặt lại ghế.

### Locust

- [ ] `N3` Hoàn thành L1 — tải đọc.
- [ ] `N3` Hoàn thành L2 — tải hỗn hợp.
- [ ] `N3` Hoàn thành L3 — tranh ghế.
- [ ] `N3` Hoàn thành L4 — đăng nhập.
- [ ] `N3` Chạy mức 10 user.
- [ ] `N3` Chạy mức 50 user.
- [ ] `N3` Chạy mức 100 user.
- [ ] `N3` Chạy mức 200 user.
- [ ] `N3` Ghi RPS, p50, p95, p99 và tỷ lệ lỗi.
- [ ] `N3` Xác nhận L3 không tạo vé trùng.

### Kaggle

- [ ] `N3` Notebook ghi cấu hình CPU/RAM.
- [ ] `N3` Notebook cài và chạy PostgreSQL.
- [ ] `N3` Seed khoảng 2.000 user và 50 suất chiếu.
- [ ] `N3` Sinh token trước cho L1–L3.
- [ ] `N3` Chạy Locust headless.
- [ ] `N3` Xuất kết quả CSV.
- [ ] `N3` Vẽ biểu đồ RPS.
- [ ] `N3` Vẽ biểu đồ p95.
- [ ] `N3` Viết nhận xét nút thắt.

**Nghiệm thu Mốc G**

- [ ] `ALL` Tất cả E2E quan trọng chạy ổn định.
- [ ] `ALL` Không có ghế bị bán hai lần.
- [ ] `ALL` Có báo cáo và biểu đồ kiểm thử tải.
- [ ] `ALL` Các lỗi 5xx đã được phân tích.

---

## 8. Mốc H — Tài liệu và chuẩn bị demo

- [ ] `ALL` README giới thiệu bài toán.
- [ ] `ALL` README có sơ đồ kiến trúc.
- [ ] `ALL` README có mô hình dữ liệu.
- [ ] `ALL` README có bảng endpoint.
- [ ] `ALL` README hướng dẫn xác thực JWT.
- [x] `ALL` README hướng dẫn chạy bằng Docker.
- [ ] `ALL` README hướng dẫn chạy test.
- [ ] `ALL` README có kết quả kiểm thử tải.
- [ ] `ALL` OpenAPI khớp với implementation.
- [ ] `ALL` Tất cả tài liệu trong `docs/` được cập nhật.
- [ ] `ALL` Chuẩn bị dữ liệu demo.
- [ ] `ALL` Chuẩn bị tài khoản CUSTOMER và ADMIN.
- [ ] `ALL` Chuẩn bị kịch bản demo.
- [ ] `ALL` Diễn tập demo từ đầu đến cuối.
- [ ] `ALL` Chuẩn bị phương án khi mạng hoặc dịch vụ demo gặp lỗi.

---

## 9. Checklist phát hành cuối cùng

- [ ] Tất cả mục bắt buộc trong các mốc A–H đã hoàn thành.
- [ ] Nhánh `main` chạy được.
- [ ] CI xanh trên commit cuối.
- [ ] Unit test đạt.
- [ ] API integration test đạt.
- [ ] PostgreSQL integration test đạt.
- [ ] Frontend test đạt.
- [ ] End-to-end test đạt.
- [ ] Import-linter đạt.
- [x] Docker image build thành công.
- [x] Docker Compose chạy thành công.
- [x] Migration chạy được trên database trống.
- [x] Seed tạo được dữ liệu demo.
- [ ] Swagger hoạt động.
- [ ] Frontend hoạt động trên mobile và desktop.
- [ ] Không có ghế bị bán trùng.
- [ ] Không còn lỗi nghiêm trọng.
- [ ] Không còn lỗ hổng Critical/High chưa được xử lý.
- [ ] Tài liệu và mã nguồn đồng bộ.
- [ ] Báo cáo kiểm thử tải hoàn thành.
- [ ] Kịch bản demo đã được diễn tập.

## 10. Xác nhận hoàn thành

| Vai trò | Người xác nhận | Ngày | Trạng thái |
|---|---|---|---|
| Người 1 — Backend & dữ liệu |  |  | Chưa xác nhận |
| Người 2 — Frontend & UX/UI |  |  | Chưa xác nhận |
| Người 3 — QA & DevOps |  |  | Chưa xác nhận |
| Cả nhóm — Nghiệm thu cuối |  |  | Chưa xác nhận |
