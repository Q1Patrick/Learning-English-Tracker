# Kế hoạch ổn định và hoàn thiện Learning English Tracker

Ngày lập: 09/11/2026. Phạm vi: mã nguồn local trên `feature/database-features`, gồm các thay đổi AI feedback và quiz chưa commit.

Khi lập kế hoạch và bắt đầu triển khai, `AGENTS.md` đang trống. File đã được người dùng lưu nội dung trong lúc thực hiện; đã đọc lại và đối chiếu trước bàn giao. Phạm vi được duyệt là yêu cầu của người dùng thực hiện kế hoạch này; commit/push/merge, live AI và deployment vẫn chưa thực hiện. Trạng thái bàn giao: In Review, chờ người dùng xem diff và nghiệm thu.

Mục tiêu: sửa lỗi đã tái hiện, giúp cài đặt nhất quán, ghi nhận nguyên nhân lỗi rõ ràng và hoàn thiện luồng quiz.

Tiến độ sau triển khai: bộ verify đã qua 184 test, coverage 95%, migrations trên database mới và bản sao database hiện tại đều thành công. Đã kiểm tra bằng môi trường Python 3.9 cài mới với Django 4.2.30; CI cấu hình thêm Python 3.10–3.12. Test AI dùng mock; chưa gọi provider thật. Database nguồn giữ nguyên; chưa stage, commit hay push.

Theo yêu cầu kiểm tra trước commit của người dùng, mốc công việc ban đầu được lưu bằng snapshot code và SQLite backup ngoài repository thay cho commit tự động. Xem README và docs/MAINTENANCE.md để chạy lại kiểm tra.

## 1. Lưu mốc công việc hiện tại

- [x] Kiểm tra `git status --short --branch`, `git diff` và nội dung các file chưa được Git theo dõi.
- [ ] Lưu công việc hiện tại thành commit snapshot trên `feature/database-features`; bao gồm code, migrations, test và dependency cần thiết. Kiểm tra file được stage trước khi commit để loại `.env`, khóa bí mật, database và môi trường ảo.
- [ ] Push branch nếu cần bản sao trên GitHub. Ghi lại commit làm mốc quay lại.
- [x] Đọc lại `AGENTS.md` nếu vừa lưu hoặc bổ sung nội dung.

Hoàn thành khi: công việc hiện tại có mốc commit rõ ràng, danh sách file được lưu đã được kiểm tra, dữ liệu học tập local được giữ nguyên.

## 2. Làm cho môi trường cài đặt và cấu hình nhất quán

File chính: `requirements/base.txt`, `requirements/development.txt`, `requirements/production.txt`, `requirements.txt`, `config/settings/`, `config/wsgi.py`, `config/asgi.py`, `.github/workflows/django.yml`.

- [x] Chọn bộ `requirements/` làm nguồn khai báo dependency chính; bổ sung dependency AI theo phiên bản tương thích và kiểm tra cách cài bằng môi trường mới.
- [x] Để `requirements.txt` tham chiếu nguồn chính nếu tiếp tục giữ file này; production kế thừa dependency nền và khai báo thành phần triển khai thực sự cần dùng.
- [x] Chuyển `SECRET_KEY`, domain và cấu hình triển khai sang biến môi trường; thêm `.env.example` chỉ chứa giá trị mẫu. Nếu dùng `.env`, ghi rõ cơ chế nạp file.
- [x] Cấu hình rõ settings cho development, test và production. CI dùng khóa dành riêng cho test; AI được mock nên không cần khóa AI thật.
- [x] Xác định thông báo khi chức năng AI thiếu cấu hình; ghi rõ cách đặt `OPENAI_API_KEY` và `OPENAI_MODEL`.
- [x] Kiểm tra đường dẫn database: `BASE_DIR` hiện trỏ vào thư mục `config`. Nếu thay đổi cách tính đường dẫn, giữ rõ đường dẫn dữ liệu hiện có để tránh vô tình mở một database trống khác.

Hoàn thành khi: môi trường mới cài được dependency, `manage.py check` chạy được, bộ test qua, production dùng đúng settings và các cảnh báo triển khai được xử lý theo môi trường thực tế.

Commit đề xuất: `fix: align dependencies and environment configuration`.

## 3. Sửa lỗi API đã xác nhận và thêm test hồi quy

File chính: `apps/vocabulary/serializers.py`, `apps/vocabulary/views.py`, `apps/goals/serializers.py`, `apps/goals/views.py`, `apps/accounts/serializers.py`, các test tương ứng.

