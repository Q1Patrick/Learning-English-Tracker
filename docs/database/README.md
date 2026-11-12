# Nguồn ERD và cách tái tạo

- `erd.json`: nguồn có thể sửa gồm entity, field tóm tắt, vị trí card và các đường quan hệ.
- `erd.svg`: export vector, có thể phóng to, sửa bằng công cụ SVG hoặc mở trực tiếp trong trình duyệt.
- `erd.png`: export raster 2480×2070, 150 DPI để đưa vào tài liệu; được kiểm tra trực quan sau khi render.
- `../../scripts/render_database_erd.py`: renderer độc lập Django/database. Kiểm tra entity trùng, card chồng lấn, row tràn và đường quan hệ đi xuyên card khác.

SVG dùng hoàn toàn Python standard library:

```sh
python scripts/render_database_erd.py --svg-only
```

PNG cần Pillow trong môi trường riêng dùng làm tài liệu, không cần thêm vào dependency ứng dụng. Môi trường thực hiện có sẵn Pillow11.3.0 trong system Python; lệnh đã dùng để tái tạo cả SVG và PNG:

```sh
/usr/bin/python3 scripts/render_database_erd.py
```

Trên máy khác dùng interpreter có Pillow (renderer fallback font dùng Pillow10.1+). Có thể chỉ xuất SVG bằng môi trường ứng dụng nếu chưa có Pillow; không cần cài thêm package để chạy backend hoặc kiểm tra schema.

Có thể xuất sang thư mục tạm để đối chiếu mà không ghi đè artifact đã review:

```sh
/usr/bin/python3 scripts/render_database_erd.py --output-dir /tmp/learning-tracker-erd
```

Nguồn JSON là layout được review thủ công, không tự lấy schema bằng kết nối database. Khi model thay đổi, đối chiếu model/migration, sửa JSON và `docs/DATABASE.md`, render lại, xem PNG/SVG rồi mới commit. Phần fields trong hình là bản tóm tắt; tài liệu DATABASE.md chứa chi tiết đầy đủ.

Cardinality ghi tại mỗi entity: `1`, `0..1`, `0..N`. Đường liền mô tả quan hệ CASCADE của Django; đường đứt là FK nguồn nullable/SET_NULL. Các nhánh User dùng chung một bus. Tên `UserAnswer` của yêu cầu được ánh xạ sang `QuizAttemptAnswer` hiện có. Auth Group/Permission và AI được loại khỏi ERD 10 model, không có nghĩa các bảng đó không tồn tại.

`on_delete` ở đây là hành vi ORM/Django deletion collector; không khẳng định mọi backend tạo SQL `ON DELETE CASCADE/SET NULL` có cú pháp giống hệt. Xem `docs/DATABASE.md` để phân biệt database constraints với validation/service rules.
