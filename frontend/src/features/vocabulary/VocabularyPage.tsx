import { Link } from 'react-router'

// Các thao tác từ vựng sẽ dùng API theo tài khoản khi tích hợp dữ liệu.
export default function VocabularyPage() {
  return (
    <section aria-labelledby="vocabulary-title">
      <h1 id="vocabulary-title">Từ vựng</h1>
      <p>Quản lý từ đã lưu, ý nghĩa, ví dụ và mức độ ghi nhớ.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
