# Architecture Decision Records

Mỗi ADR ghi lại một quyết định kiến trúc: bối cảnh, các phương án đã cân nhắc, lựa chọn và hệ quả. ADR không bị sửa sau khi đã `Accepted`; muốn đổi quyết định thì viết ADR mới và đánh dấu ADR cũ là `Superseded by`.

| Mã | Quyết định | Trạng thái | Liên quan |
|---|---|---|---|
| [0001](0001-lua-chon-stack.md) | Lựa chọn stack: Python 3.12 + FastAPI + SQLAlchemy + Alembic + PostgreSQL | Accepted | Mục 8.1, mục 14 |
| [0002](0002-kiem-soat-dong-thoi-inventory-ghe.md) | Kiểm soát đồng thời cho inventory ghế | Accepted | BR-01, BR-03, BR-04, BR-08 |
| [0003](0003-xu-ly-het-han-hold.md) | Thu hồi hold hết hạn ngay trên đường ghi, không dùng tác vụ nền | Accepted | FR-08, BR-07 |
| [0004](0004-nguon-thoi-gian-quyet-dinh.md) | Nguồn thời gian quyết định là `clock_timestamp()` của PostgreSQL | Accepted | BR-05, BR-13 |
| [0005](0005-xac-thuc-jwt.md) | Xác thực JWT HS256, không có giới hạn tần suất | Accepted | FR-01, AS-08, RI-10 |
| 0006+ | Cải tiến Pha 2 | Chưa viết | Mục 11 |

ADR của Pha 2 phải có sơ đồ kiến trúc trước/sau, giả thuyết đo được và cách giữ nguyên các bất biến (mục 11.1).

Mẫu: [0000-template.md](0000-template.md).
