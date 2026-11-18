import aiFeedback from '../../assets/layout/ai-feedback.svg'
import dashboard from '../../assets/layout/dashboard.svg'
import goals from '../../assets/layout/daily-goals.svg'
import home from '../../assets/layout/home.svg'
import notification from '../../assets/layout/notification.svg'
import profile from '../../assets/layout/profile.svg'
import quiz from '../../assets/layout/quiz.svg'
import search from '../../assets/layout/search.svg'
import statistics from '../../assets/layout/statistics.svg'
import studySessions from '../../assets/layout/study-sessions.svg'
import user from '../../assets/layout/user.svg'
import vocabulary from '../../assets/layout/vocabulary.svg'

const sources: Record<string, string> = {
  'ai-feedback': aiFeedback,
  dashboard,
  goals,
  home,
  notification,
  profile,
  quiz,
  search,
  statistics,
  'study-sessions': studySessions,
  user,
  vocabulary,
}

// Mask giữ hình dạng gốc; currentColor thể hiện active mà không sửa asset.
// Tên truy cập nằm trên link/button bao quanh icon trang trí.
export default function LayoutIcon({ name, className = '' }: { name: string; className?: string }) {
  const source = sources[name]
  if (!source) throw new Error(`Thiếu SVG cho layout icon: ${name}. Kiểm tra LayoutIcon.tsx và navigation.ts.`)

  return (
    <span
      aria-hidden="true"
      className={`layout-icon ${className}`}
      style={{ maskImage: `url("${source}")`, WebkitMaskImage: `url("${source}")` }}
    />
  )
}
