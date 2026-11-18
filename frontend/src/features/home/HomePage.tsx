import { Link } from 'react-router'

// Trang công khai giới thiệu sản phẩm, chưa đọc dữ liệu học tập cá nhân.
export default function HomePage() {
  return (
    <section aria-labelledby="home-title">
      <h1 id="home-title">Learning English Tracker</h1>
      <p>Ghi lại buổi học, quản lý từ vựng và theo dõi mục tiêu học tiếng Anh mỗi ngày.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <nav aria-label="Tài khoản">
        <ul>
          <li><Link to="/login">Đăng nhập</Link></li>
          <li><Link to="/register">Đăng ký</Link></li>
        </ul>
      </nav>
    </section>
  )
}
