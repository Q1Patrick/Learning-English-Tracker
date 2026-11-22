import type { ComponentPropsWithoutRef, ReactNode, Ref } from 'react'

import './form-controls.css'

export interface FormFieldProps extends Omit<ComponentPropsWithoutRef<'input'>, 'children'> {
  id: string
  label: string
  errors?: readonly string[]
  hint?: string
  leadingIcon?: ReactNode
  trailingControl?: ReactNode
  ref?: Ref<HTMLInputElement>
}

// Field giữ liên kết label/helper/lỗi; form cha quản lý validation, thông báo và focus khi submit.
export default function FormField({
  id,
  label,
  errors = [],
  hint,
  leadingIcon,
  trailingControl,
  ref,
  className,
  'aria-describedby': externalDescription,
  'aria-invalid': externalInvalid,
  ...inputProps
}: FormFieldProps) {
  const hasErrors = errors.length > 0
  const isInvalid = hasErrors
    || (externalInvalid !== undefined && externalInvalid !== false && externalInvalid !== 'false')
  const descriptionIds = [...new Set([
    ...(externalDescription?.split(/\s+/) ?? []),
    hint ? `${id}-hint` : undefined,
    hasErrors ? `${id}-errors` : undefined,
  ])].filter(Boolean).join(' ') || undefined

  return (
    <div
      className="auth-field"
      data-invalid={isInvalid || undefined}
      data-disabled={inputProps.disabled || undefined}
    >
      <label className="auth-field__label" htmlFor={id}>{label}</label>
      <div className="auth-field__control">
        {leadingIcon && <span className="auth-field__icon" aria-hidden="true">{leadingIcon}</span>}
        <input
          {...inputProps}
          ref={ref}
          id={id}
          className={['auth-field__input', className].filter(Boolean).join(' ')}
          aria-invalid={hasErrors ? true : externalInvalid}
          aria-describedby={descriptionIds}
        />
        {trailingControl && <span className="auth-field__trailing">{trailingControl}</span>}
      </div>
      {hint && <p id={`${id}-hint`} className="auth-field__hint">{hint}</p>}
      {hasErrors && (
        <ul id={`${id}-errors`} className="auth-field__errors">
          {errors.map((message, index) => <li key={`${id}-error-${index}`}>{message}</li>)}
        </ul>
      )}
    </div>
  )
}
