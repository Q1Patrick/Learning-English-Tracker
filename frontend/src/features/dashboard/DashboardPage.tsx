import { Link } from 'react-router'

// Dashboard sẽ đọc số liệu từ API sau khi cơ chế xác thực được triển khai.
export default function DashboardPage() {
  return (
    <section aria-labelledby="dashboard-title">
      <h1 id="dashboard-title">Bảng điều khiển</h1>
      <p>Xem tiến độ học hôm nay, mục tiêu theo ngày và tổng thời gian học trong tuần.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
