import { EventEmitter } from 'events';
import { logger } from './logger';
import type { PerformanceConfig } from '../types/base';

export interface SystemMetrics {
  timestamp: Date;
  cpu: {
    usage: number; // percentage
    loadAverage: number[];
  };
  memory: {
    used: number; // bytes
    total: number; // bytes
    usage: number; // percentage
    heapUsed: number; // bytes
    heapTotal: number; // bytes
  };
  network: {
    bytesIn: number;
    bytesOut: number;
    connectionsActive: number;
  };
  process: {
    uptime: number; // seconds
    pid: number;
  };
}

export interface OperationMetrics {
  operationId: string;
  operationType: string;
  startTime: Date;
  endTime?: Date;
  duration?: number; // milliseconds
  success: boolean;
  errorMessage?: string;
  metadata?: any;
}

export class PerformanceMonitor extends EventEmitter {
  private config: PerformanceConfig;
  private systemMetricsHistory: SystemMetrics[] = [];
  private operationMetrics: Map<string, OperationMetrics> = new Map();
  private operationHistory: OperationMetrics[] = [];
  private monitoringInterval: NodeJS.Timeout | null = null;
  private isMonitoring: boolean = false;
  // @ts-ignore: startTime is used in startMonitoring method
  private startTime: Date = new Date();

  constructor(config: Partial<PerformanceConfig> = {}) {
    super();
    
    this.config = {
      enableCPUMonitoring: true,
      enableMemoryMonitoring: true,
      enableNetworkMonitoring: false, // 绠€鍖栧疄鐜帮紝榛樿鍏抽棴
      monitoringInterval: 5000, // 5绉?
      alertThresholds: {
        cpuUsage: 80,
        memoryUsage: 85,
        responseTime: 5000
      },
      historySize: 1000,
      ...config
    };
  }

  public startMonitoring(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.startTime = new Date();
    
    this.monitoringInterval = setInterval(() => {
      this.collectSystemMetrics();
    }, this.config.monitoringInterval);
    
    logger.info('Performance monitoring started', { config: this.config }, 'PerformanceMonitor');
    this.emit('monitoringStarted');
  }

  public stopMonitoring(): void {
    if (!this.isMonitoring) return;
    
    this.isMonitoring = false;
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
    
    logger.info('Performance monitoring stopped', {}, 'PerformanceMonitor');
    this.emit('monitoringStopped');
  }

  private collectSystemMetrics(): void {
    try {
      const metrics: SystemMetrics = {
        timestamp: new Date(),
        cpu: this.getCPUMetrics(),
        memory: this.getMemoryMetrics(),
        network: this.getNetworkMetrics(),
        process: this.getProcessMetrics()
      };

      this.systemMetricsHistory.push(metrics);
      
      // 淇濇寔鍘嗗彶璁板綍鍦ㄥ悎鐞嗚寖鍥村唴
      if (this.systemMetricsHistory.length > this.config.historySize) {
        this.systemMetricsHistory.shift();
      }

      // 妫€鏌ュ憡璀﹂槇鍊?
      this.checkAlerts(metrics);
      
      this.emit('metricsCollected', metrics);
      
    } catch (error) {
      logger.error('Failed to collect system metrics', { error }, 'PerformanceMonitor');
      this.emit('metricsError', error);
    }
  }

  private getCPUMetrics(): SystemMetrics['cpu'] {
    if (!this.config.enableCPUMonitoring) {
      return { usage: 0, loadAverage: [] };
    }

    // 绠€鍖栫殑CPU浣跨敤鐜囪绠楋紙鍦ㄥ疄闄呯幆澧冧腑闇€瑕佷娇鐢ㄧ郴缁烝PI锛?
    const usage = Math.random() * 100; // 妯℃嫙CPU浣跨敤鐜?
    const loadAverage = [1.0, 1.2, 1.1]; // 妯℃嫙璐熻浇骞冲潎鍊?
    
    return { usage, loadAverage };
  }

  private getMemoryMetrics(): SystemMetrics['memory'] {
    if (!this.config.enableMemoryMonitoring) {
      return { used: 0, total: 0, usage: 0, heapUsed: 0, heapTotal: 0 };
    }

    const memUsage = process.memoryUsage();
    const totalMemory = 8 * 1024 * 1024 * 1024; // 鍋囪8GB鎬诲唴瀛?
    const usedMemory = memUsage.rss;
    
    return {
      used: usedMemory,
      total: totalMemory,
      usage: (usedMemory / totalMemory) * 100,
      heapUsed: memUsage.heapUsed,
      heapTotal: memUsage.heapTotal
    };
  }

  private getNetworkMetrics(): SystemMetrics['network'] {
    if (!this.config.enableNetworkMonitoring) {
      return { bytesIn: 0, bytesOut: 0, connectionsActive: 0 };
    }

    // 绠€鍖栧疄鐜帮紝杩斿洖妯℃嫙鏁版嵁
    return {
      bytesIn: Math.floor(Math.random() * 1000000),
      bytesOut: Math.floor(Math.random() * 1000000),
      connectionsActive: Math.floor(Math.random() * 100)
    };
  }

