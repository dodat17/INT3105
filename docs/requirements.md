**Đặc tả yêu cầu — Backend đặt vé xem phim**  
Phiên bản: 1.2  
   
 Ngày: 01/10/2026  
   
 Trạng thái: Đặc tả để triển khai và nghiệm thu môn học; đã qua rà soát nghiệp vụ lần 1.  
**1. Mục tiêu và nguyên tắc**  
Xây dựng dịch vụ backend và frontend cho một rạp phim, cho phép người dùng đăng nhập, xem lịch chiếu, xem ghế, giữ ghế, xác nhận đặt vé và hủy đặt chỗ chưa xác nhận.  
Dự án thực hiện theo hai pha:  
- **Pha 1:** Hoàn thành nghiệp vụ cơ bản, REST API JSON, xác thực tập trung, kiến trúc phân tầng, truy cập dữ liệu bằng ORM/data mapper, tài liệu OpenAPI, Docker và đo tải ban đầu trên Kaggle CPU.  
- **Pha 2:** Dựa trên số liệu của Pha 1 để đề xuất, triển khai và đánh giá cải tiến thuộc tính chất lượng. Trọng tâm dự kiến là hiệu năng khi nhiều người truy cập và tranh đặt ghế, với điều kiện giữ nguyên tính đúng đắn.  
Các từ **phải**,  **không được** thể hiện yêu cầu bắt buộc.  **Có thể** thể hiện lựa chọn hoặc phần mở rộng. Các ngưỡng hiệu năng trong tài liệu là mục tiêu thử nghiệm, không phải kết quả đã đo.  
Quy ước đánh mã: FR-xx yêu cầu chức năng, NFR-xx yêu cầu phi chức năng, BR-xx quy tắc nghiệp vụ, T-xx kiểm thử bắt buộc, L-xx kịch bản tải, AS-xx giả định, DP-xx phụ thuộc ngoài, RI-xx rủi ro. Các mã này là định danh ổn định và được đối chiếu ở mục 13.2.  
**2. Phạm vi**  
**2.1. Trong phạm vi Pha 1**  
- Một rạp, nhiều phòng chiếu, mỗi phòng có sơ đồ ghế cố định.  
- Danh mục phim, suất chiếu và giá vé theo suất chiếu.  
- Tài khoản người dùng được tạo bằng seed; đăng nhập và truy cập dữ liệu cá nhân.  
- Giữ một hoặc nhiều ghế thuộc cùng một suất chiếu trong 5 phút.  
- Xác nhận đặt vé mô phỏng, không xử lý tiền thật.  
- Hủy đặt chỗ đang giữ và thu hồi ghế hết hạn.  
- Xem danh sách và chi tiết đặt vé của chính mình.  
- Frontend.  
- Kiểm thử chức năng, tích hợp, tranh chấp đồng thời và tải trên kaggle notebook.  
- Thêm các chức năng của admin (chỉ thêm thằng admin thôi: thêm/sửa/xoá phim/xuất chiếu/user).  
**2.2. Ngoài phạm vi bắt buộc**  
- Cổng thanh toán, hoàn tiền, hóa đơn tài chính, gửi email/SMS, quét vé tại rạp.  
- Đổi ghế, hủy vé đã xác nhận, khuyến mãi, combo đồ ăn, giá vé theo loại ghế.  
- Quản lý chuỗi rạp, đề xuất phim, tìm kiếm nâng cao.  
- Microservices, Kubernetes hoặc triển khai cloud như yêu cầu bắt buộc.  
- Quy tắc chọn ghế nâng cao: bắt buộc ghế liền kề, chống bỏ trống ghế lẻ, ghế ưu tiên/người khuyết tật và ghế đi kèm.  
- Hủy suất chiếu, dời suất chiếu và đổi giá suất chiếu khi đang tồn tại hold hoặc booking đã xác nhận; xem AS-03 và BR-12.  
- API CRUD quản trị danh mục; danh mục chỉ thay đổi qua seed/migration khi dịch vụ không phục vụ.  
- Chấm dứt TLS trong ứng dụng; xem AS-05.  
- Giới hạn tần suất, chống credential stuffing và mọi biện pháp chống lạm dụng khác trên POST /auth/login cũng như trên đường ghi; xem AS-08 và RI-10.  
Không mở rộng phạm vi trước khi hoàn tất tiêu chí nghiệm thu Pha 1. Các mục ngoài phạm vi ở trên là quyết định có chủ đích, không phải thiếu sót; hệ quả và rủi ro kèm theo được ghi ở mục 15.  
**3. Tác nhân và thuật ngữ**  
| | |  
|-|-|  
| **Thành phần** | **Vai trò** |   
| Khách chưa đăng nhập | Xem phim, suất chiếu, sơ đồ ghế; đăng nhập |   
| Người dùng đã đăng nhập | Giữ ghế, xác nhận, hủy đặt chỗ, xem đặt vé của mình |   
| Admin | CRUD phim/xuất chiếu/user.... |   
| Nhóm dev | Khởi tạo dữ liệu, chạy migration, vận hành Docker và thực hiện benchmark |   
| Showtime | Một suất chiếu của một phim trong một phòng tại một thời điểm |   
| Booking | Một lần đặt chỗ cho một hoặc nhiều ghế trong cùng suất chiếu |   
| Hold | Quyền giữ ghế tạm thời của một booking đang có hiệu lực |   
| Booking item | Một ghế và giá vé tương ứng trong booking: loại ghế |   
| ShowtimeSeat | Bản ghi inventory cho một cặp suất chiếu–ghế; nơi duy nhất quyết định quyền chiếm ghế |   
| Trạng thái hiệu lực | Trạng thái booking sau khi đã xét thời hạn thực tế, có thể khác giá trị status đang lưu trong DB |   
| EXPIRED | Trạng thái hiệu lực của booking HELD khi now >= expiresAt, kể cả khi chưa được ghi vật lý |   
| Hold TTL | Thời hạn giữ ghế, mặc định 5 phút, lấy từ cấu hình |   
   
