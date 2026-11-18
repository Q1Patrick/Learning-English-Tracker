import { Link } from 'react-router'

// Mục tiêu phút theo ngày sẽ được đọc và cập nhật qua API goals.
export default function DailyGoalsPage() {
  return (
    <section aria-labelledby="daily-goals-title">
      <h1 id="daily-goals-title">Mục tiêu hằng ngày</h1>
      <p>Đặt và quản lý mục tiêu số phút học tiếng Anh cho từng ngày.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
