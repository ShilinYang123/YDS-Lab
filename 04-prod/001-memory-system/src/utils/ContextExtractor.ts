// src/utils/ContextExtractor.ts
import { Logger } from './logger';
import * as fs from 'fs';
import * as path from 'path';

export interface ContextData {
  activeFile?: string;
  projectState?: any;
  cursorPos?: {
    line: number;
    column: number;
  };
  workspaceRoot?: string;
  openFiles?: string[];
  gitBranch?: string;
  gitCommit?: string;
}

export interface ExtractedContext {
  file: {
    path?: string;
    name?: string;
    extension?: string;
    size?: number;
    lastModified?: string;
    content?: string;
    language?: string;
  };
  project: {
    name?: string;
    type?: string;
    dependencies?: string[];
    structure?: any;
  };
  workspace: {
    root?: string;
    openFiles?: string[];
    activeEditor?: string;
  };
  git: {
    branch?: string;
    commit?: string;
    status?: string;
  };
  cursor: {
    line?: number;
    column?: number;
    surroundingCode?: string;
  };
  environment: {
    platform: string;
    nodeVersion: string;
    timestamp: string;
  };
}

export class ContextExtractor {
  private logger: Logger;
  private cache: Map<string, any> = new Map();
  private cacheTimeout: number = 30000; // 30秒缓存

  constructor() {
    this.logger = new Logger('ContextExtractor');
  }

  // 主要的上下文提取方法
  public extract(contextData: ContextData): ExtractedContext {
    try {
      const context: ExtractedContext = {
        file: this.extractFileContext(contextData.activeFile),
        project: this.extractProjectContext(contextData.projectState, contextData.workspaceRoot),
        workspace: this.extractWorkspaceContext(contextData),
        git: this.extractGitContext(contextData.workspaceRoot),
        cursor: this.extractCursorContext(contextData.cursorPos, contextData.activeFile),
        environment: this.extractEnvironmentContext()
      };

      this.logger.debug('Context extracted successfully');
      return context;
    } catch (error) {
      this.logger.error('Error extracting context:', error);
      return this.getMinimalContext();
    }
  }

