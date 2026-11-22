# Learning English Tracker — Frontend

React + TypeScript + Vite. FE-03.5 đã chuyển luồng web sang Django server-side session: AuthContext quản lý user, khôi phục khi F5, Remember me và Logout thật phía server. Cookie HttpOnly do browser quản lý; web không nhận JWT. Django5.2 LTS; JWT API cũ được giữ tương thích. Dashboard còn là trang khung công khai, Protected Routes thuộc FE-03.6. Các mục FE-03.2–03.4 bên dưới là lịch sử; xem mục FE-03.5 cho hành vi/lệnh hiện tại.

## Chạy và kiểm tra

Trong PowerShell, từ thư mục gốc project:

```powershell
Set-Location .\frontend
npm.cmd run dev
```

Mở URL terminal in ra, ví dụ thêm `/dashboard` hoặc `/profile`. Ctrl+C dừng server của bạn.

Trong terminal khác tại `frontend`:

```powershell
npm.cmd run lint
npm.cmd run build
npm.cmd run preview -- --host 127.0.0.1
```

Lint kiểm tra source; build kiểm tra TypeScript và xuất `dist/`; preview xem thử bản build local. Project chưa có script `test`; `check:api` bên dưới kiểm tra HTTP thật, không dùng test framework. Máy mới cần Node/npm và `npm.cmd ci` theo lockfile; không cần cài lại dependency sau mỗi sửa nhỏ.

## FE-03.2 — API client và development proxy

`src/shared/api/client.ts` cung cấp `apiClient.request<T>(endpoint, options)` và `createApiClient({ baseUrl })`. Endpoint tương đối, ví dụ `health/` hoặc `auth/me/`, được ghép dưới `/api/v1/`; client giữ nguyên JSON trả về, không tự lấy `.data`.

Options hỗ trợ method, JSON body, AbortSignal và accessToken được truyền rõ khi cần Bearer. Mặc định không gửi token/cookie, không lưu token và không tự refresh/retry. API auth công khai phải dùng mặc định này. Các lỗi có kind, status, code, details và requestId; không dump token/password vào log. HTTP error, lỗi mạng, response không hợp lệ và hủy request được phân biệt.

`frontend/.env.example` ghi hai cấu hình, có giá trị mặc định hoạt động mà không cần copy thành `.env`:

| Biến | Giá trị mặc định | Ý nghĩa |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1/` | Công khai trong browser/bundle; không chứa secret |
| `DEV_API_TARGET` | `http://127.0.0.1:8000` | Origin Django cho Vite dev/preview, không kèm path `/api/v1/` |

Khởi động lại Vite khi đổi cấu hình. Proxy giữ nguyên `/api/v1/...`, không rewrite mất prefix. Endpoint không được vượt origin hoặc API root đã cấu hình. Vite preview kế thừa proxy; build `dist/` không chứa server proxy, hosting production vẫn cần routing riêng.

### Double-check bằng Django thật, không tạo dữ liệu

Terminal 1 tại gốc project, sau khi Python/dependency đã sẵn sàng:

```powershell
.\.venv\Scripts\python.exe manage.py check --settings=config.settings.test
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.settings.test --noreload
```

Đây là cấu hình test có sẵn với SQLite trong bộ nhớ, chỉ phục vụ kiểm tra transport/validation/anonymous access. Không dùng cho tài khoản thật hoặc production. Cảnh báo unapplied migrations ở server này là dự kiến: các case bên dưới không cần bảng ứng dụng, không chạy migration và không tạo user/token. Bước Login thật sau này cần môi trường development/database được chuẩn bị riêng.

Terminal 2 tại gốc project:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Mở `http://127.0.0.1:5173/api/v1/health/?format=json`: phải nhận JSON có `status: healthy`. Query format=json giúp trình duyệt hiển thị JSON trực tiếp. Terminal 3 tại gốc project:

```powershell
npm.cmd --prefix frontend run check:api -- --save
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
```

