import {
  BookOpen,
  ChartNoAxesCombined,
  ClipboardList,
  Clock3,
  House,
  LayoutDashboard,
  Sparkles,
  Target,
  UserRound,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface AppNavigationItem {
  id: string
  label: string
  icon: LucideIcon
  to?: string
  disabled?: boolean
  end?: boolean
  keywords?: string
}

// Dùng chung cho Sidebar và tìm trang: chỉ khai báo URL đã có trong AppRouter.
// Các mục chưa có trang giữ dạng không tương tác, không dùng link giả "#".
export const navigationItems: readonly AppNavigationItem[] = [
  // Home khớp chính xác; các trang app nhận cả dấu / cuối và route con về sau.
  { id: 'home', label: 'Home', icon: House, to: '/', end: true, keywords: 'trang chủ' },
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    to: '/dashboard',
    end: false,
    keywords: 'bảng điều khiển tổng quan',
  },
  {
    id: 'vocabulary',
    label: 'Vocabulary',
    icon: BookOpen,
    to: '/vocabulary',
    end: false,
    keywords: 'từ vựng',
  },
  {
    id: 'goals',
    label: 'Daily Goals',
    icon: Target,
    to: '/goals',
    end: false,
    keywords: 'mục tiêu hằng ngày',
  },
  {
    id: 'study-sessions',
    label: 'Study Sessions',
    icon: Clock3,
    to: '/study-sessions',
    end: false,
    keywords: 'buổi học phiên học',
  },
  { id: 'statistics', label: 'Statistics', icon: ChartNoAxesCombined, disabled: true },
  { id: 'quiz', label: 'Quiz', icon: ClipboardList, disabled: true },
  { id: 'ai-feedback', label: 'AI Feedback', icon: Sparkles, disabled: true },
]

// Profile và Settings dùng cùng một route; tránh hai mục cùng active.
export const accountNavigationItems: readonly AppNavigationItem[] = [
  {
    id: 'profile',
    label: 'Profile & Settings',
    icon: UserRound,
    to: '/profile',
    end: false,
    keywords: 'hồ sơ cài đặt tài khoản',
  },
]

export const implementedNavigationItems = [...navigationItems, ...accountNavigationItems].filter(
  (item): item is AppNavigationItem & { to: string } => Boolean(item.to) && !item.disabled,
)
