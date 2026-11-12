# API v1

API dữ liệu yêu cầu `Authorization: Bearer <access-token>`. Health check và đăng ký/đăng nhập công khai. Endpoint kết thúc bằng `/`.

## Response

JWT giữ `access`, `refresh`, `user`. Hồ sơ, dashboard, tạo AI và chi tiết quiz dùng `{ "success": true, "data": ... }`. CRUD phiên học/mục tiêu/từ vựng và chi tiết AI giữ object serializer trực tiếp. DELETE thành công trả 204.

Danh sách đã đổi từ mảng sang phân trang DRF; client cần đọc `results`:

```json
{"count": 42, "next": "...page=2", "previous": null, "results": []}
```

Mặc định 20 bản ghi; `?page=2&page_size=50`, tối đa 100. Response có `X-Request-ID`. UUID đầu vào hợp lệ được giữ; giá trị khác được thay bằng UUID mới. Lỗi API dùng:

```json
{
  "success": false,
  "error": {"code": "duplicate_record", "message": "Check the submitted fields.", "details": {"word": ["You already have this word in your vocabulary."]}},
  "request_id": "d9428888-122b-11e1-b85c-61cd3cbb3210"
}
```

Client xử lý theo HTTP status và `error.code`; `error.details` chứa lỗi trường. Header xác thực và Retry-After của DRF được giữ. Lỗi ngoài DRF, ví dụ URL không tồn tại hoặc admin, có thể giữ HTML của Django nhưng vẫn có request ID.

## Tài khoản và học tập

| Method | Endpoint | Nội dung |
|---|---|---|
| GET | `/api/v1/health/` | Health check |
| POST | `/api/v1/auth/register/` | `email`, `password`, `password_confirm`; tên tùy chọn |
| POST | `/api/v1/auth/login/` | `email`, `password` → token |
| POST | `/api/v1/auth/token/refresh/` | `refresh` → access mới |
| POST | `/api/v1/auth/token/verify/` | `token` |
| GET/PATCH/PUT | `/api/v1/auth/me/` | Tài khoản và profile |
| GET/POST | `/api/v1/study-sessions/` | Phiên học cá nhân |
| GET/PATCH/PUT/DELETE | `/api/v1/study-sessions/{id}/` | Chi tiết phiên học |
| GET/POST | `/api/v1/goals/` | Mục tiêu ngày |
| GET/PATCH/PUT/DELETE | `/api/v1/goals/{id}/` | Chi tiết mục tiêu |
| GET/POST | `/api/v1/vocabulary/` | Từ vựng cá nhân |
| GET/PATCH/PUT/DELETE | `/api/v1/vocabulary/{id}/` | Chi tiết từ vựng |
| GET | `/api/v1/statistic/dashboard/` | Tiến độ hôm nay và tổng tuần |

Profile: `display_name`, `english_level` (A1–C2), `daily_target_minutes` (5–480), `learning_goal`, `timezone` (IANA). Email và trạng thái xác minh chỉ đọc. Phiên học: `activity_type`, `duration_minutes` (1–720), `score` (0–100, tùy chọn), `notes`, `studied_at`. Mục tiêu: `target_date`, `target_minutes`, `notes`.

Bộ lọc chỉ áp dụng trong dữ liệu của chính người dùng:

- Phiên học: `activity_type`, `date_from`, `date_to`, `search` trong ghi chú. Khoảng ngày bao gồm cả hai đầu theo múi giờ hồ sơ, kể cả ngày chuyển DST.
- Mục tiêu: `date_from`, `date_to`, `search` trong ghi chú.
- Từ vựng: `mastery_level`, `part_of_speech`, `search` trong từ/nghĩa/bản dịch/ví dụ/ghi chú.

Ví dụ: `/api/v1/study-sessions/?date_from=2026-11-01&date_to=2026-11-09&activity_type=reading`.

## Quiz statistics trong dashboard

`GET /api/v1/statistic/dashboard/` bổ sung `data.quiz_statistics`, giữ nguyên các trường thống kê học tập hiện có. Mọi phép tính chỉ dùng lịch sử của người đăng nhập và tính **mọi lượt làm bài**, kể cả làm lại cùng một đề.

| Field | Quy tắc |
|---|---|
| `total_completed` | Tổng lượt làm đã lưu, toàn thời gian |
| `average_score` | Trung bình điểm từng lượt, không trọng số theo số câu; làm tròn half-up một chữ số thập phân; `null` nếu chưa có lượt |
| `best_score` | Điểm cao nhất toàn thời gian, `null` nếu chưa có lượt |
| `recent_score` | Điểm lượt mới nhất theo `completed_at`, sau đó ID để thứ tự ổn định; `null` nếu chưa có lượt |
| `total_correct_answers` | Tổng số câu đúng của mọi lượt, toàn thời gian |
| `progress_over_time` | Đúng 30 ngày lịch, từ 29 ngày trước đến hôm nay theo `data.timezone` |

