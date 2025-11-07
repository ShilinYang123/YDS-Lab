// src/services/ContentProcessor.ts
import { Logger } from '../utils/logger';
import { MemoryData } from './MemoryService';

export interface ProcessingConfig {
  enableContentEnhancement: boolean;
  enableSemanticAnalysis: boolean;
  enableKeywordExtraction: boolean;
  enableSentimentAnalysis: boolean;
  enableCodeAnalysis: boolean;
  maxContentLength: number;
  compressionThreshold: number;
}

export interface ProcessingResult {
  processedMemory: MemoryData;
  enhancements: Enhancement[];
  metrics: ProcessingMetrics;
}

export interface Enhancement {
  type: 'keyword' | 'summary' | 'sentiment' | 'code_analysis' | 'context' | 'compression';
  data: any;
  confidence: number;
}

export interface ProcessingMetrics {
  processingTime: number;
  originalSize: number;
  processedSize: number;
  compressionRatio: number;
  enhancementsCount: number;
}

export interface CodeAnalysisResult {
  language: string;
  functions: string[];
  classes: string[];
  imports: string[];
  complexity: number;
  linesOfCode: number;
  hasErrors: boolean;
  errorTypes: string[];
}

export interface SentimentResult {
  score: number; // -1 to 1
  magnitude: number; // 0 to 1
  label: 'positive' | 'negative' | 'neutral';
  confidence: number;
}

export class ContentProcessor {
  private logger: Logger;
  private config: ProcessingConfig;
  private keywordPatterns: Map<string, RegExp> = new Map();
  private codePatterns: Map<string, RegExp> = new Map();

  constructor(config?: Partial<ProcessingConfig>) {
    this.logger = new Logger('ContentProcessor');
    this.config = {
      enableContentEnhancement: true,
      enableSemanticAnalysis: true,
      enableKeywordExtraction: true,
      enableSentimentAnalysis: true,
      enableCodeAnalysis: true,
      maxContentLength: 10000,
      compressionThreshold: 2000,
      ...config
    };

    this.initializePatterns();
  }

  // 主要的处理方法
  public async processMemory(memory: MemoryData): Promise<ProcessingResult> {
    const startTime = Date.now();
    const originalSize = this.calculateSize(memory);

    try {
      let processedMemory = { ...memory };
      const enhancements: Enhancement[] = [];

      // 内容预处理
      processedMemory = this.preprocessContent(processedMemory);

      // 关键词提取
      if (this.config.enableKeywordExtraction) {
        const keywordEnhancement = await this.extractKeywords(processedMemory);
        if (keywordEnhancement) {
          enhancements.push(keywordEnhancement);
          processedMemory.metadata = {
            ...processedMemory.metadata,
            keywords: keywordEnhancement.data.keywords
          };
        }
      }

      // 代码分析
      if (this.config.enableCodeAnalysis) {
        const codeEnhancement = await this.analyzeCode(processedMemory);
        if (codeEnhancement) {
          enhancements.push(codeEnhancement);
          processedMemory.metadata = {
            ...processedMemory.metadata,
            codeAnalysis: codeEnhancement.data
          };
        }
      }

      // 情感分析
      if (this.config.enableSentimentAnalysis) {
        const sentimentEnhancement = await this.analyzeSentiment(processedMemory);
        if (sentimentEnhancement) {
          enhancements.push(sentimentEnhancement);
          processedMemory.metadata = {
            ...processedMemory.metadata,
            sentiment: sentimentEnhancement.data
          };
        }
      }

      // 内容摘要
      if (this.config.enableSemanticAnalysis) {
        const summaryEnhancement = await this.generateSummary(processedMemory);
        if (summaryEnhancement) {
          enhancements.push(summaryEnhancement);
          processedMemory.metadata = {
            ...processedMemory.metadata,
            summary: summaryEnhancement.data.summary
          };
        }
      }

      // 内容压缩
      const compressionEnhancement = await this.compressContent(processedMemory);
      if (compressionEnhancement) {
        enhancements.push(compressionEnhancement);
        processedMemory = compressionEnhancement.data.compressedMemory;
      }

      // 上下文增强
      if (this.config.enableContentEnhancement) {
        const contextEnhancement = await this.enhanceContext(processedMemory);
        if (contextEnhancement) {
          enhancements.push(contextEnhancement);
          processedMemory.context = {
            ...processedMemory.context,
            ...contextEnhancement.data
          };
        }
      }

      const processingTime = Date.now() - startTime;
      const processedSize = this.calculateSize(processedMemory);

      const metrics: ProcessingMetrics = {
        processingTime,
        originalSize,
        processedSize,
        compressionRatio: originalSize > 0 ? processedSize / originalSize : 1,
        enhancementsCount: enhancements.length
      };

      this.logger.debug(`Memory processed in ${processingTime}ms with ${enhancements.length} enhancements`);

      return {
        processedMemory,
        enhancements,
        metrics
      };
    } catch (error) {
      this.logger.error('Error processing memory:', error);
      
      // 返回原始记忆和错误信息
      return {
        processedMemory: memory,
        enhancements: [],
        metrics: {
          processingTime: Date.now() - startTime,
          originalSize,
          processedSize: originalSize,
          compressionRatio: 1,
          enhancementsCount: 0
        }
      };
    }
  }