`check:api` chạy cùng TypeScript client của frontend, qua Vite tới Django thật. Script đã được kiểm tra với Node26.13.1 có hỗ trợ chạy TypeScript trực tiếp. Kết quả HTTP lưu tại `docs/qa/fe-03.2/http-results.json` khi thêm `--save`; bỏ cờ này nếu chỉ muốn xem kết quả terminal. Có thể đặt `API_VERIFY_BASE_URL` cho script khi Vite chạy ở cổng khác. Dừng từng server do bạn khởi động bằng Ctrl+C.

Các case kiểm tra: health/query, me401, register/login/refresh thiếu trường400, HTML404, format không phù hợp406, cancellation và URL không được vượt API root. Body `{}` chỉ kiểm tra lỗi thiếu dữ liệu, không tạo tài khoản. Client không giả lập response hoặc server. Runner này chưa kiểm tra success không phải JSON/JSON hỏng hoặc204/205. Kiểm tra riêng đã xác nhận HTML200 thật từ Django admin bị phân loại invalid-response và backend đã dừng gây network error an toàn; xem protocol-results.json trong minh chứng.

Để kiểm tra trực tiếp trong Console của tab frontend đang chạy Vite:

```js
const { apiClient } = await import('/src/shared/api/client.ts')
await apiClient.request('health/')
```

Kết quả thành công là JSON thật từ Django. API client không làm thay đổi giao diện hiện tại. Bearer hợp lệ, Login/Refresh thành công và Profile sẽ kiểm tra cùng các task auth tiếp theo; không suy từ health PASS thành auth đã hoàn thành.

### Kết quả kiểm tra ngày19/11/2026

- Django check với settings.test: PASS.
- check:api:12/12 checks PASS, gồm9 HTTP thật qua Vite và3 kiểm tra cancellation/URL/config tại client.
- Chrome profile riêng:15 checks PASS, gồm9 client checks và6 smoke layout cho Dashboard/Login/Profile tại375/1487px. Các request API của client không tự gửi Authorization hoặc Cookie.
- Lint/build: PASS; không thêm dependency frontend hoặc thay lockfile.
- Kiểm tra protocol riêng:2/2 PASS cho Django HTML200 và kết nối tới backend đã dừng.
- FE-03.2 hoàn thành kỹ thuật, chờ người dùng double-check; các bước auth còn lại chưa triển khai.

Xem [tổng hợp kết quả](../docs/qa/fe-03.2/verification-summary.json), [HTTP checks](../docs/qa/fe-03.2/http-results.json), [browser checks](../docs/qa/fe-03.2/browser-results.json), [protocol checks](../docs/qa/fe-03.2/protocol-results.json), [ảnh health](../docs/qa/fe-03.2/health.png) và [Dashboard](../docs/qa/fe-03.2/dashboard.png). Đó là minh chứng QA của lần chạy này; chạy lại các lệnh phía trên để xác nhận trên máy bạn. Chưa stage/commit/push trong task.

## FE-03.3 — Register với API thật

Register A theo quyết định D-01 trong [bàn giao TV4](../docs/TV4_HOME_AUTH_HANDOFF.md): chỉ có `email`, `password`, `password_confirm`. Full name, English level và Learning goal thuộc bước Profile sau này. Request là `POST /api/v1/auth/register/`; thành công HTTP201 chuyển sang `/login` kèm thông báo. Register không cấp JWT, không tự đăng nhập và không lưu thông tin đăng ký vào Web Storage/history.

### Cách chạy để double-check

Terminal 1 **tại thư mục gốc project**, dùng Python/dependency trong `.venv` đã có:

```powershell
.\.venv\Scripts\python.exe frontend/scripts/run-auth-qa.py --init
```

`--init` áp dụng các migration backend có sẵn vào SQLite riêng trong `%TEMP%/learning-english-tracker-fe033-qa/manual/auth.sqlite3`, rồi chạy Django tại `127.0.0.1:8000`. Dùng development settings với PBKDF2 thật; key QA nằm riêng trong Temp. Script không đọc `.env`, không seed tài khoản và không dùng database học tập của project. Đăng ký trên giao diện sẽ tạo tài khoản QA thật trong database này. Lần sau có thể bỏ `--init`; dữ liệu QA được giữ nguyên. Thêm `--check-only` để kiểm tra schema rồi thoát.

