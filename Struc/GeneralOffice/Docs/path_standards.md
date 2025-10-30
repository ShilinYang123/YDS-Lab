# YDS-Lab 路径标准化规范

## 概述

本项目采用统一的路径管理策略，避免硬编码路径和文件散乱问题。所有路径配置集中在 `config/paths.py` 中管理。

## 核心原则

1. **统一配置**: 所有路径在 `config/paths.py` 中统一定义
2. **自动检测**: 根据项目上下文自动选择合适的路径
3. **分类管理**: 按功能分类管理不同类型的文件
4. **回退机制**: 提供简单可靠的回退路径

## 目录结构

```
YDS-Lab/
├── assets/           # 静态资源
│   └── audio/        # 音频资源
├── cache/            # 缓存文件
├── config/           # 配置文件
│   └── paths.py      # 路径配置
├── Struc/            # 组织结构目录
│   └── GeneralOffice/
│       ├── Docs/     # 文档目录
│       └── logs/     # 统一日志管理中心
├── projects/         # 项目目录
│   └── JS001-meetingroom/
│       └── tests/
│           └── audio_samples/  # 项目音频测试文件
├── scripts/          # 脚本文件
├── tools/            # 工具文件
└── utils/            # 工具函数
```

## 使用方法

### 基本用法

```python
from config.paths import get_tts_audio_path, paths

# 获取TTS音频文件路径（自动检测项目上下文）
audio_path = get_tts_audio_path("my_audio.mp3")

# 获取临时音频文件路径
temp_path = get_tts_audio_path("temp_audio.mp3", temp=True)

# 获取特定项目的音频路径
js001_path = get_tts_audio_path("test.mp3", project="JS001-meetingroom")
```

### 路径配置对象

```python
from config.paths import paths

# 获取各种目录
audio_dir = paths.get_tts_audio_dir("JS001-meetingroom")
temp_dir = paths.get_temp_audio_dir()
log_file = paths.get_log_file("tts")
cache_dir = paths.get_cache_dir("audio")
```

### 项目上下文检测

系统会自动检测当前工作目录所属的项目：

- 如果在 `JS001-meetingroom` 项目中，音频文件会保存到 `projects/JS001-meetingroom/tests/audio_samples/`
- 其他情况下，音频文件保存到 `assets/audio/generated/`
- 临时文件统一保存到 `tmp/audio/`

## 迁移指南

### 从硬编码路径迁移

**之前:**
```python
# 硬编码路径
audio_path = "tests/audio_samples/test.mp3"
```

**现在:**
```python
# 使用标准化路径
from config.paths import get_tts_audio_path
audio_path = get_tts_audio_path("test.mp3")
```

### 从复杂路径逻辑迁移

**之前:**
```python
# 复杂的路径检测逻辑
current_dir = Path(__file__).resolve().parent
project_root = None
for parent in current_dir.parents:
    if (parent / "projects" / "JS001-meetingroom").exists():
        project_root = parent / "projects" / "JS001-meetingroom"
        break
if project_root:
    audio_dir = project_root / "tests" / "audio_samples"
else:
    audio_dir = Path("tmp")
```

**现在:**
```python
# 简单的标准化调用
from config.paths import get_tts_audio_path
audio_path = get_tts_audio_path("test.mp3")
```

## 最佳实践

1. **始终使用标准化路径函数**，避免直接构造路径
2. **区分临时文件和持久文件**，使用 `temp=True` 参数
3. **让系统自动检测项目上下文**，除非有特殊需求
4. **使用有意义的文件名**，便于调试和维护

## 兼容性

- 提供回退机制，即使路径配置不可用也能正常工作
- 向后兼容现有代码，逐步迁移
- 支持多项目环境，自动适配不同项目需求