  // 内容预处理
  private preprocessContent(memory: MemoryData): MemoryData {
    let content = this.extractTextContent(memory.content);

    // 清理多余的空白字符
    content = content.replace(/\s+/g, ' ').trim();

    // 移除敏感信息（如API密钥、密码等）
    content = this.sanitizeContent(content);

    // 标准化换行符
    content = content.replace(/\r\n/g, '\n');

    return {
      ...memory,
      content: typeof memory.content === 'string' ? content : memory.content
    };
  }

  // 提取关键词
  private async extractKeywords(memory: MemoryData): Promise<Enhancement | null> {
    try {
      const content = this.extractTextContent(memory.content);
      const keywords: { word: string; score: number; category: string }[] = [];

      // 技术关键词提取
      for (const [category, pattern] of this.keywordPatterns) {
        const matches = content.match(pattern);
        if (matches) {
          for (const match of matches) {
            const word = match.toLowerCase();
            const existingKeyword = keywords.find(k => k.word === word);
            if (existingKeyword) {
              existingKeyword.score += 0.1;
            } else {
              keywords.push({
                word,
                score: this.calculateKeywordScore(word, content),
                category
              });
            }
          }
        }
      }

      // 频率分析
      const words = content.toLowerCase().match(/\b\w{3,}\b/g) || [];
      const wordFreq = new Map<string, number>();
      
      words.forEach(word => {
        if (!this.isStopWord(word)) {
          wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
        }
      });

      // 添加高频词
      for (const [word, freq] of wordFreq) {
        if (freq > 1 && !keywords.find(k => k.word === word)) {
          keywords.push({
            word,
            score: Math.min(freq / words.length * 10, 1),
            category: 'frequency'
          });
        }
      }

      // 排序并限制数量
      keywords.sort((a, b) => b.score - a.score);
      const topKeywords = keywords.slice(0, 20);

      if (topKeywords.length === 0) return null;

      return {
        type: 'keyword',
        data: {
          keywords: topKeywords,
          totalWords: words.length,
          uniqueWords: wordFreq.size
        },
        confidence: Math.min(topKeywords.length / 10, 1)
      };
    } catch (error) {
      this.logger.error('Error extracting keywords:', error);
      return null;
    }
  }

  // 代码分析
  private async analyzeCode(memory: MemoryData): Promise<Enhancement | null> {
    try {
      const content = this.extractTextContent(memory.content);
      
      // 检测是否包含代码
      if (!this.containsCode(content)) {
        return null;
      }

      const analysis: CodeAnalysisResult = {
        language: this.detectLanguage(content),
        functions: this.extractFunctions(content),
        classes: this.extractClasses(content),
        imports: this.extractImports(content),
        complexity: this.calculateComplexity(content),
        linesOfCode: content.split('\n').length,
        hasErrors: this.detectErrors(content),
        errorTypes: this.extractErrorTypes(content)
      };

      return {
        type: 'code_analysis',
        data: analysis,
        confidence: this.calculateCodeAnalysisConfidence(analysis)
      };
    } catch (error) {
      this.logger.error('Error analyzing code:', error);
      return null;
    }
  }