- [x] Viết test thể hiện lỗi trước khi sửa: tạo từ trùng, cập nhật từ thành từ đã tồn tại và cập nhật mục tiêu sang ngày đã có mục tiêu.
- [x] Trả HTTP 400 với lỗi tại trường liên quan; kiểm tra trùng theo đúng người dùng và bỏ qua chính bản ghi đang cập nhật.
- [x] Giữ constraint database để bảo vệ khi có request đồng thời. Xử lý đúng lỗi constraint trong transaction/savepoint phù hợp; để lỗi database khác được ghi nhận theo nguyên nhân thực tế.
- [x] Kiểm tra múi giờ bằng `ZoneInfo`; từ chối giá trị không hợp lệ ngay khi cập nhật hồ sơ.
- [x] Gói cập nhật User và Profile trong transaction để hai phần thành công hoặc thất bại cùng nhau.
- [x] Bổ sung test truy cập chéo người dùng cho API từ vựng, mục tiêu và phiên học.

Hoàn thành khi: các trường hợp trùng trả 400 thay vì 500, người dùng khác không đọc/sửa được dữ liệu, cập nhật hồ sơ không để dữ liệu ở trạng thái dở dang.

Commit đề xuất: `fix: validate duplicate records and profile updates`.

## 4. Dọn code và bổ sung khả năng debug

File chính: `apps/accounts/views.py`, `apps/accounts/urls.py`, `apps/ai_feedback/urls.py`, `common/exceptions.py`, cấu hình logging và test.

- [x] Giữ một khai báo `CurrentUserView`, một route hồ sơ và một route tạo AI; dọn import trùng hoặc không dùng.
- [x] Thiết lập logging theo module; dùng `logger.exception()` cho lỗi bất ngờ để lưu stack trace.
- [x] Gắn mã request vào log và phản hồi lỗi để đối chiếu một lần gọi cụ thể. Tránh ghi token, khóa API và toàn bộ nội dung bài viết vào log.
- [x] Định nghĩa mã lỗi ổn định, ví dụ `duplicate_record`, `invalid_timezone`, `ai_unavailable`; phân biệt lỗi đầu vào, lỗi dịch vụ ngoài và lỗi lập trình.
- [x] Ghi lại định dạng response hiện tại trước khi chuẩn hóa; cập nhật tài liệu và test hợp đồng cho những thay đổi ảnh hưởng client.
- [x] Bỏ lệnh in toàn bộ phản hồi đăng nhập trong `tests/test_jwt_authentication.py`.

Hoàn thành khi: mỗi lỗi bất ngờ có stack trace và mã đối chiếu; API vẫn giữ được hành vi đã kiểm thử sau khi dọn code.

Commit đề xuất: `refactor: simplify routes and improve error logging`.

## 5. Làm vững luồng AI feedback

File chính: `apps/ai_feedback/services.py`, `views.py`, `models.py`, `schemas.py`, `tests/test_ai_feedback_api.py`; bổ sung test service khi cần.

- [x] Đưa quy trình tạo bản ghi, gọi AI, lưu kết quả và cập nhật trạng thái vào service; view tập trung vào request, quyền truy cập và response.
- [x] Xử lý kết quả đã parse bị thiếu, phản hồi chưa hoàn tất, từ chối trả lời, lỗi cấu hình và lỗi kết nối. Ghi nhận lỗi bất ngờ bằng stack trace thay vì quy tất cả thành lỗi nhà cung cấp.
- [x] Đặt timeout và chính sách retry phù hợp; giới hạn lượt gọi theo người dùng. Xác định hành vi khi người dùng gửi lại một yêu cầu để kiểm soát việc xử lý và chi phí lặp.
- [x] Bổ sung test trạng thái `pending → completed` và `pending → failed`, đầu vào rỗng/quá dài, lịch sử, chi tiết và quyền truy cập chéo người dùng.
- [x] Nếu tải thực tế cần xử lý nền, thiết kế job và cơ chế khôi phục bản ghi pending bị treo. Transaction database chỉ bao quanh phần ghi dữ liệu cần nguyên tử, không kéo dài qua lời gọi mạng. Hiện giữ luồng đồng bộ có timeout; đã có lệnh thu hồi pending và cập nhật trạng thái có điều kiện. Worker nền là bước khi tăng tải.
- [ ] Kiểm tra thủ công một lời gọi AI thật trong môi trường phát triển khi có cấu hình phù hợp; ghi kết quả riêng với test dùng mock.

Hoàn thành khi: các tình huống lỗi có kết quả xác định và test; trạng thái bản ghi nhất quán; lời gọi thật được xác minh trước khi công bố chức năng hoạt động với nhà cung cấp.

Commit đề xuất: `fix: harden AI feedback processing`.

## 6. Hoàn thiện quiz theo một luồng nhỏ chạy được

