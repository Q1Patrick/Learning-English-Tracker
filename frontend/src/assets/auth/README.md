# Asset Register

Nguồn: `Register.png` (1556×1091) do người dùng cung cấp từ thiết kế Figma Learning English Tracker. Figma MCP hết quota trước khi lấy context/node Register. Người dùng giao quyền chọn nguồn gần Figma nhất; đã chọn crop pixel gốc từ ảnh này, giữ nguyên file nguồn. Không dùng screenshot cả màn hình làm UI, không vẽ lại bằng AI và không nhận đây là export vector Figma.

| Asset | Vùng nguồn `(left, top, right, bottom)` | Kích thước |
|---|---|---|
| `register-illustration.webp` | `(1, 1, 756, 1090)` | 755×1089 |
| `register-cap.png` | `(1054, 43, 1190, 154)` | 136×111 |
| `register-email.png` | `(882, 368, 922, 407)` | 40×39 |
| `register-lock.png` | `(888, 486, 927, 526)` | 39×40 |
| `register-eye-off.png` | `(1344, 481, 1395, 532)` | 51×51 |

Minh họa là WebP lossless; các icon giữ PNG. `source.json` lưu hash SHA256 của nguồn, crop box và kết quả so sánh RGBA sau giải mã. Tất cả vùng xuất đều có `pixelIdentityVerified: true`. Không có đổi màu/tái tạo nét hoặc sao chép trường nhập thành ảnh. Form dùng label/input/button thật; icon mắt khi password đang hiện dùng Lucide Eye có sẵn.

Để xuất lại, từ gốc project chạy `frontend/scripts/extract-register-assets.py` bằng Python có Pillow13 và truyền đường dẫn ảnh gốc qua positional argument. Script kiểm tra đúng kích thước trước khi xuất; Pillow chỉ cần cho chuẩn bị asset, không cần cho npm build/deploy. Không ghi thêm địa chỉ máy hoặc thông tin liên hệ từ ảnh vào manifest. Ảnh vẫn có nền trắng ở icon; CSS giữ nền trắng khi form đang disabled để không tạo ô màu lệch.

Register A có ba field theo D-01 của TV4, còn ảnh nguồn có sáu field; do đó đây là thích nghi layout theo contract đã duyệt. Chưa có thiết kế mobile. Tham khảo [hướng dẫn Register](../../../README.md#fe-033--register-với-api-thật) và [script xuất asset](../../../scripts/extract-register-assets.py).

## Login — FE-03.4

`login-illustration.webp` lấy vùng trang trí `(1,101,820,974)` từ Login.png1556×1091 do người dùng cung cấp. Output819×873, WebP lossless437850bytes, giữ nguyên source. Không lấy card/header/footer hoặc thông tin liên hệ cá nhân. `login-source.json` có hash nguồn và xác nhận pixel identity. Script tái xuất: [extract-login-assets.py](../../../scripts/extract-login-assets.py), yêu cầu Pillow chỉ khi xuất lại.

Figma MCP vẫn báo Starter quota; tiếp tục cách dùng ảnh gốc người dùng đã chọn ở Register. Card và control là React/HTML thật, nền phần còn lại là CSS. Logo48px dùng vector gốc `assets/layout/logo.svg`, email/lock/eye-off tái sử dụng asset Register; icon mắt ở trạng thái hiện mật khẩu dùng Lucide như Register. Minh họa dùng object-fit:cover trong cột trang trí để thích nghi viewport; không khẳng định mọi góc crop khớp toàn frame Figma. Chưa có Figma mobile. Xem [hướng dẫn Login](../../../README.md#fe-034--login-ui-và-api-thật).
