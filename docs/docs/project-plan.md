# Kế hoạch thực hiện

Chi tiết hóa các mốc M1–M6 ở mục 12.3 của [requirements.md](../requirements.md) thành công việc có điều kiện hoàn thành kiểm chứng được.

## 1. Nguyên tắc sắp xếp thứ tự

Thứ tự dưới đây không theo độ dễ mà theo **rủi ro**. Ba việc được kéo lên sớm hơn trực giác thông thường:

| Việc | Bị kéo lên vì |
|---|---|
| Kiểm chứng môi trường Kaggle | RI-02: nếu Internet bị tắt và không mở được, toàn bộ mục 10 sụp đổ. Phát hiện ở M1 còn xoay được; phát hiện ở M4 thì không |
| Kiểm thử phụ thuộc kiến trúc (import-linter) | RI-07: ranh giới kiến trúc bị vi phạm dần. Thêm ở M2 tốn một buổi; retrofit ở M6 là viết lại |
| `T-07`, `T-08`, `T-25` | RI-05: nếu cơ chế chống tranh chấp sai, sửa nó kéo theo đổi schema và viết lại kiểm thử. Phải biết sớm nhất có thể |

## 2. M1 — Chốt nền tảng và kiểm chứng môi trường

**Mục tiêu:** loại bỏ những rủi ro có thể giết dự án, trước khi viết nghiệp vụ.

| Việc | Kết quả |
|---|---|
| Chốt stack, viết ADR-0001 | `docs/adr/0001-*.md` ở trạng thái Accepted |
| Skeleton Python + FastAPI, các package `api`/`domain`/`infrastructure`/`bootstrap` | `uv run fastapi dev app/main.py` chạy được |
| Alembic baseline theo [data-model.md](data-model.md) | `uv run alembic upgrade head` tạo được schema đầy đủ |
| `Dockerfile` + `compose.yaml` + `.env.example` | Khởi động sạch, `GET /health/ready` trả `200` |
| **Thử chạy thật trên Kaggle**: cài Python dependency, PostgreSQL 16 và k6 trong notebook | Notebook chạy được ba tiến trình và gọi được một endpoint |
| **Pilot đo thời gian** một tổ hợp kịch bản/mức tải | Con số thật để chốt ma trận rút gọn ở M4 |

**Điều kiện hoàn thành**

- [ ] Từ môi trường sạch, `docker compose up` → `/health/ready` = `200` trong dưới 120 giây (`NFR-04`)
- [ ] Notebook Kaggle chạy được backend + DB + k6, hoặc **rủi ro RI-02 đã được ghi nhận kèm phương án dự phòng cụ thể**
- [ ] Có số đo thời gian thực của một lần chạy đầy đủ, gồm cả reset

> Nếu Internet trên Kaggle không mở được: đóng gói Python wheelhouse, binary PostgreSQL và k6 thành Kaggle Dataset và kiểm chứng đường cài đặt offline **ngay trong M1**. Không chuyển sang M2 khi câu hỏi này còn bỏ ngỏ.

## 3. M2 — Danh mục, đăng nhập, phân tầng, OpenAPI

| Việc | Kết quả |
|---|---|
| FR-01 đăng nhập: bcrypt, PyJWT HS256, `JwtAuthMiddleware` | `T-01`, `T-02`, `T-23` xanh |
| FR-02, FR-03, FR-04 danh mục và sơ đồ ghế | `T-03`, `T-29` xanh |
| Port + adapter: repository, `UnitOfWork`, `Clock` (ADR-0004) | `PostgresClock` dùng cùng SQLAlchemy Session; unit test dùng clock giả |
| **import-linter trong CI** | `T-28` xanh và thực sự fail khi cố tình vi phạm |
| Seed 10 phim / 3 phòng / 60 suất / 200 tài khoản, có `showtime_seat` đầy đủ | `scripts/seed.sh` chạy xác định theo `SEED_RANDOM_SEED` |
| FastAPI OpenAPI + Swagger UI, đối chiếu `docs/api/openapi.yaml` | `/openapi.json` khớp spec đã commit |
| Hợp đồng lỗi mục 6.4, `requestId` xuyên suốt | `T-27` xanh; `NFR-07` kiểm được trong smoke test |

