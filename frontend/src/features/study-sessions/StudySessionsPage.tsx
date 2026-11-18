import { Link } from 'react-router'

// Nhật ký học sẽ được lấy và lưu qua API phiên học khi tích hợp dữ liệu.
export default function StudySessionsPage() {
  return (
    <section aria-labelledby="study-sessions-title">
      <h1 id="study-sessions-title">Buổi học</h1>
      <p>Ghi lại hoạt động học theo kỹ năng, thời lượng và ghi chú.</p>
      <p>Giao diện khung, chưa kết nối API.</p>
      <Link to="/">Về trang chủ</Link>
    </section>
  )
}