  // 情感分析
  private async analyzeSentiment(memory: MemoryData): Promise<Enhancement | null> {
    try {
      const content = this.extractTextContent(memory.content);
      
      // 简单的情感分析实现
      const positiveWords = ['good', 'great', 'excellent', 'success', 'working', 'fixed', 'solved', 'completed'];
      const negativeWords = ['error', 'bug', 'failed', 'broken', 'issue', 'problem', 'wrong', 'crash'];
      
      const words = content.toLowerCase().split(/\s+/);
      let positiveScore = 0;
      let negativeScore = 0;

      words.forEach(word => {
        if (positiveWords.includes(word)) positiveScore++;
        if (negativeWords.includes(word)) negativeScore++;
      });

      const totalSentimentWords = positiveScore + negativeScore;
      if (totalSentimentWords === 0) return null;

      const score = (positiveScore - negativeScore) / totalSentimentWords;
      const magnitude = totalSentimentWords / words.length;
      
      let label: 'positive' | 'negative' | 'neutral';
      if (score > 0.1) label = 'positive';
      else if (score < -0.1) label = 'negative';
      else label = 'neutral';

      const sentiment: SentimentResult = {
        score,
        magnitude,
        label,
        confidence: Math.min(totalSentimentWords / 5, 1)
      };

      return {
        type: 'sentiment',
        data: sentiment,
        confidence: sentiment.confidence
      };
    } catch (error) {
      this.logger.error('Error analyzing sentiment:', error);
      return null;
    }
  }

