# Person 3 — tiến độ và ràng buộc

Ngày: 10/11/2026. Branch: `feature/database-features`. Trạng thái chung: **In Review**; chưa nghiệm thu trên database thật và chưa commit/push.

## Những quyết định đã chốt

- Thống kê tính mọi lượt làm, gồm cả làm lại cùng đề. Trung bình theo điểm mỗi lượt, không trọng số theo số câu.
- Biểu đồ đủ 30 ngày theo múi giờ hồ sơ; ngày trống có count 0/average null, điểm 0 thực tế được giữ là 0.
- Giữ snapshot lịch sử khi đề/câu/lựa chọn nguồn thay đổi hoặc bị xóa. Choice được quản lý trong Question inline; lịch sử đáp án chỉ đọc trong Attempt.
- Hiện tại chỉ thử seed/migrations trên database tạm hoặc bản sao. Theo yêu cầu của người dùng, sau này bắt buộc kiểm chứng trên database thật của ứng dụng để dự án hoàn chỉnh hơn; cần backup, phê duyệt riêng và ghi kết quả thực tế. Ràng buộc này cũng đã được thêm vào Person3.md.

## Kết quả theo bước

| Bước | Công việc | Bằng chứng hiện có |
|---|---|---|
|1 — P3-11–15|Thêm 14 model/lifecycle tests; sửa lệnh test trong Person3/README|41 quiz tests PASS|
|2 — P3-16/17|5 đề mẫu/15 câu/60 lựa chọn, seed UUID5/version, dry-run và bỏ qua đề đã tồn tại|53 seed/API/model tests PASS, gồm 15 test seed mới|
|3 — P3-08/09|Ba index có query-plan evidence; migration learning0002/quiz0006|Thử 4.800 attempts + 4.800 sessions; 10 regression tests PASS; nâng bản sao DB hiện tại thành công, giữ integrity/FK/số dòng|
|4 — P3-21/22|Alias history và thống kê quiz ba truy vấn, đủ 30 ngày, điền ngày trống|34 API/statistics tests PASS, bao gồm DST và cách ly người dùng|
|5 — P3-23/24|Schema docs và ERD sửa được + PNG/SVG|Đã review đủ 10 model; PNG/SVG và nguồn JSON; root đã kiểm tra ảnh trực quan|
|6 — P3-25|Journey đăng ký/JWT → đề mẫu → nộp/replay → history → dashboard|227 tests PASS; coverage apps/common 96%; verify trên DB mới và bản sao PASS|
|7 — Nghiệm thu DB thật|Backup/maintenance window/áp dụng migrations và test luồng thật|Chưa thực hiện; chờ phê duyệt riêng|
|8 — P3-26|Review staging, commit và push|Chưa thực hiện; chờ phê duyệt riêng|

## Các phần phức tạp và vì sao

| Phần | Độ phức tạp | Ràng buộc hoặc việc cần chốt trước khi dùng thật |
|---|---|---|
|Thống kê thời gian|Ngày local và UTC khác nhau; DST tạo ngày23/25giờ; làm lại ảnh hưởng cách tính|Đã chốt mọi lượt/30ngày; totals toàn thời gian, chart theo local timezone|
|Lịch sử khi sửa/xóa nguồn|Quan hệ nguồn có thể mất nhưng điểm/đáp án cũ phải giữ ý nghĩa|Giữ snapshot và FK nullable SET_NULL; không sửa lịch sử đã chấm qua admin|
|Index/migration SQLite|Index tăng storage/chi phí ghi; tạo index hoặc nâng schema có thể khóa writers|Mới chứng minh query plan trên dữ liệu thử; cần thống nhất thời gian bảo trì và thời gian khóa tối đa trên DB thật|
|Seed chạy lại|Trùng dữ liệu hoặc ghi đè sửa tay có thể làm hỏng demo/lịch sử|UUID5 có version; skip nguyên đề đã tồn tại; không có chế độ reset/update ngầm|
|Nâng database thật|Schema cũ có thể chứa dữ liệu không hợp lệ hoặc lịch sử chưa có đáp án từng câu|Backup có thể phục hồi, thử bản sao, xử lý dữ liệu sai bằng quyết định riêng; không tự sửa/xóa dữ liệu thật|
|Tăng tải hoặc đổi database|Lock/query planner khác giữa SQLite và PostgreSQL; kết quả test hiện tại không chứng minh hạ tầng khác|Đo lại query plan và concurrency trên hạ tầng đích trước khi scale/chuyển DB|

## Lệnh kiểm tra

```sh
python manage.py test tests.test_person3_journey --settings=config.settings.test --verbosity=2
python scripts/verify.py --database-copy config/db.sqlite3
```

Chỉ sau khi tự xem diff và stage các file cần commit:

```sh
python scripts/verify.py --staged --database-copy config/db.sqlite3
```

Seed phát triển cần migration đầy đủ. Các lệnh seed trên DB thật, live AI, Git publishing và deployment chưa được thực hiện. Frontend, mở rộng loại câu hỏi và nâng framework major nằm ngoài đợt hoàn thiện Person3 này.

## Kiểm chứng cuối ngày 10/11/2026

`PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/verify.py --database-copy config/db.sqlite3` → PASS: 227 test, coverage apps/common 96%, 123 file Python qua lint/format, không có migration chưa tạo, fresh/copy migrations và production settings/WSGI/ASGI checks qua.

Database thật vẫn ở learning0001, quiz0004 và AI0001. Đã nâng bản sao qua learning0002, quiz0005/0006 và AI0002; integrity, foreign keys và số dòng dữ liệu học tập được giữ. Chưa áp dụng migrations/seed trên DB thật; chưa stage/commit/push, chưa gọi AI thật.
