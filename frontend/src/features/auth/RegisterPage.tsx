import { Link } from 'react-router'

// API tạo tài khoản và bước hoàn thiện hồ sơ sẽ được tích hợp riêng.
export default function RegisterPage() {
  return (
    <section aria-labelledby="register-title">
      <h1 id="register-title">Đăng ký</h1>
      <p>Tạo tài khoản để lưu và theo dõi quá trình học tiếng Anh của bạn.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
