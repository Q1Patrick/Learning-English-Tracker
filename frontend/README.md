# Learning English Tracker — Frontend

React + TypeScript + Vite. Hiện có tám trang khung, NotFound, layout dùng chung và CSS responsive cơ bản; chưa tích hợp đăng nhập/API hay nội dung đầy đủ của từng màn hình.

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

Lint kiểm tra source; build kiểm tra TypeScript và xuất `dist/`; preview xem thử bản build local. Project chưa có script `test`. Máy mới cần Node/npm và `npm.cmd ci` theo lockfile; không cần cài lại dependency sau mỗi sửa nhỏ.

## Tài liệu cần đọc

- [Cấu trúc, route, Figma, debug và deploy](src/README.md).
- [FE-02.7: từng giai đoạn, kết quả và checklist double-check](../docs/FE-02.7-QA.md).
- [Ảnh và JSON minh chứng trước–sau](../docs/qa/fe-02.7/README.md).
- [Contract API hiện tại](../docs/API.md).

FE-02.7 đã hoàn thành kiểm tra kỹ thuật và bản sửa; chờ người dùng double-check. `/goals` là URL chính, `/daily-goals` chuyển về URL này và giữ query/hash. Tiêu đề tab đổi theo trang; Header/Sidebar giữ thiết kế đã duyệt.

Vite preview không phải server production. Khi deploy BrowserRouter cần SPA fallback cho URL frontend, đồng thời giữ API/admin/asset đúng tuyến; xem hướng dẫn chi tiết trong src/README. Chưa commit/push/tạo PR hoặc deploy trong task này.