**4. Yêu cầu chức năng và phi chức năng**  
**FR-01 — Đăng nhập**  
- Nhận email và mật khẩu, trả access token, loại token và thời gian có hiệu lực.  
- Email được chuẩn hóa bằng trim và chuyển chữ thường khi seed và khi đăng nhập; mật khẩu được giữ nguyên.  
- Sai email hoặc mật khẩu trả cùng thông báo chung, không tiết lộ tài khoản có tồn tại hay không.  
- Mật khẩu phải được lưu bằng thuật toán hash chuyên dụng có salt, không lưu plaintext hoặc hash nhanh thông thường.  
- Access token dùng Bearer JWT, thời hạn mặc định 60 phút; kiểm tra chữ ký và thời hạn qua middleware/filter/interceptor hoặc cơ chế xác thực tập trung tương đương của framework.  
- Claim bắt buộc: sub chứa ID người dùng, iat, exp. Không đặt dữ liệu cá nhân ngoài ID vào token.  
- Khóa ký lấy từ biến môi trường; với HS256 yêu cầu tối thiểu 32 byte entropy. Dung sai lệch đồng hồ khi kiểm tra exp tối đa 60 giây.  
- Trường expiresIn trong response tính bằng giây.  
- Không trả hoặc ghi log mật khẩu và token đầy đủ.  
**FR-02 — Xem phim**  
- Xem danh sách phim có phân trang và chi tiết một phim.  
- Thông tin tối thiểu: mã phim, tên, thumbnail, mô tả, thời lượng phút.  
- Mã phim không tồn tại trả 404.  
**FR-03 — Xem suất chiếu**  
- Xem danh sách có phân trang và chi tiết một suất chiếu.  
- Thông tin tối thiểu: mã suất, phim, phòng, giờ bắt đầu/kết thúc, giá vé, trạng thái nhận đặt chỗ.  
- Lọc tùy chọn theo movieName và date; khi truyền cả hai thì kết hợp theo phép AND. Không truyền bộ lọc nào thì trả toàn bộ suất chiếu theo thứ tự ở mục 6.1.  
- Trường lọc ngày có định dạng YYYY-MM-DD, áp dụng trên startsAt, được diễn giải theo múi giờ rạp lấy từ cấu hình, mặc định Asia/Ho_Chi_Minh. Một suất chiếu thuộc đúng một ngày lọc, xác định bởi startsAt quy đổi sang múi giờ rạp, kể cả khi endsAt rơi sang ngày kế tiếp.  
- date sai định dạng hoặc tham số lọc sai kiểu trả 400. movieName đúng định dạng nhưng không tồn tại trả danh sách rỗng, không trả 404.  
- Mã suất chiếu không tồn tại trả 404.  
- Suất chiếu chỉ nhận đặt chỗ khi đang mở bán và thời gian hiện tại nhỏ hơn giờ bắt đầu.  
**FR-04 — Xem sơ đồ ghế**  
- Trả danh sách ghế của phòng chiếu cùng trạng thái theo suất chiếu: AVAILABLE, HELD, BOOKED.  
- Trả mã ghế, hàng, số thứ tự để bên gọi dựng sơ đồ.  
- Không tiết lộ người giữ ghế, mã booking của người khác hoặc dữ liệu cá nhân.  
- Kết quả phản ánh trạng thái tại thời điểm đọc; ghế hiển thị còn trống không bảo đảm lần giữ ghế tiếp theo thành công.  
- Ghế có hold hết hạn được xem là AVAILABLE, kể cả khi tác vụ dọn dữ liệu chưa chạy.  
- Endpoint sơ đồ ghế không phân trang: trả toàn bộ ghế của phòng chiếu trong một response. Đây là ngoại lệ có chủ đích so với quy ước phân trang ở mục 6.1, được giới hạn bởi sức chứa phòng tối đa 300 ghế theo AS-07.  
- Thứ tự ghế trả về phải ổn định theo rowLabel, seatNumber.  
**FR-05 — Tạo booking và giữ ghế**  
- Chỉ người dùng đã đăng nhập được tạo booking cho chính mình; danh tính lấy từ ngữ cảnh xác thực.  
- Một yêu cầu nhận showtimeId và danh sách seatIds, tối thiểu 1, tối đa 8 ghế khác nhau.  
- Tất cả ghế phải thuộc phòng của suất chiếu và còn trống tại thời điểm cấp quyền giữ.  
- showtimeId không tồn tại trả 404. seatIds chứa ghế không tồn tại, ghế trùng lặp, ghế sai định dạng hoặc ghế thuộc phòng khác đều là lỗi đầu vào và trả 400 VALIDATION_ERROR; chỉ tình trạng ghế đang bị chiếm mới trả 409 SEAT_UNAVAILABLE. Quy ước này cố định để mã lỗi không phụ thuộc thứ tự kiểm tra nội bộ.  
- Số booking đang giữ hiệu lực của một người dùng bị giới hạn theo BR-11.  
- Giữ ghế theo nguyên tắc toàn bộ hoặc không ghế nào: nếu một ghế không hợp lệ/bị chiếm, không tạo booking hay giữ một phần ghế.  
- Booking mới có trạng thái HELD, createdAt, expiresAt và tổng tiền do server tính.  
- expiresAt = min(thời điểm tạo + 5 phút, giờ bắt đầu suất chiếu); thời hạn giữ ghế có thể cấu hình.  
- Client không được chỉ định chủ booking, trạng thái, giá, tổng tiền hoặc thời hạn giữ ghế.  
- Mỗi yêu cầu tạo mới là một thao tác độc lập. Pha 1 không bảo đảm idempotency cho POST /bookings; client không tự động thử lại khi chưa biết kết quả mà phải kiểm tra danh sách booking.  
**FR-06 — Xác nhận đặt vé**  
- Chỉ chủ booking được xác nhận booking đang HELD, chưa hết hạn và suất chiếu còn nhận đặt chỗ.  
- Việc xác nhận và chuyển toàn bộ ghế sang đã đặt phải là một thao tác nguyên tử.  
- Thành công chuyển booking sang CONFIRMED, ghi thời điểm xác nhận và mã đặt vé duy nhất.  
- Gọi xác nhận lại booking đã CONFIRMED trả thông tin đã xác nhận với 200, không tạo vé hoặc bản ghi mới.  
- Booking CANCELLED hoặc EXPIRED không được xác nhận, trả 409.  
- Thứ tự kiểm tra điều kiện là cố định để mỗi tình huống có đúng một mã lỗi kỳ vọng: quyền sở hữu → trạng thái booking → thời hạn hold → khả năng nhận đặt chỗ của suất chiếu. Tương ứng: không phải chủ sở hữu trả 404 RESOURCE_NOT_FOUND; booking CANCELLED trả 409 INVALID_BOOKING_STATE; booking HELD đã quá hạn trả 409 BOOKING_EXPIRED; booking HELD còn hạn nhưng suất chiếu đã ngừng bán hoặc đã bắt đầu trả 409 SHOWTIME_NOT_BOOKABLE. Booking CONFIRMED đi vào nhánh idempotent ở trên và trả 200 trước mọi kiểm tra còn lại, kể cả khi suất chiếu đã bắt đầu.  
- Đây là xác nhận mô phỏng; API và README không được mô tả là thanh toán thành công.  
**FR-07 — Hủy đặt chỗ**  
- Chỉ chủ booking được hủy booking HELD; chuyển sang CANCELLED và giải phóng tất cả ghế nguyên tử.  
- Gọi hủy lại booking CANCELLED hoặc EXPIRED trả 204, không phát sinh tác dụng phụ.  
- Hủy không phụ thuộc trạng thái suất chiếu. Booking HELD của suất đã bắt đầu luôn đã hết hạn theo công thức expiresAt ở FR-05, nên rơi vào nhánh idempotent và trả 204.  
- Không cho hủy booking CONFIRMED, trả 409 INVALID_BOOKING_STATE.  
- Hủy là thay đổi trạng thái nghiệp vụ, không xóa vật lý booking hoặc lịch sử booking item.  
**FR-08 — Xử lý hết hạn**  
- Booking HELD hết hiệu lực khi now >= expiresAt và có trạng thái nghiệp vụ EXPIRED.  
- Xác nhận, hủy, xem và cấp quyền giữ mới phải xét thời hạn thực tế, không chỉ dựa vào trạng thái lưu trong DB.  
- Pha 1 có thể thu hồi hold hết hạn khi có thao tác liên quan; không bắt buộc tác vụ nền.  
- Nếu chưa cập nhật vật lý, API vẫn trả trạng thái hiệu lực đúng; không được trả HELD cho booking đã hết hạn.  
- Pha 2 có thể bổ sung tác vụ nền nếu đo lường cho thấy cần thiết. Tính đúng đắn không được phụ thuộc tần suất chạy tác vụ này.  
**FR-09 — Xem booking cá nhân**  
- Danh sách có phân trang, sắp xếp mới nhất trước, hỗ trợ lọc theo trạng thái hiệu lực.  
- status nhận đúng một giá trị thuộc HELD, CONFIRMED, CANCELLED, EXPIRED. Bỏ trống tham số nghĩa là không lọc và trả mọi trạng thái. Giá trị ngoài tập này, chuỗi rỗng hoặc nhiều giá trị phân tách bằng dấu phẩy đều trả 400 VALIDATION_ERROR.  
- Bộ lọc áp dụng trên trạng thái hiệu lực, không phải trên giá trị status đang lưu trong DB. Lọc HELD không được trả booking đã quá expiresAt; lọc EXPIRED phải trả các booking đó kể cả khi bản ghi vẫn đang mang status = HELD.  
- Điều kiện lọc, sắp xếp, phân trang và totalItems phải được giải quyết trong cùng một truy vấn trên nguồn dữ liệu. Không được lấy một trang rồi lọc lại trong bộ nhớ, vì khi đó totalItems và ranh giới trang không còn nhất quán với nội dung trả về.  
- Chi tiết gồm phim, suất chiếu, phòng, ghế, đơn giá, tổng tiền, trạng thái và các mốc thời gian liên quan.  
- Không cho đọc, xác nhận hoặc hủy booking người khác; trả 404 giống booking không tồn tại.  
**NFR-01 — Tính đúng đắn dưới tải**  
- Ở mọi mức đồng thời được đo, số vi phạm BR-01, số bản ghi inventory không khớp booking và số lần ghi dữ liệu một phần phải bằng 0.  
- Đây là điều kiện chặn nghiệm thu ở cả hai pha, không phải mục tiêu phấn đấu. Một phiên bản có thông lượng cao nhưng vi phạm bất biến bị coi là không đạt.  
- Kiểm chứng bằng T-07, T-08, T-15, T-16, T-17 và bước kiểm tra bất biến DB sau mỗi lần đo ở mục 10.5.  
**NFR-02 — Ngân sách lỗi ở tải không chủ đích gây quá tải**  
- Với các kịch bản L-01, L-02, L-03, L-05, L-06 tại mức đồng thời đã chốt, tỉ lệ 5xx cộng timeout phải dưới 1% tổng số request.  
- 409 do tranh chấp nghiệp vụ hợp lệ không tính vào ngân sách lỗi và phải được báo cáo thành cột riêng.  
- L-04 cố ý tạo tranh chấp nên không áp ngưỡng này, nhưng vẫn áp NFR-01.  
- Áp dụng cho cả baseline Pha 1 và các phiên bản Pha 2.  
**NFR-03 — Độ trễ**  
- Pha 1 không đặt ngưỡng tuyệt đối cho p50/p95/p99. Baseline là giá trị đo được, không phải giá trị phải đạt. Đây là quyết định có chủ đích để tránh chốt ngưỡng trước khi biết năng lực thực tế của môi trường Kaggle CPU.  
- Ngưỡng so sánh của Pha 2 được chốt sau pilot theo mục 11.3 và phải ghi lại trước khi chạy so sánh chính thức.  
- Bắt buộc thu thập p50, p95 và p99 theo endpoint và theo kịch bản ở cả hai pha, kể cả khi chưa có ngưỡng.  
**NFR-04 — Khởi động và sẵn sàng**  
- Từ môi trường sạch, tính từ lúc khởi động container đến khi GET /health/ready trả 200 không quá 120 giây, chưa tính thời gian build image và chạy seed.  
- GET /health/ready chỉ trả 200 khi kết nối được DB và schema đã ở phiên bản migration mới nhất; thiếu một trong hai điều kiện trả 503.  
- GET /health/live chỉ kiểm tra tiến trình, không kiểm tra phụ thuộc ngoài.  
**NFR-06 — Giới hạn đầu vào**  
- Body request tối đa 64 KB; vượt quá trả 413.  
- Endpoint có body nhận Content-Type khác application/json trả 415.  
- Method không được hỗ trợ trên một route đã tồn tại trả 405.  
**NFR-07 — Khả năng quan sát**  
- Mỗi request ghi đúng một dòng log gồm requestId, method, route template, HTTP status và thời gian xử lý.  
- requestId do server sinh. Nếu chấp nhận header X-Request-Id từ bên gọi thì phải kiểm tra định dạng và giới hạn độ dài; giá trị không hợp lệ bị thay bằng giá trị do server sinh.  
- requestId trong body lỗi ở mục 6.4 phải trùng với requestId trong dòng log của chính request đó, để truy vết được từ phản hồi về log.  
**NFR-08 — Khả năng tái lập**  
- Cùng một commit SHA, cùng random seed và cùng cấu hình phải tạo ra cùng một tập dữ liệu khởi tạo.  
- Mọi số liệu trong báo cáo phải truy ngược được về commit SHA, profile dữ liệu, cấu hình đo và file kết quả thô tương ứng.  
**5. Quy tắc nghiệp vụ và bất biến**  
| | |  
|-|-|  
| **Mã** | **Quy tắc bắt buộc** |   
| BR-01 | Một ghế trong một suất chiếu chỉ có tối đa một quyền chiếm chỗ có hiệu lực: hold chưa hết hạn hoặc booking đã xác nhận. |   
| BR-02 | Cùng ghế vật lý có thể được đặt ở các suất chiếu khác nhau. |   
| BR-03 | Tạo booking, xác nhận và hủy đều nguyên tử; rollback toàn bộ khi lỗi. |   
| BR-04 | Kiểm tra rồi ghi rời rạc không đủ để bảo đảm BR-01; phải có bảo vệ ở transaction/constraint hoặc cơ chế tương đương trong DB. |   
| BR-05 | Thời gian do server/DB xác định; lưu UTC, trả ISO 8601 có timezone. Không tin thời gian client. |   
| BR-06 | Giá vé dùng số nguyên VND; giá booking item được chụp tại lúc giữ ghế; tổng bằng tổng các item. |   
| BR-07 | Không có chuyển trạng thái từ CONFIRMED, CANCELLED, EXPIRED về HELD. |   
| BR-08 | Khi xác nhận, hết hạn và giữ mới cạnh tranh, chỉ một kết quả hợp lệ được commit; thao tác cũ không được giải phóng quyền giữ mới. |   
| BR-09 | Không tạo booking cho suất đã bắt đầu, ngừng bán hoặc không tồn tại. |   
| BR-10 | Cache, nếu có, không phải nguồn quyết định cấp ghế; DB là nguồn dữ liệu quyết định. |   
| BR-11 | Một người dùng có tối đa 2 booking đang giữ hiệu lực trên cùng một suất chiếu và tối đa 5 booking đang giữ hiệu lực trên toàn hệ thống. Vượt giới hạn trả 409 HOLD_LIMIT_EXCEEDED. Hai ngưỡng lấy từ cấu hình và phải dùng cùng giá trị cho hai pha đo. |   
| BR-12 | Danh mục phim, phòng, ghế và suất chiếu là bất biến trong lúc hệ thống đang phục vụ; chỉ thay đổi qua seed/migration ở môi trường development/benchmark khi dịch vụ không phục vụ. Vì vậy Pha 1 không định nghĩa hành vi cho việc đổi giá, dời hoặc hủy suất chiếu khi đang tồn tại hold hoặc booking đã xác nhận. Xem AS-03. |   
| BR-13 | Phải chốt một nguồn thời gian quyết định duy nhất cho createdAt, expiresAt, confirmedAt, cancelledAt và mọi phép so sánh hết hạn; khuyến nghị đồng hồ DB lấy trong cùng transaction với thao tác ghi. Không được trộn đồng hồ ứng dụng và đồng hồ DB trong cùng một luồng quyết định. Lựa chọn ghi trong README; tầng nghiệp vụ truy cập qua cổng clock để unit test kiểm tra được biên hết hạn. |   
| BR-14 | Đơn vị tiền tệ là hằng số VND ở Pha 1; hệ thống không hỗ trợ nhiều loại tiền tệ và không lưu trường currency trong dữ liệu. |   
   
