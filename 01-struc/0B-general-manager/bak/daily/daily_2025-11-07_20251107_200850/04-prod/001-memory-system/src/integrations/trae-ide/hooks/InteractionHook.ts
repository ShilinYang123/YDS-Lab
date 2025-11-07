// src/integrations/trae-ide/hooks/InteractionHook.ts
import { EventEmitter } from 'events';
import { MemoryService } from '../../../services/MemoryService';
import { ContextExtractor } from '../../../utils/ContextExtractor';
import { Logger } from '../../../utils/logger';

// 定义事件类型枚举
export enum EventType {
  USER_INPUT = 'user_input',
  AGENT_RESPONSE = 'agent_response',
  CODE_EXECUTION = 'code_execution',
  FILE_CHANGE = 'file_change',
  ERROR_LOG = 'error_log',
  CONVERSATION_END = 'conversation_end'
}

// 定义交互事件接口
export interface InteractionEvent {
  type: EventType;
  data: any;
  timestamp: string;
  conversationId?: string;
}

// 定义IDE插件接口
export interface IDEPlugin extends EventEmitter {
  on(event: EventType, listener: (event: InteractionEvent) => void): this;
  emit(event: EventType, data: InteractionEvent): boolean;
}

export class InteractionHook {
  private plugin: IDEPlugin;
  private memoryService: MemoryService;
  private contextExtractor: ContextExtractor;
  private logger: Logger;
  private isEnabled: boolean = true;

  constructor(plugin: IDEPlugin) {
    this.plugin = plugin;
    this.memoryService = new MemoryService();
    this.contextExtractor = new ContextExtractor();
    this.logger = new Logger('InteractionHook');
    this.initEventListeners(); // 初始化监听器
  }

  // 初始化各类交互事件监听器
  private initEventListeners() {
    if (!this.isEnabled) return;

    try {
      // 1. 对话交互事件（用户输入+Agent响应）
      this.plugin.on(EventType.USER_INPUT, (event: InteractionEvent) => 
        this.handleUserInput(event.data)
      );
      this.plugin.on(EventType.AGENT_RESPONSE, (event: InteractionEvent) => 
        this.handleAgentResponse(event.data)
      );

      // 2. 开发操作事件
      this.plugin.on(EventType.CODE_EXECUTION, (event: InteractionEvent) => 
        this.handleCodeExecution(event.data)
      );
      this.plugin.on(EventType.FILE_CHANGE, (event: InteractionEvent) => 
        this.handleFileChange(event.data)
      );

      // 3. 系统事件
      this.plugin.on(EventType.ERROR_LOG, (event: InteractionEvent) => 
        this.handleErrorLog(event.data)
      );
      this.plugin.on(EventType.CONVERSATION_END, (event: InteractionEvent) => 
        this.handleConversationEnd(event.data.conversationId)
      );

      this.logger.info('Event listeners initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize event listeners:', error);
    }
  }

  // 处理用户输入事件
  private async handleUserInput(data: any) {
    try {
      const context = this.contextExtractor.extract({
        activeFile: data.activeFile,
        projectState: data.projectState,
        cursorPos: data.cursorPosition
      });

      // 提交至记忆服务（异步非阻塞）
      await this.memoryService.submitMemory({
        type: 'user_input',
        content: data.content,
        conversationId: data.conversationId,
        timestamp: new Date().toISOString(),
        context,
        metadata: {
          source: 'trae_ide',
          priority: this.calculatePriority(data.content)
        }
      });

      this.logger.debug('User input processed and stored');
    } catch (error) {
      this.logger.error('Error handling user input:', error);
    }
  }

  // 处理Agent响应事件
  private async handleAgentResponse(data: any) {
    try {
      await this.memoryService.submitMemory({
        type: 'agent_response',
        content: data.content,
        conversationId: data.conversationId,
        timestamp: new Date().toISOString(),
        metadata: {
          confidenceScore: data.confidenceScore,
          responseTime: data.responseTime,
          source: 'trae_ide',
          priority: 'high'
        }
      });

      this.logger.debug('Agent response processed and stored');
    } catch (error) {
      this.logger.error('Error handling agent response:', error);
    }
  }

