import { Link } from 'react-router'

// Trang fallback phía trình duyệt không tự đặt mã HTTP 404 của máy chủ.
export default function NotFoundPage() {
  return (
    <section aria-labelledby="not-found-title">
      <h1 id="not-found-title">Không tìm thấy trang</h1>
      <p>Địa chỉ bạn truy cập không có trong ứng dụng.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
