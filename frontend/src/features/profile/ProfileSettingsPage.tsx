import { Link } from 'react-router'

// Hồ sơ sẽ dùng API auth/me; trang này chưa thay đổi dữ liệu tài khoản.
export default function ProfileSettingsPage() {
  return (
    <section aria-labelledby="profile-settings-title">
      <h1 id="profile-settings-title">Hồ sơ và cài đặt</h1>
      <p>Quản lý tên hiển thị, trình độ tiếng Anh, mục tiêu học tập và múi giờ.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