Vòng đời booking:  
                 xác nhận trước hạn  
            HELD --------------------> CONFIRMED  
              |  
              +----- chủ động hủy ---> CANCELLED  
              |  
              +----- đến hạn --------> EXPIRED  
   
Việc kiểm tra hết hạn và giành quyền cập nhật phải diễn ra trong thao tác nguyên tử. Thời điểm quyết định được lấy sau khi giành quyền xử lý bản ghi liên quan để tránh xác nhận dựa trên thời gian cũ sau một lần chờ khóa dài.  
**6. Hợp đồng REST API**  
**6.1. Quy ước chung**  
- Prefix: /api/v1; request/response có body sử dụng application/json.  
- 204 No Content không có body. Các endpoint vận hành cũng trả JSON nếu có body.  
- ID là chuỗi định danh opaque; chọn UUID hoặc biểu diễn chuỗi của ID DB và dùng nhất quán.  
- Các endpoint được bảo vệ nhận header Authorization: Bearer <access_token>.  
- Phân trang: page mặc định 1; pageSize mặc định 20, tối đa 100; giá trị không hợp lệ trả 400. page vượt quá số trang hiện có trả 200 với items rỗng và totalItems đúng, không trả 404.  
- Quy ước phân trang áp dụng cho /movies, /showtimes và /me/bookings. GET /showtimes/{showtimeId}/seats không phân trang theo FR-04; tham số page hoặc pageSize gửi tới endpoint này bị từ chối theo quy tắc DTO bên dưới.  
- Response danh sách gồm items, page, pageSize, totalItems. Không có totalPages; bên gọi tự tính nếu cần.  
- Thứ tự danh sách phải ổn định: phim theo ID; suất chiếu theo startsAt, id; booking theo createdAt DESC, id DESC.  
- Các DTO ghi dữ liệu phải từ chối trường ngoài hợp đồng để tránh gán thuộc tính trái phép; quy tắc này áp dụng cho cả body và query parameter.  
- Ngôn ngữ của error.message là tiếng Việt và có thể thay đổi. Bên gọi phải xử lý theo error.code, không phân tích error.message.  
**6.2. Danh sách endpoint bắt buộc**  
| | | | | |  
|-|-|-|-|-|  
| **Method** | **Endpoint** | **Xác thực** | **Thành công** | **Lỗi chính** |   
| POST | /auth/login | Không | 200 | 400, 401 |   
| GET | /movies | Không | 200 | 400 |   
| GET | /movies/{movieId} | Không | 200 | 404 |   
| GET | /showtimes?movieName=&date= | Không | 200 | 400 |   
| GET | /showtimes/{showtimeId} | Không | 200 | 404 |   
| GET | /showtimes/{showtimeId}/seats | Không | 200 | 404 |   
| POST | /bookings | Có | 201 | 400, 401, 404, 409 |   
| GET | /me/bookings?status= | Có | 200 | 400, 401 |   
| GET | /bookings/{bookingId} | Có | 200 | 401, 404 |   
| POST | /bookings/{bookingId}/confirm | Có | 200 | 401, 404, 409 |   
| DELETE | /bookings/{bookingId} | Có | 204 | 401, 404, 409 |   
   
Các đường dẫn trong bảng được ghép với /api/v1. Bổ sung GET /health/live và GET /health/ready ngoài prefix: live kiểm tra tiến trình, ready kiểm tra khả năng truy cập DB và phiên bản migration theo NFR-04; trả 503 khi chưa sẵn sàng. Hai endpoint này không yêu cầu xác thực và chỉ trả trạng thái tổng hợp cùng tên các kiểm tra thành phần; không trả phiên bản thư viện, chuỗi kết nối, tên host hay thông tin nội bộ khác.  
**6.3. Ví dụ payload**  
Đăng nhập:  
{  
   "email": "user01@example.test",  
   "password": "demo-password"  
 }  
   
Response đăng nhập:  
{  
   "accessToken": "<jwt>",  
   "tokenType": "Bearer",  
   "expiresIn": 3600  
 }  
   
Tạo booking:  
{  
   "showtimeId": "showtime-001",  
   "seatIds": ["seat-a01", "seat-a02"]  
 }  
   
Response 201, kèm Location: /api/v1/bookings/booking-001:  
{  
   "id": "booking-001",  
   "showtimeId": "showtime-001",  
   "status": "HELD",  
   "items": [  
     {"seatId": "seat-a01", "unitPrice": 90000},  
     {"seatId": "seat-a02", "unitPrice": 90000}  
   ],  
   "totalAmount": 180000,  
   "currency": "VND",  
   "createdAt": "2026-09-10T12:00:00Z",  
   "expiresAt": "2026-09-10T12:05:00Z",  
   "confirmedAt": null,  
   "cancelledAt": null,  
   "bookingCode": null  
 }  
   
Các ID trong ví dụ chỉ minh họa, không ràng buộc định dạng triển khai. POST .../confirm không cần body, trả booking đầy đủ với trạng thái mới. Chi tiết booking bổ sung thông tin phim/phòng/ghế theo FR-09.  
Response danh sách:  
{  
   "items": [],  
   "page": 1,  
   "pageSize": 20,  
   "totalItems": 0  
 }  
   
**6.4. Hợp đồng lỗi**  
{  
   "error": {  
     "code": "SEAT_UNAVAILABLE",  
     "message": "Một hoặc nhiều ghế không còn trống.",  
     "details": {"seatIds": ["seat-a01"]},  
     "requestId": "request-001"  
   }  
 }  
   
| | | |  
|-|-|-|  
| **HTTP** | **Mã lỗi gợi ý** | **Trường hợp** |   
| 400 | VALIDATION_ERROR | JSON lỗi, thiếu trường, trường ngoài hợp đồng, trùng ghế, quá 8 ghế, ghế không tồn tại, ghế không thuộc phòng, status ngoài tập cho phép, bộ lọc hoặc tham số phân trang không hợp lệ |   
| 401 | INVALID_CREDENTIALS, UNAUTHENTICATED | Đăng nhập sai; thiếu/sai/hết hạn token |   
| 404 | RESOURCE_NOT_FOUND | Không có tài nguyên hoặc booking không thuộc người gọi |   
| 405 | METHOD_NOT_ALLOWED | Method không được hỗ trợ trên route đã tồn tại |   
| 409 | SEAT_UNAVAILABLE | Ghế đang giữ còn hiệu lực hoặc đã được đặt |   
| 409 | BOOKING_EXPIRED, INVALID_BOOKING_STATE, SHOWTIME_NOT_BOOKABLE | Xung đột trạng thái nghiệp vụ |   
| 409 | HOLD_LIMIT_EXCEEDED | Vượt giới hạn hold đang hiệu lực theo BR-11 |   
| 413 | PAYLOAD_TOO_LARGE | Body vượt giới hạn ở NFR-06 |   
| 415 | UNSUPPORTED_MEDIA_TYPE | Content-Type không phải application/json trên endpoint có body |   
| 500 | INTERNAL_ERROR | Lỗi hệ thống ngoài dự kiến; không lộ stack trace/SQL |   
| 503 | SERVICE_UNAVAILABLE | Dịch vụ/phụ thuộc tạm thời không sẵn sàng |   
   
