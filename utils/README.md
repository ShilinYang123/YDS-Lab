# 工具函数目录

本目录包含 YDS-Lab 系统的通用工具函数和实用程序。

## 📁 文件说明

### 📝 logger.py - 日志管理
统一的日志记录工具：
- 支持多级别日志 (DEBUG, INFO, WARNING, ERROR)
- 自动日志轮转和归档
- 结构化日志输出
- 与系统日志目录集成

### 🔊 tts.py - 文本转语音
文本转语音功能模块：
- 支持多种TTS引擎
- 语音合成和播放
- 音频文件导出
- 语音参数配置

## 🚀 使用方法

### 日志记录
```python
from utils.logger import get_logger

# 获取日志器
logger = get_logger(__name__)

# 记录日志
logger.info("系统启动成功")
logger.warning("配置文件未找到，使用默认配置")
logger.error("连接数据库失败")
```

### 文本转语音
```python
from utils.tts import TextToSpeech

# 初始化TTS
tts = TextToSpeech()

# 语音合成
tts.speak("欢迎使用YDS-Lab系统")

# 保存音频文件
tts.save_audio("你好世界", "output.wav")
```

## 🔧 配置说明

### 日志配置
- 日志级别：通过环境变量 `LOG_LEVEL` 设置
- 日志文件：自动保存到 `/Struc/GeneralOffice/logs/system/`
- 日志格式：时间戳 + 级别 + 模块 + 消息

### TTS配置
- 引擎选择：支持系统默认、Azure、Google等
- 语音参数：语速、音调、音量可调
- 输出格式：支持WAV、MP3等格式

## 📦 依赖管理

本目录的工具函数依赖：
- `logging` - Python标准日志库
- `pyttsx3` - 文本转语音库 (可选)
- `azure-cognitiveservices-speech` - Azure语音服务 (可选)

## 🔄 扩展指南

### 添加新工具函数
1. 创建新的 `.py` 文件
2. 遵循统一的代码风格
3. 添加完整的文档字符串
4. 更新本README文件
5. 编写单元测试

### 工具函数规范
- 函数命名：使用动词+名词格式
- 参数验证：检查输入参数有效性
- 异常处理：优雅处理错误情况
- 返回值：明确的返回类型和格式

## 📊 工具函数清单

| 文件名 | 功能 | 状态 | 依赖 |
|--------|------|------|------|
| logger.py | 日志管理 | ✅ 稳定 | logging |
| tts.py | 文本转语音 | ✅ 稳定 | pyttsx3 |

## 🔍 最佳实践

- 保持函数的单一职责原则
- 使用类型提示增强代码可读性
- 编写详细的文档字符串
- 考虑性能和内存使用
- 提供使用示例和测试用例