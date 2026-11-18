const applicationName = 'Learning English Tracker'

// Giữ tên trang cùng nhãn h1 hiện có; không phụ thuộc dữ liệu API hoặc tên tài khoản.
const pageTitles: ReadonlyMap<string, string> = new Map([
  ['/', applicationName],
  ['/login', 'Đăng nhập'],
  ['/register', 'Đăng ký'],
  ['/dashboard', 'Bảng điều khiển'],
  ['/vocabulary', 'Từ vựng'],
  ['/study-sessions', 'Buổi học'],
  ['/goals', 'Mục tiêu hằng ngày'],
  ['/profile', 'Hồ sơ và cài đặt'],
])

export function getPageTitle(pathname: string): string {
  // Router không phân biệt hoa/thường và chấp nhận dấu / cuối; title phải khớp trang.
  const normalizedPath = pathname.toLowerCase().replace(/\/+$/, '') || '/'
  const canonicalPath = normalizedPath === '/daily-goals' ? '/goals' : normalizedPath
  const title = pageTitles.get(canonicalPath) ?? 'Không tìm thấy trang'

  return title === applicationName ? applicationName : `${title} | ${applicationName}`
}
