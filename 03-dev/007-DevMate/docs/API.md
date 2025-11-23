# TraeMate API 文档

## 概述

本文档描述了TraeMate 2.0的API接口，包括各个模块的类和方法。

## 数据层 (src/data)

### ConfigManager

配置管理器，负责加载、保存和验证配置。

#### 方法

- `__init__(config_file: str)`: 初始化配置管理器
- `get_config() -> dict`: 获取完整配置
- `get(key: str, default=None)`: 获取配置项
- `set(key: str, value)`: 设置配置项
- `save_config() -> bool`: 保存配置到文件
- `validate_config() -> bool`: 验证配置有效性
- `reset_to_default()`: 重置为默认配置

#### 示例

```python
from src.data import ConfigManager

# 创建配置管理器
config = ConfigManager("config.json")

# 获取配置
app_name = config.get("app_name")
window_width = config.get("window.width")

# 设置配置
config.set("window.width", 500)
config.save_config()
```

### LogManager

日志管理器，负责日志的写入、读取和管理。

#### 方法

- `__init__(log_file: str)`: 初始化日志管理器
- `write_log(level: LogLevel, message: str)`: 写入日志
- `info(message: str)`: 写入信息日志
- `warning(message: str)`: 写入警告日志
- `error(message: str)`: 写入错误日志
- `read_logs() -> str`: 读取所有日志
- `clear_logs() -> bool`: 清空日志
- `get_log_size() -> int`: 获取日志大小

#### 示例

```python
from src.data import LogManager, LogLevel

# 创建日志管理器
logger = LogManager("app.log")

# 写入日志
logger.info("程序启动")
logger.warning("这是一个警告")
logger.error("发生错误")

# 读取日志
logs = logger.read_logs()
print(logs)
```

## 服务层 (src/services)

### ImageRecognitionService

图像识别服务，负责屏幕截图和模板匹配。

#### 方法

- `__init__(config_manager: ConfigManager, log_manager: LogManager)`: 初始化图像识别服务
- `take_screenshot() -> numpy.ndarray`: 截取屏幕
- `find_template(template_path: str, threshold: float = 0.8) -> tuple`: 查找模板
- `find_all_templates(template_path: str, threshold: float = 0.8) -> list`: 查找所有模板
- `save_screenshot(file_path: str)`: 保存截图

#### 示例

```python
from src.services import ImageRecognitionService
from src.data import ConfigManager, LogManager

# 创建服务
config = ConfigManager("config.json")
logger = LogManager("app.log")
image_service = ImageRecognitionService(config, logger)

# 查找模板
position = image_service.find_template("button.png")
if position:
    x, y = position
    print(f"找到按钮，位置：({x}, {y})")
```

### AutoClickService

自动点击服务，负责鼠标操作。

#### 方法

- `__init__(log_manager: LogManager)`: 初始化自动点击服务
- `click(x: int, y: int, button: str = "left")`: 点击
- `double_click(x: int, y: int)`: 双击
- `right_click(x: int, y: int)`: 右键点击
- `drag(start_x: int, start_y: int, end_x: int, end_y: int)`: 拖拽
- `scroll(x: int, y: int, clicks: int)`: 滚动

#### 示例

```python
from src.services import AutoClickService
from src.data import LogManager

# 创建服务
logger = LogManager("app.log")
click_service = AutoClickService(logger)

# 执行点击
click_service.click(100, 200)
click_service.double_click(150, 250)
```

### ProcessMonitorService

进程监控服务，负责进程状态检测。

#### 方法

- `__init__(log_manager: LogManager)`: 初始化进程监控服务
- `is_process_running(process_name: str) -> bool`: 检查进程是否运行
- `get_process_list() -> list`: 获取进程列表
- `get_process_info(process_name: str) -> dict`: 获取进程信息
- `terminate_process(process_name: str) -> bool`: 终止进程

#### 示例

```python
from src.services import ProcessMonitorService
from src.data import LogManager

# 创建服务
logger = LogManager("app.log")
process_service = ProcessMonitorService(logger)

# 检查进程
if process_service.is_process_running("notepad.exe"):
    print("记事本正在运行")
else:
    print("记事本未运行")
```

