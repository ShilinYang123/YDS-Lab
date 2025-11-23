import React from 'react';
import { cn } from '../../utils/cn';
import { InputSize, BaseComponentProps } from '../../types/theme';

export interface InputProps extends BaseComponentProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  error?: boolean;
  size?: InputSize;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  name?: string;
  id?: string;
  autoComplete?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = 'text',
      placeholder,
      value,
      defaultValue,
      disabled = false,
      readOnly = false,
      required = false,
      error = false,
      size = 'md',
      leftIcon,
      rightIcon,
      onChange,
      onFocus,
      onBlur,
      name,
      id,
      autoComplete,
      testId,
      ...props
    },
    ref
  ) => {
    const baseClasses = [
      'block',
      'w-full',
      'rounded-md',
      'border-gray-300',
      'shadow-sm',
      'placeholder-gray-400',
      'focus:outline-none',
      'focus:ring-1',
      'disabled:bg-gray-50',
      'disabled:text-gray-500',
      'disabled:cursor-not-allowed',
      'transition-colors',
      'duration-200',
    ];

    // 尺寸样式
    const sizeClasses = {
      sm: 'px-2 py-1 text-sm',
      md: 'px-3 py-2 text-sm',
      lg: 'px-3 py-2 text-base',
    };

    // 状态样式
    const stateClasses = [
      error ? [
        'border-error-300',
        'text-error-900',
        'focus:border-error-500',
        'focus:ring-error-500',
      ] : [
        'border-gray-300',
        'text-gray-900',
        'focus:border-primary-500',
        'focus:ring-primary-500',
      ],
      readOnly && 'bg-gray-50',
    ];

    const inputContainerClasses = cn(
      'relative',
      leftIcon && 'pl-10',
      rightIcon && 'pr-10'
    );

    const inputClasses = cn(
      baseClasses,
      sizeClasses[size],
      stateClasses.flat(),
      className
    );

    return (
      <div className={inputContainerClasses}>
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400 sm:text-sm">
              {leftIcon}
            </span>
          </div>
        )}
        
        <input
          ref={ref}
          type={type}
          className={inputClasses}
          placeholder={placeholder}
          value={value}
          defaultValue={defaultValue}
          disabled={disabled}
          readOnly={readOnly}
          required={required}
          onChange={onChange}
          onFocus={onFocus}
          onBlur={onBlur}
          name={name}
          id={id}
          autoComplete={autoComplete}
          data-testid={testId}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <span className="text-gray-400 sm:text-sm">
              {rightIcon}
            </span>
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;