**Điều kiện hoàn thành**

- [ ] `T-01`, `T-02`, `T-03`, `T-23`, `T-27`, `T-28`, `T-29` xanh trong CI
- [ ] Cố tình thêm `import fastapi` hoặc `import sqlalchemy` vào `app.domain` → CI **fail**
- [ ] Swagger UI cho nhập token và gọi thử được endpoint cần đăng nhập
- [ ] Invariant I7 (mọi cặp suất–ghế có dòng inventory) trả 0 dòng sau seed

## 4. M3 — Booking, transaction, quyền sở hữu, đồng thời

Mốc nặng nhất và rủi ro nhất.

| Việc | Kết quả |
|---|---|
| FR-05 giữ ghế theo ADR-0002: sort `seatId` → `FOR UPDATE` → SQLAlchemy Core `UPDATE … WHERE` → xét `result.rowcount` | `T-04`, `T-05`, `T-06` xanh |
| BR-11 giới hạn hold | `T-22` xanh |
| FR-06 xác nhận, gồm nhánh idempotent và thứ tự kiểm tra cố định | `T-09`, `T-10`, `T-18` xanh |
| FR-07 hủy, gồm nhánh idempotent | `T-11`, `T-12` xanh |
| FR-08 hết hạn theo ADR-0003: thu hồi ở đường ghi, suy ra ở đường đọc | `T-14`, `T-19` xanh |
| FR-09 xem booking cá nhân, lọc theo trạng thái hiệu lực trong một truy vấn | `T-13`, `T-24` xanh |
| Ánh xạ lỗi hạ tầng → `409` trong repository | Không có `5xx` nào trong toàn bộ kiểm thử tranh chấp |
| **Kiểm thử đồng thời** với testcontainers-python và `ThreadPoolExecutor` | `T-07`, `T-08` (100 vòng), `T-15`, `T-16`, `T-17`, `T-25` xanh |
| `scripts/check-invariants.sql` | I1–I7 trả 0 dòng sau mọi bài kiểm thử đồng thời |

**Điều kiện hoàn thành**

- [ ] Toàn bộ `T-01` … `T-29` xanh
- [ ] `T-08` chạy 100 vòng không deadlock, không `5xx`
- [ ] Xóa thử lệnh sắp xếp `seatId` → `T-08` **fail** (chứng minh bài kiểm thử có tác dụng thật)
- [ ] `scripts/smoke.sh` xanh trên môi trường Docker sạch
- [ ] Gắn tag `phase1-baseline`

## 5. M4 — Baseline trên Kaggle và bàn giao Pha 1

| Việc | Kết quả |
|---|---|
| Kịch bản k6 cho `L-01`…`L-06`, có công thức phân bổ ghế theo VU | `benchmarks/` chạy lại được |
| Chốt **ma trận rút gọn** dựa trên pilot M1 | Ghi trong báo cáo kèm lý do |
| Chạy baseline theo quy trình mục 3 của [benchmark-plan.md](benchmark-plan.md) | Kết quả thô + `environment.json` cho mỗi lần chạy |
| Báo cáo baseline: bảng chi tiết + bảng tổng hợp trung vị/độ dao động | `docs/reports/baseline.md` |
| Phân tích điểm nghẽn làm căn cứ cho Pha 2 | Nêu rõ chỉ số nào chưa thu được |

**Điều kiện hoàn thành**

- [ ] Số liệu **thực sự chạy trên Kaggle CPU**, không phải kết quả local báo cáo thay
- [ ] `NFR-01`: 0 vi phạm bất biến ở mọi mức tải
- [ ] `NFR-02`: dưới 1% `5xx`+timeout ở L-01, L-02, L-03, L-05, L-06
- [ ] Toàn bộ 8 mục trong danh sách kiểm tra ở mục 9.2 đặc tả được tick
- [ ] Đã ghi rõ CPU của k6 và liệu client có phải điểm nghẽn không

