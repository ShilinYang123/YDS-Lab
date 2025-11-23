// 主题相关类型定义

import type React from 'react';

export interface ThemeColors {
  primary: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  secondary: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  gray: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  success: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  warning: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  error: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
}

export interface ThemeConfig {
  colors: ThemeColors;
  fontFamily: {
    sans: string[];
    mono: string[];
  };
  spacing: Record<string, string>;
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  boxShadow: {
    soft: string;
    medium: string;
    strong: string;
  };
  animation: {
    'fade-in': string;
    'slide-up': string;
    'bounce-subtle': string;
  };
}

export interface ThemeContextType {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  colors: ThemeColors;
  isDark: boolean;
}

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';
export type InputSize = 'sm' | 'md' | 'lg';
export type CardVariant = 'default' | 'outlined' | 'elevated';
export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface ComponentSizes {
  button: ButtonSize;
  input: InputSize;
  modal: ModalSize;
}

export interface ComponentVariants {
  button: ButtonVariant;
  card: CardVariant;
}

export interface DesignTokens {
  spacing: Record<string, number>;
  typography: {
    fontSize: Record<string, string>;
    fontWeight: Record<string, string>;
    lineHeight: Record<string, string>;
  };
  colors: ThemeColors;
  borderRadius: Record<string, string>;
  shadows: Record<string, string>;
  transitions: {
    fast: string;
    normal: string;
    slow: string;
  };
}

// 组件属性接口
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  testId?: string;
}

export interface BaseComponentWithVariant<T extends string> extends BaseComponentProps {
  variant?: T;
}

export interface BaseComponentWithSize<T extends string> extends BaseComponentProps {
  size?: T;
}

export interface BaseComponentWithTheme extends BaseComponentProps {
  theme?: 'light' | 'dark';
}

// 状态类型
export type ComponentStatus = 'success' | 'warning' | 'error' | 'info';

// 尺寸映射
export const SIZE_MAP = {
  sm: { button: 'px-3 py-1.5 text-sm', input: 'px-2 py-1 text-sm', modal: 'max-w-sm' },
  md: { button: 'px-4 py-2 text-sm', input: 'px-3 py-2 text-sm', modal: 'max-w-md' },
  lg: { button: 'px-4 py-2 text-base', input: 'px-3 py-2 text-base', modal: 'max-w-lg' },
  xl: { button: 'px-6 py-3 text-base', input: 'px-4 py-3 text-base', modal: 'max-w-xl' },
};

// 变体映射
export const VARIANT_MAP = {
  button: {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    outline: 'btn-outline',
    ghost: 'btn-ghost',
    danger: 'bg-error-600 text-white hover:bg-error-700 focus:ring-error-500',
  },
  card: {
    default: 'card',
    outlined: 'border-2 border-gray-200 bg-white',
    elevated: 'shadow-medium bg-white',
  },
};