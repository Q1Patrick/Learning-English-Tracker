import { Link } from 'react-router'

// API đăng nhập và cơ chế quản lý phiên sẽ được nối ở bước xác thực riêng.
export default function LoginPage() {
  return (
    <section aria-labelledby="login-title">
      <h1 id="login-title">Đăng nhập</h1>
      <p>Đăng nhập để truy cập nhật ký học, từ vựng và mục tiêu của bạn.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
