# Kế hoạch đo tải trên Kaggle CPU

Triển khai mục 10 của [requirements.md](../requirements.md) thành quy trình thực hiện được. Mục tiêu là **baseline trung thực**, không phải con số đẹp.

## 1. Ràng buộc định hình kế hoạch này

| Ràng buộc | Hệ quả |
|---|---|
| Backend, PostgreSQL và k6 chạy **chung một máy** (AS-06) | Phải ghi CPU/RAM của từng tiến trình; không suy rộng thành năng lực production |
| Không có Docker daemon trên Kaggle | Cần script chạy trực tiếp ba tiến trình trong notebook, cùng phiên bản và cấu hình logic với bản Docker |
| Kaggle **tắt Internet theo mặc định** (DP-02) | Phải xác minh tài khoản ở M1; dự phòng: đóng gói Python wheelhouse, PostgreSQL và k6 thành Kaggle Dataset |
| Ngân sách thời gian một phiên (RI-01) | Ma trận đầy đủ không khả thi; phải rút gọn sau pilot |

## 2. Ngân sách thời gian: vì sao phải rút gọn

Ma trận đầy đủ theo mục 10.5:

```
6 kịch bản × 5 mức đồng thời × 3 lần lặp × 2 phiên bản = 180 lần chạy
180 × (30 s warm-up + 120 s đo)                        ≈ 7,5 giờ  ← chỉ riêng thời gian đo
+ reset + seed + khởi động lại + kiểm tra bất biến     ≈ 180 × 60–90 s ≈ 3–4,5 giờ
                                                        ------------------------------
                                                         ≈ 11–12 giờ
```

Con số này chạm trần của một phiên notebook Kaggle CPU, không còn biên an toàn nào. Vì vậy **bước 1 của mục 10.5 là pilot**, và ma trận chính thức chỉ được chốt sau khi có số đo thật.

### Quy tắc rút gọn

- Một **kịch bản neo** giữ đủ 5 mức đồng thời `1, 10, 25, 50, 100`. Khuyến nghị **L-04**, vì tranh chấp ghế là trọng tâm của đồ án.
- Các kịch bản còn lại rút xuống 3 mức: `1, 25, 100`.
- Vẫn giữ tối thiểu 3 lần lặp cho mọi tổ hợp. Cắt số lần lặp là thứ **cuối cùng** được cắt, vì độ dao động là thông tin bắt buộc để kết luận (RI-04).

Ma trận rút gọn: `(5 + 5×3) × 3 × 2 = 120` lần chạy ≈ 5 giờ đo. Phải **giống hệt nhau** cho baseline và bản cải tiến, và được ghi lại kèm lý do trong báo cáo.

## 3. Chuẩn bị môi trường

### 3.1. Metadata phải ghi cho mỗi phiên

Lưu thành `docs/benchmark-results/<run-id>/environment.json`:

```json
{
  "runId": "2026-09-20T09-00Z-baseline",
  "commitSha": "…",
  "gitTag": "phase1-baseline",
  "cpuModel": "…", "cpuCount": 4, "ramGb": 16, "os": "…",
  "python": "3.12.x", "fastapi": "locked", "sqlalchemy": "locked",
  "alembic": "locked", "psycopg": "locked", "uvicorn": "locked",
  "postgres": "16.x", "k6": "locked",
  "webWorkers": 2, "anyioThreadTokens": 40, "dbPoolMaxSize": 20,
  "holdTtlSeconds": 300,
  "seedRandomSeed": 20260911, "dataProfile": "empty-seats",
  "notes": "…"
}
```

### 3.2. Biến kiểm soát

Bốn giá trị sau **phải giữ nguyên** giữa baseline và bản cải tiến (mục 10.2): `webWorkers`, `anyioThreadTokens`, `dbPoolMaxSize` và timeout của k6. Nếu chính một giá trị là nội dung cải tiến được đo, phải khai báo rõ và đo riêng tác động, không đổi cùng lúc với thay đổi kiến trúc.

### 3.3. Tải đăng nhập phải đo tách riêng

`POST /auth/login` không có giới hạn tần suất (RI-10) và hash mật khẩu cố tình chậm. Nếu để đăng nhập lẫn vào kịch bản nghiệp vụ, riêng nó có thể chiếm hết CPU của máy dùng chung và làm sai lệch mọi số liệu khác. Vì vậy: **chuẩn bị toàn bộ token trước bài đo** (bước 4 của quy trình), và nếu cần số liệu về đăng nhập thì đo nó như một kịch bản riêng, không gộp vào L-01 … L-06.

### 3.4. Quy trình mỗi lần chạy

