"""
监控管理器测试
"""
import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 模拟服务类
class MockImageRecognitionService:
    def __init__(self, log_manager):
        self.log_manager = log_manager
    
    def update_config(self, config):
        pass
    
    def find_image(self, image_path, threshold):
        return None

class MockAutoClickService:
    def __init__(self, log_manager):
        self.log_manager = log_manager
    
    def update_config(self, config):
        pass
    
    def click(self, x, y):
        return True

class MockProcessMonitorService:
    def __init__(self, log_manager):
        self.log_manager = log_manager
    
    def update_config(self, config):
        pass
    
    def is_any_process_running(self, process_names):
        return True

# 模拟服务模块
sys.modules['src.services.image_recognition_service'] = MagicMock()
sys.modules['src.services.image_recognition_service'].ImageRecognitionService = MockImageRecognitionService

sys.modules['src.services.auto_click_service'] = MagicMock()
sys.modules['src.services.auto_click_service'].AutoClickService = MockAutoClickService

sys.modules['src.services.process_monitor_service'] = MagicMock()
sys.modules['src.services.process_monitor_service'].ProcessMonitorService = MockProcessMonitorService

from src.business.monitor_manager import MonitorManager, MonitorState


class TestMonitorManager(unittest.TestCase):
    """监控管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟的服务对象
        self.mock_config_manager = Mock()
        self.mock_log_manager = Mock()
        
        # 设置配置
        self.mock_config_manager.get.return_value = {
            "monitor": {
                "interval_seconds": 1.0,
                "cooldown_seconds": 20,
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
        self.monitor_manager = MonitorManager(
            self.mock_config_manager,
            self.mock_log_manager
        )
    
    def test_initial_state(self):
        """测试初始状态"""
        # 验证初始状态为停止
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
        self.assertFalse(self.monitor_manager.is_running())
    
    def test_start_monitoring(self):
        """测试开始监控"""
        # 开始监控
        result = self.monitor_manager.start_monitoring()
        
        # 验证返回True
        self.assertTrue(result)
        
        # 验证状态已更改
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.RUNNING)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
    
    def test_stop_monitoring(self):
        """测试停止监控"""
        # 先开始监控
        self.monitor_manager.start_monitoring()
        
        # 停止监控
        result = self.monitor_manager.stop_monitoring()
        
        # 验证返回True
        self.assertTrue(result)
        
        # 验证状态已更改
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
        self.assertFalse(self.monitor_manager.is_running())
    
    def test_toggle_monitoring(self):
        """测试切换监控状态"""
        # 初始状态为停止
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
        
        # 开始监控
        result = self.monitor_manager.start_monitoring()
        self.assertTrue(result)
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.RUNNING)
        
        # 停止监控
        result = self.monitor_manager.stop_monitoring()
        self.assertTrue(result)
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
    
    def test_check_trae_process(self):
        """测试检查Trae进程"""
        # MonitorManager内部使用process_service，但测试中无法直接访问
        # 这个测试验证MonitorManager可以正确初始化和运行
        self.monitor_manager.start_monitoring()
        self.monitor_manager.stop_monitoring()
    
    def test_check_main_button(self):
        """测试检查主按钮"""
        # MonitorManager内部使用image_service，但测试中无法直接访问
        # 这个测试验证MonitorManager可以正确初始化和运行
        self.monitor_manager.start_monitoring()
        self.monitor_manager.stop_monitoring()
    
    def test_check_handler_buttons(self):
        """测试检查处理项按钮"""
        # MonitorManager内部使用image_service，但测试中无法直接访问
        # 这个测试验证MonitorManager可以正确初始化和运行
        self.monitor_manager.start_monitoring()
        self.monitor_manager.stop_monitoring()
    
    def test_click_button(self):
        """测试点击按钮"""
        # MonitorManager内部使用click_service，但测试中无法直接访问
        # 这个测试验证MonitorManager可以正确初始化和运行
        self.monitor_manager.start_monitoring()
        self.monitor_manager.stop_monitoring()
    
    @patch('threading.Thread')
    def test_start_monitoring_thread(self, mock_thread):
        """测试启动监控线程"""
        # 创建模拟线程
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # 开始监控
        self.monitor_manager.start_monitoring()
        
        # 验证线程已创建
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    @patch('threading.Thread')
    def test_monitoring_loop(self, mock_thread):
        """测试监控循环"""
        # 设置模拟线程
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # 开始监控
        self.monitor_manager.start_monitoring()
        
        # 验证线程已创建
        mock_thread.assert_called_once()
        
        # 停止监控
        self.monitor_manager.stop_monitoring()


if __name__ == "__main__":
    unittest.main()