Tranh ghế hợp lệ không được biến thành lỗi 500, kể cả khi tầng DB phát sinh vi phạm ràng buộc unique, xung đột serialization hay deadlock; các trường hợp đó phải được ánh xạ về 409 SEAT_UNAVAILABLE. Middleware xác thực chạy trước logic endpoint. Sau xác thực, kiểm tra quyền sở hữu trước khi trả thông tin trạng thái booking.  
Thứ tự đánh giá lỗi là cố định để mỗi tình huống có đúng một mã lỗi kỳ vọng và kiểm thử viết được assertion chắc chắn: định dạng body và Content-Type → xác thực → hợp lệ của DTO và tham số → tồn tại của tài nguyên → quyền sở hữu → trạng thái nghiệp vụ → tranh chấp inventory. FR-06 mô tả thứ tự chi tiết cho thao tác xác nhận.  
Trường details là object tùy chọn. Khi lỗi liên quan tới ghế, details.seatIds phải liệt kê toàn bộ ghế gây lỗi, không dừng ở ghế đầu tiên, và được sắp xếp tăng dần để kết quả ổn định giữa các lần gọi. Khi lỗi là validation trường, details.fields liệt kê tên các trường sai. details không được chứa dữ liệu của người dùng khác.  
**6.5. OpenAPI/Swagger**  
- Có tài liệu OpenAPI được commit hoặc sinh tự động, và Swagger UI với hướng dẫn truy cập trong README.  
- Mô tả toàn bộ endpoint, query/path parameter, schema, ví dụ, mã lỗi, phân trang và Bearer security scheme.  
- Đánh dấu đúng endpoint yêu cầu đăng nhập; Swagger UI cho nhập token để thử các API.  
- Hợp đồng tài liệu phải khớp hành vi thực tế; nêu rõ thao tác xác nhận không thanh toán thật.  
**7. Mô hình dữ liệu tối thiểu**  
| | |  
|-|-|  
| **Thực thể** | **Thuộc tính chính và ràng buộc** |   
| User | id, email unique sau chuẩn hóa, passwordHash, createdAt |   
| Movie | id, title, description, durationMinutes > 0 |   
| Auditorium | id, name unique |   
| Seat | id, auditoriumId, rowLabel, seatNumber; unique theo phòng/hàng/số |   
| Showtime | id, movieId, auditoriumId, startsAt, endsAt, ticketPrice >= 0, isOpenForBooking |   
| Booking | id, userId, showtimeId, status thuộc tập HELD, CONFIRMED, CANCELLED, EXPIRED, createdAt, expiresAt, confirmedAt?, cancelledAt?, totalAmount, bookingCode? unique khi có |   
| BookingItem | bookingId, seatId, unitPrice; unique theo booking/ghế; giữ lại lịch sử |   
| ShowtimeSeat | Một bản ghi inventory cho mỗi cặp showtimeId, seatId unique; liên kết booking đang chiếm ghế nếu có |   
   
- ShowtimeSeat là thiết kế inventory đề xuất để tách quyền chiếm ghế hiện tại khỏi lịch sử. Có thể chọn mô hình tương đương nếu chứng minh được BR-01 và các chuyển trạng thái nguyên tử.  
- Không chỉ đặt unique trên BookingItem(showtimeId, seatId) cho toàn bộ lịch sử vì ghế phải đặt lại được sau khi hủy/hết hạn.  
- Có foreign key và các constraint cần thiết; không xóa danh mục đang được booking tham chiếu.  
- Seed phải bảo đảm endsAt > startsAt, thời lượng hợp lý và không có suất chiếu chồng lấn trong cùng phòng.  
- Giá trị totalAmount lưu trong booking phải khớp tổng item; server không nhận tổng tiền từ client.  
- Các bản ghi ShowtimeSeat phải được tạo sẵn đầy đủ cho mọi cặp showtimeId, seatId ngay khi suất chiếu được seed, trong cùng transaction với việc tạo suất chiếu. Không được tạo bản ghi inventory theo kiểu lazy ở đường ghi: hai transaction cùng thấy chưa có bản ghi sẽ tái tạo đúng race mà BR-04 muốn loại bỏ. Nếu chọn mô hình tương đương thay cho ShowtimeSeat, phải chỉ rõ bản ghi nào đã tồn tại trước thời điểm tranh chấp và ràng buộc nào bảo đảm BR-01.  
- Cấp quyền giữ ghế phải là một câu lệnh ghi có điều kiện trên bản ghi inventory đã tồn tại, ví dụ UPDATE ... WHERE ghế còn trống hoặc hold đã hết hạn; số dòng bị ảnh hưởng quyết định thành công hay xung đột. Không dùng mẫu đọc trước rồi ghi sau ở đường cấp ghế.  
- Sức chứa mỗi phòng chiếu tối đa 300 ghế, để endpoint sơ đồ ghế không phân trang giữ kích thước response hợp lý; xem AS-07.  
- bookingCode chỉ được sinh khi xác nhận thành công, dùng nguồn ngẫu nhiên an toàn với độ dài và bảng ký tự cố định, không suy ra được từ id hoặc thứ tự tạo. Trùng mã phải được phát hiện bằng ràng buộc unique và sinh lại tối đa một số lần hữu hạn trước khi trả 500.  
- Không lưu currency trong dữ liệu theo BR-14; API luôn trả hằng số VND.  
- User ở Pha 1 không có trạng thái vô hiệu hóa; xem AS-04 về hệ quả của việc không thu hồi token.  
- Khởi tạo schema bằng migration có quản lý phiên bản, không phụ thuộc tạo bảng thủ công.  
**8. Kiến trúc và ràng buộc triển khai**  
**8.1. Kiến trúc Pha 1**  
Sử dụng monolith phân tầng. Không bắt buộc một ngôn ngữ/framework cụ thể. Nhóm phải chốt stack và ghi lý do trong README trước khi triển khai.  
Client → API / Authentication middleware → Application/Domain service  
                                               ↓  
                                   Repository / Unit of Work interfaces  
                                               ↑ implements  
                                   Infrastructure: ORM / Database  
   
- **API:** Routing, parse/validate DTO, lấy danh tính từ middleware, gọi service, chuyển kết quả/lỗi thành HTTP JSON.  
- **Application/Domain:** Quy tắc giữ ghế, giá, vòng đời booking, quyền sở hữu; khai báo các port repository, transaction, clock và token/password nếu cần.  
- **Infrastructure:** Triển khai repository bằng ORM/data mapper, transaction, clock, hash/token provider và truy cập DB.  
- **Composition root:** Khởi tạo và inject các implementation vào service.  
- Tầng nghiệp vụ không import framework web, thư viện DB hoặc ORM entity; không trả HTTP response trực tiếp.  
- API không truy vấn ORM/DB trực tiếp. Service nhận user ID từ ngữ cảnh đã xác thực, không tự đọc HTTP header.  
- Ranh giới transaction phải bao trùm toàn bộ use case nhiều thao tác ghi; không commit riêng từng repository khi cần tính nguyên tử.  
- Ranh giới kiến trúc phải được kiểm chứng tự động, không chỉ bằng review thủ công: có một bài kiểm thử phụ thuộc chạy trong CI, làm fail build khi tầng nghiệp vụ import framework web hoặc thư viện DB/ORM, hoặc khi tầng API import trực tiếp implementation repository. Công cụ tùy stack, ví dụ ArchUnit, import-linter, dependency-cruiser hoặc một script kiểm tra danh sách import. Bài kiểm thử này phải tồn tại từ mốc M2, vì ràng buộc kiến trúc không thể vá lại ở cuối kỳ.  
- Khuyến nghị DB quan hệ hỗ trợ transaction; nếu chọn PostgreSQL, giữ cùng loại DB và phiên bản trong hai pha đo chính.  
**8.2. Bảo mật và vận hành cơ bản**  
- Dùng middleware xác thực dùng chung cho các route được bảo vệ, không sao chép việc xác thực trong từng handler.  
- Secret và chuỗi kết nối lấy từ biến môi trường; có .env.example chứa giá trị minh họa, không commit secret thật.  
- Lỗi validation và nghiệp vụ được xử lý nhất quán; không lộ thông tin nội bộ.  
- Log có request ID, method, route template, HTTP status và thời gian xử lý; không log mật khẩu/token.  
- Không dùng user ID hoặc booking ID làm nhãn metric có số lượng giá trị không giới hạn.  
- Tài khoản demo do seed tạo không phải secret: mật khẩu demo được ghi công khai trong README và chỉ dùng cho môi trường development/benchmark. Quy tắc không commit secret ở trên áp dụng cho khóa ký JWT, chuỗi kết nối thật và mọi thông tin đăng nhập ngoài môi trường development.  
- Các lệnh seed/reset phá hủy dữ liệu chỉ áp dụng môi trường development/benchmark và phải được ghi rõ trong hướng dẫn.  
**8.3. Docker và khả năng tái lập**  
- Có Dockerfile build/chạy backend và Docker Compose chạy backend cùng DB cho môi trường local.  
- Có hướng dẫn chạy migration, seed, xem Swagger và thực hiện một booking mẫu từ môi trường sạch.  
- Cố định phiên bản dependency bằng lockfile/cơ chế tương đương và ghi rõ phiên bản runtime/DB.  
- Có health check và cấu hình tối thiểu: DB URL, JWT secret và thuật toán ký, token TTL, hold TTL, giới hạn hold theo BR-11, kích thước connection pool, số worker, cổng HTTP và múi giờ rạp.  
- Không giả định Docker daemon khả dụng trên Kaggle: cung cấp thêm script/notebook chạy backend, DB và load generator trực tiếp trong môi trường notebook CPU. Giữ cùng phiên bản phần mềm và cấu hình logic với bản Docker.  
- Kiểm chứng khả năng khởi động DB và cài dependency trên Kaggle sớm; ghi lại hạn chế môi trường thực tế, không báo cáo kết quả local là kết quả Kaggle.  
**9. Kiểm thử và tiêu chí đúng đắn**  
**9.1. Kiểm thử bắt buộc**  
| | | |  
|-|-|-|  
| **Mã** | **Kịch bản** | **Kết quả kỳ vọng** |   
| T-01 | Đăng nhập đúng/sai | Token hợp lệ hoặc 401; không lộ thông tin nhạy cảm |   
| T-02 | Gọi GET cá nhân và POST booking thiếu/sai/hết hạn token | 401, không thay đổi dữ liệu |   
| T-03 | Xem danh mục, phân trang và lọc ngày | Dữ liệu và timezone đúng; đầu vào lỗi trả 400 |   
| T-04 | Giữ 1 ghế và nhiều ghế hợp lệ | 201, đúng hạn giữ, giá và số item |   
| T-05 | Giữ ghế trùng, rỗng, quá giới hạn, khác phòng | 400, không tạo dữ liệu một phần |   
| T-06 | Một trong nhiều ghế đã bị chiếm | 409, những ghế còn lại không bị giữ |   
| T-07 | Ít nhất 20 yêu cầu đồng thời tranh cùng một ghế trống; chạy hai biến thể, 20 người dùng khác nhau và cùng một người dùng | Chính xác 1 request trả 201, 19 request còn lại trả 409 SEAT_UNAVAILABLE, không có 5xx; sau bài đo, bản ghi inventory của ghế trỏ đúng tới booking thắng và chỉ tồn tại 1 booking HELD cho ghế đó |   
| T-08 | Hai yêu cầu đồng thời với hai nhóm ghế giao nhau, ví dụ A1/A2 và A2/A3 | Chính xác một booking thành công, request còn lại trả 409; ghế chỉ thuộc nhóm thất bại, ví dụ A3, phải còn AVAILABLE; không tồn tại hold một phần |   
| T-09 | Xác nhận trước hạn và xác nhận lại | Booking CONFIRMED, mã vé ổn định, không sinh bản ghi trùng |   
| T-10 | Xác nhận đúng hạn hoặc sau hạn | 409 BOOKING_EXPIRED, không tạo vé |   
| T-11 | Hủy, hủy lại, đặt lại ghế vừa hủy | 204, 204, giữ mới thành công |   
| T-12 | Hủy vé đã xác nhận | 409, ghế vẫn đã đặt |   
| T-13 | Đọc/xác nhận/hủy booking của người khác | 404, không thay đổi dữ liệu |   
| T-14 | Hold hết hạn khi không có tác vụ nền | GET trả trạng thái hiệu lực đúng, người khác giữ lại được |   
| T-15 | Xác nhận đồng thời với hủy | Chỉ một chuyển trạng thái thắng, inventory khớp booking cuối cùng |   
| T-16 | Xác nhận/thu hồi hết hạn/giữ mới cạnh tranh | Không ghi đè hoặc giải phóng quyền chiếm ghế mới; giữ đúng BR-01 |   
| T-17 | Lỗi giữa thao tác ghi nhiều bảng | Rollback, không có booking/ghế bị ghi một phần |   
| T-18 | Suất đã bắt đầu hoặc ngừng bán | Không tạo/xác nhận hold mới; xác nhận lặp vé đã thành công vẫn trả kết quả cũ |   
| T-19 | Khởi động lại backend | Booking đã commit còn nguyên, hạn giữ không được kéo dài |   
| T-20 | Đặt cùng một ghế vật lý ở hai suất chiếu khác nhau | Cả hai thành công; kiểm chứng BR-02 |   
| T-21 | Đọc lại booking vừa tạo và kiểm tra biểu diễn thời gian, tiền tệ và giá | Mốc thời gian lưu UTC và trả ISO 8601 có timezone; currency là VND; unitPrice bằng ticketPrice tại thời điểm giữ; totalAmount bằng tổng item; kiểm chứng BR-05, BR-06, BR-14 |   
| T-22 | Vượt giới hạn hold đang hiệu lực của một người dùng, trên cùng suất và trên toàn hệ thống | 409 HOLD_LIMIT_EXCEEDED; sau khi hủy một hold thì tạo mới lại thành công; kiểm chứng BR-11 |   
| T-23 | Token bị sửa payload, token ký bằng khóa khác, token khai alg: none, token thiếu sub, token quá hạn trong dung sai và ngoài dung sai | 401 UNAUTHENTICATED cho mọi trường hợp trừ trường hợp còn trong dung sai lệch đồng hồ; không thay đổi dữ liệu; kiểm chứng FR-01 |   
| T-24 | GET /me/bookings với status hợp lệ, status sai, nhiều status, không truyền status, và page vượt quá số trang hiện có | Lọc theo trạng thái hiệu lực đúng cho cả HELD và EXPIRED; status sai hoặc nhiều giá trị trả 400; totalItems khớp số bản ghi thỏa điều kiện; trang vượt quá trả 200 với items rỗng; kiểm chứng FR-09 |   
| T-25 | Nhiều yêu cầu đồng thời giữ một ghế của suất chiếu chưa từng có giao dịch nào | Kết quả như T-07; không có 500 do vi phạm ràng buộc unique; kiểm chứng cách khởi tạo bản ghi inventory ở mục 7 |   
| T-27 | Gọi endpoint có body với Content-Type sai, body vượt 64 KB, method không được hỗ trợ, DTO chứa trường ngoài hợp đồng, và query parameter lạ trên endpoint sơ đồ ghế | Lần lượt 415, 413, 405, 400, 400; không tạo dữ liệu; kiểm chứng NFR-06 và mục 6.1 |   
| T-28 | Kiểm thử phụ thuộc kiến trúc trong CI | Build fail khi tầng nghiệp vụ import framework web hoặc thư viện DB/ORM; kiểm chứng mục 8.1 |   
| T-29 | Đọc sơ đồ ghế của một suất chiếu trong phòng 100 ghế | Trả đủ 100 ghế trong một response, thứ tự theo rowLabel, seatNumber, không phân trang; kiểm chứng FR-04 |   
| T-30 | Chỉ áp dụng cho phiên bản Pha 2 có cache: đọc sơ đồ ghế đã cũ rồi giữ ghế đã bị chiếm | Quyết định cấp ghế dựa trên DB; dữ liệu cache cũ không cho phép giữ ghế đã bị chiếm; kiểm chứng BR-10 |   
   
