# Quy trình đóng góp

## Nhánh

- `main` chỉ nhận thay đổi qua pull request đã chạy CI xanh.
- `dev` là nhánh tích hợp trước khi hợp nhất vào `main`.
- Nhánh công việc dùng tiền tố `feat/`, `fix/`, `test/`, `docs/` hoặc `chore/`.

Việc tạo nhánh `dev` trên remote và bật branch protection cần được thực hiện trong phần cài đặt
repository bởi người có quyền quản trị.

## Commit

Thông điệp commit tuân theo Conventional Commits, ví dụ:

```text
feat(auth): add login endpoint
fix(booking): prevent duplicate seat hold
test(api): cover health endpoint
```

Các loại thường dùng: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci` và `build`.

## Pull request

- Giữ pull request nhỏ và tập trung vào một mục tiêu.
- Nêu cách kiểm tra thay đổi.
- Không hợp nhất khi CI đỏ hoặc còn secret trong diff.