  private getProcessMetrics(): SystemMetrics['process'] {
    return {
      uptime: process.uptime(),
      pid: process.pid
    };
  }

  private checkAlerts(metrics: SystemMetrics): void {
    const alerts: string[] = [];
    
    if (metrics.cpu.usage > this.config.alertThresholds.cpuUsage) {
      alerts.push(`High CPU usage: ${metrics.cpu.usage.toFixed(2)}%`);
    }
    
    if (metrics.memory.usage > this.config.alertThresholds.memoryUsage) {
      alerts.push(`High memory usage: ${metrics.memory.usage.toFixed(2)}%`);
    }
    
    if (alerts.length > 0) {
      logger.warn('Performance alerts triggered', { alerts, metrics }, 'PerformanceMonitor');
      this.emit('performanceAlert', { alerts, metrics });
    }
  }

  public startOperation(operationType: string, metadata?: any): string {
    const operationId = `${operationType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const operation: OperationMetrics = {
      operationId,
      operationType,
      startTime: new Date(),
      success: false,
      metadata
    };
    
    this.operationMetrics.set(operationId, operation);
    
    logger.debug('Operation started', { operationId, operationType, metadata }, 'PerformanceMonitor');
    this.emit('operationStarted', operation);
    
    return operationId;
  }

  public endOperation(operationId: string, success: boolean = true, errorMessage?: string): OperationMetrics | undefined {
    const operation = this.operationMetrics.get(operationId);
    if (!operation) {
      logger.warn('Attempted to end unknown operation', { operationId }, 'PerformanceMonitor');
      return undefined;
    }
    
    operation.endTime = new Date();
    operation.duration = operation.endTime.getTime() - operation.startTime.getTime();
    operation.success = success;
    if (errorMessage !== undefined) {
      operation.errorMessage = errorMessage;
    }
    
    // 绉诲姩鍒板巻鍙茶褰?
    this.operationHistory.push({ ...operation });
    this.operationMetrics.delete(operationId);
    
    // 淇濇寔鍘嗗彶璁板綍鍦ㄥ悎鐞嗚寖鍥村唴
    if (this.operationHistory.length > this.config.historySize) {
      this.operationHistory.shift();
    }
    
    // 妫€鏌ュ搷搴旀椂闂村憡璀?
    if (operation.duration! > this.config.alertThresholds.responseTime) {
      logger.warn('Slow operation detected', { 
        operationId, 
        duration: operation.duration,
        threshold: this.config.alertThresholds.responseTime 
      }, 'PerformanceMonitor');
      this.emit('slowOperation', operation);
    }
    
    logger.debug('Operation completed', { 
      operationId, 
      duration: operation.duration, 
      success 
    }, 'PerformanceMonitor');
    
    this.emit('operationCompleted', operation);
    
    return operation;
  }

  public measureAsync<T>(
    operationType: string, 
    operation: () => Promise<T>, 
    metadata?: any
  ): Promise<T> {
    const operationId = this.startOperation(operationType, metadata);
    
    return operation()
      .then(result => {
        this.endOperation(operationId, true);
        return result;
      })
      .catch(error => {
        this.endOperation(operationId, false, error.message);
        throw error;
      });
  }

  public measureSync<T>(
    operationType: string, 
    operation: () => T, 
    metadata?: any
  ): T {
    const operationId = this.startOperation(operationType, metadata);
    
    try {
      const result = operation();
      this.endOperation(operationId, true);
      return result;
    } catch (error) {
      this.endOperation(operationId, false, (error as Error).message);
      throw error;
    }
  }

  public getCurrentMetrics(): SystemMetrics | null {
    const lastMetrics = this.systemMetricsHistory.length > 0 ? 
      this.systemMetricsHistory[this.systemMetricsHistory.length - 1] : undefined;
    return lastMetrics || null;
  }

  // 鍏煎鏃ф帴鍙ｏ細鎻愪緵 getMetrics 鍒悕锛岃繑鍥炲綋鍓嶇郴缁熸寚鏍?
  public getMetrics(): SystemMetrics | null {
    return this.getCurrentMetrics();
  }

  
  // 兼容接口：记录自定义指标（与旧版 recordMetric 调用兼容）
  // 兼容接口：记录自定义指标（与旧版 recordMetric 调用兼容）
  public recordMetric(name: string, value: number | Record<string, any>, metadata?: any): void {
    try {
      const payload = { name, value, metadata, timestamp: new Date() };
      // 将指标作为一次操作记录，便于统一统计
      const operationId = this.startOperation('custom_metric', payload);
      this.endOperation(operationId, true);
      this.emit('metricRecorded', payload);
    } catch (error) {
      logger.warn('Failed to record metric', { name, value, error }, 'PerformanceMonitor');
    }
  }  public getMetricsHistory(minutes?: number): SystemMetrics[] {
    if (!minutes) return [...this.systemMetricsHistory];
    
    const cutoffTime = new Date(Date.now() - minutes * 60 * 1000);
    return this.systemMetricsHistory.filter(m => m.timestamp >= cutoffTime);
  }

  public getOperationStats(operationType?: string): {
    totalOperations: number;
    successfulOperations: number;
    failedOperations: number;
    averageDuration: number;
    minDuration: number;
    maxDuration: number;
    successRate: number;
  } {
    const operations = operationType ? 
      this.operationHistory.filter(op => op.operationType === operationType) :
      this.operationHistory;
    
    if (operations.length === 0) {
      return {
        totalOperations: 0,
        successfulOperations: 0,
        failedOperations: 0,
        averageDuration: 0,
        minDuration: 0,
        maxDuration: 0,
        successRate: 0
      };
    }
    
    const successful = operations.filter(op => op.success);
    const durations = operations.map(op => op.duration!).filter(d => d !== undefined);
    
    return {
      totalOperations: operations.length,
      successfulOperations: successful.length,
      failedOperations: operations.length - successful.length,
      averageDuration: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      successRate: successful.length / operations.length
    };
  }

  public getOperationMetrics(): OperationMetrics[] {
    return [...this.operationHistory];
  }

  public isMonitoringActive(): boolean {
    return this.isMonitoring;
  }

  public getPerformanceReport(startTime?: number, endTime?: number): {
    systemMetrics: SystemMetrics[];
    operationMetrics: OperationMetrics[];
    summary: {
      totalOperations: number;
      averageResponseTime: number;
      successRate: number;
      errorRate: number;
    };
  } {
    // 杩囨护鎿嶄綔鎸囨爣锛堝鏋滄彁渚涗簡鏃堕棿鑼冨洿锛?
    let filteredOperations = [...this.operationHistory];
    if (startTime !== undefined && endTime !== undefined) {
      filteredOperations = this.operationHistory.filter(op => {
        const opTime = op.startTime.getTime();
        return opTime >= startTime && opTime <= endTime;
      });
    }

    // 璁＄畻姹囨€荤粺璁?
    const totalOperations = filteredOperations.length;
    const successfulOperations = filteredOperations.filter(op => op.success);
    const averageResponseTime = totalOperations > 0 
      ? filteredOperations.reduce((sum, op) => sum + (op.duration || 0), 0) / totalOperations
      : 0;
    const successRate = totalOperations > 0 ? (successfulOperations.length / totalOperations) * 100 : 0;
    const errorRate = 100 - successRate;

    return {
      systemMetrics: [...this.systemMetricsHistory],
      operationMetrics: filteredOperations,
      summary: {
        totalOperations,
        averageResponseTime,
        successRate,
        errorRate
      }
    };
  }

  public exportMetrics(): {
    systemMetrics: SystemMetrics[];
    operationMetrics: OperationMetrics[];
    config: PerformanceConfig;
    exportTime: Date;
  } {
    return {
      systemMetrics: [...this.systemMetricsHistory],
      operationMetrics: [...this.operationHistory],
      config: this.config,
      exportTime: new Date()
    };
  }

  public updateConfig(newConfig: Partial<PerformanceConfig>): void {
    // 楠岃瘉閰嶇疆鍙傛暟
    if (newConfig.monitoringInterval !== undefined && newConfig.monitoringInterval <= 0) {
      throw new Error('鐩戞帶闂撮殧蹇呴』澶т簬0');
    }
    if (newConfig.historySize !== undefined && newConfig.historySize <= 0) {
      throw new Error('鍘嗗彶璁板綍澶у皬蹇呴』澶т簬0');
    }
    if (newConfig.alertThresholds) {
      const { cpuUsage, memoryUsage, responseTime } = newConfig.alertThresholds;
      if (cpuUsage !== undefined && (cpuUsage < 0 || cpuUsage > 100)) {
        throw new Error('CPU浣跨敤鐜囬槇鍊煎繀椤诲湪0-100涔嬮棿');
      }
      if (memoryUsage !== undefined && (memoryUsage < 0 || memoryUsage > 100)) {
        throw new Error('鍐呭瓨浣跨敤鐜囬槇鍊煎繀椤诲湪0-100涔嬮棿');
      }
      if (responseTime !== undefined && responseTime <= 0) {
        throw new Error('鍝嶅簲鏃堕棿闃堝€煎繀椤诲ぇ浜?');
      }
    }

    this.config = { ...this.config, ...newConfig };
    
    // 濡傛灉鐩戞帶闂撮殧鏀瑰彉锛岄噸鍚洃鎺?
    if (this.isMonitoring && newConfig.monitoringInterval) {
      this.stopMonitoring();
      this.startMonitoring();
    }
  }

  public destroy(): void {
    this.stopMonitoring();
    this.systemMetricsHistory = [];
    this.operationHistory = [];
    this.operationMetrics.clear();
    this.removeAllListeners();
  }

  public clearHistory(): void {
    this.systemMetricsHistory = [];
    this.operationHistory = [];
    logger.info('Performance history cleared', {}, 'PerformanceMonitor');
    this.emit('historyCleared');
  }
}

// 鍏ㄥ眬鎬ц兘鐩戞帶瀹炰緥
export const performanceMonitor = new PerformanceMonitor();