- Unit test tập trung vào service nghiệp vụ và chuyển trạng thái; inject clock để kiểm tra chính xác biên hết hạn mà không cần chờ 5 phút.  
- Integration test dùng DB cùng loại với môi trường chạy, đặc biệt cho transaction và tranh chấp đồng thời; mock repository không đủ chứng minh chống double booking.  
- Sau kiểm thử tranh chấp phải kiểm tra dữ liệu DB, không chỉ đếm HTTP status.  
- Kiểm thử biên hết hạn phải phủ cả ba điểm now < expiresAt, now = expiresAt và now > expiresAt, tương ứng T-09 và T-10.  
- Mọi kiểm thử trong bảng trên là bắt buộc cho Pha 1, trừ T-30 chỉ bắt buộc khi phiên bản Pha 2 có cache. Hai mã T-26 và NFR-05 đã bị thu hồi ở phiên bản 1.2 và không được dùng lại cho nội dung khác.  
- Có smoke test luồng đăng nhập → tìm suất → giữ ghế → xác nhận → xem vé, đồng thời kiểm tra một dòng log của request theo NFR-07 và trạng thái GET /health/ready theo NFR-04.  
**9.2. Tiêu chí nghiệm thu Pha 1**  
- Toàn bộ FR-01 đến FR-09, các NFR còn hiệu lực và BR-01 đến BR-14 được đáp ứng, đối chiếu qua ma trận ở mục 13.2.  
- Có REST API JSON gồm GET, POST, DELETE và tài liệu Swagger/OpenAPI đúng thực tế.  
- Cả năm endpoint POST /bookings, GET /me/bookings, GET /bookings/{bookingId}, POST /bookings/{bookingId}/confirm và DELETE /bookings/{bookingId} được bảo vệ bởi cùng một cơ chế xác thực tập trung; không endpoint nào tự kiểm tra token riêng.  
- Phân tầng và chiều phụ thuộc đúng mục 8.1, có kiểm thử phụ thuộc tự động chạy trong CI theo T-28; repository dùng ORM/data mapper.  
- Toàn bộ kiểm thử bắt buộc ở bảng 9.1 đạt; không có double booking, không có ghi dữ liệu một phần; NFR-01 ghi nhận 0 vi phạm.  
- Build/chạy được bằng Docker theo README trên môi trường sạch; thời gian tới trạng thái ready đạt NFR-04.  
- Có kết quả tải baseline thực sự chạy trên Kaggle CPU kèm dữ liệu thô và metadata môi trường; NFR-02 đạt ở các kịch bản áp dụng.  
- README chứa đủ các mục liệt kê ở 12.2; repository GitHub công khai; có commit ở cả bốn mốc M1–M4 và không có commit gộp toàn bộ dự án; không chứa secret.  
**10. Kế hoạch kiểm thử tải trên Kaggle CPU**  
**10.1. Mục tiêu**  
Đo baseline Pha 1 để xác định điểm nghẽn; so sánh với Pha 2 trên cùng cấu hình. Không đặt kết luận cải thiện trước khi có số liệu. Tính đúng đắn là điều kiện bắt buộc ở mọi mức tải.  
**10.2. Môi trường cố định**  
- Chọn notebook Kaggle CPU, không dùng GPU/TPU.  
- Ghi CPU model, số CPU khả dụng, RAM, hệ điều hành, runtime, DB, dependency, worker count, connection pool, cấu hình load generator và commit SHA.  
- Chạy baseline và phiên bản cải tiến lần lượt trong cùng phiên notebook nếu có thể; dừng phiên bản trước khi chạy phiên bản sau.  
- Khi phải đổi phiên, đối chiếu cấu hình thực tế; không gộp kết quả khác phần cứng thành một so sánh trực tiếp.  
- Backend, DB và load generator dùng chung máy nên phải ghi nhận tải CPU/RAM của từng tiến trình, cùng ngân sách CPU/RAM tổng thể cho hai phiên bản.  
- Nếu thêm Redis hoặc worker nền, tài nguyên của chúng được tính vào ngân sách tổng; không tăng phần cứng để tạo ra cải thiện.  
- Số worker của backend, kích thước connection pool và timeout của load generator là biến kiểm soát: phải giữ nguyên giá trị giữa baseline và phiên bản cải tiến. Nếu chính một trong các giá trị này là nội dung cải tiến được đo, phải khai báo rõ và đo riêng tác động của nó, không thay đổi cùng lúc với thay đổi kiến trúc.  
- Báo cáo số liệu phản ánh môi trường cùng máy, không suy rộng thành năng lực production.  
**10.3. Dữ liệu và chuẩn bị**  
- Seed xác định bằng random seed cố định: tối thiểu 10 phim, 3 phòng × 100 ghế, 60 suất chiếu và 200 tài khoản giả lập.  
- Ngày giờ suất chiếu được sinh tương đối so với thời điểm chạy để không vô tình dùng suất đã hết giờ; giữ nguyên khoảng cách thời gian giữa các lần đo.  
- Có profile dữ liệu ghế trống và profile hỗn hợp, ví dụ 20% ghế đã đặt và 10% đang giữ; ghi rõ profile cho mỗi bài đo.  
- Reset về cùng trạng thái trước mỗi lần lặp; tách thời gian seed/migration khỏi thời gian đo.  
- Đăng nhập và chuẩn bị token trước bài đo nghiệp vụ, bảo đảm token không hết hạn giữa bài; tải đăng nhập được đo riêng nếu cần.  
- Tập ghế/suất cho kịch bản ghi phải đủ lớn hoặc có bước hủy/chu kỳ reset được mô tả để không biến toàn bộ bài đo thành xung đột do hết ghế.  
- Mỗi máy ảo người dùng của load generator được gán một phần không giao nhau của không gian (suất chiếu, dải ghế) theo công thức xác định từ chỉ số VU, để kịch bản ít tranh chấp thực sự ít tranh chấp và lặp lại được giữa hai phiên bản. Ở mức đồng thời 100 với nhóm tối đa 8 ghế, nhu cầu ghế của một đợt vượt sức chứa một phòng, nên phân bổ bắt buộc phải trải trên nhiều suất chiếu; ghi công thức phân bổ trong cấu hình benchmark.  
- Load generator không được tự động thử lại POST /bookings khi gặp timeout hoặc lỗi mạng, vì endpoint này không idempotent theo FR-05: mỗi lần thử lại tạo thêm hold mồ côi, làm sai lệch cả tỉ lệ 409 lẫn lượng ghế còn trống. Nếu cần thử lại cho endpoint chỉ đọc thì phải cấu hình riêng và ghi rõ.  
- Thời gian seed, reset và chuẩn bị token không tính vào thời gian đo nhưng phải được ghi lại, vì tổng của chúng ảnh hưởng trực tiếp tới ngân sách phiên notebook ở mục 10.5.  
**10.4. Các kịch bản tải**  
| | | |  
|-|-|-|  
| **Mã** | **Kịch bản** | **Thiết kế** |   
| L-01 | Đọc danh mục | GET phim và suất chiếu với cùng phân phối tham số giữa hai phiên bản |   
| L-02 | Đọc sơ đồ ghế nóng | Nhiều client đọc cùng một hoặc vài suất chiếu |   
| L-03 | Giữ ghế ít tranh chấp | Client chọn ghế khác nhau, tạo rồi hủy; đo cả giao dịch và từng endpoint |   
| L-04 | Tranh ghế nóng | Các đợt client tranh cùng ghế/tập ghế nhỏ; reset giữa đợt, đếm người thắng và xung đột |   
| L-05 | Luồng hỗn hợp | Tỉ lệ request mục tiêu: 70% đọc công khai, 10% đọc booking cá nhân, 10% tạo, 5% xác nhận, 5% hủy |   
| L-06 | Hết hạn | Tạo hold rồi bỏ dở, xác minh ghế tái sử dụng được và đo chi phí thu hồi |   
   