Nếu đang chạy server `config.settings.test` của FE-03.2 ở cổng8000, nhấn Ctrl+C trong terminal đó trước. Server test trong RAM ở hướng dẫn cũ chỉ kiểm tra transport; không dùng cho đăng ký thành công.

Terminal 2 **tại thư mục gốc project**:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Giữ cả hai terminal chạy. Nếu đã tự đặt `DEV_API_TARGET`, bảo đảm nó trỏ tới `http://127.0.0.1:8000` rồi khởi động lại Vite. Mở **http://127.0.0.1:5173/register**.

1. Bỏ trống rồi Register: ba lỗi dưới field; focus về Email; không gửi POST.
2. Nhập email sai hoặc xác nhận password khác nhau: có lỗi tương ứng; sửa được bằng bàn phím. Hai nút mắt hoạt động độc lập và không submit.
3. Dùng email QA mới và mật khẩu đủ mạnh do bạn tự chọn: Network có POST201, chuyển `/login`, hiện thông báo đăng ký thành công. Không gửi mật khẩu/token vào hội thoại hoặc ảnh chụp.
4. Đăng ký lại cùng email: nhận400, lỗi tại Email, không tạo bản ghi thứ hai. Password yếu phải hiển thị lỗi thật từ Django.
5. Nhấn Register liên tiếp: chỉ một POST khi đang gửi. Dừng backend rồi thử: hiện lỗi kết nối, không báo thành công; khởi động lại backend để thử tiếp.
6. Dùng Tab/Shift+Tab/Enter, thu cửa sổ tới375px và zoom200%: form không tràn ngang; desktop có minh họa, cửa sổ hẹp ưu tiên form. Reload trực tiếp `/register` vẫn render đúng.

Terminal 3 **tại gốc project**, kiểm tra số bản ghi mà không in email/password/hash:

```powershell
'{"instance":"manual"}' | .\.venv\Scripts\python.exe -B frontend/scripts/inspect-auth-qa.py
```

Sau mỗi email đăng ký thành công, `users` và `profiles` tăng cùng nhau một bản ghi; email trùng không làm tăng counts. Inspector chỉ đọc database QA đã có. Không truyền password qua command line hoặc ghi password vào log.

### File cần review và cách debug

| File | Trách nhiệm |
|---|---|
| `src/features/auth/RegisterPage.tsx` | State form, submit/khóa request, focus lỗi, abort khi rời trang, chuyển Login |
| `src/features/auth/api.ts` và `types.ts` | DTO ba field, chuẩn hóa email, gọi client có sẵn, xác minh response runtime |
| `src/features/auth/registration.ts` | Validation phía client và chuyển lỗi Django về field/form; server quyết định chính sách password |
| `src/shared/ui/FormField.tsx`, `PasswordField.tsx`, `form-controls.css` | Label, hint/error ARIA, ref, visibility toggle và CSS control dùng lại |
| `src/features/auth/auth.css` | Giao diện Register và responsive, CSS được giới hạn scope |
| `src/features/auth/LoginPage.tsx` | Đọc cờ thông báo thành công an toàn; chưa thêm Login API |
| `src/assets/auth/` | Minh họa/icon gốc và manifest nguồn; [chi tiết asset](src/assets/auth/README.md) |
| `scripts/run-auth-qa.py`, `inspect-auth-qa.py` | Khởi động database/server QA riêng và kiểm tra counts/điều kiện dữ liệu |

Các đoạn xử lý có chú thích tiếng Việt giải thích lý do. Khi lỗi: kiểm tra terminal Django/Vite, Network POST và lỗi dưới field trước. `requestId` nếu backend cung cấp giúp đối chiếu log; không thêm console log chứa form/password. HTTP400 là validation; lỗi kết nối cần cả hai server đang chạy. Không tự sửa API backend khi contract đã được xác minh.

### Nguồn hình ảnh và giới hạn thiết kế

Mình chọn trích vùng pixel từ `Register.png` người dùng đã cung cấp vì Figma MCP hết quota trước khi lấy được context Register. Giữ nguyên file gốc; minh họa dùng WebP lossless, icon dùng PNG. Script `extract-register-assets.py` kiểm tra ảnh nguồn1556×1091 và xác nhận pixel giải mã trùng crop; xem `source.json`. Không dùng toàn bộ ảnh chụp làm giao diện và không vẽ lại minh họa bằng AI. Các control đều là HTML/React thật.

