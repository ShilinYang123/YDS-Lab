"""
错误处理和边缘情况测试
"""

import sys
import os
import unittest
import tempfile
import time
import json
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入项目模块
from src.data.config_manager import ConfigManager
from src.data.log_manager import LogManager
from src.business.monitor_manager import MonitorManager, MonitorState
from src.business.handler_manager import HandlerManager


class TestErrorHandling(unittest.TestCase):
    """错误处理和边缘情况测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建临时配置文件
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.valid_config = {
            "app_name": "Test App",
            "window": {
                "width": 300,
                "height": 30,
                "always_on_top": True
            },
            "monitor": {
                "interval_seconds": 1.0,
                "cooldown_seconds": 20.0,
                "max_clicks_per_minute": 30
            },
            "detection": {
                "scale_factor": 1.0,
                "threshold_main": 0.7,
                "threshold_handlers": 0.8
            },
            "process": {
                "names": ["test_process.exe"],
                "check_interval": 5.0
            },
            "logging": {
                "level": "INFO",
                "file": "test.log",
                "max_size_mb": 10
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(self.valid_config, f)
        
        # 创建临时日志文件
        self.log_file = os.path.join(self.temp_dir, "test.log")
        
        # 初始化组件
        self.config_manager = ConfigManager(self.config_file)
        self.log_manager = LogManager(self.log_file, force_new=True)
        self.handler_manager = HandlerManager(self.config_manager, self.log_manager)
        self.monitor_manager = MonitorManager(self.config_manager, self.log_manager)
    
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
            try:
                os.rmdir(self.temp_dir)
            except:
                pass
    
    def test_invalid_config_file_handling(self):
        """测试无效配置文件处理"""
        # 创建不存在的配置文件路径
        nonexistent_config = os.path.join(self.temp_dir, "nonexistent.json")
        
        # 使用不存在的配置文件初始化配置管理器
        config_manager = ConfigManager(nonexistent_config)
        
        # 验证使用了默认配置
        config = config_manager.get_config()
        self.assertIn("app_name", config)
        self.assertIn("window", config)
        
        # 验证配置验证成功（默认配置是有效的）
        self.assertTrue(config_manager.validate_config())
    
    def test_invalid_json_config_handling(self):
        """测试无效JSON配置文件处理"""
        # 创建包含无效JSON的配置文件
        invalid_json_config = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_config, 'w') as f:
            f.write("{ invalid json content")
        
        # 使用无效JSON配置文件初始化配置管理器
        config_manager = ConfigManager(invalid_json_config)
        
        # 验证使用了默认配置
        config = config_manager.get_config()
        self.assertIn("app_name", config)
        
        # 清理
        os.remove(invalid_json_config)
    
    def test_invalid_config_values(self):
        """测试无效配置值处理"""
        # 测试负数窗口尺寸
        self.config_manager.set("window.width", -100)
        self.config_manager.set("window.height", -50)
        
        # 验证配置验证失败
        self.assertFalse(self.config_manager.validate_config())
        
        # 测试过大的监控间隔
        self.config_manager.set("monitor.interval_seconds", 1000.0)
        
        # 验证配置验证失败
        self.assertFalse(self.config_manager.validate_config())
        
        # 测试无效的阈值
        self.config_manager.set("detection.threshold_main", 1.5)
        self.config_manager.set("detection.threshold_handlers", -0.1)
        
        # 验证配置验证失败
        self.assertFalse(self.config_manager.validate_config())
    
    def test_missing_config_sections(self):
        """测试缺少配置节处理"""
        # 创建缺少必要节的配置
        incomplete_config = {
            "app_name": "Test App"
            # 缺少 window, monitor, detection 等必要节
        }
        
        incomplete_config_file = os.path.join(self.temp_dir, "incomplete.json")
        with open(incomplete_config_file, 'w') as f:
            json.dump(incomplete_config, f)
        
        # 使用不完整配置初始化配置管理器
        config_manager = ConfigManager(incomplete_config_file)
        
        # 验证配置验证失败
        self.assertFalse(config_manager.validate_config())
        
        # 清理
        os.remove(incomplete_config_file)
    
    def test_invalid_image_file_handling(self):
        """测试无效图像文件处理"""
        # 创建不存在的图像文件路径
        nonexistent_image = os.path.join(self.temp_dir, "nonexistent.png")
        
        # 尝试使用不存在的图像文件添加处理项
        handler = {
            "name": "测试处理项",
            "description": "测试描述",
            "image_file": nonexistent_image,
            "offset_x": 0,
            "offset_y": 0,
            "enabled": True
        }
        
        # 验证添加失败
        result = self.handler_manager.add_handler(handler)
        self.assertFalse(result)
    
    def test_invalid_process_name_handling(self):
        """测试无效进程名处理"""
        # 测试空进程名列表
        self.config_manager.set("process.names", [])
        
        # 验证配置验证仍然成功（空列表是有效的）
        self.assertTrue(self.config_manager.validate_config())
        
        # 测试None进程名
        self.config_manager.set("process.names", None)
        
        # 验证配置验证失败（None是无效的）
        self.assertFalse(self.config_manager.validate_config())
    
    def test_log_file_permission_error(self):
        """测试日志文件权限错误处理"""
        # 模拟日志文件权限错误
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # 创建日志管理器
            log_manager = LogManager(self.log_file)
            
            # 尝试写入日志
            try:
                log_manager.info("测试日志")
                # 如果没有抛出异常，说明错误被正确处理
                self.assertTrue(True)
            except PermissionError:
                # 如果抛出了异常，说明错误处理有问题
                self.fail("日志权限错误未被正确处理")
    
    def test_monitor_manager_concurrent_operations(self):
        """测试监控管理器并发操作"""
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 尝试再次启动监控（应该被忽略）
        self.monitor_manager.start_monitoring()
        
        # 验证监控仍在运行
        self.assertTrue(self.monitor_manager.is_running())
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
        
        # 尝试再次停止监控（应该被忽略）
        self.monitor_manager.stop_monitoring()
        
        # 验证监控已停止
        self.assertFalse(self.monitor_manager.is_running())
    
    def test_handler_manager_duplicate_names(self):
        """测试处理项管理器重复名称处理"""
        # 创建临时图像文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
            temp_img_path = temp_img.name
        
        try:
            # 添加处理项
            handler = {
                "name": "测试处理项",
                "description": "测试描述",
                "image_file": temp_img_path,
                "offset_x": 0,
                "offset_y": 0,
                "enabled": True
            }
            result = self.handler_manager.add_handler(handler)
            self.assertTrue(result)
            
            # 尝试添加同名处理项
            result = self.handler_manager.add_handler(handler)
            self.assertFalse(result)  # 应该失败
            
            # 删除处理项
            self.handler_manager.delete_handler("测试处理项")
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_img_path)
            except:
                pass
    
    def test_auto_click_service_edge_cases(self):
        """测试自动点击服务边缘情况"""
        # 测试无效坐标
        with patch('pyautogui.click') as mock_click:
            # 尝试点击无效坐标
            self.auto_click_service.click(-100, -100)
            
            # 验证点击被调用（即使坐标无效）
            mock_click.assert_called_once()
        
        # 测试无效拖拽坐标
        with patch('pyautogui.dragTo') as mock_drag:
            # 尝试拖拽到无效坐标
            self.auto_click_service.drag(0, 0, -100, -100)
            
            # 验证拖拽被调用（即使坐标无效）
            mock_drag.assert_called_once()
    
    def test_image_detection_service_edge_cases(self):
        """测试图像检测服务边缘情况"""
        # 测试空屏幕截图
        with patch('pyautogui.screenshot', return_value=None):
            # 尝试检测图像
            result = self.image_detection_service.detect_image("test.png")
            
            # 验证返回None（没有找到图像）
            self.assertIsNone(result)
        
        # 测试无效阈值
        with patch.object(self.image_detection_service, 'threshold', -1.0):
            # 尝试检测图像
            result = self.image_detection_service.detect_image("test.png")
            
            # 验证返回None（阈值无效）
            self.assertIsNone(result)
    
    def test_config_update_with_invalid_values(self):
        """测试使用无效值更新配置"""
        # 尝试设置无效配置值
        with patch.object(self.config_manager, 'validate_config', return_value=False):
            # 尝试保存配置
            result = self.config_manager.save_config()
            
            # 验证保存失败
            self.assertFalse(result)
    
    def test_memory_cleanup(self):
        """测试内存清理"""
        # 启动监控
        self.monitor_manager.start_monitoring()
        
        # 等待一小段时间
        time.sleep(1)
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
        
        # 验证状态已重置
        self.assertEqual(self.monitor_manager.get_state(), MonitorState.STOPPED)
        self.assertFalse(self.monitor_manager.is_running())
        
        # 验证统计信息已重置
        stats = self.monitor_manager.get_stats()
        self.assertIn("total_clicks", stats)
        self.assertIn("total_detections", stats)


if __name__ == "__main__":
    unittest.main(verbosity=2)