L-05 phải duy trì trạng thái theo từng người dùng: chỉ xác nhận/hủy booking thực sự tạo thành công, chia hai nhóm booking riêng cho xác nhận và hủy. Báo cáo tỉ lệ request thực tế vì xung đột có thể làm thay đổi tỉ lệ mục tiêu.  
L-06 có thể dùng hold TTL ngắn riêng cho thử nghiệm, nhưng phải dùng cùng TTL cho hai phiên bản và ghi rõ khác biệt với mặc định 5 phút.  
**10.5. Quy trình đo**  
1. Chạy pilot một tổ hợp kịch bản/mức tải để đo thời gian thực tế của một lần chạy đầy đủ gồm reset, warm-up, đo và kiểm tra bất biến; dùng số liệu này để chốt ma trận đo khả thi trong ngân sách một phiên notebook.  
2. Kiểm tra correctness và smoke test trước khi đo tải.  
3. Khởi động dịch vụ, seed/reset dữ liệu, chuẩn bị token.  
4. Với mỗi kịch bản, dùng các mức đồng thời ban đầu 1, 10, 25, 50, 100; điều chỉnh sau pilot cho phù hợp Kaggle nhưng phải chốt chung cho hai phiên bản trước so sánh chính thức.  
5. Warm-up 30 giây, đo ổn định 120 giây; ghi rõ thời gian ramp-up, timeout và think time. L-04 có thể đo theo đợt nhưng phải cố định số đợt/kích thước đợt.  
6. Lặp ít nhất 3 lần cho mỗi tổ hợp phiên bản/kịch bản/mức tải; luân phiên thứ tự baseline/cải tiến để giảm ảnh hưởng thời gian.  
7. Thu metric, dữ liệu thô và kiểm tra bất biến DB sau mỗi lần đo.  
8. Tổng hợp trung vị và độ dao động giữa các lần chạy; không gộp p95 bằng cách lấy trung bình rồi gọi đó là p95 của toàn bộ request.  
Ma trận đầy đủ gồm 6 kịch bản × 5 mức đồng thời × 3 lần lặp × 2 phiên bản là 180 lần chạy; với warm-up 30 giây và đo ổn định 120 giây, riêng thời gian đo đã khoảng 7,5 giờ, chưa tính seed, reset, khởi động dịch vụ và cài đặt phụ thuộc. Một phiên notebook Kaggle CPU không bảo đảm đủ ngân sách này; xem RI-01. Vì vậy pilot ở bước 1 phải đo thời gian thực của một tổ hợp và chốt ma trận rút gọn trước khi chạy so sánh chính thức, theo nguyên tắc: giữ đủ 5 mức đồng thời cho một kịch bản neo, khuyến nghị L-04, và rút còn 3 mức cho các kịch bản còn lại. Ma trận đã rút gọn phải giống hệt nhau cho hai phiên bản và được ghi lại kèm lý do rút gọn.  
Chọn một load generator có khả năng tái lập như k6 hoặc Locust và dùng nhất quán. Nếu client là điểm nghẽn, ghi rõ giới hạn đó và không kết luận server đã đạt công suất tối đa.  
**10.6. Chỉ số phải thu thập**  
- Số request, throughput HTTP (request/giây), p50/p95/p99 và độ trễ trung bình theo endpoint/kịch bản.  
- Hai chỉ số riêng biệt: số hold thành công mỗi giây và số xác nhận thành công mỗi giây. Không gộp hai chỉ số này vào một cột và không đánh đồng throughput HTTP với lượng vé đặt thành công.  
- Tỉ lệ 2xx, xung đột nghiệp vụ dự kiến 409, lỗi đầu vào/xác thực ngoài dự kiến, 5xx, timeout và lỗi kết nối.  
- CPU/RAM backend, DB, load generator và thành phần bổ sung; chu kỳ lấy mẫu phải nhất quán.  
- Số truy vấn DB hoặc truy vấn/request, thời gian truy vấn và chờ khóa nếu công cụ hỗ trợ; chỉ ra chỉ số nào chưa thu được.  
- Với cache: hit/miss, TTL, chi phí bộ nhớ và mức độ cũ của dữ liệu.  
- Số vi phạm double booking, inventory không khớp booking và ghi dữ liệu một phần: bắt buộc bằng 0.  
- Với hết hạn: thời gian từ expiresAt đến khi ghế có thể giữ lại và, nếu có worker, thời gian đến khi bản ghi được dọn vật lý.  
**10.7. Bảng kết quả chuẩn**  
| | | | | | | | | | | | | | | | |  
|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|  
| **Phiên bản/commit** | **Kịch bản** | **Profile dữ liệu** | **Đồng thời** | **Lần chạy** | **p50 (ms)** | **p95 (ms)** | **p99 (ms)** | **HTTP req/s** | **Hold thành công/s** | **Xác nhận thành công/s** | **409 (%)** | **5xx/timeout (%)** | **CPU** | **RAM** | **Vi phạm bất biến** |   
| Điền sau khi đo |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   
   
Kèm theo bảng trên phải có bảng tổng hợp theo tổ hợp phiên bản/kịch bản/mức tải, gồm trung vị giữa các lần chạy và độ dao động, ví dụ khoảng min–max hoặc IQR, theo bước 8 của mục 10.5.  
Lưu CSV/JSON kết quả thô và cấu hình đo. Không đưa số liệu minh họa vào báo cáo như kết quả thực nghiệm.  
**11. Pha 2 — Đề xuất và đánh giá cải tiến**  
**11.1. Phương pháp lựa chọn**  
1. Phân tích baseline để xác định điểm nghẽn thực tế.  
2. Viết giả thuyết: thay đổi nào, tác động đến chỉ số nào, vì sao có thể cải thiện, đánh đổi gì.  
3. Chọn ít nhất một cải tiến kiến trúc có phạm vi rõ; không bắt buộc làm tất cả hướng dưới đây.  
4. Ghi quyết định bằng ADR, sơ đồ trước/sau và cách giữ đúng các bất biến.  
5. Đo cùng bộ kịch bản, dữ liệu và phần cứng; nếu kết hợp nhiều thay đổi, đo từng thay đổi khi khả thi để phân biệt tác động.  
**11.2. Các hướng ứng viên**  
| | | |  
|-|-|-|  
| **Hướng** | **Khi nào xem xét** | **Đánh đổi cần đánh giá** |   
| Cache-aside cho phim/suất chiếu | Truy vấn đọc lặp lại chiếm tài nguyên đáng kể | TTL, vô hiệu hóa cache, RAM, xử lý khi cache lỗi |   
| Cache sơ đồ ghế hoặc tách dữ liệu tĩnh/động | L-02 là điểm nghẽn | Ghế hiển thị có thể cũ; ghi vẫn phải kiểm tra DB; cache lỗi nên fallback DB |   
| Điều chỉnh chiến lược đồng thời/transaction | Chờ khóa hoặc transaction dài hạn chế L-03/L-04 | Retry có giới hạn, deadlock, starvation, duy trì tính nguyên tử |   
| Worker thu hồi hold hết hạn | Thu hồi trong request gây tăng độ trễ | Thêm thành phần vận hành; job idempotent; không giải phóng booking đã xác nhận/hold mới |   
| Tối ưu đường đọc và truy vấn | N+1 hoặc query plan cho thấy truy vấn kém hiệu quả | Chi phí index/ghi, độ phức tạp; phân biệt tối ưu truy vấn với thay đổi kiến trúc |   
   