Ba field là Register A đã chốt, nên vị trí form được thích nghi từ bản sáu field. Chưa có Figma mobile; layout hẹp là fallback responsive. Font vẫn dùng stack của project, chưa bundle Inter; không tuyên bố khớp pixel trên mọi máy. Border/focus/link có điều chỉnh để dễ nhìn và dùng bàn phím. Khi cần xuất lại asset, script yêu cầu Pillow13 (công cụ trong `.venv`, không phải dependency runtime/build); chỉ chạy với đúng ảnh nguồn đã bàn giao.

### Kiểm chứng đã chạy ngày19/11/2026

```powershell
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe manage.py test tests.test_authentication --settings=config.settings.test --noinput
npm.cmd --prefix frontend run check:api
```

- Lint/build PASS;8/8 test authentication Django có sẵn PASS trên test database riêng.
- Chrome thật + Django thật + SQLite QA đã migrate:28/28 checks PASS, gồm validation,201, duplicate400, mạng lỗi, abort, chống double-submit, ARIA, tám độ rộng320–1556px và zoom trình duyệt200%.
- Một đăng ký QA thật tạo đúng một user và một profile; kiểm tra PBKDF2, email chuẩn hóa và password giữ khoảng trắng đều PASS. Không tạo dữ liệu học tập hoặc response giả.
- Regression client/proxy FE-03.2:12/12 checks PASS, gồm9 HTTP thật và3 kiểm tra local; không ghi đè minh chứng FE-03.2.
- Chưa chạy screen reader thực tế, Safari/Firefox, thiết bị cảm ứng, UI với5xx/JSON success hỏng, hoặc deploy production. Login/Refresh/session/Protected Route thuộc các task sau.

Minh chứng: [tổng hợp](../docs/qa/fe-03.3/verification-summary.json), [28 browser checks](../docs/qa/fe-03.3/browser-results.json), [phạm vi thay đổi](../docs/qa/fe-03.3/scope-check.json), [desktop](../docs/qa/fe-03.3/register-desktop.png), [mobile](../docs/qa/fe-03.3/register-mobile.png), [thành công](../docs/qa/fe-03.3/register-success-login.png), [lỗi bắt buộc](../docs/qa/fe-03.3/register-required-errors.png), [zoom200%](../docs/qa/fe-03.3/register-zoom-200.png). Đây là kết quả lần chạy QA, không thay cho double-check trên máy bạn. FE-03.3 hoàn thành kỹ thuật, chờ bạn nghiệm thu; chưa stage/commit/push/deploy.

## FE-03.4 — Login UI và API thật

Login dùng ảnh `Login.png` đã bàn giao, card480px với vùng field420px theo kích thước Register người dùng vừa nghiệm thu. Có label thật, password toggle, focus lỗi, loading/disable, chống gửi lặp và hủy request khi rời trang. Thông báo Register thành công được giữ nguyên. Mỗi phần xử lý chính có chú thích trong source để review/debug.

### Chạy lại để double-check

**Terminal 1 tại gốc project:** dừng Django cũ bằng Ctrl+C rồi chạy lại để nhận bản sửa serializer; launcher dùng `--noreload` nên không tự reload khi code backend đổi.

```powershell
.\.venv\Scripts\python.exe frontend/scripts/run-auth-qa.py --init
```

Lệnh này vẫn dùng database QA `manual` của Register tại Temp và giữ tài khoản đã tạo; không reset/seed dữ liệu, không dùng learner DB. Không cần tạo lại tài khoản chỉ vì khởi động server. Bỏ `--init` cũng được nếu schema đã có.

**Terminal 2 tại gốc project:**

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Mở **http://127.0.0.1:5173/login** và Ctrl+F5 nếu đang mở bản cũ. Giữ cả hai server chạy; `DEV_API_TARGET` nếu đã tùy chỉnh phải trỏ đúng Django8000.

