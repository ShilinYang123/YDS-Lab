"""
监控管理器
负责协调各服务模块的工作，实现监控逻辑
"""
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

from src.data.config_manager import ConfigManager
from src.data.log_manager import LogManager
from src.services.image_recognition_service import ImageRecognitionService
from src.services.auto_click_service import AutoClickService
from src.services.process_monitor_service import ProcessMonitorService


class MonitorState(Enum):
    """监控状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class MonitorManager:
    """监控管理器"""
    
    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        """
        初始化监控管理器
        
        Args:
            config_manager: 配置管理器
            log_manager: 日志管理器
        """
        self.config_manager = config_manager
        self.log_manager = log_manager
        
        # 服务实例
        self.image_service = ImageRecognitionService(log_manager)
        self.click_service = AutoClickService(log_manager)
        self.process_service = ProcessMonitorService(log_manager)
        
        # 监控状态
        self.state = MonitorState.STOPPED
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # 回调函数
        self.state_change_callback: Optional[Callable[[MonitorState], None]] = None
        self.indicator_callback: Optional[Callable[[bool], None]] = None
        
        # 监控统计
        self.stats = {
            "start_time": None,
            "last_detection_time": None,
            "detection_count": 0,
            "click_count": 0,
            "error_count": 0
        }
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置"""
        self.config = self.config_manager.config
        self.monitor_config = self.config.get("monitor", {})
        self.detection_config = self.config.get("detection", {})
        self.window_config = self.config.get("window", {})
        
        # 更新服务配置
        self.image_service.update_config(self.detection_config)
        self.click_service.update_config(self.config.get("click", {}))
        self.process_service.update_config(self.monitor_config)
    
    def set_state_change_callback(self, callback: Callable[[MonitorState], None]) -> None:
        """设置状态变化回调函数"""
        self.state_change_callback = callback
    
    def set_indicator_callback(self, callback: Callable[[bool], None]) -> None:
        """设置指示器回调函数"""
        self.indicator_callback = callback
    
    def start_monitoring(self) -> bool:
        """
        开始监控
        
        Returns:
            bool: 是否成功开始监控
        """
        if self.state != MonitorState.STOPPED:
            self.log_manager.warning("监控已在运行中")
            return False
        
        self.log_manager.info("开始监控")
        self._set_state(MonitorState.STARTING)
        
        # 重置停止事件
        self.stop_event.clear()
        
        # 创建并启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        return True
    
    def stop_monitoring(self) -> bool:
        """
        停止监控
        
        Returns:
            bool: 是否成功停止监控
        """
        if self.state == MonitorState.STOPPED:
            self.log_manager.warning("监控未在运行")
            return False
        
        self.log_manager.info("停止监控")
        self._set_state(MonitorState.STOPPING)
        
        # 设置停止事件
        self.stop_event.set()
        
        # 等待线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self._set_state(MonitorState.STOPPED)
        return True
    
    def _set_state(self, new_state: MonitorState) -> None:
        """设置监控状态"""
        old_state = self.state
        self.state = new_state
        self.log_manager.debug(f"监控状态变更: {old_state.value} -> {new_state.value}")
        
        # 调用状态变化回调
        if self.state_change_callback:
            self.state_change_callback(new_state)
        
        # 更新指示器
        if self.indicator_callback:
            self.indicator_callback(new_state == MonitorState.RUNNING)
    
    def _monitor_loop(self) -> None:
        """监控主循环"""
        try:
            # 初始化统计信息
            self.stats["start_time"] = time.time()
            self.stats["detection_count"] = 0
            self.stats["click_count"] = 0
            self.stats["error_count"] = 0
            
            self._set_state(MonitorState.RUNNING)
            
            # 主循环
            while not self.stop_event.is_set():
                try:
                    # 检查进程
                    if not self._check_process():
                        time.sleep(self.monitor_config.get("interval_seconds", 2.0))
                        continue
                    
                    # 检测主按钮
                    main_button_pos = self._detect_main_button()
                    if main_button_pos:
                        self.log_manager.debug("检测到主按钮")
                        self.stats["detection_count"] += 1
                        self.stats["last_detection_time"] = time.time()
                        
                        # 点击主按钮
                        if self._click_main_button(main_button_pos):
                            # 检测并点击处理项
                            self._process_handlers()
                        
                        # 冷却时间
                        cooldown = self.monitor_config.get("cooldown_seconds", 30)
                        self.log_manager.debug(f"进入冷却时间: {cooldown}秒")
                        time.sleep(cooldown)
                    else:
                        # 未检测到主按钮，等待下次检测
                        time.sleep(self.monitor_config.get("interval_seconds", 2.0))
                
                except Exception as e:
                    self.log_manager.error(f"监控循环异常: {e}")
                    self.stats["error_count"] += 1
                    time.sleep(1.0)
        
        except Exception as e:
            self.log_manager.error(f"监控线程异常: {e}")
            self._set_state(MonitorState.ERROR)
        
        finally:
            self.log_manager.info("监控线程结束")
            if self.state != MonitorState.ERROR:
                self._set_state(MonitorState.STOPPED)
    
    def _check_process(self) -> bool:
        """
        检查目标进程是否运行
        
        Returns:
            bool: 进程是否运行
        """
        if self.monitor_config.get("skip_process_check", False):
            return True
        
        process_names = self.monitor_config.get("process_names", ["trae", "cursor"])
        return self.process_service.is_any_process_running(process_names)
    
    def _detect_main_button(self) -> Optional[tuple]:
        """
        检测主按钮
        
        Returns:
            Optional[tuple]: 按钮位置 (x, y)，如果未找到则为None
        """
        # 获取主按钮图像路径
        main_button_image = self.config.get("main_button_image", "handler_btn.png")
        
        # 检测按钮
        threshold = self.detection_config.get("threshold_main", 0.6)
        position = self.image_service.find_image(main_button_image, threshold)
        
        return position
    
    def _click_main_button(self, position: tuple) -> bool:
        """
        点击主按钮
        
        Args:
            position: 按钮位置 (x, y)
            
        Returns:
            bool: 是否成功点击
        """
        x, y = position
        self.log_manager.info(f"点击主按钮: ({x}, {y})")
        
        # 点击按钮
        if self.click_service.click(x, y):
            self.stats["click_count"] += 1
            time.sleep(1.0)  # 等待界面响应
            return True
        
        return False
    
    def _process_handlers(self) -> None:
        """处理自定义处理项"""
        handlers = self.config.get("custom_handlers", [])
        
        for handler in handlers:
            if not handler.get("enabled", True):
                continue
            
            # 检测处理项按钮
            image_file = handler.get("image_file")
            if not image_file:
                continue
            
            threshold = self.detection_config.get("threshold_handlers", 0.85)
            position = self.image_service.find_image(image_file, threshold)
            
            if position:
                # 计算点击位置（考虑偏移）
                x, y = position
                offset_x = handler.get("offset_x", 0)
                offset_y = handler.get("offset_y", 0)
                click_x = x + offset_x
                click_y = y + offset_y
                
                # 点击处理项
                self.log_manager.info(f"点击处理项 '{handler.get('name', '未知')}': ({click_x}, {click_y})")
                if self.click_service.click(click_x, click_y):
                    self.stats["click_count"] += 1
                    time.sleep(0.5)  # 短暂等待
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取监控统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.stats.copy()
        
        # 计算运行时间
        if stats["start_time"]:
            stats["uptime_seconds"] = time.time() - stats["start_time"]
            stats["uptime_formatted"] = self._format_duration(stats["uptime_seconds"])
        else:
            stats["uptime_seconds"] = 0
            stats["uptime_formatted"] = "00:00:00"
        
        # 计算最后检测时间
        if stats["last_detection_time"]:
            stats["time_since_last_detection"] = time.time() - stats["last_detection_time"]
            stats["time_since_last_detection_formatted"] = self._format_duration(
                stats["time_since_last_detection"])
        else:
            stats["time_since_last_detection"] = None
            stats["time_since_last_detection_formatted"] = "从未"
        
        return stats
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长为 HH:MM:SS"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self.log_manager.info("重新加载配置")
        self._load_config()
    
    def get_state(self) -> MonitorState:
        """获取当前监控状态"""
        return self.state
    
    def is_running(self) -> bool:
        """检查监控是否正在运行"""
        return self.state == MonitorState.RUNNING