Mọi phiên bản có cache phải chạy thêm T-30 để chứng minh BR-10: dữ liệu cache cũ không được trở thành căn cứ cấp ghế.  
Không cố tình bỏ constraint hoặc viết baseline sai để tạo ra cải thiện. Chỉ thêm index đơn lẻ có thể chưa đủ thể hiện cải tiến kiến trúc theo kỳ vọng môn học; nhóm cần giải thích thay đổi cấu trúc/trách nhiệm thành phần được lựa chọn.  
**11.3. Mục tiêu đánh giá đề xuất**  
- Không có vi phạm bất biến và không làm mất chức năng Pha 1.  
- Sau pilot baseline, chốt một mục tiêu chính trước khi chạy so sánh chính thức: ví dụ giảm p95 ít nhất 20% hoặc tăng throughput hữu ích ít nhất 20% tại cùng mức tải/ngân sách tài nguyên.  
- Theo dõi hồi quy ở các kịch bản khác; mọi thay đổi độ trễ/tài nguyên đáng kể phải được giải thích.  
- Với kịch bản không chủ đích gây quá tải, áp dụng NFR-02 cho cả baseline và phiên bản cải tiến; 409 hợp lệ được báo cáo thành cột riêng.  
- Nếu mục tiêu không đạt, báo cáo trung thực kết quả, nguyên nhân và giới hạn; không coi giả thuyết cải thiện là sự thật.  
**11.4. Tiêu chí nghiệm thu Pha 2**  
- Có vấn đề và số liệu baseline làm căn cứ.  
- Có ADR mô tả kiến trúc trước/sau, giả thuyết và đánh đổi.  
- Có ít nhất một cải tiến được triển khai và kiểm thử.  
- Kiểm thử correctness vẫn đạt, đặc biệt các tình huống tranh ghế/hết hạn; NFR-01 ghi nhận 0 vi phạm ở mọi mức tải đã đo.  
- So sánh trên cùng cấu hình Kaggle CPU, cùng tải/dữ liệu và ngân sách tài nguyên.  
- Có kết quả thô, biểu đồ/bảng so sánh và hướng dẫn tái lập.  
- Kết luận chỉ rõ cải thiện, hồi quy hoặc không đạt; không chỉ đưa phần trăm thiếu số tuyệt đối.  
**12. Sản phẩm bàn giao và quản lý dự án**  
**12.1. Cấu trúc sản phẩm gợi ý**  
requirements.md  
 README.md  
 src/                         # API, nghiệp vụ, infrastructure  
 tests/                       # unit, integration, concurrency  
 migrations/  
 scripts/                     # seed, startup, smoke  
 benchmarks/                  # workload và cấu hình  
 notebooks/                   # chạy trên Kaggle CPU  
 docs/  
   architecture.md  
   api/                       # OpenAPI nếu xuất thành file  
   adr/  
   reports/                   # baseline, so sánh trước/sau  
   benchmark-results/         # kết quả thô có kích thước phù hợp  
 Dockerfile  
 compose.yaml  
 .env.example  
   
Cấu trúc thư mục cụ thể tùy stack; phải giữ rõ ranh giới kiến trúc. Artifact đo quá lớn có thể lưu ngoài Git nhưng báo cáo phải có đường dẫn truy cập và thông tin đối chiếu.  
**12.2. README bắt buộc**  
- Tên đề tài, thành viên, mục tiêu và phạm vi.  
- Stack, phiên bản, sơ đồ kiến trúc, trách nhiệm từng tầng và chiều phụ thuộc.  
- Mô hình dữ liệu, vòng đời booking, cách chống double booking và xử lý hết hạn.  
- Cách chạy Docker, chạy trực tiếp, cấu hình, migration/seed và tài khoản demo giả lập.  
- Đường dẫn Swagger/OpenAPI và ví dụ luồng sử dụng API.  
- Cách chạy test và benchmark trên Kaggle CPU; link notebook và báo cáo.  
- Lựa chọn thuật toán ký JWT, nguồn thời gian quyết định theo BR-13 và giới hạn hold theo BR-11, kèm giá trị mặc định.  
- Danh sách giả định và rủi ro còn hiệu lực, đối chiếu mục 15.  
- Tóm tắt cải tiến Pha 2, đánh đổi và giới hạn còn lại.  
**12.3. Git và các mốc thực hiện**  
- Repository GitHub công khai; commit nhỏ, mô tả thay đổi có ý nghĩa, tránh dồn toàn bộ dự án vào một commit cuối kỳ.  
- Không commit .env, token, mật khẩu thật hoặc dữ liệu cá nhân thật. Tài khoản demo chỉ dành cho môi trường thử nghiệm.  
- Gắn tag hoặc lưu commit SHA cho baseline Pha 1 và từng phiên bản Pha 2 được đo.  
- M1: Chốt stack, khởi động skeleton/DB/Docker và thử chạy môi trường Kaggle.  
- M2: Hoàn tất danh mục, đăng nhập, phân tầng và OpenAPI.  
- M3: Hoàn tất booking, transaction, quyền sở hữu và kiểm thử đồng thời.  
- M4: Đo baseline trên Kaggle, hoàn tất bàn giao Pha 1.  
- M5: Viết ADR, triển khai cải tiến, kiểm thử và đo so sánh Pha 2.  
- M6: Hoàn thiện báo cáo, README và kiểm tra tái lập từ môi trường sạch.  
**13. Ma trận đối chiếu**  
**13.1. Đối chiếu đề bài môn học**  
| | | |  
|-|-|-|  
| **Yêu cầu môn học** | **Phần đáp ứng** | **Bằng chứng bàn giao** |   
| REST JSON, POST/GET/DELETE | Mục 6 | API chạy được, OpenAPI, smoke test |   
| Tài liệu Swagger/OpenAPI | Mục 6.5 | File hoặc endpoint đặc tả, Swagger UI |   
| API → Nghiệp vụ → Truy cập dữ liệu | Mục 8.1 | Sơ đồ và cấu trúc/import của mã nguồn |   
| Nghiệp vụ không import web/DB | Mục 8.1 | Review dependency và unit test service |   
| Repository dùng ORM/data mapper | Mục 7, 8.1 | Implementation repository và migration |   
| Đăng nhập, GET/POST cần xác thực tập trung | FR-01, FR-05, FR-09 | Middleware và T-01/T-02/T-13 |   
| Đóng gói Docker | Mục 8.3 | Dockerfile, Compose, hướng dẫn chạy |   
| GitHub công khai, commit cẩn thận, README | Mục 12 | Repository, lịch sử commit và README |   
| Pha 1 chỉ chức năng cơ bản | Mục 2 | Phạm vi nghiệm thu giới hạn |   
| Kiểm thử tải Kaggle CPU | Mục 10 | Notebook, metadata môi trường, kết quả thô |   
| Pha 2 cải tiến chất lượng, đánh giá trước/sau | Mục 11 | ADR, mã nguồn, báo cáo so sánh cùng cấu hình |   
   
**13.2. Đối chiếu yêu cầu — endpoint — kiểm thử**  
Mọi dòng phải có ít nhất một kiểm thử hoặc một lý do rõ ràng vì sao không kiểm thử được. Dòng trống ở cột kiểm thử là một khoảng trống phạm vi cần xử lý trước nghiệm thu.  
| | | | |  
|-|-|-|-|  
| **Mã** | **Nội dung** | **Endpoint liên quan** | **Kiểm thử** |   
| FR-01 | Đăng nhập | POST /auth/login | T-01, T-02, T-23 |   
| FR-02 | Xem phim | GET /movies, GET /movies/{movieId} | T-03 |   
| FR-03 | Xem suất chiếu | GET /showtimes, GET /showtimes/{showtimeId} | T-03 |   
| FR-04 | Xem sơ đồ ghế | GET /showtimes/{showtimeId}/seats | T-14, T-29 |   
| FR-05 | Tạo booking và giữ ghế | POST /bookings | T-04, T-05, T-06, T-07, T-08, T-22, T-25, T-27 |   
| FR-06 | Xác nhận đặt vé | POST /bookings/{bookingId}/confirm | T-09, T-10, T-15, T-18 |   
| FR-07 | Hủy đặt chỗ | DELETE /bookings/{bookingId} | T-11, T-12, T-15 |   
| FR-08 | Xử lý hết hạn | Toàn bộ đường đọc và ghi booking | T-10, T-14, T-16, T-19 |   
| FR-09 | Xem booking cá nhân | GET /me/bookings, GET /bookings/{bookingId} | T-13, T-24 |   
| NFR-01 | Đúng đắn dưới tải | Toàn bộ đường ghi | T-07, T-08, T-15, T-16, T-17, kiểm tra bất biến ở L-04 |   
| NFR-02 | Ngân sách lỗi | Toàn bộ | L-01, L-02, L-03, L-05, L-06 |   
| NFR-03 | Độ trễ | Toàn bộ | Mục 10.6 và 10.7 |   
| NFR-04 | Khởi động và sẵn sàng | GET /health/live, GET /health/ready | Smoke test mục 9.1 |   
| NFR-06 | Giới hạn đầu vào | Mọi endpoint có body | T-27 |   
| NFR-07 | Khả năng quan sát | Toàn bộ | Kiểm tra log trong smoke test |   
| NFR-08 | Khả năng tái lập | — | Mục 10.3 và 12.3 |   
| BR-01 | Một quyền chiếm ghế hiệu lực | POST /bookings, confirm | T-07, T-08, T-16, T-25 |   
| BR-02 | Ghế dùng lại ở suất chiếu khác | POST /bookings | T-20 |   
| BR-03 | Nguyên tử | Đường ghi booking | T-17 |   
| BR-04 | Bảo vệ ở transaction/constraint | POST /bookings | T-07, T-25 |   
| BR-05 | Thời gian UTC, ISO 8601 | Mọi response có thời gian | T-21 |   
| BR-06 | Giá nguyên VND, chụp giá lúc giữ | POST /bookings | T-04, T-21 |   
| BR-07 | Không quay lại HELD | confirm, cancel | T-11, T-12, T-15 |   
| BR-08 | Cạnh tranh xác nhận/hết hạn/giữ mới | confirm, POST /bookings | T-15, T-16 |   
| BR-09 | Không đặt suất đã bắt đầu hoặc ngừng bán | POST /bookings | T-18 |   
| BR-10 | Cache không quyết định cấp ghế | Pha 2 | T-30 |   
| BR-11 | Giới hạn hold mỗi người dùng | POST /bookings | T-22 |   
| BR-12 | Danh mục bất biến khi đang phục vụ | — | Không kiểm thử; là giả định AS-03 |   
| BR-13 | Nguồn thời gian quyết định duy nhất | Mọi đường xét hết hạn | T-09, T-10, T-19 |   
| BR-14 | Đơn vị tiền tệ hằng số | Response booking | T-21 |   
| Mục 8.1 | Ranh giới kiến trúc | — | T-28 |   
   
