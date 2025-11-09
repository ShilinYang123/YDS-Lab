import * as fs from 'fs-extra';
import * as path from 'path';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4
}

export interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  context?: any;
  source?: string;
  userId?: string;
  sessionId?: string;
}

export interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableFile: boolean;
  logDir: string;
  maxFileSize: number; // bytes
  maxFiles: number;
  dateFormat: string;
  enableStructuredLogging: boolean;
}

export class Logger {
  private config: LoggerConfig;
  private logBuffer: LogEntry[] = [];
  private bufferFlushInterval: NodeJS.Timeout | null = null;
  private currentLogFile: string | null = null;
  // 当使用字符串构造时，记录默认的 source 名称
  private defaultSource?: string;

  // 兼容旧用法：允许用字符串作为 source 构造
  constructor(config: Partial<LoggerConfig> | string = {}) {
    const resolvedConfig = typeof config === 'string' ? {} : config;
    this.config = {
      level: LogLevel.INFO,
      enableConsole: true,
      enableFile: true,
      logDir: './logs',
      maxFileSize: 10 * 1024 * 1024, // 10MB
      maxFiles: 10,
      dateFormat: 'YYYY-MM-DD',
      enableStructuredLogging: true,
      ...resolvedConfig
    };

    if (typeof config === 'string') {
      this.defaultSource = config;
    }

    this.initializeLogger();
  }

  private async initializeLogger(): Promise<void> {
    if (this.config.enableFile) {
      await fs.ensureDir(this.config.logDir);
      this.setupBufferFlush();
    }
  }

  private setupBufferFlush(): void {
    this.bufferFlushInterval = setInterval(() => {
      this.flushBuffer();
    }, 5000); // 每5秒刷新一次缓冲区
  }

  public debug(message: string, context?: any, source?: string): void {
    this.log(LogLevel.DEBUG, message, context, source);
  }

  public info(message: string, context?: any, source?: string): void {
    this.log(LogLevel.INFO, message, context, source);
  }

  public warn(message: string, context?: any, source?: string): void {
    this.log(LogLevel.WARN, message, context, source);
  }

  public error(message: string, context?: any, source?: string): void {
    this.log(LogLevel.ERROR, message, context, source);
  }

  public fatal(message: string, context?: any, source?: string): void {
    this.log(LogLevel.FATAL, message, context, source);
  }

  private log(level: LogLevel, message: string, context?: any, source?: string): void {
    if (level < this.config.level) return;

    const entry: LogEntry = {
      timestamp: new Date(),
      level,
      message,
      context,
      source: source || this.defaultSource || 'Unknown'
    };

    if (this.config.enableConsole) {
      this.logToConsole(entry);
    }

    if (this.config.enableFile) {
      this.logBuffer.push(entry);
    }
  }