1. Bỏ trống rồi Login: Email/Password có lỗi, focus Email và không gửi POST. Email sai định dạng cũng bị chặn trước HTTP.
2. Dùng tài khoản đã Register, nhập sai password: POST401, thông báo chung “Email hoặc mật khẩu không đúng”, không chuyển Dashboard.
3. Nhập đúng email/password của bạn: POST `/api/v1/auth/login/` trả200, chuyển `/dashboard`. Response có access/refresh/user; không sao chép hoặc chụp JWT/password vào ảnh/hội thoại.
4. Nhấn Login liên tiếp khi đang gửi: chỉ một POST. Tắt Django rồi thử: báo lỗi kết nối, không báo thành công; bật lại để thử tiếp.
5. Dùng nút mắt và Tab/Shift+Tab/Enter; thử375px,320px và zoom200%. Field vẫn có tên trong accessibility tree, target nút mắt44px; lỗi dài được phép làm trang cuộn dọc.
6. Khi cần kiểm tra fix password, Register tài khoản QA mới với password có khoảng trắng đầu/cuối. Login bằng đúng giá trị phải200, bản tự bỏ khoảng trắng phải401. Không thay đổi password của tài khoản hiện có để kiểm thử.

### Ranh giới với FE-03.5 trở đi

`pendingLogin.ts` giữ bản sao response Login đã được kiểm tra cấu trúc trong **bộ nhớ của tab**. Không lưu password; không ghi JWT vào localStorage/sessionStorage, URL/router history hoặc log. Reload/đóng tab sẽ mất dữ liệu này. Đây là điểm bàn giao cho AuthContext ở FE-03.5, chưa phải cơ chế khôi phục phiên hoặc refresh.

Dashboard và các route ứng dụng chưa có guard, vẫn có thể mở trực tiếp như baseline; FE-03.6 sẽ bảo vệ chúng. Chưa lấy dữ liệu Dashboard/Profile qua API trong giao diện. QA có gọi Bearer GET me để xác nhận token thật hoạt động, không đồng nghĩa Profile UI đã tích hợp. Login.user.id là string; GET me.id hiện là number, cần chuẩn hóa khi triển khai Profile.

Remember me và Forgot password đang disabled kèm lời giải thích vì session/reset contract TV1 chưa có. Không gửi thêm `remember_me`, không tạo API reset hoặc báo gửi email giả. Các yêu cầu này vẫn phải hoàn thành trước nghiệm thu toàn bộ FE-03.

### Các file cần review

| File | Trách nhiệm |
|---|---|
| `src/features/auth/LoginPage.tsx` | Điều khiển form, focus, request lock/abort và chuyển Dashboard sau200 |
| `src/features/auth/api.ts`, `types.ts` | Login DTO đúng hai field, runtime guard raw `{access,refresh,user}`; Register giữ nguyên |
| `src/features/auth/login.ts` | Validation và mapping400/401/network/5xx, không áp policy đăng ký cho Login |
| `src/features/auth/pendingLogin.ts` | Bàn giao token/user qua RAM với bản sao, chuẩn bị cho FE-03.5 |
| `src/features/auth/login.css` | CSS có scope, card/field compact và fallback responsive; không sửa Register CSS |
| `src/app/layouts/AuthLayout.tsx` | Footer Login dùng link repo, giữ đúng một main; không chép liên hệ cá nhân từ ảnh |
| `src/assets/auth/login-source.json`, `scripts/extract-login-assets.py` | Nguồn minh họa/crop/lossless, nguyên bản không bị sửa |
| `../apps/accounts/serializers.py` | Fix đã được người dùng phê duyệt: password Login không tự trim |
| `../tests/test_jwt_authentication.py` | Test hồi quy password giữ khoảng trắng200, bản bị strip401 |

Figma MCP vẫn hết quota, nên dùng vùng minh họa nguyên pixel từ Login.png và logo/icon sẵn có. Nền bên phải được dựng bằng CSS; PublicHeader giữ các link thật Home/Login/Sign up. Không tuyên bố pixel-perfect với Figma; chưa có Figma mobile hoặc font Inter bundled. Không đưa ảnh cả màn hình hoặc thông tin liên hệ cá nhân ở footer vào runtime.

### Kiểm chứng ngày19/11/2026