File chính: `apps/quizzes/models.py`, `admin.py`, serializers, services, views, urls, migrations và test mới.

- [x] Bắt đầu với câu hỏi trắc nghiệm một đáp án. Ghi rõ các loại câu hỏi khác là phần phát triển sau nếu chưa có cách chấm tương ứng.
- [x] Tạo API danh sách đề đang hoạt động, chi tiết đề, nộp bài và xem kết quả/lịch sử của chính người dùng.
- [x] Backend tự tính điểm từ đáp án lưu trong database; dữ liệu gửi xuống trước khi nộp bài không chứa cờ đáp án đúng.
- [x] Bổ sung model lưu đáp án từng câu của lượt làm bài để xem lại kết quả. Chốt cách giữ lịch sử nếu đề hoặc đáp án được chỉnh sửa sau đó.
- [x] Thêm constraint phù hợp: điểm 0–100, số câu đúng không vượt tổng số câu và một câu chỉ được trả lời một lần trong một lượt. Kiểm tra dữ liệu hiện có trước khi áp dụng constraint mới.
- [x] Kiểm tra đáp án thuộc đúng câu và câu thuộc đúng đề; xử lý đề rỗng, đề ngừng hoạt động, câu bị bỏ sót và request nộp bài lặp.
- [x] Đăng ký admin để quản lý nội dung và kiểm tra điều kiện một đáp án đúng cho loại trắc nghiệm đã chọn.
- [x] Tạo migration mới cho thay đổi schema; giữ nguyên lịch sử migration đã được sử dụng.

Hoàn thành khi: người dùng lấy đề, nộp bài, nhận điểm do backend tính và xem lại đáp án; dữ liệu không hợp lệ bị từ chối; quyền riêng tư được kiểm thử.

Commit đề xuất: tách `feat: add quiz submission and answer history` và `test: cover quiz scoring and access control` nếu phạm vi lớn.

## 7. Phân trang và hoàn thiện hướng dẫn bảo trì

- [x] Bổ sung phân trang cho lịch sử AI, phiên học, mục tiêu và từ vựng; ghi rõ hình dạng response và cập nhật test/client liên quan.
- [x] Thêm lọc hoặc tìm kiếm theo nhu cầu đã có: ngày học, kỹ năng, từ khóa và mức thành thạo. Giữ lọc theo người dùng ở mọi truy vấn.
- [x] Viết README: phiên bản Python hỗ trợ, cài đặt, môi trường, migrations, chạy server, chạy test và ví dụ API.
- [x] Ghi ngắn cách lần theo lỗi: mã request → log → module → test tái hiện.
- [x] Đưa kiểm tra migration chưa tạo vào CI; cấu hình kiểm tra định dạng và lỗi tĩnh ở mức phù hợp với dự án.

Hoàn thành khi: người khác có thể làm theo README để chạy dự án trong môi trường mới và tìm được nguyên nhân một lỗi mẫu từ mã request.

Commit đề xuất: `chore: document setup and strengthen CI checks`.

## Thứ tự thực hiện và kiểm chứng

Đi theo bước 1 → 2 → 3 → 4 → 5 → 6 → 7. Trong mỗi bước, chia commit nhỏ theo hành vi thay đổi. Ghi lại kết quả kiểm tra trong mô tả commit hoặc PR; xử lý xong bước hiện tại trước khi mở rộng tính năng liên quan.

Các lệnh kiểm tra nền, chạy bằng Python của môi trường đã cài dependency:

```sh
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Chạy test liên quan trong lúc sửa; chạy toàn bộ bộ test trước khi kết thúc mỗi nhóm thay đổi. Kiểm tra production bằng settings và biến môi trường riêng:

```sh
python manage.py check --deploy --settings=config.settings.production
```

Chạy migrate và kiểm thử từ database mới trong môi trường tạm để xác nhận đầy đủ lịch sử migration. Chỉ áp dụng migrations lên dữ liệu đang dùng sau khi đã kiểm tra ảnh hưởng và có bản sao dữ liệu cần giữ.

Các branch cũ xử lý sau khi có mốc code ổn định: đối chiếu từng thay đổi còn cần thiết trong `feature/custom-user-model` và `feature/user-profile`, giải quyết xung đột model/migration trước khi đưa vào. Việc xóa branch đã merge là công việc dọn repository riêng.

Bước tiếp theo của người dùng: xem diff, chạy lại scripts/verify.py, stage các file đã xem, chạy verify với --staged rồi mới commit/push. Kiểm tra AI thật riêng khi có khóa/model; nâng nền Python/Django đang hết hỗ trợ thành thay đổi riêng trước khi triển khai công khai (xem docs/MAINTENANCE.md).
