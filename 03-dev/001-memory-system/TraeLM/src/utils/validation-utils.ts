/**
 * 验证工具函数
 * 提供数据验证相关的实用工具
 */

/**
 * 验证邮箱格式
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证URL格式
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证字符串长度
 */
export function isValidLength(str: string, min: number, max?: number): boolean {
  if (str.length < min) {
    return false;
  }
  
  if (max !== undefined && str.length > max) {
    return false;
  }
  
  return true;
}

/**
 * 验证数字范围
 */
export function isInRange(num: number, min: number, max: number): boolean {
  return num >= min && num <= max;
}

/**
 * 验证对象是否包含必需属性
 */
export function hasRequiredProperties(obj: any, requiredProps: string[]): boolean {
  if (!obj || typeof obj !== 'object') {
    return false;
  }
  
  return requiredProps.every(prop => obj.hasOwnProperty(prop));
}

/**
 * 验证数组是否非空
 */
export function isNonEmptyArray(arr: any): arr is any[] {
  return Array.isArray(arr) && arr.length > 0;
}

/**
 * 验证字符串是否为有效的JSON
 */
export function isValidJson(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证日期格式
 */
export function isValidDate(date: any): date is Date {
  return date instanceof Date && !isNaN(date.getTime());
}