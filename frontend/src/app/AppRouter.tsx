import { Navigate, Route, Routes, useLocation } from 'react-router'

import LoginPage from '../features/auth/LoginPage'
import RegisterPage from '../features/auth/RegisterPage'
import DashboardPage from '../features/dashboard/DashboardPage'
import DailyGoalsPage from '../features/goals/DailyGoalsPage'
import HomePage from '../features/home/HomePage'
import NotFoundPage from '../features/not-found/NotFoundPage'
import ProfileSettingsPage from '../features/profile/ProfileSettingsPage'
import StudySessionsPage from '../features/study-sessions/StudySessionsPage'
import VocabularyPage from '../features/vocabulary/VocabularyPage'
import AuthLayout from './layouts/AuthLayout'
import MainLayout from './layouts/MainLayout'
import PublicLayout from './layouts/PublicLayout'

function DailyGoalsAlias() {
  const { search, hash } = useLocation()

  // Giữ bộ lọc/anchor và thay history để Back không lặp lại URL alias.
  return <Navigate to={{ pathname: '/goals', search, hash }} replace />
}

// Layout không có path: URL hiện có được giữ nguyên; Outlet nhận trang con tương ứng.
export default function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
      </Route>
      <Route element={<AuthLayout variant="login" />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route element={<AuthLayout variant="register" />}>
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route path="/daily-goals" element={<DailyGoalsAlias />} />

      {/* Đây là các trang khung; bảo vệ bằng phiên đăng nhập thật thuộc phần tích hợp auth. */}
      <Route element={<MainLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/vocabulary" element={<VocabularyPage />} />
        <Route path="/study-sessions" element={<StudySessionsPage />} />
        <Route path="/goals" element={<DailyGoalsPage />} />
        <Route path="/profile" element={<ProfileSettingsPage />} />
      </Route>

      {/* Bắt URL không tồn tại trong React; HTTP fallback của hosting cấu hình riêng. */}
      <Route element={<PublicLayout />}>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