## 6. M5 — Cải tiến Pha 2

| Việc | Kết quả |
|---|---|
| Chọn một hướng cải tiến từ mục 11.2 dựa trên **số liệu**, không dựa trên linh cảm | Giả thuyết viết ra trước khi code |
| Chốt ngưỡng đánh giá chính trước khi chạy so sánh | Ghi trong ADR |
| ADR-0006+ với sơ đồ trước/sau và cách giữ nguyên bất biến | `docs/adr/` |
| Triển khai và chạy lại **toàn bộ** kiểm thử correctness | `T-01`…`T-29` (+ `T-30` nếu có cache) xanh |
| Đo lại trên cùng ma trận, cùng dữ liệu, cùng ngân sách tài nguyên | Kết quả thô + báo cáo so sánh |

**Điều kiện hoàn thành**

- [ ] `NFR-01` vẫn 0 vi phạm — điều kiện chặn, số liệu đẹp không bù được
- [ ] Nếu có cache: `T-30` xanh, chứng minh BR-10
- [ ] Biến kiểm soát (pool, worker, timeout) giữ nguyên, hoặc chênh lệch được khai báo và đo riêng
- [ ] Gắn tag `phase2-<tên-cải-tiến>`
- [ ] Kết luận nêu **cả** số tuyệt đối lẫn phần trăm; nếu không đạt mục tiêu thì báo cáo trung thực

## 7. M6 — Hoàn thiện và kiểm tra tái lập

| Việc | Kết quả |
|---|---|
| README đủ các mục 12.2, gồm giả định và rủi ro còn hiệu lực | `README.md` |
| Kiểm tra tái lập từ môi trường sạch **bởi người không viết phần đó** | Biên bản kiểm tra |
| Rà secret trong toàn bộ lịch sử commit | gitleaks hoặc `git log -p` rà thủ công: 0 phát hiện |
| Đối chiếu ma trận 13.2: mọi FR/NFR/BR có kiểm thử hoặc lý do rõ ràng | Không ô trống |

**Điều kiện hoàn thành**

- [ ] Một thành viên clone mới, đọc README và chạy được tới bước đặt vé mẫu, không cần hỏi ai
- [ ] Không có `.env`, token, mật khẩu thật hay dữ liệu cá nhân thật trong lịch sử commit
- [ ] Có commit ở cả sáu mốc; không có commit nào gộp toàn bộ dự án
- [ ] Mọi `TODO` trong README đã được điền

## 8. Bám sát rủi ro

Rà lại bảng 15.3 của đặc tả ở cuối mỗi mốc. Mỗi rủi ro được đánh dấu **đã đóng**, **còn mở** hoặc **đã xảy ra**; rủi ro đã xảy ra phải ghi lại việc thực tế đã làm gì.

| Mốc | Rủi ro phải được trả lời |
|---|---|
| M1 | RI-02 (Internet Kaggle), RI-01 (ngân sách thời gian) |
| M2 | RI-07 (ranh giới kiến trúc) |
| M3 | RI-05 (cơ chế chống tranh chấp) |
| M4 | RI-03 (client là điểm nghẽn), RI-04 (nhiễu), RI-06 (hold mồ côi), RI-10 (tải đăng nhập) |
| M5 | RI-08 (cải tiến phá vỡ bất biến) |
| M6 | RI-09 (dồn commit) |

## 9. Quy ước Git

- Commit nhỏ, thông điệp mô tả **thay đổi gì và vì sao**, không phải "update".
- Nhánh theo mốc: `m2/auth-and-catalog`, `m3/booking-concurrency`.
- Tag cho mọi phiên bản được đo: `phase1-baseline`, `phase2-<tên>`. Báo cáo phải dẫn được commit SHA.
- Không commit `.env`, khóa ký, mật khẩu thật, dữ liệu cá nhân thật.
- Mỗi PR vào nhánh chính phải có CI xanh, gồm `lint-imports`, Alembic checks và kiểm thử đồng thời.