  private logToConsole(entry: LogEntry): void {
    const levelName = LogLevel[entry.level];
    const timestamp = entry.timestamp.toISOString();
    const source = entry.source ? `[${entry.source}]` : '';
    
    let logMessage = `${timestamp} ${levelName} ${source} ${entry.message}`;
    
    if (entry.context && this.config.enableStructuredLogging) {
      logMessage += ` ${JSON.stringify(entry.context)}`;
    }

    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(logMessage);
        break;
      case LogLevel.INFO:
        console.info(logMessage);
        break;
      case LogLevel.WARN:
        console.warn(logMessage);
        break;
      case LogLevel.ERROR:
      case LogLevel.FATAL:
        console.error(logMessage);
        break;
    }
  }

  private async flushBuffer(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const entries = [...this.logBuffer];
    this.logBuffer = [];

    try {
      await this.writeToFile(entries);
    } catch (error) {
      console.error('Failed to write logs to file:', error);
      // 将失败的日志重新加入缓冲区
      this.logBuffer.unshift(...entries);
    }
  }

  private async writeToFile(entries: LogEntry[]): Promise<void> {
    const logFile = await this.getLogFile();
    const logLines = entries.map(entry => this.formatLogEntry(entry)).join('\n') + '\n';
    
    await fs.appendFile(logFile, logLines);
    
    // 检查文件大小并轮转
    await this.rotateLogIfNeeded(logFile);
  }

  private formatLogEntry(entry: LogEntry): string {
    if (this.config.enableStructuredLogging) {
      return JSON.stringify({
        timestamp: entry.timestamp.toISOString(),
        level: LogLevel[entry.level],
        message: entry.message,
        context: entry.context,
        source: entry.source,
        userId: entry.userId,
        sessionId: entry.sessionId
      });
    } else {
      const timestamp = entry.timestamp.toISOString();
      const level = LogLevel[entry.level];
      const source = entry.source ? `[${entry.source}]` : '';
      const context = entry.context ? ` ${JSON.stringify(entry.context)}` : '';
      
      return `${timestamp} ${level} ${source} ${entry.message}${context}`;
    }
  }

  private async getLogFile(): Promise<string> {
    const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const logFile = path.join(this.config.logDir, `app-${date}.log`);
    
    if (this.currentLogFile !== logFile) {
      this.currentLogFile = logFile;
    }
    
    return logFile;
  }

  private async rotateLogIfNeeded(logFile: string): Promise<void> {
    try {
      const stats = await fs.stat(logFile);
      if (stats.size > this.config.maxFileSize) {
        await this.rotateLog(logFile);
      }
    } catch (error) {
      // 文件不存在或其他错误，忽略
    }
  }

  private async rotateLog(logFile: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const rotatedFile = logFile.replace('.log', `-${timestamp}.log`);
    
    await fs.move(logFile, rotatedFile);
    
    // 清理旧日志文件
    await this.cleanupOldLogs();
  }

  private async cleanupOldLogs(): Promise<void> {
    try {
      const files = await fs.readdir(this.config.logDir);
      const logFiles = files
        .filter(file => file.endsWith('.log'))
        .map(file => ({
          name: file,
          path: path.join(this.config.logDir, file),
          stat: fs.statSync(path.join(this.config.logDir, file))
        }))
        .sort((a, b) => b.stat.mtime.getTime() - a.stat.mtime.getTime());

      // 保留最新的文件，删除多余的
      if (logFiles.length > this.config.maxFiles) {
        const filesToDelete = logFiles.slice(this.config.maxFiles);
        for (const file of filesToDelete) {
          await fs.remove(file.path);
        }
      }
    } catch (error) {
      console.error('Failed to cleanup old logs:', error);
    }
  }

  public async setContext(userId?: string, sessionId?: string): Promise<void> {
    // 为后续日志设置上下文
    this.logBuffer.forEach(entry => {
      if (userId) entry.userId = userId;
      if (sessionId) entry.sessionId = sessionId;
    });
  }

  public createChildLogger(source: string): Logger {
    const childLogger = new Logger(this.config);
    
    // 重写log方法以包含source
    const originalLog = childLogger.log.bind(childLogger);
    childLogger.log = (level: LogLevel, message: string, context?: any, childSource?: string) => {
      originalLog(level, message, context, childSource || source);
    };
    
    return childLogger;
  }

  public async getLogStats(): Promise<{
    totalEntries: number;
    entriesByLevel: Record<string, number>;
    logFiles: string[];
    totalLogSize: number;
  }> {
    const stats = {
      totalEntries: this.logBuffer.length,
      entriesByLevel: {} as Record<string, number>,
      logFiles: [] as string[],
      totalLogSize: 0
    };

    // 统计缓冲区中的日志级别
    for (const entry of this.logBuffer) {
      const levelName = LogLevel[entry.level];
      stats.entriesByLevel[levelName] = (stats.entriesByLevel[levelName] || 0) + 1;
    }

    // 统计文件信息
    try {
      const files = await fs.readdir(this.config.logDir);
      stats.logFiles = files.filter(file => file.endsWith('.log'));
      
      for (const file of stats.logFiles) {
        const filePath = path.join(this.config.logDir, file);
        const stat = await fs.stat(filePath);
        stats.totalLogSize += stat.size;
      }
    } catch (error) {
      // 忽略错误
    }

    return stats;
  }

  public async searchLogs(
    query: string, 
    level?: LogLevel, 
    startDate?: Date, 
    endDate?: Date
  ): Promise<LogEntry[]> {
    const results: LogEntry[] = [];
    
    // 搜索缓冲区
    for (const entry of this.logBuffer) {
      if (this.matchesSearchCriteria(entry, query, level, startDate, endDate)) {
        results.push(entry);
      }
    }
    
    // 搜索文件（简化实现）
    try {
      const files = await fs.readdir(this.config.logDir);
      for (const file of files) {
        if (file.endsWith('.log')) {
          const filePath = path.join(this.config.logDir, file);
          const content = await fs.readFile(filePath, 'utf-8');
          const lines = content.split('\n').filter(line => line.trim());
          
          for (const line of lines) {
            try {
              const entry = this.config.enableStructuredLogging ? 
                JSON.parse(line) : this.parseLogLine(line);
              
              if (entry && this.matchesSearchCriteria(entry, query, level, startDate, endDate)) {
                results.push(entry);
              }
            } catch (error) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to search log files:', error);
    }
    
    return results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  private matchesSearchCriteria(
    entry: LogEntry, 
    query: string, 
    level?: LogLevel, 
    startDate?: Date, 
    endDate?: Date
  ): boolean {
    // 级别过滤
    if (level !== undefined && entry.level !== level) return false;
    
    // 时间范围过滤
    if (startDate && entry.timestamp < startDate) return false;
    if (endDate && entry.timestamp > endDate) return false;
    
    // 文本搜索
    if (query) {
      const searchText = `${entry.message} ${JSON.stringify(entry.context || {})}`.toLowerCase();
      if (!searchText.includes(query.toLowerCase())) return false;
    }
    
    return true;
  }

  private parseLogLine(line: string): LogEntry | null {
    // 简化的日志行解析
    const match = line.match(/^(\S+)\s+(\S+)\s+(?:\[([^\]]+)\])?\s+(.+)$/);
    if (!match) return null;
    
    const [, timestamp, levelStr, source, message] = match;
    const level = LogLevel[levelStr as keyof typeof LogLevel];
    
    if (level === undefined) return null;
    
    return {
      timestamp: new Date(timestamp || Date.now()),
      level,
      message: message || '',
      source: source || 'Unknown'
    };
  }

  public async destroy(): Promise<void> {
    if (this.bufferFlushInterval) {
      clearInterval(this.bufferFlushInterval);
      this.bufferFlushInterval = null;
    }
    
    // 刷新剩余的缓冲区
    await this.flushBuffer();
  }
}

// 全局日志实例
export const logger = new Logger();