  // 提取文件上下文
  private extractFileContext(activeFile?: string): ExtractedContext['file'] {
    if (!activeFile) {
      return {};
    }

    try {
      // 检查缓存
      const cacheKey = `file_${activeFile}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) {
        return cached;
      }

      const fileContext: ExtractedContext['file'] = {
        path: activeFile,
        name: path.basename(activeFile),
        extension: path.extname(activeFile)
      };

      // 获取文件信息
      if (fs.existsSync(activeFile)) {
        const stats = fs.statSync(activeFile);
        fileContext.size = stats.size;
        fileContext.lastModified = stats.mtime.toISOString();

        // 读取文件内容（限制大小）
        if (stats.size < 100000) { // 100KB限制
          fileContext.content = fs.readFileSync(activeFile, 'utf8');
        }

        // 检测编程语言
        fileContext.language = this.detectLanguage(activeFile);
      }

      // 缓存结果
      this.setCachedData(cacheKey, fileContext);
      return fileContext;
    } catch (error) {
      this.logger.error('Error extracting file context:', error);
      return { path: activeFile };
    }
  }

  // 提取项目上下文
  private extractProjectContext(projectState?: any, workspaceRoot?: string): ExtractedContext['project'] {
    try {
      const cacheKey = `project_${workspaceRoot}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) {
        return cached;
      }

      const projectContext: ExtractedContext['project'] = {};

      if (workspaceRoot && fs.existsSync(workspaceRoot)) {
        // 检测项目类型和名称
        const packageJsonPath = path.join(workspaceRoot, 'package.json');
        if (fs.existsSync(packageJsonPath)) {
          try {
            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            projectContext.name = packageJson.name;
            projectContext.type = 'nodejs';
            projectContext.dependencies = Object.keys(packageJson.dependencies || {});
          } catch (error) {
            this.logger.warn('Error reading package.json:', error);
          }
        }

        // 检测其他项目类型
        if (fs.existsSync(path.join(workspaceRoot, 'pom.xml'))) {
          projectContext.type = 'maven';
        } else if (fs.existsSync(path.join(workspaceRoot, 'Cargo.toml'))) {
          projectContext.type = 'rust';
        } else if (fs.existsSync(path.join(workspaceRoot, 'go.mod'))) {
          projectContext.type = 'go';
        }

        // 获取项目结构
        projectContext.structure = this.getProjectStructure(workspaceRoot);
      }

      // 使用传入的项目状态
      if (projectState) {
        Object.assign(projectContext, projectState);
      }

      this.setCachedData(cacheKey, projectContext);
      return projectContext;
    } catch (error) {
      this.logger.error('Error extracting project context:', error);
      return {};
    }
  }

  // 提取工作区上下文
  private extractWorkspaceContext(contextData: ContextData): ExtractedContext['workspace'] {
    try {
      const workspace: ExtractedContext['workspace'] = {};
      if (contextData.workspaceRoot) {
        workspace.root = contextData.workspaceRoot;
      }
      if (contextData.openFiles && contextData.openFiles.length > 0) {
        workspace.openFiles = contextData.openFiles;
      }
      if (contextData.activeFile) {
        workspace.activeEditor = contextData.activeFile;
      }
      return workspace;
    } catch (error) {
      this.logger.error('Error extracting workspace context:', error);
      return {};
    }
  }

  // 提取Git上下文
  private extractGitContext(workspaceRoot?: string): ExtractedContext['git'] {
    if (!workspaceRoot) {
      return {};
    }

    try {
      const cacheKey = `git_${workspaceRoot}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) {
        return cached;
      }

      const gitContext: ExtractedContext['git'] = {};
      const gitDir = path.join(workspaceRoot, '.git');

      if (fs.existsSync(gitDir)) {
        // 获取当前分支
        const headPath = path.join(gitDir, 'HEAD');
        if (fs.existsSync(headPath)) {
          const headContent = fs.readFileSync(headPath, 'utf8').trim();
          if (headContent.startsWith('ref: refs/heads/')) {
            gitContext.branch = headContent.replace('ref: refs/heads/', '');
          }
        }

        // 获取最新提交
        try {
          const { execSync } = require('child_process');
          const commit = execSync('git rev-parse HEAD', { 
            cwd: workspaceRoot, 
            encoding: 'utf8' 
          }).trim();
          gitContext.commit = commit.substring(0, 8); // 短哈希

          const status = execSync('git status --porcelain', { 
            cwd: workspaceRoot, 
            encoding: 'utf8' 
          }).trim();
          gitContext.status = status ? 'dirty' : 'clean';
        } catch (error) {
          // Git命令执行失败，忽略
        }
      }

      this.setCachedData(cacheKey, gitContext);
      return gitContext;
    } catch (error) {
      this.logger.error('Error extracting git context:', error);
      return {};
    }
  }

  // 提取光标上下文
  private extractCursorContext(cursorPos?: { line: number; column: number }, activeFile?: string): ExtractedContext['cursor'] {
    try {
      const cursorContext: ExtractedContext['cursor'] = {};

      if (cursorPos) {
        cursorContext.line = cursorPos.line;
        cursorContext.column = cursorPos.column;

        // 获取光标周围的代码
        if (activeFile && fs.existsSync(activeFile)) {
          cursorContext.surroundingCode = this.getSurroundingCode(activeFile, cursorPos.line);
        }
      }

      return cursorContext;
    } catch (error) {
      this.logger.error('Error extracting cursor context:', error);
      return {};
    }
  }

  // 提取环境上下文
  private extractEnvironmentContext(): ExtractedContext['environment'] {
    return {
      platform: process.platform,
      nodeVersion: process.version,
      timestamp: new Date().toISOString()
    };
  }

  // 获取光标周围的代码
  private getSurroundingCode(filePath: string, line: number, range: number = 5): string {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      const startLine = Math.max(0, line - range);
      const endLine = Math.min(lines.length - 1, line + range);
      
      return lines.slice(startLine, endLine + 1).join('\n');
    } catch (error) {
      this.logger.error('Error getting surrounding code:', error);
      return '';
    }
  }

  // 检测编程语言
  private detectLanguage(filePath: string): string {
    const extension = path.extname(filePath).toLowerCase();
    const languageMap: { [key: string]: string } = {
      '.js': 'javascript',
      '.ts': 'typescript',
      '.jsx': 'javascript',
      '.tsx': 'typescript',
      '.py': 'python',
      '.java': 'java',
      '.cpp': 'cpp',
      '.c': 'c',
      '.cs': 'csharp',
      '.php': 'php',
      '.rb': 'ruby',
      '.go': 'go',
      '.rs': 'rust',
      '.swift': 'swift',
      '.kt': 'kotlin',
      '.scala': 'scala',
      '.html': 'html',
      '.css': 'css',
      '.scss': 'scss',
      '.less': 'less',
      '.json': 'json',
      '.xml': 'xml',
      '.yaml': 'yaml',
      '.yml': 'yaml',
      '.md': 'markdown',
      '.sh': 'bash',
      '.ps1': 'powershell'
    };

    return languageMap[extension] || 'text';
  }

  // 获取项目结构
  private getProjectStructure(workspaceRoot: string, maxDepth: number = 2): any {
    try {
      const readDir = (dirPath: string, currentDepth: number) => {
        if (currentDepth > maxDepth) return;

        const items = fs.readdirSync(dirPath);
        const result: any = {};

        for (const item of items) {
          // 跳过隐藏文件和常见的忽略目录
          if (item.startsWith('.') || ['node_modules', 'dist', 'build', 'target'].includes(item)) {
            continue;
          }

          const itemPath = path.join(dirPath, item);
          const stats = fs.statSync(itemPath);

          if (stats.isDirectory()) {
            result[item] = readDir(itemPath, currentDepth + 1);
          } else {
            result[item] = {
              type: 'file',
              size: stats.size,
              extension: path.extname(item)
            };
          }
        }

        return result;
      };

      return readDir(workspaceRoot, 0);
    } catch (error) {
      this.logger.error('Error getting project structure:', error);
      return {};
    }
  }

  // 获取缓存数据
  private getCachedData(key: string): any {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  // 设置缓存数据
  private setCachedData(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });

    // 清理过期缓存
    if (this.cache.size > 100) {
      this.cleanupCache();
    }
  }

  // 清理过期缓存
  private cleanupCache(): void {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.cacheTimeout) {
        this.cache.delete(key);
      }
    }
  }

  // 获取最小上下文（错误情况下的后备）
  private getMinimalContext(): ExtractedContext {
    return {
      file: {},
      project: {},
      workspace: {},
      git: {},
      cursor: {},
      environment: this.extractEnvironmentContext()
    };
  }

  // 清理资源
  public cleanup(): void {
    this.cache.clear();
    this.logger.info('ContextExtractor cleaned up');
  }
}