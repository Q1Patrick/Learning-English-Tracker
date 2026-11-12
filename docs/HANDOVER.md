TASK: TV1/TV3/TV4 — Triển khai kế hoạch ổn định backend, AI và quiz
BRANCH: feature/database-features
STATUS: In Review

## 1. Hiện trạng và nguyên nhân

Đầu vào là worktree đang có AI/quiz chưa commit. Đã giữ các thay đổi đó và lưu snapshot code/SQLite trước khi sửa tại `/private/tmp/english-tracker-before-implementation-zldsn37c`. AGENTS.md ban đầu trống; người dùng lưu nội dung trong khi triển khai, đã đọc lại trước bàn giao. Luồng thực tế hiện tại: HTTP → URL → View/permissions → Serializer → Service hoặc Model → SQLite → Response. Chưa có frontend trong phạm vi này.

## 2. Các file đã đọc

AGENTS.md, IMPLEMENTATION_PLAN.md, cấu hình/dependency/CI, các URL/view/serializer/model/migration/test thuộc accounts, learning, goals, statistic, vocabulary, ai_feedback và quizzes. Đã đối chiếu Git state, lịch sử và diff, kiểm tra các file mới chưa được Git theo dõi.

## 3. Kế hoạch và phạm vi được duyệt

Nguồn phê duyệt là yêu cầu của người dùng thực hiện IMPLEMENTATION_PLAN.md và bàn giao lệnh kiểm tra trước commit. Công việc bao gồm sửa API, cấu hình, logging, AI, quiz, test, migrations, CI và tài liệu; ngoài phạm vi là frontend, đổi database, nâng framework major, live AI, deployment và Git publishing.

| Workstream | Owner | Deliverables | Trạng thái |
|---|---|---|---|
| Ổn định cấu hình/auth | TV1 | Env settings, email/profile validation, JWT regression tests | In Review |
| Core CRUD/thống kê | TV3 | Duplicate/race handling, filters, timezone, ownership tests | In Review |
| AI writing feedback | TV4 | Provider boundary, lifecycle, quota, idempotency/recovery | In Review |
| Quiz | TV3 | Server scoring, snapshots, constraints, private history | In Review |
| QA/Docs | TV4 | Verification script, coverage, CI, API/maintenance docs | In Review |

Không có deadline được giao. Các phần triển khai phụ thuộc cấu hình chung; bàn giao sau kiểm thử tích hợp. Việc chia agent là cách phân công triển khai/review; bằng chứng nghiệm thu là lệnh và test thực chạy, không phải sự tự xác nhận của agent.

## 4. Các file thực tế có thay đổi

Danh sách dưới đây gồm công việc local đầu vào được giữ và thay đổi sau triển khai. Có định dạng/import cleanup cho các module trong phạm vi để lint/format thống nhất. AGENTS.md là nội dung do người dùng lưu, không do tác vụ này sửa.

