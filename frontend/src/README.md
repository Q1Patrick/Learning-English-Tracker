# Frontend — cấu trúc hiện tại đến FE-03.5

React + TypeScript + Vite, React Router Declarative. FE-03.5 dùng Django server-side session, AuthProvider toàn ứng dụng và cookie HttpOnly. Login cập nhật Context trước khi chuyển Dashboard; F5 khôi phục qua server. Các trang học còn là khung; Protected Routes thuộc FE-03.6. Mục FE-02.x/FE-03.4 bên dưới giữ lịch sử tại thời điểm đó. Xem [hướng dẫn session và double-check](../README.md#fe-035--authcontext-và-django-session-phía-server).

## Cấu trúc và trách nhiệm

```text
src/
  app/
    AppRouter.tsx
    pageTitles.ts
    layouts/
      PublicLayout.tsx
      PublicHeader.tsx
      AuthLayout.tsx
      MainLayout.tsx
      Header.tsx
      Sidebar.tsx
      LayoutIcon.tsx
      navigation.ts
      navigationEvents.ts
      layouts.css
  features/
    home/HomePage.tsx
    auth/LoginPage.tsx
    auth/RegisterPage.tsx
    auth/api.ts             # Register DTO → client; xác minh response
    auth/types.ts
    auth/registration.ts    # Validation và ánh xạ lỗi server
    auth/auth.css
    auth/login.ts           # Validation và ánh xạ lỗi Login
    auth/login.css          # CSS scope Login, không đổi Register
    auth/AuthContext.ts
    auth/AuthProvider.tsx
    auth/useAuth.ts
    auth/session.ts         # Coordinator, race/abort/recheck và đồng bộ tab
    auth/session-api.ts     # DTO/cookie/CSRF cho web; JWT API cũ giữ riêng
    auth/SessionStatus.tsx
    auth/session-status.css
    dashboard/DashboardPage.tsx
    vocabulary/VocabularyPage.tsx
    study-sessions/StudySessionsPage.tsx
    goals/DailyGoalsPage.tsx
    profile/ProfileSettingsPage.tsx
    not-found/NotFoundPage.tsx
  shared/
    api/                    # Fetch client và ApiError của FE-03.2
    ui/
      FormField.tsx
      PasswordField.tsx
      form-controls.css
    styles/
      tokens.css
      global.css
  assets/
    layout/                 # Vector gốc và tài liệu nguồn
    auth/                   # Crop pixel gốc Register; source.json + README
  App.tsx
  main.tsx
  index.css
```

| Vị trí | Trách nhiệm |
|---|---|
| `main.tsx` | Mount React, StrictMode, một BrowserRouter và một AuthProvider bọc App |
| `App.tsx` | Render router, import CSS layout, cập nhật title tab và focus main khi pathname đổi |
| `app/AppRouter.tsx` | Ghép URL/layout/trang; alias /daily-goals về /goals, giữ query/hash và replace history |
| `app/pageTitles.ts` | Metadata title theo route, chuẩn hóa chữ hoa/thường và slash cuối |
| `MainLayout.tsx` | Sidebar + Header + một main với SessionStatus; menu hẹp đóng theo pathname |
| `navigation.ts` | Nguồn cấu hình chung cho menu và tìm trang; không khai báo URL chưa có |
| `navigationEvents.ts` | Guard side effect khi Link điều hướng cùng tab; giữ Ctrl/Meta/Shift/Alt-click mặc định |
| `Sidebar.tsx` | NavLink, active/aria-current, nhóm tài khoản và mục Sắp có |
| `Header.tsx` | Tìm trang đang có, liên kết hồ sơ, trạng thái thông báo chưa triển khai |
| `PublicLayout.tsx / PublicHeader.tsx` | Khung công khai, logo và các link Home/Login/Sign up |
| `AuthLayout.tsx` | Login có header; Register dùng khung độc lập |
| `LayoutIcon.tsx / assets/layout/` | Dùng vector gốc làm mask cho icon; logo hai màu dùng img |
| `layouts.css` | CSS hình học layout, dùng tokens; responsive ở hai mốc 1024/480px |
| `index.css` | Entry import global.css; main.tsx giữ một import index.css |
| `shared/styles/tokens.css` | Màu, font, spacing, radius, shadow và kích thước chung |
| `shared/styles/global.css` | Import tokens, baseline/reset, focus, skip link và visually-hidden |
| `features/` | Component trang và logic riêng; giữ nguyên chín trang trong FE-02.5 |
| `shared/ui` | FormField/PasswordField dùng lại; label/ref/error ARIA và visibility toggle |
| `features/auth/api.ts` | Register DTO ba field, chuẩn hóa email, giữ nguyên password, guard response runtime |
| `features/auth/registration.ts` | Validation client và ánh xạ lỗi API; không sao chép chính sách password của Django |
| `features/auth/RegisterPage.tsx` | Orchestrate form, khóa/hủy request, focus lỗi và chuyển Login sau201 |
| `features/auth/auth.css` | CSS Register có scope; fallback hẹp chưa có Figma mobile |
| `features/auth/AuthProvider.tsx / useAuth.ts` | Một AuthState chung checking/authenticated/anonymous/unavailable; không JWT trong Context |
| `features/auth/session.ts` | Bootstrap single-flight, mutation queue/Web Locks, generation và revalidate server |
| `features/auth/session-api.ts` | Contract session, cookie same-origin và masked CSRF riêng trong RAM |
| `features/auth/SessionStatus.tsx` | User thật, retry, Logout server; không thay ProtectedRoute |

Các layout sở hữu đúng một `main#main-content`, không lồng main trong App. Link “Đến nội dung chính” hỗ trợ bàn phím. Thay đổi route chuyển focus đến nội dung mới, kể cả chuyển giữa Public/Auth/Main.

## Route và tiêu đề để kiểm tra

| URL | Layout | Component | Tiêu đề h1 |
|---|---|---|---|
| `/` | PublicLayout | HomePage | Learning English Tracker |
| `/login` | AuthLayout login | LoginPage | Learning English Tracker |
| `/register` | AuthLayout register | RegisterPage | Register |
| `/dashboard` | MainLayout | DashboardPage | Bảng điều khiển |
| `/vocabulary` | MainLayout | VocabularyPage | Từ vựng |
| `/study-sessions` | MainLayout | StudySessionsPage | Buổi học |
| `/goals` | MainLayout | DailyGoalsPage | Mục tiêu hằng ngày |
| `/daily-goals` | Alias, replace về `/goals` | DailyGoalsPage sau chuyển | Mục tiêu hằng ngày |
| `/profile` | MainLayout | ProfileSettingsPage | Hồ sơ và cài đặt |
| URL khác, ví dụ `/khong-ton-tai` | PublicLayout | NotFoundPage | Không tìm thấy trang |

Mỗi trang có một h1 và mô tả. Năm trang ứng dụng dùng cùng Sidebar/Header; Home, Login, Register và NotFound không có Sidebar. Profile & Settings dùng một route. Menu vẫn active khi URL có query hoặc dấu `/` cuối. FE-03.5 đã đọc user session thật và hiển thị email tại SessionStatus; chưa có ProtectedRoute, chưa hiển thị dữ liệu học tập/Profile.

FE-02.7 cập nhật title tab theo metadata trang, không thêm title trực quan vào Header. Register/Login hiện có h1 tiếng Anh theo ảnh, title tab vẫn là Đăng ký/Đăng nhập. Query/hash giữ nguyên pathname sẽ không gọi lại effect chuyển focus. Xem [báo cáo và bằng chứng QA](../../docs/FE-02.7-QA.md).

## Phạm vi so với Figma/TV4

Tham chiếu desktop: [Figma node 32:157](https://www.figma.com/design/7Z0gBaqUE3W6tWMFcRgnUP/Learning-English-Tracker?node-id=32-157), SVG 1487 × 1058 do người dùng gửi. Ở FE-02.5, Figma MCP hết quota nên đối chiếu SVG bàn giao. Ngày 17/11/2026, FE-02.6 đã lấy được get_design_context cùng screenshot của node này, xác nhận hình học, bộ màu và font Inter. Ưu tiên giữ phần layout FE-02.5 đã được người dùng nghiệm thu; chưa mở rộng sang nội dung Dashboard.

- Sidebar 245px, Header 88px; ở viewport 1487px, ô tìm trang bắt đầu x=289px và rộng 490px.
- Logo 48 × 48, icon menu 25 × 25, search 23 × 23. Người dùng cho phép tách vector gốc; dữ liệu đường path và màu trong file được giữ nguyên. Xem [nguồn và mapping asset](assets/layout/README.md).
- Icon đơn sắc dùng mask/currentColor để active có màu trắng. Logo dùng ảnh SVG hai màu. Không dùng toàn bộ ảnh/SVG Dashboard làm giao diện runtime.
- Profile và Settings được gộp thành “Profile & Settings” theo route đã thống nhất. Statistics, Quiz, AI Feedback chưa có trang trong frontend này: hiển thị “Sắp có”, không tạo link giả. Việc backend có API không đồng nghĩa màn hình frontend đã được triển khai.
- Ô tìm kiếm thực sự **tìm trang**, hỗ trợ tên tiếng Anh và từ khóa tiếng Việt không dấu. Enter chuyển trang khi chỉ có một kết quả; Tab/Enter chọn link khi có nhiều kết quả; Escape đóng kết quả và giữ focus trong ô tìm. Chưa tìm dữ liệu qua API.
- Header dùng liên kết “Hồ sơ”; không hardcode tên Minh, ảnh người dùng, badge thông báo hoặc dropdown giả. Thông báo bị vô hiệu hóa và có nhãn Sắp có.
- Đầu gradient active được tối nhẹ từ màu tham chiếu sang `#0873e8`, giữ đầu còn lại `#0865ea`, để chữ trắng đạt tối thiểu 4.5:1. Màu link chữ dùng `#0865d8`.
- SVG bàn giao dùng chữ dạng outline; context Figma lấy ở FE-02.6 xác nhận font Inter. Chưa có file font được bundle nên CSS tiếp tục ưu tiên Inter nếu có sẵn, rồi font hệ thống. Brand đang giữ 18px của baseline đã nghiệm thu; metadata Figma là 17px. Chưa tuyên bố typography khớp pixel trên mọi máy.
- Home vẫn là trang khung. FE-03.3 dùng crop nguyên pixel Register.png cho minh họa/icon và form React ba field theo D-01; FE-03.4 thêm Login với minh họa Login.png, card/field compact và CSS nền. Xem [nguồn asset](assets/auth/README.md). Header giữ các link thật, Features/About chưa có section đích nên chưa thêm liên kết. Chưa khẳng định pixel-perfect Figma.
- Chưa có bản Figma mobile được duyệt. FE-02.6 hoàn thiện responsive cơ bản: dưới 1024px dùng menu disclosure trong luồng trang; dưới 480px ô tìm trang xuống hàng riêng. Logo/icon giữ kích thước gốc, phần chữ được wrap khi cần. Phương án này hỗ trợ cửa sổ hẹp, chưa phải nghiệm thu theo thiết kế mobile.

## Chạy trong VS Code

Mở thư mục gốc repository, chạy trong terminal PowerShell:

```powershell
Set-Location .\frontend
npm.cmd run dev
```

Mở URL Vite in ra rồi thêm `/dashboard`. Cổng mặc định là 5173, có thể đổi khi đã có server khác. Dừng server do bạn khởi động bằng Ctrl+C.

Trong terminal khác, tại thư mục frontend:

```powershell
npm.cmd run lint
npm.cmd run build
```

- `lint`: kiểm tra source bằng Oxlint.
- `build`: kiểm tra TypeScript rồi tạo bản production tại `frontend/dist/`.
- FE-02.5/FE-02.6 không thêm thư viện, sửa lockfile, backend hoặc cơ chế xác thực.

## Double-check FE-02.5 — đã được người dùng xác nhận

Người dùng báo double-check thành công ngày 17/11/2026. Danh sách dưới đây giữ làm regression checklist; xác nhận này là của người dùng, không thay cho review độc lập của TV4.

- [ ] Mở `/dashboard` trên desktop: logo đúng hai màu, Sidebar bên trái, Header ở trên; so sánh phần khung với SVG.
- [ ] Bấm Vocabulary, Daily Goals, Study Sessions, Profile & Settings: đúng tiêu đề và chỉ một mục active.
- [ ] Mở trực tiếp rồi F5 tại `/dashboard`, `/profile` và `/profile/`: trang vẫn hiển thị đúng, menu active.
- [ ] Bấm Home, Login và Sign up: không có Sidebar; Login có public header, Register độc lập.
- [ ] Dùng Back/Forward; mở `/khong-ton-tai` và bấm về Home.
- [ ] Tìm `muc tieu`, nhấn Enter: tới Daily Goals. Tìm `profile`, Tab tới kết quả rồi Enter: tới hồ sơ.
- [ ] Tìm `zzzzzz`: có thông báo không tìm thấy. Escape đóng kết quả, vẫn nhập tiếp được.
- [ ] Dùng Tab/Shift+Tab/Enter: focus nhìn thấy, link bỏ qua điều hướng đưa đến main, không bị kẹt bàn phím.
- [ ] Thu hẹp cửa sổ dưới 1024px: mở menu, dùng Tab, Escape trả focus về nút menu; chọn trang thì menu đóng.
- [ ] Statistics/Quiz/AI Feedback và thông báo chỉ hiện Sắp có, không điều hướng hoặc gọi API giả.
- [ ] DevTools Console không có lỗi; Network không có asset hỏng. Chấp nhận nội dung trang vẫn ghi “Giao diện khung, chưa kết nối API”.
- [ ] Chạy lint/build và review file mới trong Git; chỉ đánh dấu nghiệm thu sau khi bạn kiểm tra giao diện.

HTTP 200 chỉ chứng minh server trả nội dung; SPA có thể trả index.html cho nhiều URL. Cần kiểm tra trang React thực sự hiển thị.

## Kết quả kiểm tra ngày 16/11/2026

FE-02.4 trước đó: lint/build PASS; 12 trường hợp render qua MemoryRouter PASS; phiên FE-02.4 chưa chạy browser tự động. Người dùng đã báo kiểm thử thành công trước khi bắt đầu FE-02.5.

FE-02.5 được kiểm tra bằng bản build và Chrome headless local:

| Kiểm tra | Kết quả |
|---|---|
| Oxlint và TypeScript + Vite build | PASS |
| Render thực tế qua MemoryRouter | PASS: 13 trường hợp, đúng h1/main/layout/active |
| Browser tải trực tiếp | PASS: 8 URL chính, 2 URL không tồn tại, query và 2 trailing slash |
| Browser reload | PASS: /dashboard và /profile |
| Click, Back/Forward, chuyển layout và focus | PASS |
| Skip link bằng Tab/Enter | PASS |
| Tìm trang, Enter, chọn kết quả bằng Tab/Enter, no-result/Escape | PASS |
| Kiểm tra tràn ngang | PASS: viewport 1487, 1366, 1024, 1023, 768, 375px |
| Menu cửa sổ hẹp | PASS: mở, Tab, Escape, focus trở lại nút và đóng sau navigation |
| Hình học desktop và asset | PASS: 245/88/490px, logo 48px, 12 icon mask đúng kích thước |
| Browser exception, console error, request tải lỗi | Không phát hiện trong các luồng đã chạy |
| SVG | PASS: 15 file hợp lệ, 32 path/158 thuộc tính khớp nguồn, không clipping hoặc tham chiếu ngoài |
| Nghiệm thu hình ảnh | Người dùng xác nhận double-check thành công ngày 17/11/2026; TV4 chưa có xác nhận riêng |

Các kiểm tra render/browser là script kiểm tra một lần dùng công cụ sẵn có, không thêm dependency hay bộ test source vào repository. Đã đối chiếu ảnh desktop của phần layout với SVG; nội dung Dashboard giữ nguyên khung FE-02.4. Chưa kiểm tra screen reader thực tế, Firefox, Safari hoặc responsive theo bản thiết kế mobile.


## FE-02.6 — nơi chỉnh CSS và cách debug

Chỉ năm file được sửa: tokens.css, global.css, index.css, layouts.css và README này. React components/router, SVG gốc, API, dependency và cấu hình deploy giữ nguyên.

Luồng nạp CSS:

```text
main.tsx → index.css → shared/styles/global.css → tokens.css
App.tsx  → app/layouts/layouts.css
```

`@import` phải ở đầu file CSS. Token được khai báo ở :root, layout dùng var(); không sao chép bảng màu PROPOSED cũ trong DESIGN.md đè lên giao diện đã nghiệm thu.

| Muốn chỉnh | Vị trí |
|---|---|
| Màu chữ/nền/link | tokens.css: --color-ink, --color-bg, --color-link |
| Nền Sidebar/active | --color-sidebar-start/end, --color-active-start/end |
| Font chung/cỡ chữ | --font-family-sans, --font-size-body/brand/heading; dùng rem để chữ theo thiết lập người dùng |
| Sidebar/Header | --sidebar-width, --header-height, --header-inset-block |
| Khoảng cách nội dung | --content-inset-inline, --space-* |
| Search | --search-width, --search-height; popup giới hạn chiều cao theo viewport trong layouts.css |
| Radius/shadow | --radius-*, --shadow-search |
| Focus/skip link | global.css; màu --color-focus |
| Quy tắc cửa sổ hẹp | Hai @media cuối layouts.css, các mốc max-width 1023px và 479px |

Các số 19/29/49/245px là số đo thiết kế, có chú thích ở source. Header padding và Sidebar padding có token riêng để chỉnh một vùng không làm vùng kia thay đổi ngoài ý muốn. Logo 48px, icon 25px và search icon 23px là kích thước asset đã bàn giao, không dùng reset img/svg 100% để kéo giãn chúng.

Khi giao diện sai:

1. Inspect phần tử trong DevTools, mở Computed để kiểm tra giá trị token và rule đang ghi đè.
2. Nếu var() không có giá trị, kiểm tra chuỗi import và tên token trước khi thêm màu/kích thước khác.
3. Nếu có tràn ngang, tìm phần tử có width/white-space bất thường; không dùng overflow-x:hidden để che lỗi.
4. Khi sửa token, kiểm tra lại cả Public/Auth/Main và viewport hai phía breakpoint.
5. App.css còn CSS mẫu và chưa được import; sửa file đó hiện sẽ không đổi giao diện đang chạy.

Responsive giữ mô hình disclosure đã nghiệm thu. FE-02.6 thêm wrap cho chữ dài/brand, giữ icon cố định, gom focus/skip link về global, và cho popup tìm trang cuộn khi viewport thấp. Không thêm drawer/modal hoặc component form trong nhiệm vụ này.

### Kết quả kiểm tra FE-02.6 ngày 17/11/2026

| Kiểm tra | Kết quả |
|---|---|
| Oxlint; TypeScript + Vite production build | PASS |
| Token/import | Parse CSS thành công; không token thiếu hoặc vòng var() |
| Desktop Dashboard trước–sau | PASS: 18 selector giữ nguyên hình học và style; ảnh PNG trước/sau trùng hoàn toàn trong cùng Chrome QA |
| Desktop tám route chính trước–sau | PASS: h1, main, font, margin/padding và public/auth header giữ nguyên |
| Matrix 9 route × 9 viewport | PASS: 81 trường hợp, không tràn ngang |
| Viewport | 320, 375, 479, 480, 768, 1023, 1024, 1366, 1487px |
| Logo/icon | PASS: logo 48px và 12 mask icon giữ 25/23px, đúng slot và asset local |
| Reload/query/trailing slash/Back/Forward | PASS; active và focus sau chuyển layout đúng |
| Bàn phím | PASS: Tab/Shift+Tab/Enter, focus ring, skip link, tìm trang, menu/Escape |
| Viewport thấp 320 × 240px | PASS: kết quả tìm trang cuộn được; no-result/chuỗi dài không gây tràn ngang |
| Phóng lớn chữ root lên 32px | PASS: 9 route tại 320px, gồm menu đang mở |
| Zoom trình duyệt thật 200% | PASS: 9 route, không tràn ngang; menu/focus/Escape hoạt động |
| Browser exception / console error / request tải lỗi | Không phát hiện trong matrix và luồng kiểm tra |
| Nghiệm thu FE-02.6 bởi người dùng | CHỜ DOUBLE-CHECK |

Zoom 200% được đặt bằng Chrome settingsPrivate.setDefaultZoom(2) trong profile QA riêng sau khi clear device metrics override: viewport từ 1471 × 963 CSS px / DPR1 thành 735 × 481 / DPR2. Đây là browser zoom, không dùng pageScaleFactor để thay thế. Đã trả zoom về 100% trong profile QA sau kiểm tra.

Các script QA chạy một lần với công cụ sẵn có; không cài thư viện hoặc thêm test source chỉ để kiểm tra CSS. Chưa kiểm tra screen reader thực tế, Firefox/Safari hoặc độ khớp theo bản Figma mobile.

### Double-check FE-02.6

```powershell
Set-Location C:\Users\Admin\Downloads\Learning-English-Tracker\frontend
npm.cmd run dev
```

- [ ] Mở /dashboard trên desktop, so sánh phần Sidebar/Header với bản bạn đã duyệt.
- [ ] Mở tám URL chính và /khong-ton-tai: font, spacing, link và một h1/main đúng.
- [ ] Trong DevTools Responsive, thử 320/375/768/1023/1024/1487px; không mất chữ hoặc tràn ngang.
- [ ] Dưới 1024px mở menu; Tab, Escape và chọn trang vẫn dùng được.
- [ ] Dưới 480px ô tìm trang xuống hàng riêng; thử muc tieu, profile và chuỗi không có kết quả.
- [ ] Dùng menu Zoom của Chrome đặt 200%, kiểm tra đọc/điều hướng rồi trả 100%.
- [ ] Tab/Shift+Tab/Enter có focus nhìn thấy; link bỏ qua điều hướng đưa đến main.
- [ ] F5 tại /dashboard và /profile, thử Back/Forward; Console không có lỗi.
- [ ] Chạy lint/build, review file thay đổi; xác nhận trước khi chuyển FE-02.7.

### Tài liệu thiết kế có sẵn và phần cần bổ sung

FE-02.6 hiện đủ tham chiếu: SVG đã gửi, vector local và context/screenshot Dashboard Figma node 32:157 đã đọc được ngày 17/11/2026. Bạn chưa cần gửi thêm ảnh để hoàn thành phần CSS nền này.

Khi muốn nghiệm thu đúng thiết kế trên điện thoại/tablet, cung cấp **link tới frame mobile/tablet cụ thể trong Figma** hoặc **PNG/SVG xuất toàn bộ frame từ Figma**, kèm chiều rộng frame (ví dụ 375px) và trạng thái menu đóng/mở. Ảnh toàn frame giúp đối chiếu bố cục, không được dùng thay component runtime.

Figma xác nhận font Inter. Để đồng nhất font trên các máy, có thể cung cấp file .woff2 hợp lệ cho các weight đang dùng 400/600/700 hoặc thống nhất nguồn font với TV4 ở bước riêng. Hiện system fallback vẫn hoạt động, không phụ thuộc tải font từ Internet.

## Debug nhanh

| Hiện tượng | Điểm kiểm tra |
|---|---|
| Trang trắng | Console/terminal, import/export, bundle và #root trong index.html |
| Router lồng Router | BrowserRouter chỉ đặt tại main.tsx |
| Sai trang hoặc NotFound | Đối chiếu Link với AppRouter.tsx; sửa cấu hình menu tại navigation.ts |
| Thiếu hoặc sai icon | Đối chiếu id trong navigation.ts với LayoutIcon.tsx và assets/layout |
| Menu không active | Kiểm tra URL, end của NavLink; Home dùng end=true, route app dùng boundary matching |
| Menu ẩn khi cửa sổ hẹp | Mở nút menu; breakpoint fallback là 1024px |
| Menu không đóng sau Back/Forward | Kiểm tra so sánh previousPath trong MainLayout, không chỉ callback click |
| Ctrl-click làm mất query của tab gốc | Kiểm tra guard isSameTabNavigation trong Header/Sidebar |
| Sai title tab hoặc alias Daily Goals | Kiểm tra pageTitles.ts, effect trong App và DailyGoalsAlias trong AppRouter |
| Chữ khác bản thiết kế | Figma xác nhận Inter; chưa bundle font, kiểm tra font fallback trong Computed |
| Reload URL sâu trả 404 trên hosting | Cấu hình SPA fallback của web server |
| Asset trả HTML/lỗi MIME | Kiểm tra asset và tránh rewrite asset thiếu sang index.html |
| git diff trống | Frontend đang untracked; kiểm tra danh sách file mới |

## Build và deploy

Môi trường mới có thể cài dependency theo lockfile:

```powershell
npm.cmd ci
npm.cmd run lint
npm.cmd run build
```

Không cần chạy lại npm ci trong mỗi lần chỉnh trang. Xem thử bản build local:

```powershell
npm.cmd run preview
```

Vite preview dùng kiểm tra local, không phải server production.

Khi deploy:

1. Phục vụ file trong `frontend/dist/`.
2. Fallback các đường dẫn **frontend** như /dashboard về index.html để BrowserRouter xử lý khi truy cập trực tiếp hoặc F5.
3. Giữ `/api/*` và `/admin/*` đi tới Django, không rewrite sang SPA.
4. Asset thật phải trả đúng file; asset không tồn tại phải trả lỗi thay vì HTML của SPA.
5. Hiện cấu hình cho gốc domain. Nếu dùng subpath, thống nhất Vite base, BrowserRouter basename và fallback hosting.

Route * chỉ hiển thị NotFound phía client, không tự đặt HTTP 404 của hosting. FE-02.5/FE-02.6 chưa thay đổi hosting, reverse proxy hoặc backend; không deploy trong nhiệm vụ này.

Tài liệu: [React Router](https://reactrouter.com/start/declarative/routing), [Vite static deployment](https://vite.dev/guide/static-deploy.html).

## Bước tiếp theo và review Git

- FE-02.6: đã triển khai CSS nền và responsive cơ bản; kiểm tra lại trong FE-02.7.
- Rà soát template còn lại khi có scope riêng: App.css, asset Vite và favicon hiện chưa được đổi/xóa.
- FE-02.7: hoàn thành giai đoạn1–7 trong phạm vi QA nền; chờ người dùng double-check, chưa tạo PR.
- [Kết quả FE-02.7](../../docs/FE-02.7-QA.md): lint/build/dependency PASS; 81 cặp route/viewport, 18 case Header, 15 nhóm regression, 9 route zoom200% đều đạt. Source/CSS/API ngoài phạm vi giữ nguyên.
- Các bước feature: xây nội dung từng màn hình theo Figma, auth/session thật và request theo [API](../../docs/API.md).
- Forgot/Reset Password vẫn cần contract theo [bàn giao TV4](../../docs/TV4_HOME_AUTH_HANDOFF.md).

FE-03.3 local hiện có cả file tracked đã sửa và file mới untracked; lịch sử FE-02.7 bên trên có trạng thái tại thời điểm đó. Từ thư mục gốc:

```powershell
git status --short --untracked-files=all -- frontend
git ls-files --others --exclude-standard -- frontend
git diff --check
```

Git diff thông thường chưa hiển thị file untracked; review file mới trong Source Control. Giữ package-lock.json, xác nhận node_modules/dist được ignore. Chưa stage, commit, push hoặc tạo PR; các thao tác này chờ người dùng cho phép riêng.

Với lần sửa FE-02.7, có [patch bảy file source](../../docs/qa/fe-02.7/implementation.patch) để review trước–sau. Patch là snapshot cũ, không phải toàn bộ diff hiện tại. Frontend chưa có test framework; FE-03.2 có `check:api`, FE-03.3 có browser/API QA thật. Hướng dẫn chạy hai server, database QA, checklist và giới hạn nằm trong [frontend README](../README.md#fe-033--register-với-api-thật).
