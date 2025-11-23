"""
系统测试脚本
验证TraeMate的端到端功能
"""
import sys
import os
import time
import threading
import unittest
from unittest.mock import Mock, patch

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.config_manager import ConfigManager
from src.data.log_manager import LogManager
from src.business.monitor_manager import MonitorManager, MonitorState
from src.business.handler_manager import HandlerManager
from src.ui.status_bar import StatusBar
from src.ui.system_tray import SystemTray


class TestSystemFunctionality(unittest.TestCase):
    """系统功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置和日志文件
        self.temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        self.config_file = os.path.join(self.temp_dir, "system_test_config.json")
        self.log_file = os.path.join(self.temp_dir, "system_test_log.txt")
        
        # 创建配置管理器
        self.config_manager = ConfigManager(self.config_file)
        
        # 创建日志管理器（强制创建新实例）
        self.log_manager = LogManager(self.log_file, force_new=True)
        
        # 创建业务层组件
        self.monitor_manager = MonitorManager(self.config_manager, self.log_manager)
        self.handler_manager = HandlerManager(self.config_manager, self.log_manager)
    
    def tearDown(self):
        """测试后清理"""
        # 停止监控
        if self.monitor_manager.is_running():
            self.monitor_manager.stop_monitoring()
        
        # 删除临时文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_config_manager_initialization(self):
        """测试配置管理器初始化"""
        # 验证配置加载
        config = self.config_manager.get_config()
        self.assertIn("app_name", config)
        self.assertIn("window", config)
        self.assertIn("monitor", config)
        self.assertIn("detection", config)
        
        # 验证配置验证
        self.assertTrue(self.config_manager.validate_config())
    
    def test_log_manager_functionality(self):
        """测试日志管理器功能"""
        # 写入不同级别的日志
        self.log_manager.info("测试信息日志")
        self.log_manager.warning("测试警告日志")
        self.log_manager.error("测试错误日志")
        
        # 读取日志
        logs = self.log_manager.read_logs()
        self.assertIn("测试信息日志", logs)
        self.assertIn("测试警告日志", logs)
        self.assertIn("测试错误日志", logs)
        
        # 获取日志大小
        size = self.log_manager.get_log_size()
        self.assertGreater(size, 0)
        
        # 清空日志
        result = self.log_manager.clear_logs()
        self.assertTrue(result)
        
        # 验证日志已清空
        logs_after = self.log_manager.read_logs()
        self.assertEqual(logs_after, "")
    
    def test_monitor_manager_lifecycle(self):
        """测试监控管理器生命周期"""
        # 初始状态应为停止
        self.assertFalse(self.monitor_manager.is_running())
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
        
        # 启动监控
        self.monitor_manager.start_monitoring()
        self.assertTrue(self.monitor_manager.is_running())
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.RUNNING)
        
        # 等待一小段时间让监控循环运行
        time.sleep(1)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
        self.assertFalse(self.monitor_manager.is_running())
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
    
    def test_handler_manager_functionality(self):
        """测试处理项管理器功能"""
        # 获取处理项列表
        handlers = self.handler_manager.get_handlers()
        self.assertIsInstance(handlers, list)
        original_count = len(handlers)
        
        # 创建一个临时图像文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
            temp_img_path = temp_img.name
        
        # 添加处理项
        test_handler = {
            "name": "测试处理项_" + str(int(time.time())),  # 添加时间戳确保唯一性
            "description": "测试描述",
            "image_file": temp_img_path,
            "offset_x": 0,
            "offset_y": 0,
            "enabled": True
        }
        result = self.handler_manager.add_handler(test_handler)
        self.assertTrue(result)  # 确保添加成功
        
        # 验证处理项已添加
        handlers_after = self.handler_manager.get_handlers()
        self.assertEqual(len(handlers_after), original_count + 1)  # 确保数量增加1
        
        # 验证新添加的处理项在列表中
        found = False
        for handler in handlers_after:
            if handler.get("name") == test_handler.get("name"):
                found = True
                break
        self.assertTrue(found)
        
        # 删除处理项
        self.handler_manager.delete_handler(test_handler.get("name"))
        handlers_final = self.handler_manager.get_handlers()
        self.assertEqual(len(handlers_final), original_count)  # 确保数量恢复
        
        # 清理临时文件
        import os
        try:
            os.unlink(temp_img_path)
        except:
            pass
    
    def test_component_integration(self):
        """测试组件集成"""
        # 创建模拟回调
        state_change_callback = Mock()
        indicator_callback = Mock()
        
        # 设置回调
        self.monitor_manager.set_state_change_callback(state_change_callback)
        self.monitor_manager.set_indicator_callback(indicator_callback)
        
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 等待一小段时间让监控循环运行
        time.sleep(1)
        
        # 验证回调被调用
        self.assertTrue(state_change_callback.called)
        self.assertTrue(indicator_callback.called)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
    
    def test_configuration_updates(self):
        """测试配置更新"""
        # 获取原始配置
        original_config = self.config_manager.get_config()
        
        # 修改配置
        self.config_manager.set("monitor.interval_seconds", 5.0)
        self.config_manager.set("window.width", 500)
        
        # 保存配置
        result = self.config_manager.save_config()
        self.assertTrue(result)
        
        # 创建新的配置管理器实例验证保存结果
        new_config_manager = ConfigManager(self.config_file)
        self.assertEqual(new_config_manager.get("monitor.interval_seconds"), 5.0)
        self.assertEqual(new_config_manager.get("window.width"), 500)
        
        # 重新加载配置到监控管理器
        self.monitor_manager.reload_config()
        
        # 验证配置已更新 - 直接从配置管理器获取
        self.assertEqual(self.config_manager.get("monitor.interval_seconds"), 5.0)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效配置
        invalid_config = {
            "app_name": "Test",
            "window": {
                "width": -1,  # 无效值
                "height": 30
            },
            "monitor": {
                "interval_seconds": 1.0,
                "cooldown_seconds": 20
            },
            "detection": {
                "scale_factor": 1.0,
                "threshold_main": 0.7,
                "threshold_handlers": 0.8
            }
        }
        
        # 创建新的配置管理器并设置无效配置
        temp_config_file = os.path.join(self.temp_dir, "invalid_config.json")
        with open(temp_config_file, 'w') as f:
            import json
            json.dump(invalid_config, f)
        
        invalid_config_manager = ConfigManager(temp_config_file)
        
        # 验证配置验证失败
        self.assertFalse(invalid_config_manager.validate_config())
        
        # 清理
        os.remove(temp_config_file)


if __name__ == "__main__":
    # 运行系统测试
    unittest.main(verbosity=2)