## 业务逻辑层 (src/business)

### MonitorManager

监控管理器，协调各服务模块，实现监控逻辑。

#### 方法

- `__init__(image_service, click_service, process_service, config_manager, log_manager)`: 初始化监控管理器
- `start_monitoring()`: 开始监控
- `stop_monitoring()`: 停止监控
- `toggle_monitoring()`: 切换监控状态
- `is_monitoring() -> bool`: 检查是否正在监控
- `get_state() -> MonitorState`: 获取当前状态

#### 示例

```python
from src.business import MonitorManager
from src.services import ImageRecognitionService, AutoClickService, ProcessMonitorService
from src.data import ConfigManager, LogManager

# 创建服务和配置
config = ConfigManager("config.json")
logger = LogManager("app.log")
image_service = ImageRecognitionService(config, logger)
click_service = AutoClickService(logger)
process_service = ProcessMonitorService(logger)

# 创建监控管理器
monitor = MonitorManager(image_service, click_service, process_service, config, logger)

# 开始监控
monitor.start_monitoring()

# 检查状态
if monitor.is_monitoring():
    print("监控中...")
```

### HandlerManager

处理项管理器，管理自定义处理项。

#### 方法

- `__init__(config_manager: ConfigManager, log_manager: LogManager)`: 初始化处理项管理器
- `add_handler(handler: dict)`: 添加处理项
- `remove_handler(index: int)`: 删除处理项
- `update_handler(index: int, handler: dict)`: 更新处理项
- `get_handlers() -> list`: 获取所有处理项
- `get_handler(index: int) -> dict`: 获取指定处理项
- `import_handlers(file_path: str) -> bool`: 导入处理项
- `export_handlers(file_path: str) -> bool`: 导出处理项

#### 示例

```python
from src.business import HandlerManager
from src.data import ConfigManager, LogManager

# 创建管理器
config = ConfigManager("config.json")
logger = LogManager("app.log")
handler_manager = HandlerManager(config, logger)

# 添加处理项
handler = {
    "name": "自定义按钮",
    "description": "这是一个自定义按钮",
    "image_file": "custom_button.png",
    "offset_x": 0,
    "offset_y": 0,
    "enabled": True
}
handler_manager.add_handler(handler)

# 获取所有处理项
handlers = handler_manager.get_handlers()
print(f"共有 {len(handlers)} 个处理项")
```

## UI层 (src/ui)

### StatusBar

状态栏组件，显示监控状态和指示器。

#### 方法

- `__init__(parent, config_manager: ConfigManager, log_manager: LogManager)`: 初始化状态栏
- `create_ui()`: 创建UI
- `set_monitoring_state(is_monitoring: bool)`: 设置监控状态
- `start_blinking()`: 开始闪烁
- `stop_blinking()`: 停止闪烁

### SystemTray

系统托盘组件，管理托盘图标和菜单。

#### 方法

- `__init__(config_manager: ConfigManager, log_manager: LogManager)`: 初始化系统托盘
- `start_tray()`: 启动托盘
- `stop_tray()`: 停止托盘
- `update_icon(icon_path: str)`: 更新图标
- `update_tooltip(text: str)`: 更新提示文本
- `set_menu_callback(callback)`: 设置菜单回调

### Dialogs

对话框组件，提供配置对话框和日志查看对话框。

#### 类

- `ConfigDialog`: 配置对话框
- `HandlerDialog`: 处理项对话框
- `LogsDialog`: 日志查看对话框

## 常量

### LogLevel

日志级别枚举：

- `INFO`: 信息
- `WARNING`: 警告
- `ERROR`: 错误

### MonitorState

监控状态枚举：

- `STOPPED`: 停止
- `RUNNING`: 运行中
- `PAUSED`: 暂停

## 异常

### ConfigError

配置错误，当配置无效时抛出。

### ServiceError

服务错误，当服务操作失败时抛出。

### MonitorError

监控错误，当监控操作失败时抛出。