```powershell
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe manage.py test tests.test_authentication tests.test_jwt_authentication apps.accounts.tests.test_jwt_authentication --settings=config.settings.test --noinput
```

- Lint/build PASS;17 test Django PASS sau fix được duyệt, dùng test database trong RAM.
- Chrome thật:32 checks Login/layout/accessibility PASS, thêm7 checks regression password khoảng trắng PASS sau khi restart backend; tổng39.
- Luồng chuẩn có response401/201/401/200; regression khoảng trắng có201/401/200. Offline/abort không có response thành công. GET me dùng token thật xác nhận đúng user, không in token/danh tính trong evidence.
- Hai tài khoản/profile QA thật được tạo bằng Register UI trong instance `fe034-final`, riêng với `manual` của người dùng. Một instance điều tra `fe034-review` giữ lại dữ liệu chẩn đoán trước fix, không reset/xóa. Database `manual` kiểm tra vẫn1 user/1 profile, không chỉnh dữ liệu tài khoản người dùng.
- Native Chrome zoom200%, keyboard Tab, accessibility tree, asset local và các viewport320/375/768/900/901/1024/1280/1366/1556 PASS. Chưa chạy screen reader thật, Firefox/Safari/touch hoặc UI với5xx/JSON success hỏng.

Xem [tổng hợp](../docs/qa/fe-03.4/verification-summary.json), [32 checks](../docs/qa/fe-03.4/browser-results.json), [7 regression checks](../docs/qa/fe-03.4/password-whitespace-results.json), [17 backend tests](../docs/qa/fe-03.4/backend-tests.txt), [scope](../docs/qa/fe-03.4/scope-check.json), [desktop](../docs/qa/fe-03.4/login-desktop.png), [mobile](../docs/qa/fe-03.4/login-mobile.png), [zoom200%](../docs/qa/fe-03.4/login-zoom-200.png) và [Dashboard sau Login](../docs/qa/fe-03.4/login-success-dashboard.png).

FE-03.4 hoàn thành kỹ thuật, chờ người dùng double-check. FE-03.5–03.9 chưa được coi là hoàn thành. Server/browser do agent mở được dừng sau QA; bạn tự mở hai terminal phía trên. Không stage/commit/push/merge/deploy.

## FE-03.5 — AuthContext và Django session phía server

AuthProvider bao quanh App trong BrowserRouter, tồn tại qua các lần chuyển route. Context chỉ có status/user/expiresAt và actions; CSRF ở RAM riêng, session ID trong cookie HttpOnly. Đã bỏ pendingLogin.ts để chỉ có một nguồn AuthState. JWT Login/Refresh legacy vẫn tồn tại cho client cũ, không được web dùng làm fallback.

### Chạy và double-check

Tất cả lệnh chạy tại gốc project. Dừng Django/Vite cũ bằng Ctrl+C trước khi khởi động lại. Python tối thiểu3.10; máy QA đã nâng .venv lên Django5.2.19. Máy mới cài dependency theo requirements như README gốc.

Terminal 1:

```powershell
Set-Location "C:\Users\Admin\Downloads\Learning-English-Tracker"
.\.venv\Scripts\python.exe -m django --version
.\.venv\Scripts\python.exe frontend/scripts/run-auth-qa.py --init
```

Phiên bản mong đợi5.2.19. Launcher giữ database QA manual/tài khoản Register cũ trong Temp, key ổn định giữa các lần restart; không reset, seed hoặc dùng learner DB. --init áp migrations chuẩn có sẵn, không có app migration mới. Database phiên là bảng django_session trong cùng file auth.sqlite3; cookie chỉ giữ ID phiên. Đây không phải mã hóa database/backup.

Terminal 2:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Mở **http://127.0.0.1:5173/login**, giữ đúng origin này và Ctrl+F5 nếu thấy bản cũ. DEV_API_TARGET nếu đã chỉnh phải trỏ Django8000, VITE_API_BASE_URL dùng /api/v1/. Nếu đổi cổng/hostname frontend, chạy Django với --frontend-origin tương ứng, ví dụ --frontend-origin http://localhost:5173. Vite đổi Host qua proxy nên CSRF cần khai báo origin browser đúng; không mở wildcard để né lỗi403.