- `.env.example`
- `.github/workflows/django.yml`
- `.gitignore`
- `IMPLEMENTATION_PLAN.md`
- `README.md`
- `apps/accounts/admin.py`
- `apps/accounts/apps.py`
- `apps/accounts/managers.py`
- `apps/accounts/models.py`
- `apps/accounts/serializers.py`
- `apps/accounts/tests/test_jwt_authentication.py`
- `apps/accounts/urls.py`
- `apps/accounts/views.py`
- `apps/ai_feedback/admin.py`
- `apps/ai_feedback/apps.py`
- `apps/ai_feedback/management/__init__.py`
- `apps/ai_feedback/management/commands/__init__.py`
- `apps/ai_feedback/management/commands/ai_feedback_smoke.py`
- `apps/ai_feedback/management/commands/expire_ai_feedback.py`
- `apps/ai_feedback/migrations/0001_initial.py`
- `apps/ai_feedback/migrations/0002_feedback_idempotency.py`
- `apps/ai_feedback/models.py`
- `apps/ai_feedback/schemas.py`
- `apps/ai_feedback/serializers.py`
- `apps/ai_feedback/services.py`
- `apps/ai_feedback/tests.py`
- `apps/ai_feedback/throttles.py`
- `apps/ai_feedback/urls.py`
- `apps/ai_feedback/views.py`
- `apps/goals/admin.py`
- `apps/goals/apps.py`
- `apps/goals/models.py`
- `apps/goals/serializers.py`
- `apps/goals/tests.py`
- `apps/goals/urls.py`
- `apps/goals/views.py`
- `apps/learning/admin.py`
- `apps/learning/apps.py`
- `apps/learning/models.py`
- `apps/learning/serializers.py`
- `apps/learning/tests.py`
- `apps/learning/urls.py`
- `apps/learning/views.py`
- `apps/quizzes/__init__.py`
- `apps/quizzes/admin.py`
- `apps/quizzes/apps.py`
- `apps/quizzes/migrations/0001_initial.py`
- `apps/quizzes/migrations/0002_question.py`
- `apps/quizzes/migrations/0003_choice.py`
- `apps/quizzes/migrations/0004_quizattempt.py`
- `apps/quizzes/migrations/0005_attempt_answer_history_and_constraints.py`
- `apps/quizzes/migrations/__init__.py`
- `apps/quizzes/models.py`
- `apps/quizzes/serializers.py`
- `apps/quizzes/services.py`
- `apps/quizzes/tests.py`
- `apps/quizzes/urls.py`
- `apps/quizzes/views.py`
- `apps/statistic/admin.py`
- `apps/statistic/apps.py`
- `apps/statistic/models.py`
- `apps/statistic/serializers.py`
- `apps/statistic/services.py`
- `apps/statistic/tests.py`
- `apps/statistic/urls.py`
- `apps/statistic/views.py`
- `apps/vocabulary/admin.py`
- `apps/vocabulary/apps.py`
- `apps/vocabulary/models.py`
- `apps/vocabulary/serializers.py`
- `apps/vocabulary/tests.py`
- `apps/vocabulary/urls.py`
- `apps/vocabulary/views.py`
- `common/database.py`
- `common/environment.py`
- `common/exceptions.py`
- `common/filters.py`
- `common/logging.py`
- `common/middleware.py`
- `common/pagination.py`
- `common/timezones.py`
- `config/asgi.py`
- `config/db.sqlite3.backup`
- `config/settings/base.py`
- `config/settings/development.py`
- `config/settings/production.py`
- `config/settings/test.py`
- `config/urls.py`
- `config/wsgi.py`
- `docs/API.md`
- `docs/MAINTENANCE.md`
- `manage.py`
- `pyproject.toml`
- `requirements.txt`
- `requirements/base.txt`
- `requirements/development.txt`
- `requirements/production.txt`
- `scripts/verify.py`
- `tests/test_ai_feedback_api.py`
- `tests/test_ai_feedback_lifecycle.py`
- `tests/test_ai_feedback_model.py`
- `tests/test_ai_feedback_services.py`
- `tests/test_authentication.py`
- `tests/test_configuration.py`
- `tests/test_current_user_profile.py`
- `tests/test_daily_goal_api.py`
- `tests/test_daily_goal_model.py`
- `tests/test_dashboard_statistics_api.py`
- `tests/test_database.py`
- `tests/test_jwt_authentication.py`
- `tests/test_learning.py`
- `tests/test_list_filters.py`
- `tests/test_observability.py`
- `tests/test_quiz_api.py`
- `tests/test_quiz_concurrency.py`
- `tests/test_quiz_migrations.py`
- `tests/test_quiz_models.py`
- `tests/test_study_session_model.py`
- `tests/test_verification.py`
- `tests/test_vocabulary_api.py`
- `tests/test_vocabulary_model.py`

## 5. Kết quả kiểm chứng thực chạy

Môi trường cài mới: `/private/tmp/english-tracker-validation-21gljq33`, Python 3.9.6, Django 4.2.30. Dependency development và production được cài thành công. Môi trường venv sẵn có của người dùng không bị nâng package bởi tác vụ này.