```text
1. reset DB → `uv run alembic upgrade head` → seed theo profile
   (đo thời gian, KHÔNG tính vào thời gian đo)
2. khởi động lại FastAPI/Uvicorn, chờ GET /health/ready = 200
3. chạy scripts/smoke.sh  → phải xanh, nếu không thì dừng
4. chuẩn bị token cho toàn bộ VU, kiểm tra TTL đủ dài cho cả bài đo
5. k6 run: warm-up 30 s → đo ổn định 120 s
6. thu metric của k6 + mẫu CPU/RAM từng tiến trình (chu kỳ 1 s)
7. chạy scripts/check-invariants.sql → I1–I7 phải trả 0 dòng
8. lưu kết quả thô vào docs/benchmark-results/<run-id>/
```

Bước 7 không phải thủ tục hình thức: `NFR-01` là điều kiện chặn, và một phiên bản có thông lượng cao nhưng vi phạm bất biến bị coi là **không đạt**.

## 4. Các kịch bản

| Mã | Nội dung | Profile | Thiết kế |
|---|---|---|---|
| `L-01` | Đọc danh mục | `mixed` | `GET /movies` và `GET /showtimes` với cùng phân phối tham số cho hai phiên bản |
| `L-02` | Đọc sơ đồ ghế nóng | `mixed` | Toàn bộ VU đọc 1–3 suất chiếu cố định |
| `L-03` | Giữ ghế ít tranh chấp | `empty-seats` | Mỗi VU giữ rồi hủy trên phần ghế riêng; đo cả giao dịch lẫn từng endpoint |
| `L-04` | Tranh ghế nóng | `empty-seats` | Các đợt VU tranh cùng một tập ghế nhỏ; reset giữa các đợt; đếm người thắng và số xung đột |
| `L-05` | Luồng hỗn hợp | `mixed` | 70% đọc công khai, 10% đọc booking cá nhân, 10% tạo, 5% xác nhận, 5% hủy |
| `L-06` | Hết hạn | `empty-seats` | Tạo hold rồi bỏ dở; xác minh ghế tái sử dụng được và đo chi phí thu hồi |

### 4.1. Phân bổ ghế: điểm dễ làm hỏng bài đo

`L-03` gọi là "ít tranh chấp" nhưng ở mức đồng thời 100 với nhóm tối đa 8 ghế, nhu cầu là **800 ghế cho một đợt**, trong khi một phòng chỉ có 100. Nếu không phân bổ rõ ràng, L-03 tự biến thành một kịch bản tranh chấp và mất hết ý nghĩa.

Công thức phân bổ xác định theo chỉ số VU, ghi trong cấu hình benchmark:

```javascript
// 60 suất chiếu × 100 ghế = 6000 ghế. 100 VU × 8 ghế = 800 → thừa sức.
const SHOWTIMES_PER_VU = 1;
const SEATS_PER_VU     = 8;

function seatBlock(vuId) {
  const showtimeIdx = (vuId - 1) % SHOWTIME_COUNT;          // trải đều trên các suất
  const blockIdx    = Math.floor((vuId - 1) / SHOWTIME_COUNT);
  const firstSeat   = blockIdx * SEATS_PER_VU;              // khối ghế không giao nhau
  return { showtime: SHOWTIMES[showtimeIdx],
           seats: SEATS.slice(firstSeat, firstSeat + SEATS_PER_VU) };
}
```

`L-04` làm ngược lại một cách có chủ đích: mọi VU nhắm cùng một tập ghế nhỏ, reset giữa các đợt, với số đợt và kích thước đợt cố định.

### 4.2. Quy tắc không thử lại

k6 **không được** tự động thử lại `POST /bookings` khi timeout hoặc lỗi mạng. Endpoint này không idempotent ở Pha 1 (FR-05); mỗi lần thử lại tạo thêm một hold mồ côi, làm tăng giả tạo tỉ lệ `409` và làm cạn ghế (RI-06). Nếu cần thử lại cho endpoint chỉ đọc thì cấu hình riêng và ghi rõ.

### 4.3. Trạng thái theo người dùng ở `L-05`

`L-05` phải duy trì trạng thái riêng cho từng VU: chỉ xác nhận hoặc hủy những booking **thực sự tạo thành công**, và chia hai nhóm booking riêng cho hai thao tác đó. Vì xung đột làm lệch tỉ lệ mục tiêu, báo cáo phải ghi **tỉ lệ request thực tế** bên cạnh tỉ lệ mục tiêu.

### 4.4. TTL riêng cho `L-06`

`L-06` có thể dùng `HOLD_TTL_SECONDS` ngắn hơn (ví dụ 10 giây) để quan sát được chu kỳ hết hạn trong 120 giây đo. Bắt buộc: dùng **cùng một giá trị** cho hai phiên bản, và ghi rõ khác biệt so với mặc định 300 giây.