  // 生成摘要
  private async generateSummary(memory: MemoryData): Promise<Enhancement | null> {
    try {
      const content = this.extractTextContent(memory.content);
      
      if (content.length < 100) return null;

      // 简单的摘要生成：提取关键句子
      const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 10);
      if (sentences.length <= 2) return null;

      // 计算句子重要性
      const sentenceScores = sentences.map(sentence => ({
        sentence: sentence.trim(),
        score: this.calculateSentenceImportance(sentence, content)
      }));

      // 选择最重要的句子
      sentenceScores.sort((a, b) => b.score - a.score);
      const topSentences = sentenceScores.slice(0, Math.min(3, Math.ceil(sentences.length * 0.3)));
      
      const summary = topSentences.map(s => s.sentence).join('. ') + '.';

      return {
        type: 'summary',
        data: {
          summary,
          originalLength: content.length,
          summaryLength: summary.length,
          compressionRatio: summary.length / content.length,
          sentencesUsed: topSentences.length,
          totalSentences: sentences.length
        },
        confidence: Math.min(topSentences.length / 3, 1)
      };
    } catch (error) {
      this.logger.error('Error generating summary:', error);
      return null;
    }
  }

  // 内容压缩
  private async compressContent(memory: MemoryData): Promise<Enhancement | null> {
    try {
      const content = this.extractTextContent(memory.content);
      
      if (content.length < this.config.compressionThreshold) {
        return null;
      }

      let compressedContent = content;

      // 移除重复的空行
      compressedContent = compressedContent.replace(/\n\s*\n\s*\n/g, '\n\n');

      // 压缩重复的空格
      compressedContent = compressedContent.replace(/  +/g, ' ');

      // 如果仍然太长，进行更激进的压缩
      if (compressedContent.length > this.config.maxContentLength) {
        // 保留开头和结尾，压缩中间部分
        const start = compressedContent.substring(0, this.config.maxContentLength * 0.4);
        const end = compressedContent.substring(compressedContent.length - this.config.maxContentLength * 0.4);
        compressedContent = start + '\n...[content truncated]...\n' + end;
      }

      if (compressedContent.length >= content.length * 0.9) {
        return null; // 压缩效果不明显
      }

      const compressedMemory = {
        ...memory,
        content: typeof memory.content === 'string' ? compressedContent : memory.content,
        metadata: {
          ...memory.metadata,
          compressed: true,
          originalSize: content.length,
          compressedSize: compressedContent.length
        }
      };

      return {
        type: 'compression',
        data: {
          compressedMemory,
          originalSize: content.length,
          compressedSize: compressedContent.length,
          compressionRatio: compressedContent.length / content.length
        },
        confidence: 1 - (compressedContent.length / content.length)
      };
    } catch (error) {
      this.logger.error('Error compressing content:', error);
      return null;
    }
  }

  // 增强上下文
  private async enhanceContext(memory: MemoryData): Promise<Enhancement | null> {
    try {
      const content = this.extractTextContent(memory.content);
      const enhancedContext: any = {};

      // 检测内容类型
      enhancedContext.contentType = this.detectContentType(content);

      // 检测编程语言
      if (this.containsCode(content)) {
        enhancedContext.programmingLanguage = this.detectLanguage(content);
      }

      // 检测操作类型
      enhancedContext.operationType = this.detectOperationType(content);

      // 提取文件引用
      const fileReferences = this.extractFileReferences(content);
      if (fileReferences.length > 0) {
        enhancedContext.fileReferences = fileReferences;
      }

      // 检测错误级别
      if (content.toLowerCase().includes('error') || content.toLowerCase().includes('exception')) {
        enhancedContext.errorLevel = this.detectErrorLevel(content);
      }

      // 计算内容复杂度
      enhancedContext.complexity = this.calculateContentComplexity(content);

      if (Object.keys(enhancedContext).length === 0) return null;

      return {
        type: 'context',
        data: enhancedContext,
        confidence: Math.min(Object.keys(enhancedContext).length / 5, 1)
      };
    } catch (error) {
      this.logger.error('Error enhancing context:', error);
      return null;
    }
  }

  // 辅助方法
  private extractTextContent(content: any): string {
    if (typeof content === 'string') return content;
    if (typeof content === 'object') return JSON.stringify(content, null, 2);
    return String(content);
  }

  private calculateSize(memory: MemoryData): number {
    return JSON.stringify(memory).length;
  }

  private sanitizeContent(content: string): string {
    // 移除可能的敏感信息
    const patterns = [
      /api[_-]?key[s]?[:\s=]+[a-zA-Z0-9_-]+/gi,
      /password[s]?[:\s=]+\S+/gi,
      /token[s]?[:\s=]+[a-zA-Z0-9_.-]+/gi,
      /secret[s]?[:\s=]+\S+/gi
    ];

    let sanitized = content;
    patterns.forEach(pattern => {
      sanitized = sanitized.replace(pattern, '[REDACTED]');
    });

    return sanitized;
  }

  private calculateKeywordScore(word: string, content: string): number {
    const frequency = (content.toLowerCase().match(new RegExp(word, 'g')) || []).length;
    const position = content.toLowerCase().indexOf(word) / content.length;
    const length = word.length;
    
    return (frequency * 0.4) + ((1 - position) * 0.3) + (Math.min(length / 10, 1) * 0.3);
  }

  private isStopWord(word: string): boolean {
    const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'];
    return stopWords.includes(word.toLowerCase());
  }

  private containsCode(content: string): boolean {
    const codeIndicators = [
      /function\s+\w+\s*\(/,
      /class\s+\w+/,
      /import\s+.*from/,
      /export\s+(default\s+)?/,
      /const\s+\w+\s*=/,
      /let\s+\w+\s*=/,
      /var\s+\w+\s*=/,
      /if\s*\(/,
      /for\s*\(/,
      /while\s*\(/,
      /\{\s*\n.*\n\s*\}/s
    ];

    return codeIndicators.some(pattern => pattern.test(content));
  }

  private detectLanguage(content: string): string {
    const languagePatterns = new Map([
      ['javascript', /(?:function|const|let|var|=>|import.*from|export)/],
      ['typescript', /(?:interface|type\s+\w+\s*=|as\s+\w+|:\s*\w+\[\])/],
      ['python', /(?:def\s+\w+|import\s+\w+|from\s+\w+\s+import|class\s+\w+.*:)/],
      ['java', /(?:public\s+class|private\s+\w+|public\s+static\s+void)/],
      ['csharp', /(?:using\s+System|public\s+class|private\s+\w+)/],
      ['cpp', /(?:#include|std::|cout|cin)/],
      ['html', /(?:<\w+.*>|<!DOCTYPE)/],
      ['css', /(?:\w+\s*\{.*\}|@media|@import)/],
      ['sql', /(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)/i]
    ]);

    for (const [language, pattern] of languagePatterns) {
      if (pattern.test(content)) {
        return language;
      }
    }

    return 'unknown';
  }

  private extractFunctions(content: string): string[] {
    const functionPatterns = [
      /function\s+(\w+)\s*\(/g,
      /(\w+)\s*:\s*function\s*\(/g,
      /(\w+)\s*=\s*\([^)]*\)\s*=>/g,
      /def\s+(\w+)\s*\(/g,
      /public\s+\w+\s+(\w+)\s*\(/g
    ];

    const functions: string[] = [];
    functionPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        functions.push(match[1]);
      }
    });

    return [...new Set(functions)];
  }

  private extractClasses(content: string): string[] {
    const classPatterns = [
      /class\s+(\w+)/g,
      /interface\s+(\w+)/g,
      /type\s+(\w+)\s*=/g
    ];

    const classes: string[] = [];
    classPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        classes.push(match[1]);
      }
    });

    return [...new Set(classes)];
  }

  private extractImports(content: string): string[] {
    const importPatterns = [
      /import\s+.*from\s+['"]([^'"]+)['"]/g,
      /import\s+['"]([^'"]+)['"]/g,
      /#include\s*<([^>]+)>/g,
      /using\s+([^;]+);/g
    ];

    const imports: string[] = [];
    importPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        imports.push(match[1]);
      }
    });

    return [...new Set(imports)];
  }

  private calculateComplexity(content: string): number {
    const complexityIndicators = [
      /if\s*\(/g,
      /else\s*if\s*\(/g,
      /for\s*\(/g,
      /while\s*\(/g,
      /switch\s*\(/g,
      /case\s+.*:/g,
      /catch\s*\(/g,
      /&&|\|\|/g
    ];

    let complexity = 1; // 基础复杂度
    complexityIndicators.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches) {
        complexity += matches.length;
      }
    });

    return complexity;
  }

  private detectErrors(content: string): boolean {
    const errorPatterns = [
      /error/i,
      /exception/i,
      /failed/i,
      /cannot/i,
      /undefined/i,
      /null\s+reference/i,
      /syntax\s+error/i
    ];

    return errorPatterns.some(pattern => pattern.test(content));
  }

  private extractErrorTypes(content: string): string[] {
    const errorTypePatterns = new Map([
      ['SyntaxError', /syntax\s*error/i],
      ['TypeError', /type\s*error/i],
      ['ReferenceError', /reference\s*error/i],
      ['RangeError', /range\s*error/i],
      ['NetworkError', /network\s*error/i],
      ['TimeoutError', /timeout/i],
      ['ValidationError', /validation/i],
      ['AuthenticationError', /authentication/i],
      ['PermissionError', /permission/i]
    ]);

    const errorTypes: string[] = [];
    for (const [type, pattern] of errorTypePatterns) {
      if (pattern.test(content)) {
        errorTypes.push(type);
      }
    }

    return errorTypes;
  }

  private calculateCodeAnalysisConfidence(analysis: CodeAnalysisResult): number {
    let confidence = 0;
    
    if (analysis.language !== 'unknown') confidence += 0.3;
    if (analysis.functions.length > 0) confidence += 0.2;
    if (analysis.classes.length > 0) confidence += 0.2;
    if (analysis.imports.length > 0) confidence += 0.1;
    if (analysis.linesOfCode > 5) confidence += 0.2;

    return Math.min(confidence, 1);
  }

  private calculateSentenceImportance(sentence: string, fullContent: string): number {
    let score = 0;

    // 长度因子
    if (sentence.length > 20 && sentence.length < 200) score += 0.2;

    // 关键词因子
    const importantWords = ['error', 'success', 'completed', 'failed', 'implemented', 'created', 'updated', 'fixed'];
    importantWords.forEach(word => {
      if (sentence.toLowerCase().includes(word)) score += 0.3;
    });

    // 位置因子（开头和结尾的句子更重要）
    const position = fullContent.indexOf(sentence) / fullContent.length;
    if (position < 0.2 || position > 0.8) score += 0.2;

    // 数字和代码因子
    if (/\d+/.test(sentence)) score += 0.1;
    if (/`[^`]+`/.test(sentence)) score += 0.1;

    return score;
  }

  private detectContentType(content: string): string {
    if (this.containsCode(content)) return 'code';
    if (/error|exception|failed/i.test(content)) return 'error';
    if (/success|completed|fixed|solved/i.test(content)) return 'success';
    if (/question|\?/i.test(content)) return 'question';
    if (/todo|task|implement/i.test(content)) return 'task';
    return 'general';
  }

  private detectOperationType(content: string): string {
    const operations = new Map([
      ['create', /creat(e|ed|ing)|add(ed|ing)?|new/i],
      ['update', /updat(e|ed|ing)|modif(y|ied|ying)|chang(e|ed|ing)/i],
      ['delete', /delet(e|ed|ing)|remov(e|ed|ing)/i],
      ['read', /read|view|get|fetch|load/i],
      ['debug', /debug|fix|error|bug/i],
      ['test', /test|spec|unit|integration/i],
      ['deploy', /deploy|build|release|publish/i]
    ]);

    for (const [operation, pattern] of operations) {
      if (pattern.test(content)) {
        return operation;
      }
    }

    return 'unknown';
  }

  private extractFileReferences(content: string): string[] {
    const filePatterns = [
      /[\w-]+\.\w{2,4}/g, // 文件名.扩展名
      /\/[\w\/-]+\.\w{2,4}/g, // 路径/文件名.扩展名
      /[A-Z]:\\[\w\\-]+\.\w{2,4}/g // Windows路径
    ];

    const files: string[] = [];
    filePatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches) {
        files.push(...matches);
      }
    });

    return [...new Set(files)];
  }

  private detectErrorLevel(content: string): string {
    if (/critical|fatal|severe/i.test(content)) return 'critical';
    if (/error|exception|failed/i.test(content)) return 'error';
    if (/warning|warn/i.test(content)) return 'warning';
    if (/info|notice/i.test(content)) return 'info';
    return 'unknown';
  }

  private calculateContentComplexity(content: string): number {
    let complexity = 0;

    // 长度复杂度
    complexity += Math.min(content.length / 1000, 1) * 0.3;

    // 结构复杂度
    const lines = content.split('\n').length;
    complexity += Math.min(lines / 100, 1) * 0.2;

    // 词汇复杂度
    const words = content.split(/\s+/).length;
    const uniqueWords = new Set(content.toLowerCase().split(/\s+/)).size;
    const vocabularyRichness = uniqueWords / words;
    complexity += vocabularyRichness * 0.3;

    // 技术复杂度
    if (this.containsCode(content)) {
      complexity += 0.2;
    }

    return Math.min(complexity, 1);
  }

  private initializePatterns() {
    // 关键词模式
    this.keywordPatterns.set('programming', /\b(function|class|method|variable|array|object|string|number|boolean|null|undefined|async|await|promise|callback|event|handler|component|module|import|export|interface|type|enum|generic|abstract|static|private|public|protected|const|let|var|if|else|for|while|do|switch|case|try|catch|finally|throw|return|break|continue)\b/gi);
    this.keywordPatterns.set('web', /\b(html|css|javascript|typescript|react|vue|angular|node|express|api|rest|graphql|json|xml|http|https|url|dom|browser|client|server|frontend|backend|fullstack)\b/gi);
    this.keywordPatterns.set('database', /\b(sql|mysql|postgresql|mongodb|redis|database|table|collection|document|query|select|insert|update|delete|join|index|schema|migration)\b/gi);
    this.keywordPatterns.set('tools', /\b(git|github|npm|yarn|webpack|babel|eslint|prettier|jest|cypress|docker|kubernetes|aws|azure|gcp|ci|cd|deployment|build|test|debug)\b/gi);
    this.keywordPatterns.set('concepts', /\b(algorithm|data structure|design pattern|architecture|microservice|api|authentication|authorization|security|performance|optimization|scalability|maintainability|testing|debugging)\b/gi);

    // 代码模式
    this.codePatterns.set('function_declaration', /function\s+\w+\s*\([^)]*\)\s*\{/g);
    this.codePatterns.set('arrow_function', /\w+\s*=\s*\([^)]*\)\s*=>/g);
    this.codePatterns.set('class_declaration', /class\s+\w+(\s+extends\s+\w+)?\s*\{/g);
    this.codePatterns.set('import_statement', /import\s+.*from\s+['"][^'"]+['"]/g);
    this.codePatterns.set('export_statement', /export\s+(default\s+)?\w+/g);
  }

  // 获取处理统计信息
  public getStats() {
    return {
      config: this.config,
      keywordPatternsCount: this.keywordPatterns.size,
      codePatternsCount: this.codePatterns.size
    };
  }

  // 更新配置
  public updateConfig(newConfig: Partial<ProcessingConfig>) {
    this.config = { ...this.config, ...newConfig };
    this.logger.info('ContentProcessor config updated');
  }
}