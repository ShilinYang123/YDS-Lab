import React from 'react';
import { cn } from '../../utils/cn';
import { CardVariant, BaseComponentProps } from '../../types/theme';

export interface CardProps extends BaseComponentProps {
  variant?: CardVariant;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  shadow?: 'none' | 'soft' | 'medium' | 'strong';
}

export interface CardHeaderProps extends BaseComponentProps {
  border?: boolean;
}

export interface CardBodyProps extends BaseComponentProps {
  spacing?: 'none' | 'sm' | 'md' | 'lg';
}

export interface CardFooterProps extends BaseComponentProps {
  border?: boolean;
  spacing?: 'none' | 'sm' | 'md' | 'lg';
}

// Card 主体组件
const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      className,
      variant = 'default',
      padding = 'md',
      hover = false,
      shadow = 'soft',
      ...props
    },
    ref
  ) => {
    const baseClasses = [
      'bg-white',
      'rounded-lg',
      'overflow-hidden',
    ];

    // 变体样式
    const variantClasses = {
      default: 'border border-gray-200',
      outlined: 'border-2 border-gray-200',
      elevated: shadow === 'none' ? 'border border-gray-200' : `shadow-${shadow} border border-gray-200`,
    };

    // 内边距样式
    const paddingClasses = {
      none: '',
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6',
    };

    // 悬停效果
    const hoverClasses = hover ? [
      'transition-all',
      'duration-200',
      'hover:shadow-medium',
      'hover:-translate-y-0.5',
      'cursor-pointer',
    ] : [];

    const classes = cn(
      baseClasses,
      variantClasses[variant],
      paddingClasses[padding],
      hoverClasses,
      className
    );

    return (
      <div
        ref={ref}
        className={classes}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card Header 组件
const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  (
    {
      children,
      className,
      border = true,
      ...props
    },
    ref
  ) => {
    const classes = cn(
      'px-4 py-3',
      border && 'border-b border-gray-200',
      className
    );

    return (
      <div
        ref={ref}
        className={classes}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// Card Body 组件
const CardBody = React.forwardRef<HTMLDivElement, CardBodyProps>(
  (
    {
      children,
      className,
      spacing = 'md',
      ...props
    },
    ref
  ) => {
    const spacingClasses = {
      none: '',
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6',
    };

    const classes = cn(
      spacingClasses[spacing],
      className
    );

    return (
      <div
        ref={ref}
        className={classes}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardBody.displayName = 'CardBody';

// Card Footer 组件
const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  (
    {
      children,
      className,
      border = true,
      spacing = 'md',
      ...props
    },
    ref
  ) => {
    const spacingClasses = {
      none: '',
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6',
    };

    const classes = cn(
      'bg-gray-50',
      border && 'border-t border-gray-200',
      spacingClasses[spacing],
      className
    );

    return (
      <div
        ref={ref}
        className={classes}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = 'CardFooter';

// 导出子组件
export { CardHeader, CardBody, CardFooter };

// 命名导出主组件
export default Card;

// 完整导出类型