## 5. Chỉ số thu thập

| Nhóm | Chỉ số |
|---|---|
| Thông lượng | Số request, HTTP req/s theo endpoint và theo kịch bản |
| Độ trễ | p50, p95, p99 và trung bình, theo endpoint và theo kịch bản |
| Nghiệp vụ | **Hold thành công/s** và **xác nhận thành công/s** — hai chỉ số riêng, không gộp |
| Kết quả | Tỉ lệ `2xx`; `409` nghiệp vụ hợp lệ; lỗi `4xx` ngoài dự kiến; `5xx`; timeout; lỗi kết nối |
| Tài nguyên | CPU/RAM của Uvicorn workers, PostgreSQL và k6 — lấy mẫu cùng chu kỳ 1 s |
| DB | Số truy vấn mỗi request, thời gian truy vấn, thời gian chờ khóa (nếu thu được; chỉ rõ chỉ số nào chưa thu được) |
| Bất biến | Số vi phạm double booking, inventory lệch booking, ghi một phần — **bắt buộc bằng 0** |
| Hết hạn | Thời gian từ `expiresAt` tới lúc ghế giữ lại được; nếu có worker, thêm thời gian tới lúc dọn vật lý |

Không đánh đồng HTTP throughput với lượng vé đặt thành công. Ở `L-04`, HTTP req/s có thể rất cao trong khi số hold thành công/s rất thấp — đó chính là thông tin cần nhìn thấy.

## 6. Báo cáo kết quả

Bảng chi tiết theo mục 10.7, mỗi dòng là **một lần chạy**:

| Phiên bản/commit | Kịch bản | Profile | Đồng thời | Lần chạy | p50 | p95 | p99 | HTTP req/s | Hold/s | Xác nhận/s | 409 (%) | 5xx+timeout (%) | CPU | RAM | Vi phạm bất biến |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

Kèm bảng tổng hợp theo tổ hợp phiên bản/kịch bản/mức tải, gồm **trung vị** và **độ dao động** (min–max hoặc IQR) giữa các lần chạy.

Bốn quy tắc trình bày:

1. Không lấy trung bình của p95 rồi gọi đó là p95 của toàn bộ request. Tính lại percentile từ dữ liệu thô nếu cần gộp.
2. Không đưa số liệu minh họa vào báo cáo như kết quả thực nghiệm.
3. Khi khoảng dao động của hai phiên bản chồng lấn, kết luận là "chưa phân biệt được", không phải "có cải thiện" (RI-04).
4. Nếu k6 bão hòa CPU, ghi rõ rằng client là điểm nghẽn và **không** kết luận server đã đạt công suất tối đa (RI-03).

Kết quả thô lưu dạng CSV/JSON tại `docs/benchmark-results/<run-id>/`, kèm `environment.json` và file cấu hình k6 đã dùng.

## 7. Ngưỡng đánh giá

| Pha | Ngưỡng |
|---|---|
| Pha 1 | **Không có ngưỡng độ trễ.** Baseline là giá trị đo được (`NFR-03`). Bắt buộc đạt: `NFR-01` 0 vi phạm bất biến, và `NFR-02` dưới 1% `5xx`+timeout ở L-01, L-02, L-03, L-05, L-06 |
| Pha 2 | Chốt **sau pilot baseline và trước khi chạy so sánh chính thức**: ví dụ giảm p95 ≥ 20% hoặc tăng throughput hữu ích ≥ 20% tại cùng mức tải và cùng ngân sách tài nguyên |

`L-04` cố ý tạo tranh chấp nên không áp ngân sách lỗi của `NFR-02`, nhưng vẫn áp `NFR-01`.

Nếu mục tiêu Pha 2 không đạt: báo cáo trung thực kết quả, nguyên nhân và giới hạn. Giả thuyết cải thiện không phải sự thật cho tới khi số liệu chứng minh.

## 8. Danh mục kiểm tra trước khi công bố số liệu

- [ ] Smoke test xanh trước mỗi lần đo
- [ ] I1–I7 trả 0 dòng sau mỗi lần đo
- [ ] Metadata môi trường đầy đủ, gồm commit SHA và profile dữ liệu
- [ ] Ma trận rút gọn giống hệt nhau cho hai phiên bản
- [ ] Thứ tự baseline/cải tiến được luân phiên giữa các lần lặp
- [ ] CPU của k6 được ghi lại và không bão hòa, hoặc giới hạn này được nêu rõ
- [ ] Tỉ lệ request thực tế của `L-05` được báo cáo bên cạnh tỉ lệ mục tiêu
- [ ] Kết quả thô đã commit hoặc có đường dẫn truy cập được ghi trong báo cáo
