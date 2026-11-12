# Bảo trì, debug và nâng cấp

## Lần theo lỗi

1. Lấy `X-Request-ID` từ response hoặc `request_id` trong JSON lỗi.
2. Tìm `request_id=<UUID>` trong log. Log hoàn tất request ghi method, tên view, status và thời gian; lỗi bất ngờ ghi module, exception và vị trí stack.
3. Dùng HTTP status và `error.code` phân biệt lỗi đầu vào, dịch vụ ngoài và lập trình. Thêm test tái hiện trước khi sửa.
4. Chạy test liên quan, rồi chạy bộ verify trước khi kết thúc thay đổi.

Log không ghi request body, khóa API, token hoặc toàn bộ bài viết. Formatter giữ vị trí stack nhưng bỏ giá trị exception có thể chứa dữ liệu riêng tư. Dùng dữ liệu mẫu đã bỏ thông tin cá nhân khi tái hiện; không bật log SDK chứa payload trên production.

## Ranh giới code

- `views.py`: quyền truy cập, request và response.
- `serializers.py`: hợp đồng JSON/kiểm tra đầu vào; CRUD nhỏ giữ lưu dữ liệu sát model.
- `services.py`: nghiệp vụ nhiều bước, chấm quiz và trạng thái AI. Provider được gọi ngoài transaction database.
- `models.py`/migrations: tính toàn vẹn dữ liệu. Thay schema bằng migration mới; giữ migration đã sử dụng.
- `common/`: error envelope, request ID, phân trang, bộ lọc ngày/múi giờ và retry SQLite.
- `tests/`: hành vi, rollback, quyền truy cập, DST, migrations và request đồng thời.

Retry SQLite chỉ nhận lỗi khóa đã biết sau rollback, tối đa sáu lần. Callback không chứa lời gọi AI hay side effect ngoài database. Hết lượt retry vẫn ghi nhận lỗi. Khi đổi database/tăng tải, kiểm chứng transaction và lock trên database đích; test SQLite không chứng minh hành vi của PostgreSQL.

## Database

Database mặc định vẫn là `config/db.sqlite3`. Backup từng được Git theo dõi đã được giữ ở `local_backups/db.sqlite3.backup` (ignored); đường dẫn cũ là thay đổi xóa khỏi repository.

Trước khi migrate dữ liệu thật, tạo backup bằng SQLite backup API hoặc dừng ứng dụng trước khi sao chép file. Verify chỉ đọc nguồn, tạo bản sao tạm, migrate trên bản sao và kiểm tra integrity, foreign keys, số dòng học tập. Migration quiz dừng và chỉ rõ ID dữ liệu sai thay vì tự xóa dữ liệu.

Commit đầy đủ migrations AI `0001`/`0002`, quiz `0001`–`0005` cùng model. Database đã có migration đầu chỉ chạy phần chưa áp dụng. Lịch sử quiz cũ không thể tái tạo lựa chọn chưa từng được lưu.

## AI

Test tự động mock provider. Kiểm tra lời gọi thật riêng sau khi export khóa/model; lệnh sau phát sinh chi phí provider và không tạo bản ghi học tập:

```sh
python manage.py ai_feedback_smoke --text 'I go to school yesterday.' --english-level A1
```

Model được đặt rõ bằng `OPENAI_MODEL`. Cách parse đối chiếu với [OpenAI Docs](https://developers.openai.com/api/docs/guides/structured-outputs).

Thu hồi pending bị bỏ dở:

```sh
python manage.py expire_ai_feedback --older-than-minutes 60 --dry-run
python manage.py expire_ai_feedback --older-than-minutes 60
```

Lệnh từ chối khoảng thời gian quá ngắn so với timeout/retry; cập nhật trạng thái có điều kiện tránh kết quả muộn ghi đè bản ghi hết hạn. Khi cần worker nền, giữ hợp đồng trạng thái/idempotency hiện có.

## Nâng dependency

Nhánh này giữ tương thích Python 3.9 hiện có, cập nhật Django lên 4.2.30 và cấu hình CI trên Python 3.9–3.12. Django 4.2 hết hỗ trợ bảo mật ngày 07/04/2026 theo [Django](https://www.djangoproject.com/weblog/2026/apr/07/security-releases/). Cần chuyển sang Python/Django còn hỗ trợ trước khi triển khai công khai; test xanh không chứng minh dependency không có CVE.

Nâng major bằng thay đổi riêng:

1. Chọn Python được Django mục tiêu hỗ trợ; tạo môi trường mới, cập nhật CI.
2. Đọc release notes/deprecation; kiểm tra DRF, SimpleJWT, Pydantic, OpenAI SDK tương thích.
3. Sửa dependency trong `requirements/`; chạy test và migration trên bản sao, đặc biệt constraint, token, timezone, admin và đồng thời.
4. Kiểm chứng database/proxy/cache đích; chuẩn bị rollback và backup. Không tự chạy reverse migration có thể mất dữ liệu.

Có thể audit CVE riêng qua mạng bằng `pip-audit` trong môi trường audit tạm. Bộ verify offline không thay thế việc kiểm tra CVE.

## Trước commit

```sh
python -m pip install -r requirements/development.txt -r requirements/production.txt
python scripts/verify.py --database-copy config/db.sqlite3
git status --short
git diff --stat
git diff
```

Sau khi tự xem diff và stage thay đổi cần commit, chạy trên đúng nội dung index:

```sh
python scripts/verify.py --staged --database-copy config/db.sqlite3
git diff --cached --stat
git diff --cached
```

Chỉ commit khi verify báo PASS và diff phù hợp. `--staged` yêu cầu working tree khớp index, không còn file chưa theo dõi cần xét. Bộ quét khóa chỉ nhận diện một số mẫu phổ biến; vẫn cần tự xem diff. Các lệnh trên không tự commit/push.