**14. Các quyết định còn cần chốt khi bắt đầu triển khai**  
Những mục sau không chặn việc sử dụng đặc tả, nhưng phải được ghi nhận trước khi viết implementation tương ứng:  
- Ngôn ngữ, framework, ORM/data mapper, DB và phiên bản cụ thể.  
- Cơ chế transaction/khóa/constraint bảo vệ inventory và ánh xạ lỗi tranh chấp thành lỗi nghiệp vụ.  
- Thuật toán ký JWT theo FR-01 và nguồn thời gian quyết định theo BR-13.  
- Giá trị cấu hình mặc định cho giới hạn hold theo BR-11.  
- Công cụ kiểm thử phụ thuộc kiến trúc dùng cho T-28.  
- Load generator và cách khởi chạy các tiến trình trong notebook Kaggle thực tế, bao gồm phương án dự phòng cho RI-02.  
- Ma trận đo rút gọn sau pilot theo mục 10.5.  
- Cải tiến kiến trúc Pha 2 và ngưỡng đánh giá chính, dựa trên baseline Pha 1.  
Các yêu cầu nghiệp vụ trong tài liệu không phụ thuộc vào các lựa chọn công nghệ trên.  
**15. Giả định, phụ thuộc và rủi ro**  
**15.1. Giả định**  
Các giả định dưới đây là điều kiện để đặc tả hiện tại đủ dùng. Nếu một giả định sai, phạm vi phải được mở lại chứ không vá cục bộ.  
| | | |  
|-|-|-|  
| **Mã** | **Giả định** | **Hệ quả nếu sai** |   
| AS-01 | Một rạp duy nhất, một múi giờ vận hành | Bộ lọc ngày và mọi mốc thời gian phải xét theo từng rạp; mô hình dữ liệu hiện tại không đủ |   
| AS-02 | Không có thanh toán thật; xác nhận là mô phỏng và luôn thành công nếu điều kiện nghiệp vụ đạt | Cần thêm trạng thái trung gian chờ thanh toán, timeout thanh toán và luồng hoàn tiền; vòng đời booking ở mục 5 phải viết lại |   
| AS-03 | Danh mục chỉ thay đổi qua seed/migration khi dịch vụ không phục vụ; không hủy, dời hay đổi giá suất chiếu khi đang tồn tại hold hoặc booking | Phải bổ sung luồng đền bù cho booking đã xác nhận và quy tắc xử lý hold đang treo; xem BR-12 |   
| AS-04 | Tài khoản seed không bị vô hiệu hóa trong lúc chạy nên không cần thu hồi token | Token vẫn hiệu lực tối đa 60 phút sau khi tài khoản bị vô hiệu; cần blacklist token hoặc refresh token, vốn đang ngoài phạm vi |   
| AS-05 | TLS do hạ tầng hoặc reverse proxy đảm nhiệm; ứng dụng phục vụ HTTP trong mạng nội bộ | Bearer token đi qua kênh không mã hóa; không được triển khai ra môi trường công khai ở cấu hình này |   
| AS-06 | Backend, DB và load generator chạy cùng một máy trong môi trường đo | Số liệu không suy rộng thành năng lực production; đã nêu ở mục 10.2 |   
| AS-07 | Sức chứa mỗi phòng chiếu không vượt 300 ghế | Endpoint sơ đồ ghế không phân trang sẽ trả response quá lớn; phải bổ sung phân trang hoặc nén |   
| AS-08 | Bên gọi API ở Pha 1 là client có kiểm soát, không phải Internet công cộng | Hệ thống không có biện pháp chống lạm dụng nào: POST /auth/login không bị giới hạn tần suất, nên vừa là bề mặt credential stuffing vừa là đường tự gây quá tải. Xem RI-10 |   
   
**15.2. Phụ thuộc ngoài**  
| | | |  
|-|-|-|  
| **Mã** | **Phụ thuộc** | **Ghi chú** |   
| DP-01 | Kaggle Notebook CPU | Nền tảng bắt buộc cho toàn bộ số liệu ở mục 10 và so sánh ở mục 11; giới hạn thời gian phiên và tài nguyên là ràng buộc cứng |   
| DP-02 | Truy cập Internet trong notebook Kaggle | Cần để cài runtime, DB và load generator; Kaggle tắt Internet theo mặc định và yêu cầu xác minh tài khoản để bật |   
| DP-03 | Load generator k6 hoặc Locust | Phải cài và chạy được trong notebook mà không phụ thuộc Docker daemon |   
| DP-04 | GitHub công khai | Nơi nộp mã nguồn, ADR và kết quả; cần trước mốc M1 |   
| DP-05 | Registry gói của stack đã chọn | Lockfile phải cài lại được từ môi trường sạch tại thời điểm chấm |   
   
**15.3. Rủi ro**  
| | | | | |  
|-|-|-|-|-|  
| **Mã** | **Rủi ro** | **Ảnh hưởng** | **Giảm thiểu** | **Mốc xử lý** |   
| RI-01 | Ngân sách thời gian một phiên Kaggle không đủ cho ma trận đo đầy đủ | Không hoàn thành M4, hoặc so sánh Pha 2 phải chạy khác phiên và mất tính so sánh trực tiếp | Pilot đo thời gian thực rồi chốt ma trận rút gọn theo mục 10.5; ưu tiên kịch bản neo | Pilot ở M1, chốt ở M4 |   
| RI-02 | Internet bị tắt trong notebook Kaggle theo DP-02 | Không cài được DB hoặc load generator, chặn toàn bộ mục 10 | Xác minh tài khoản sớm; chuẩn bị phương án đóng gói sẵn dependency hoặc dùng Kaggle Dataset làm nguồn cài đặt | M1 |   
| RI-03 | Load generator trở thành điểm nghẽn trên máy dùng chung | Kết luận sai rằng server đã đạt công suất tối đa | Ghi CPU của tiến trình load generator ở mọi lần đo; khi bão hòa thì ghi rõ giới hạn và không kết luận về công suất server | Mỗi lần đo |   
| RI-04 | Nhiễu do máy dùng chung làm kết quả dao động lớn | So sánh trước/sau không kết luận được | Lặp tối thiểu 3 lần, luân phiên thứ tự, báo cáo trung vị và độ dao động; không kết luận cải thiện khi khoảng dao động chồng lấn | Mục 10.5 |   
| RI-05 | Chọn sai cơ chế chống tranh chấp và phát hiện muộn | Phải đổi schema và viết lại toàn bộ kiểm thử đồng thời | Chốt cơ chế và viết T-07, T-08, T-25 ngay ở M3, trước khi mở rộng tính năng | M3 |   
| RI-06 | Hold mồ côi do client thử lại làm cạn ghế trong bài đo | Tỉ lệ 409 tăng giả tạo, kịch bản ít tranh chấp mất ý nghĩa | BR-11, quy tắc không tự động thử lại ở mục 10.3, reset giữa các lần lặp | M4 |   
| RI-07 | Ranh giới kiến trúc bị vi phạm dần và chỉ phát hiện khi chấm | Không đạt một tiêu chí nghiệm thu trọng yếu, không còn thời gian sửa | Kiểm thử phụ thuộc tự động trong CI từ M2 theo mục 8.1 và T-28 | M2 |   
| RI-08 | Cải tiến Pha 2 đạt hiệu năng nhưng phá vỡ bất biến | Không đạt nghiệm thu Pha 2 dù số liệu đẹp | Chạy lại toàn bộ kiểm thử correctness cho mỗi phiên bản được đo; NFR-01 là điều kiện chặn | M5 |   
| RI-09 | Dồn commit vào cuối kỳ | Vi phạm tiêu chí ở mục 12.3 và mất bằng chứng tiến độ | Commit theo mốc M1–M6, gắn tag cho từng phiên bản được đo | Liên tục |   
| RI-10 | POST /auth/login không có giới hạn tần suất | Hash mật khẩu cố tình chậm, nên ở mức đồng thời cao riêng endpoint đăng nhập có thể chiếm hết CPU của máy dùng chung và làm sai lệch số liệu của mọi kịch bản khác; đồng thời là bề mặt credential stuffing | Chuẩn bị token **trước** bài đo nghiệp vụ và đo tải đăng nhập tách riêng theo mục 10.3; ghi nhận là giới hạn đã biết trong README, không trình bày như hệ thống đã được bảo vệ | M4 |   
   
**16. Lịch sử thay đổi**  
| | | |  
|-|-|-|  
| **Phiên bản** | **Ngày** | **Nội dung chính** |   
| 1.0 | 10/09/2026 | Đặc tả ban đầu |   
| 1.1 | 11/09/2026 | Bổ sung NFR-01 đến NFR-08 và quy ước đánh mã; bổ sung BR-11 đến BR-14; làm rõ lọc trạng thái hiệu lực ở FR-09; chốt vòng đời bản ghi inventory ở mục 7; cố định thứ tự đánh giá và mã lỗi ở FR-05, FR-06, FR-07 và mục 6.4; bổ sung ngoại lệ phân trang cho sơ đồ ghế; siết tiêu chí T-07 và T-08; bổ sung T-20 đến T-30; siết tiêu chí nghiệm thu Pha 1; bổ sung ma trận truy vết 13.2; bổ sung mục 15 về giả định, phụ thuộc và rủi ro; điều chỉnh mục 10 theo ngân sách phiên Kaggle và bổ sung biến kiểm soát khi đo |   
| 1.2 | 11/09/2026 | Loại bỏ NFR-05 (chống dò mật khẩu) khỏi phạm vi Pha 1 cùng toàn bộ tham chiếu: mã lỗi 429 RATE_LIMITED, kiểm thử T-26, dòng cấu hình và biến kiểm soát tương ứng. Hai mã NFR-05 và T-26 được **thu hồi**, không dùng lại cho nội dung khác, để các mã còn lại giữ nguyên ý nghĩa. Bổ sung mục ngoài phạm vi ở 2.2, làm rõ hệ quả ở AS-08 và thêm rủi ro RI-10. |   
   
