import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import type { ReactNode } from 'react'

import FormField from './FormField'
import type { FormFieldProps } from './FormField'

export interface PasswordFieldProps extends Omit<FormFieldProps, 'type' | 'trailingControl'> {
  showIcon?: ReactNode
  hideIcon?: ReactNode
  showLabel?: string
  hideLabel?: string
}

// Chỉ lưu trạng thái hiển thị; giá trị mật khẩu và ref vẫn do form cha quản lý.
export default function PasswordField({
  label,
  id,
  disabled,
  showIcon,
  hideIcon,
  showLabel,
  hideLabel,
  ...inputProps
}: PasswordFieldProps) {
  const [isVisible, setIsVisible] = useState(false)
  const toggleLabel = isVisible
    ? hideLabel ?? `Ẩn nội dung trường ${label}`
    : showLabel ?? `Hiện nội dung trường ${label}`
  const toggleIcon = isVisible
    ? hideIcon ?? <EyeOff size={24} aria-hidden="true" />
    : showIcon ?? <Eye size={24} aria-hidden="true" />

  return (
    <FormField
      {...inputProps}
      id={id}
      label={label}
      disabled={disabled}
      type={isVisible ? 'text' : 'password'}
      trailingControl={(
        <button
          className="auth-field__toggle"
          type="button"
          disabled={disabled}
          aria-label={toggleLabel}
          aria-controls={id}
          onClick={() => setIsVisible((visible) => !visible)}
        >
          <span aria-hidden="true">{toggleIcon}</span>
        </button>
      )}
    />
  )
}
