"""
集成测试 - 验证组件之间的交互
"""
import unittest
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 模拟服务类
class MockImageRecognitionService:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.config = {}
    
    def update_config(self, config):
        self.config = config
    
    def find_image(self, image_path, threshold):
        # 模拟找到图像
        if "handler_btn" in image_path:
            return (100, 100)  # 返回坐标
        return None

class MockAutoClickService:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.config = {}
        self.click_count = 0
    
    def update_config(self, config):
        self.config = config
    
    def click(self, x, y):
        self.click_count += 1
        self.log_manager.info(f"模拟点击: ({x}, {y})")
        return True

class MockProcessMonitorService:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.config = {}
        self.process_running = True
    
    def update_config(self, config):
        self.config = config
    
    def is_any_process_running(self, process_names):
        return self.process_running

# 模拟服务模块
sys.modules['src.services.image_recognition_service'] = MagicMock()
sys.modules['src.services.image_recognition_service'].ImageRecognitionService = MockImageRecognitionService

sys.modules['src.services.auto_click_service'] = MagicMock()
sys.modules['src.services.auto_click_service'].AutoClickService = MockAutoClickService

sys.modules['src.services.process_monitor_service'] = MagicMock()
sys.modules['src.services.process_monitor_service'].ProcessMonitorService = MockProcessMonitorService

from src.business.monitor_manager import MonitorManager, MonitorState
from src.data.config_manager import ConfigManager
from src.data.log_manager import LogManager


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建真实的配置管理器
        self.config_manager = ConfigManager()
        
        # 创建真实的日志管理器
        self.log_manager = LogManager()
        
        # 设置测试配置
        self.test_config = {
            "monitor": {
                "interval_seconds": 0.5,  # 缩短测试时间
                "cooldown_seconds": 1,
                "process_names": ["test"],
                "skip_process_check": False
            },
            "detection": {
                "scale_factor": 1.0,
                "threshold_main": 0.7,
                "threshold_handlers": 0.8
            },
            "click": {}
        }
        
        # 创建监控管理器实例
        with patch.object(self.config_manager, 'config', self.test_config):
            self.monitor_manager = MonitorManager(
                self.config_manager,
                self.log_manager
            )
    
    def tearDown(self):
        """测试后清理"""
        # 确保监控已停止
        if self.monitor_manager.get_state() != MonitorState.STOPPED:
            self.monitor_manager.stop_monitoring()
            time.sleep(0.5)  # 等待停止
    
    def test_config_manager_log_manager_integration(self):
        """测试配置管理器与日志管理器的集成"""
        # 创建新的日志管理器，使用配置管理器提供的配置
        test_log_config = {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "test.log"
        }
        
        # 模拟配置管理器返回日志配置
        with patch.object(self.config_manager, 'config', test_log_config):
            # 创建新的日志管理器
            new_log_manager = LogManager()
            
            # 验证日志管理器已正确初始化
            self.assertIsNotNone(new_log_manager)
            
            # 测试日志记录
            new_log_manager.info("测试配置管理器与日志管理器集成")
    
    def test_monitor_manager_service_integration(self):
        """测试监控管理器与各服务的集成"""
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 验证监控状态
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.RUNNING)
        
        # 等待一段时间让监控循环运行
        time.sleep(1)
        
        # 验证服务已正确初始化
        self.assertIsNotNone(self.monitor_manager.image_service)
        self.assertIsNotNone(self.monitor_manager.click_service)
        self.assertIsNotNone(self.monitor_manager.process_service)
        
        # 验证服务配置已更新
        self.assertEqual(self.monitor_manager.image_service.config, self.test_config.get("detection", {}))
        self.assertEqual(self.monitor_manager.click_service.config, self.test_config.get("click", {}))
        self.assertEqual(self.monitor_manager.process_service.config, self.test_config.get("monitor", {}))
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
        
        # 验证监控状态
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
    
    def test_monitor_click_integration(self):
        """测试监控与点击服务的集成"""
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 等待一段时间让监控循环运行
        time.sleep(1.5)  # 增加等待时间，确保监控循环至少运行一次
        
        # 验证点击服务是否被调用
        self.assertGreater(self.monitor_manager.click_service.click_count, 0)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
    
    def test_monitor_process_check_integration(self):
        """测试监控与进程检查的集成"""
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 等待一段时间让监控循环运行
        time.sleep(1)
        
        # 模拟进程未运行
        self.monitor_manager.process_service.process_running = False
        
        # 等待一段时间让监控循环检测到进程变化
        time.sleep(1)
        
        # 验证监控仍在运行（即使进程未运行）
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.RUNNING)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
    
    def test_config_updates_integration(self):
        """测试配置更新与各服务的集成"""
        # 创建新配置
        new_config = {
            "monitor": {
                "interval_seconds": 0.2,  # 更短的间隔
                "cooldown_seconds": 0.5,
                "process_names": ["test2"],
                "skip_process_check": True
            },
            "detection": {
                "scale_factor": 0.8,
                "threshold_main": 0.9,
                "threshold_handlers": 0.95
            },
            "click": {}
        }
        
        # 更新配置
        with patch.object(self.config_manager, 'config', new_config):
            self.monitor_manager._load_config()
        
        # 验证服务配置已更新
        self.assertEqual(self.monitor_manager.image_service.config, new_config.get("detection", {}))
        self.assertEqual(self.monitor_manager.click_service.config, new_config.get("click", {}))
        self.assertEqual(self.monitor_manager.process_service.config, new_config.get("monitor", {}))
        
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 验证监控状态
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.RUNNING)
        
        # 等待一段时间让监控循环运行
        time.sleep(0.5)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()


if __name__ == "__main__":
    unittest.main()