Mỗi ngày có `date` (ISO), `total_completed` và `average_score`. Ngày không làm bài có count `0`, average `null`; một bài thực sự được 0 điểm có average `0.0`. Chỉ biểu đồ bị giới hạn 30 ngày; tổng hợp vẫn tính toàn bộ lịch sử. Lịch sử còn lưu sau khi đề bị xóa/ngừng hoạt động tiếp tục được tính. Phút học vẫn được tính từ StudySession, không suy ra thời lượng từ quiz.

Service dùng ba truy vấn cho thống kê quiz (aggregate, lượt gần nhất, nhóm ngày), không truy vấn riêng cho mỗi ngày. Mốc ngày được chuyển từ múi giờ hồ sơ sang UTC trước khi lọc; phép nhóm ngày dùng cùng múi giờ, bao gồm cả DST.

## AI feedback

| Method | Endpoint | Nội dung |
|---|---|---|
| POST | `/api/v1/ai-feedback/` | `{"text":"I go to school yesterday."}`; 3–5000 ký tự sau trim |
| GET | `/api/v1/ai-feedback/history/` | Lịch sử cá nhân, phân trang |
| GET | `/api/v1/ai-feedback/{id}/` | Chi tiết phản hồi cá nhân |

Header tùy chọn `Idempotency-Key: <UUID>` bảo vệ gửi lại request tại ứng dụng. Lần đầu trả 201; cùng người dùng/khóa/text đã thành công trả lại bản ghi với 200, không gọi provider thêm. Khóa dùng cho text khác hoặc bản ghi pending trả 409. Bản ghi failed trả lỗi an toàn với 409; dùng khóa mới cho lần thử có chủ đích. Không gửi khóa nghĩa là tạo yêu cầu mới.

Luồng đồng bộ có timeout, mặc định không retry SDK. Bật `OPENAI_MAX_RETRIES` có thể lặp công việc bên provider sau timeout không rõ kết quả; idempotency của ứng dụng không bảo đảm provider xử lý đúng một lần.

Lỗi: `ai_not_configured` (503), `ai_timeout` (504), `ai_rate_limited` (503), `ai_unavailable` (503), `ai_configuration_error` (503), `ai_provider_request_error` (502), `ai_invalid_response` (502), `ai_incomplete_response` (502), `ai_refused` (422). Lỗi lập trình trả `internal_error` (500), có traceback an toàn trong log.

Mặc định 10 POST/giờ/người dùng, chỉnh qua `AI_FEEDBACK_THROTTLE_RATE`. Throttle DRF là giới hạn gần đúng; cache mặc định trong một process. Dùng cache chia sẻ và kiểm chứng hạ tầng khi chạy nhiều process/instance; không dùng throttle như sổ tính phí tuyệt đối.

## Quiz

| Method | Endpoint | Nội dung |
|---|---|---|
| GET | `/api/v1/quizzes/` | Đề đang hoạt động, phân trang |
| GET | `/api/v1/quizzes/{id}/` | Câu hỏi/lựa chọn, chưa lộ đáp án và giải thích |
| POST | `/api/v1/quizzes/{id}/submit/` | Nộp bài, nhận điểm backend tính |
| GET | `/api/v1/quizzes/attempts/` | Lịch sử cá nhân, phân trang |
| GET | `/api/v1/quizzes/history/` | Alias lịch sử theo Person3, cùng quyền và phân trang với `/attempts/` |
| GET | `/api/v1/quizzes/attempts/{id}/` | Kết quả và đáp án từng câu cá nhân |

Body:

```json
{"answers":[{"question_id":"<UUID>","choice_id":"<UUID>"}]}
```

Chỉ chấm `multiple_choice`, mỗi câu ít nhất hai lựa chọn và đúng một đáp án đúng. Phải trả lời mỗi câu đúng một lần, tối đa 1000 câu/request. Backend kiểm tra quan hệ đề/câu/lựa chọn và tự tính điểm. Điểm là phần trăm nguyên làm tròn gần nhất, .5 làm tròn lên.

`Idempotency-Key` tùy chọn là UUID: lần đầu 201, gửi lại cùng bộ đáp án 200, dùng khóa với bài khác 409. Đề không tồn tại/ngừng hoạt động trả 404; đề rỗng, cấu hình sai hoặc loại câu chưa hỗ trợ trả 409. Lịch sử lưu snapshot nên vẫn xem được khi nội dung gốc sửa/xóa. Lượt làm bài cũ có thể không có đáp án từng câu vì phiên bản trước chưa lưu.