- `python -m ruff check .` → PASS.
- `python -m ruff format --check .` → PASS, 114 file Python.
- `python scripts/verify.py --database-copy config/db.sqlite3` → PASS.
- Bộ verify chạy `pip check`, Django check, migration dry-run, 184 test, coverage apps/common 95%, migration từ database mới và bản sao database thật, integrity/foreign-key/row-count checks, production deploy checks với key/domain giả và import WSGI/ASGI.
- Migration trên bản sao database hiện tại áp dụng AI0002 và quiz0005 thành công; database nguồn không bị migrate.
- Regression tests có request đồng thời bằng hai kết nối SQLite, permission, lỗi provider, rollback, DST, dữ liệu cũ và kiểm tra Git index trong repository tạm.
- `git diff --check`, `git diff --stat`, diff của các phần logic/settings và `git status --short` → đã xem; không sửa migration cũ của accounts/goals/learning/vocabulary.
- `verify --staged` trên repository thật → NOT RUN, vì chưa stage code; cơ chế đã được kiểm tra bằng các repository tạm trong test.
- GitHub CI matrix Python3.10–3.12 → NOT RUN ở máy local; workflow đã cấu hình, chưa push để kích hoạt.
- Lời gọi AI thật, kiểm tra hạ tầng deployed, CVE audit qua mạng → NOT RUN.

## 6. Review API/database/security

Đã sửa dữ liệu trùng thành lỗi400 có mã ổn định, giữ constraint chống race và dùng savepoint trước khi chuyển lỗi. Cập nhật User/Profile nguyên tử. Thêm request ID, traceback giữ vị trí nhưng không lộ exception payload, phân loại lỗi và bỏ in token. Secret lấy từ môi trường; không đưa khóa thật vào code mới.

API list đổi từ mảng sang `{count,next,previous,results}`; client cần đọc results. Error response đổi sang envelope có code/details/request_id. Hợp đồng được ghi trong docs/API.md. Schema mới lưu idempotency AI/quiz và snapshot đáp án; migration preflight không tự xóa dữ liệu sai. Cơ chế SQLite chỉ retry lỗi khóa đã biết sau rollback; provider nằm ngoài retry/transaction.

Backup cũ được giữ nguyên ở ignored `local_backups/db.sqlite3.backup`; đường dẫn Git cũ đang là thay đổi xóa. Lịch sử Git vẫn có thể chứa secret/backup cũ: cần thay khóa trước triển khai; xử lý lịch sử là việc riêng có phê duyệt.

## 7. Giới hạn và bước tiếp theo

Đọc diff và API compatibility notes, chạy lại verify trong venv của bạn, stage những file đã xem, rồi chạy verify --staged trước commit. Khi sử dụng schema mới, tạo backup và chạy migrate theo README; tác vụ này chỉ migrate bản sao/tạm.

Chạy AI smoke riêng khi có khóa/model hợp lệ; lệnh phát sinh chi phí. Throttle cache mặc định gần đúng theo process; cần cache chia sẻ khi scale. Chỉ quiz multiple_choice được chấm. Dữ liệu legacy chưa lưu lựa chọn không có đáp án lịch sử để khôi phục.

Django4.2/Python3.9 là nền cũ: đã đưa patch4.2 lên4.2.30 nhưng chưa nâng major; cần chuyển sang nền còn được hỗ trợ trước triển khai công khai. Xem nguồn chính thức và lộ trình tại docs/MAINTENANCE.md.

## 8. Kiến thức cần hiểu

- Serializer kiểm tra dữ liệu HTTP trước khi lưu; constraint database là bảo vệ cuối khi request đồng thời.
- Transaction/savepoint giúp nhiều thao tác thành công hoặc rollback cùng nhau; bắt lỗi sau rollback giữ kết nối sử dụng được.
- Idempotency key cho phép gửi lại cùng yêu cầu mà không tạo thêm kết quả hoặc gọi provider thêm tại ứng dụng.
- Request ID liên kết response với log; stack trace cho biết module/vị trí lỗi mà không cần ghi dữ liệu riêng tư.
- Migration là lịch sử thay đổi schema; kiểm chứng trên bản sao dữ liệu trước khi áp dụng vào database đang dùng.

GIT: Chưa stage, commit, push hoặc merge. Trạng thái In Review chờ người dùng xem diff và nghiệm thu; không tuyên bố đã deploy hoặc production-ready.
