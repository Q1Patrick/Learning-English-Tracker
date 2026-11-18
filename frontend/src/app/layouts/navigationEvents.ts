import type { MouseEvent } from 'react'

// Chỉ đóng menu/xóa query/đổi focus khi Link điều hướng ngay trong tab hiện tại.
// Ctrl/Meta/Shift/Alt-click và target khác để trình duyệt xử lý theo hành vi mặc định.
export function isSameTabNavigation(event: MouseEvent<HTMLAnchorElement>) {
  const target = event.currentTarget.getAttribute('target')

  return !event.defaultPrevented
    && event.button === 0
    && !event.ctrlKey
    && !event.metaKey
    && !event.shiftKey
    && !event.altKey
    && (!target || target === '_self')
}