  // 处理代码执行事件
  private async handleCodeExecution(data: any) {
    try {
      // 只记录重要的代码执行事件
      if (this.shouldRecordCodeExecution(data)) {
        await this.memoryService.submitMemory({
          type: 'code_execution',
          content: {
            command: data.command,
            result: data.result,
            exitCode: data.exitCode,
            duration: data.duration
          },
          conversationId: data.conversationId,
          timestamp: new Date().toISOString(),
          metadata: {
            source: 'trae_ide',
            priority: data.exitCode === 0 ? 'medium' : 'high'
          }
        });

        this.logger.debug('Code execution event processed and stored');
      }
    } catch (error) {
      this.logger.error('Error handling code execution:', error);
    }
  }

  // 处理文件变更事件
  private async handleFileChange(data: any) {
    try {
      // 只记录重要的文件变更
      if (this.shouldRecordFileChange(data)) {
        await this.memoryService.submitMemory({
          type: 'file_change',
          content: {
            filePath: data.filePath,
            changeType: data.changeType,
            diff: data.diff
          },
          conversationId: data.conversationId,
          timestamp: new Date().toISOString(),
          metadata: {
            source: 'trae_ide',
            priority: 'medium'
          }
        });

        this.logger.debug('File change event processed and stored');
      }
    } catch (error) {
      this.logger.error('Error handling file change:', error);
    }
  }

  // 处理错误日志事件
  private async handleErrorLog(data: any) {
    try {
      await this.memoryService.submitMemory({
        type: 'error_log',
        content: {
          error: data.error,
          stack: data.stack,
          context: data.context
        },
        conversationId: data.conversationId,
        timestamp: new Date().toISOString(),
        metadata: {
          source: 'trae_ide',
          priority: 'high',
          severity: data.severity || 'error'
        }
      });

      this.logger.debug('Error log processed and stored');
    } catch (error) {
      this.logger.error('Error handling error log:', error);
    }
  }

  // 处理对话结束事件
  private async handleConversationEnd(conversationId: string) {
    try {
      await this.memoryService.finalizeConversation(conversationId);
      this.logger.info(`Conversation ${conversationId} finalized`);
    } catch (error) {
      this.logger.error('Error handling conversation end:', error);
    }
  }

  // 计算内容优先级
  private calculatePriority(content: string): string {
    if (!content) return 'low';
    
    const highPriorityKeywords = ['error', 'bug', 'fix', 'issue', 'problem', 'help'];
    const mediumPriorityKeywords = ['implement', 'create', 'add', 'update', 'modify'];
    
    const lowerContent = content.toLowerCase();
    
    if (highPriorityKeywords.some(keyword => lowerContent.includes(keyword))) {
      return 'high';
    }
    
    if (mediumPriorityKeywords.some(keyword => lowerContent.includes(keyword))) {
      return 'medium';
    }
    
    return 'low';
  }

  // 判断是否应该记录代码执行事件
  private shouldRecordCodeExecution(data: any): boolean {
    // 过滤掉一些不重要的命令
    const ignoredCommands = ['ls', 'dir', 'pwd', 'echo'];
    return !ignoredCommands.includes(data.command?.split(' ')[0]);
  }

  // 判断是否应该记录文件变更事件
  private shouldRecordFileChange(data: any): boolean {
    // 过滤掉临时文件和不重要的文件
    const ignoredExtensions = ['.tmp', '.log', '.cache'];
    const ignoredPaths = ['node_modules', '.git', 'dist', 'build'];
    
    const filePath = data.filePath || '';
    
    return !ignoredExtensions.some(ext => filePath.endsWith(ext)) &&
           !ignoredPaths.some(path => filePath.includes(path));
  }

  // 启用/禁用自动记录
  public setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
    if (enabled) {
      this.initEventListeners();
    } else {
      this.plugin.removeAllListeners();
    }
    this.logger.info(`Auto recording ${enabled ? 'enabled' : 'disabled'}`);
  }

  // 获取当前状态
  public getStatus() {
    return {
      enabled: this.isEnabled,
      memoryServiceStatus: this.memoryService.getStatus(),
      lastActivity: new Date().toISOString()
    };
  }
}