1. Login bằng tài khoản bạn đã Register. POST session/login/ trả200, chuyển Dashboard; thanh tài khoản hiện email thật và nút Đăng xuất.
2. F5 tại Dashboard: thanh tài khoản phải trở lại đúng user sau bước đang kiểm tra. Network GET session/ trả authenticated=true; chỉ thấy trang Dashboard hiện chưa đủ chứng minh đã đăng nhập.
3. Mở Dashboard trong tab thứ hai. Logout ở tab đầu: backend hủy session, tab đầu về Login, tab kia cập nhật chưa đăng nhập. Cookie cũ không xác thực được nữa.
4. Login với Remember me bỏ chọn/được chọn. Application → Cookies: let_sessionid có HttpOnly, SameSite=Lax; bỏ chọn là session cookie, chọn có hạn persistent. Local HTTP Secure=false; production phải HTTPS/Secure=true.
5. document.cookie không đọc được let_sessionid/csrftoken. Local Storage/Session Storage không chứa password/JWT/session ID. Không sao chép cookie/token/password vào hội thoại hoặc ảnh.
6. Tắt Django, F5 Dashboard: trạng thái không kiểm tra được phiên, có nút Thử lại; không giả kết luận logout. Bật lại Django rồi thử lại, phiên còn hạn được khôi phục.
7. Thu cửa sổ320/375px, dùng Tab và zoom200%; thanh tài khoản và form không tràn ngang. Thử sai password:401 chung, field/loading vẫn phục hồi.

Chính sách server: bỏ chọn Remember me → absolute8 giờ/idle30 phút; chọn → absolute7 ngày/idle24 giờ. GET bootstrap/focus không gia hạn idle, absolute không trượt. Đóng browser có thể được browser khôi phục cookie; server deadline vẫn có hiệu lực.

### Lệnh kiểm tra chất lượng

Terminal 3 tại gốc project:

```powershell
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe manage.py test tests.test_session_authentication tests.test_authentication tests.test_jwt_authentication apps.accounts.tests.test_jwt_authentication --settings=config.settings.test --noinput
.\.venv\Scripts\python.exe scripts/verify.py
git diff --check
```

Test session dùng enforce_csrf_checks=True và test database riêng. verify.py kiểm tra toàn bộ Python, migration trên SQLite tạm/copy, cấu hình production và ownership; không áp migration lên database người dùng. Windows đã sửa đóng connection SQLite rõ ràng để dọn file tạm. Lint/build không thay cho kiểm tra auth trên browser.

### File map và kiến thức để debug

| Vị trí | Trách nhiệm |
|---|---|
| features/auth/AuthProvider.tsx, AuthContext.ts, useAuth.ts | Provider/useSyncExternalStore và Context, bốn trạng thái checking/authenticated/anonymous/unavailable |
| features/auth/session.ts | Single-flight bootstrap, queue mutation, generation/abort, recheck, BroadcastChannel và Web Locks |
| features/auth/session-api.ts, types.ts | DTO/guard session; không đưa CSRF/session ID/JWT vào Context |
| LoginPage.tsx, main.tsx | Login gọi Provider, Remember me thật và Provider không remount theo route |
| SessionStatus.tsx, session-status.css, MainLayout.tsx | Trạng thái tài khoản, retry và Logout được server xác nhận |
| shared/api/client.ts | session:true chỉ gửi cookie cùng origin; CSRF opt-in, chặn mixed auth/cross-origin/leakage; JWT mặc định omit giữ nguyên |
| apps/accounts/session_auth.py | Policy absolute/idle, session auth cho private APIs, không trộn session admin |
| apps/accounts/session_views.py, session_serializers.py, urls.py | Bootstrap/Login/Logout, CSRF, cookie, strict input và generic401 |
| config/settings/ | Cookie flags, trusted origins, session policy và production HTTPS |
| tests/test_session_authentication.py | CSRF, expiry, ownership, logout/reuse và JWT compatibility |

