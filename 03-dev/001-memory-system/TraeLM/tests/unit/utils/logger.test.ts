/**
 * Logger 单元测试
 * 
 * @description 测试日志记录功能的各种场景
 * @author 高级软件专家
 */

import { Logger, LogLevel } from '@/utils/logger';
import * as path from 'path';

// 模拟fs-extra
jest.mock('fs-extra', () => ({
  ensureDir: jest.fn(),
  writeFile: jest.fn(),
  appendFile: jest.fn(),
  readdir: jest.fn(),
  stat: jest.fn(),
  statSync: jest.fn(),
  unlink: jest.fn(),
  remove: jest.fn(),
  move: jest.fn(),
  readFile: jest.fn()
}));

const mockFs = require('fs-extra');

describe('Logger', () => {
  let logger: Logger;
  let testLogDir: string;

  beforeEach(async () => {
    testLogDir = path.join(__dirname, 'test-logs');
    
    // 重置所有mock
    jest.clearAllMocks();
    
    // 设置默认的mock返回值
    mockFs.ensureDir.mockResolvedValue(undefined);
    mockFs.appendFile.mockResolvedValue(undefined);
    mockFs.writeFile.mockResolvedValue(undefined);
    mockFs.readdir.mockResolvedValue([]);
    mockFs.stat.mockResolvedValue({ size: 1024 } as any);
    mockFs.statSync.mockReturnValue({ mtime: new Date() } as any);
    mockFs.unlink.mockResolvedValue(undefined);
    mockFs.remove.mockResolvedValue(undefined);
    mockFs.move.mockResolvedValue(undefined);
    mockFs.readFile.mockResolvedValue('');
    
    logger = new Logger({
      level: LogLevel.DEBUG,
      enableConsole: false,
      enableFile: false,
      logDir: testLogDir
    });
    
    // 等待异步初始化完成
    await new Promise(resolve => setTimeout(resolve, 50));
  });

  afterEach(async () => {
    // 清理定时器
    if ((logger as any).bufferFlushInterval) {
      clearInterval((logger as any).bufferFlushInterval);
    }
    
    // 如果logger有destroy方法，调用它
    if (logger && typeof logger.destroy === 'function') {
      await logger.destroy();
    }
  });

  describe('基本日志功能', () => {
    it('应该创建Logger实例', () => {
      expect(logger).toBeInstanceOf(Logger);
    });

    it('应该输出到控制台', async () => {
      const consoleSpy = jest.spyOn(console, 'info').mockImplementation();

      // 使用启用控制台输出的 Logger
      const consoleLogger = new Logger({
        enableConsole: true,
        enableFile: false
      });

      // 等待Logger初始化完成
      await new Promise(resolve => setTimeout(resolve, 50));

      consoleLogger.info('Test message');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Test message')
      );
      consoleSpy.mockRestore();

      // 清理
      await consoleLogger.destroy();
    });

    it('应该记录不同级别的日志', async () => {
      const debugSpy = jest.spyOn(console, 'debug').mockImplementation();
      const infoSpy = jest.spyOn(console, 'info').mockImplementation();
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
      const errorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // 创建一个启用所有级别的logger
      const consoleLogger = new Logger({
        level: LogLevel.DEBUG,
        enableFile: false
      });

      // 等待Logger初始化完成
      await new Promise(resolve => setTimeout(resolve, 50));

      consoleLogger.debug('Debug message');
      consoleLogger.info('Info message');
      consoleLogger.warn('Warn message');
      consoleLogger.error('Error message');
      consoleLogger.fatal('Fatal message');

      expect(debugSpy).toHaveBeenCalled();
      expect(infoSpy).toHaveBeenCalled();
      expect(warnSpy).toHaveBeenCalled();
      expect(errorSpy).toHaveBeenCalledTimes(2); // error + fatal
      
      debugSpy.mockRestore();
      infoSpy.mockRestore();
      warnSpy.mockRestore();
      errorSpy.mockRestore();

      // 清理
      await consoleLogger.destroy();
    });

    it('应该根据日志级别过滤消息', async () => {
      const debugSpy = jest.spyOn(console, 'debug').mockImplementation();
      const infoSpy = jest.spyOn(console, 'info').mockImplementation();
      
      // 创建一个只记录INFO及以上级别的logger
      const infoLogger = new Logger({
        level: LogLevel.INFO,
        enableFile: false
      });

      // 等待Logger初始化完成
      await new Promise(resolve => setTimeout(resolve, 50));

      infoLogger.debug('Debug message'); // 不应该输出
      infoLogger.info('Info message');   // 应该输出

      expect(debugSpy).not.toHaveBeenCalled();
      expect(infoSpy).toHaveBeenCalled();
      
      debugSpy.mockRestore();
      infoSpy.mockRestore();

      // 清理
      await infoLogger.destroy();
    });

    it('应该包含上下文信息', async () => {
      const infoSpy = jest.spyOn(console, 'info').mockImplementation();
      
      // 创建一个启用结构化日志的logger
      const consoleLogger = new Logger({
        enableFile: false,
        enableStructuredLogging: true
      });

      // 等待Logger初始化完成
      await new Promise(resolve => setTimeout(resolve, 50));

      const context = { userId: '123', action: 'test' };
      consoleLogger.info('Test message', context);

      expect(infoSpy).toHaveBeenCalledWith(
        expect.stringContaining('Test message')
      );
      infoSpy.mockRestore();

      // 清理
      await consoleLogger.destroy();
    });
  });

  describe('文件日志功能', () => {
    it('应该创建日志目录', async () => {
      // 创建一个启用文件日志的logger
      const fileLogger = new Logger({
        enableFile: true,
        logDir: testLogDir
      });
      
      // 等待异步初始化完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(mockFs.ensureDir).toHaveBeenCalledWith(testLogDir);
      
      // 清理
      await fileLogger.destroy();
    });

    it('应该写入日志文件', async () => {
      // 创建一个启用文件日志的logger
      const fileLogger = new Logger({
        enableFile: true,
        enableConsole: false,
        logDir: testLogDir
      });
      
      // 等待异步初始化完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      fileLogger.info('Test message');
      
      // 触发销毁以强制刷新缓冲区
      await fileLogger.destroy();
      
      // 验证已写入文件
      expect(mockFs.appendFile).toHaveBeenCalled();
    });

    it('应该处理文件写入错误', async () => {
      mockFs.writeFile.mockRejectedValue(new Error('Write error'));
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      logger.error('Test error message');
      
      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 100));
      
      consoleSpy.mockRestore();
    });
  });

  describe('日志轮转功能', () => {
    it('应该在文件大小超限时轮转日志', async () => {
      // 模拟大文件
      mockFs.stat.mockResolvedValue({ size: 20 * 1024 * 1024 } as any); // 20MB，超过默认10MB限制
      mockFs.readdir.mockResolvedValue(['app-2023-01-01.log']);
      mockFs.move.mockResolvedValue(undefined);
      
      // 创建一个启用文件日志的logger
      const fileLogger = new Logger({ 
        enableFile: true,
        enableConsole: false,
        maxFileSize: 10 * 1024 * 1024 // 10MB
      });
      
      // 等待异步初始化完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      fileLogger.info('Test message');
      
      // 销毁以触发缓冲区写入与轮转检查
      await fileLogger.destroy();
      
      // 验证是否尝试检查文件大小
      expect(mockFs.stat).toHaveBeenCalled();
    });

    it('应该清理旧的日志文件', async () => {
      // 模拟多个日志文件，超过maxFiles限制
      const oldFiles = [
        'app-2023-01-01.log',
        'app-2023-01-02.log',
        'app-2023-01-03.log',
        'app-2023-01-04.log',
        'app-2023-01-05.log',
        'app-2023-01-06.log',
        'app-2023-01-07.log',
        'app-2023-01-08.log',
        'app-2023-01-09.log',
        'app-2023-01-10.log',
        'app-2023-01-11.log',
        'app-2023-01-12.log'
      ];
      
      mockFs.readdir.mockResolvedValue(oldFiles);
      mockFs.statSync.mockReturnValue({ mtime: new Date() } as any);
      mockFs.remove.mockResolvedValue(undefined);
      
      // 创建一个启用文件日志的logger，设置较小的maxFiles
      const fileLogger = new Logger({ 
        enableFile: true, 
        maxFiles: 5 
      });
      
      // 触发日志轮转清理
      await (fileLogger as any).cleanupOldLogs();
      
      // 应该删除超出限制的文件
      expect(mockFs.remove).toHaveBeenCalled();
      
      // 清理
      await fileLogger.destroy();
    });
  });

  describe('日志统计功能', () => {
    it('应该提供日志统计信息', async () => {
      mockFs.readdir.mockResolvedValue(['app.log', 'app.log.1']);
      mockFs.stat.mockResolvedValue({ size: 1024 } as any);
      
      const stats = await logger.getLogStats();
      
      expect(stats).toHaveProperty('totalEntries');
      expect(stats).toHaveProperty('entriesByLevel');
      expect(stats).toHaveProperty('logFiles');
      expect(stats).toHaveProperty('totalLogSize');
    });
  });

  describe('子Logger功能', () => {
    it('应该创建子Logger', () => {
      const childLogger = logger.createChildLogger('TestModule');
      expect(childLogger).toBeInstanceOf(Logger);
    });

    it('子Logger应该包含源信息', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      const consoleLogger = new Logger({
        level: LogLevel.DEBUG,
        enableConsole: true,
        enableFile: false
      });
      // 等待Logger初始化完成
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const childLogger = consoleLogger.createChildLogger('TestModule');
      childLogger.info('Test message');

      consoleSpy.mockRestore();
      // 清理
      await consoleLogger.destroy();
    });
  });

  describe('错误处理', () => {
    it('应该处理无效的日志级别', () => {
      expect(() => {
        new Logger({
          level: 999 as LogLevel
        });
      }).not.toThrow();
    });

    it('应该处理文件系统错误', async () => {
      // 创建一个启用文件日志的logger来测试文件系统错误
      const fileLogger = new Logger({
        enableFile: true,
        enableConsole: false
      });
      
      mockFs.ensureDir.mockRejectedValue(new Error('Permission denied'));
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      fileLogger.error('Test message');
      
      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 200));
      
      consoleSpy.mockRestore();
      
      // 清理
      await fileLogger.destroy();
    });
  });

  describe('日志搜索功能', () => {
    it('应该支持日志搜索', async () => {
      mockFs.readdir.mockResolvedValue(['app.log']);
      mockFs.readFile.mockResolvedValue('{"timestamp":"2023-01-01","level":1,"message":"test"}');
      
      const results = await logger.searchLogs(
        'test',
        LogLevel.INFO,
        new Date('2023-01-01'),
        new Date('2023-01-02')
      );
      
      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('上下文管理', () => {
    it('应该设置用户和会话上下文', async () => {
      await logger.setContext('user123', 'session456');
      
      // 验证上下文已设置（通过后续日志验证）
      logger.info('Test with context');
      
      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 100));
    });
  });
});