Login/logout POST không tự lặp lại sau lỗi mạng. Khi chưa rõ server đã commit hay chưa, coordinator GET để đối chiếu. Response cũ không ghi đè mutation mới; Web Locks đồng bộ mutation giữa tab khi có API này, fallback là queue trong tab và recheck khi focus/visibility/notification. BroadcastChannel chỉ gửi session-changed, không gửi user hoặc secret.

Cookie HttpOnly giảm khả năng đọc trực tiếp bằng JavaScript, không chữa XSS hoặc thay thế authorization. Django kiểm tra ownership mỗi API. App vẫn chưa có route guard FE-03.6; Profile UI/Reset password chưa triển khai. Logout này hủy phiên web hiện tại, không thu hồi JWT legacy hoặc phiên độc lập ở thiết bị khác. TLS thật, mã hóa backup, CSP/MFA/rate-limit production chưa được triển khai trong task này.

### Kết quả QA ngày20/11/2026

- Django5.2.19, pip check PASS; không nâng package frontend hoặc đổi lockfile. CI cấu hình Python3.10–3.12; thực chạy QA trên Python3.12.10.
- Full verify248 tests PASS, backend coverage96%; focused auth/session37 tests PASS là tập con, không cộng thành285.
- Chrome57 checks PASS trên source cuối:42 luồng session/security,15 concurrency/accessibility. Có cookie HttpOnly, F5, CSRF403, oldcookie401, hai tab, đồng thời Login/Logout, offline/retry, owner404, fakeowner bị bỏ qua, idle/absolute thật trong DB QA, native zoom200% và vùng bấm44px.
- Ba user/profile QA thật tạo qua Register ở instance fe035-final, hai study-session QA qua API để kiểm ownership; không fake server. Instance fe035-review giữ thử nghiệm trước, dữ liệu manual của người dùng không được sửa.
- Chưa test screen reader thật, Firefox/Safari/touch hoặc TLS/deploy thật. HTTPS cookie flags kiểm bằng backend test, không coi HTTP local là HTTPS.

Minh chứng: [tổng hợp](../docs/qa/fe-03.5/verification-summary.json), [42 checks](../docs/qa/fe-03.5/browser-results.json), [15 concurrency checks](../docs/qa/fe-03.5/concurrency-results.json), [248 tests/coverage](../docs/qa/fe-03.5/full-verification.txt), [upgrade](../docs/qa/fe-03.5/upgrade-results.json), [scope](../docs/qa/fe-03.5/scope-check.json), [đã đăng nhập](../docs/qa/fe-03.5/session-authenticated-desktop.png), [mobile](../docs/qa/fe-03.5/session-authenticated-mobile.png), [zoom200%](../docs/qa/fe-03.5/session-zoom-200.png). Email QA trong ảnh authenticated được làm mờ; state/API được kiểm tra với giá trị thật.

Hai browser-checks.mjs trong thư mục QA là protocol dành cho headless Chrome/ports8105–5179 và database QA FE035 mới, không phải npm test hoặc script để chạy lên tài khoản manual. Chúng sinh credential trong RAM, không ghi credential ra file; script chính từ chối database không rỗng trước khi tạo test account.

FE-03.5 DONE kỹ thuật sau review, chờ bạn double-check. Agent dừng các server/browser riêng sau QA; bạn tự chạy hai terminal trên. Chưa stage/commit/push/merge/deploy.

## Tài liệu cần đọc

- [Cấu trúc, route, Figma, debug và deploy](src/README.md).
- [FE-02.7: từng giai đoạn, kết quả và checklist double-check](../docs/FE-02.7-QA.md).
- [Ảnh và JSON minh chứng trước–sau](../docs/qa/fe-02.7/README.md).
- [Contract API hiện tại](../docs/API.md).

FE-02.7 đã hoàn thành kiểm tra kỹ thuật và bản sửa; chờ người dùng double-check. `/goals` là URL chính, `/daily-goals` chuyển về URL này và giữ query/hash. Tiêu đề tab đổi theo trang; Header/Sidebar giữ thiết kế đã duyệt.

Vite preview không phải server production. Khi deploy BrowserRouter cần SPA fallback cho URL frontend, đồng thời giữ API/admin/asset đúng tuyến; xem hướng dẫn chi tiết trong src/README. Chưa commit/push/tạo PR hoặc deploy trong task này.
