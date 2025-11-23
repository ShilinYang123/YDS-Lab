"""
配置管理器测试
"""
import unittest
import os
import tempfile
import json
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """配置管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # 创建测试配置
        self.test_config = {
            "app_name": "TestApp",
            "window": {
                "width": 400,
                "height": 30,
                "bg_color": "#000000",
                "alpha": 0.8
            },
            "indicator": {
                "size": 12,
                "blink_interval": 500
            },
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
            "custom_handlers": [
                {
                    "name": "test_handler",
                    "description": "测试处理项",
                    "image_file": "test.png",
                    "offset_x": 0,
                    "offset_y": 0,
                    "enabled": True
                }
            ]
        }
        
        # 写入测试配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)
        
        # 创建配置管理器实例
        self.config_manager = ConfigManager(self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_load_config(self):
        """测试加载配置"""
        config = self.config_manager.get_config()
        
        # 验证配置加载
        self.assertEqual(config["app_name"], "TestApp")
        self.assertEqual(config["window"]["width"], 400)
        self.assertEqual(config["window"]["height"], 30)
        self.assertEqual(len(config["custom_handlers"]), 1)
        self.assertEqual(config["custom_handlers"][0]["name"], "test_handler")
    
    def test_get_config_value(self):
        """测试获取配置项"""
        # 测试获取存在的配置项
        self.assertEqual(self.config_manager.get("app_name"), "TestApp")
        self.assertEqual(self.config_manager.get("window.width"), 400)
        self.assertEqual(self.config_manager.get("custom_handlers.0.name"), "test_handler")
        
        # 测试获取不存在的配置项
        self.assertIsNone(self.config_manager.get("nonexistent"))
        self.assertIsNone(self.config_manager.get("window.nonexistent"))
        
        # 测试默认值
        self.assertEqual(self.config_manager.get("nonexistent", "default"), "default")
    
    def test_set_config_value(self):
        """测试设置配置项"""
        # 测试设置存在的配置项
        self.config_manager.set("app_name", "NewTestApp")
        self.assertEqual(self.config_manager.get("app_name"), "NewTestApp")
        
        # 测试设置嵌套配置项
        self.config_manager.set("window.width", 500)
        self.assertEqual(self.config_manager.get("window.width"), 500)
        
        # 测试设置新配置项
        self.config_manager.set("new_key", "new_value")
        self.assertEqual(self.config_manager.get("new_key"), "new_value")
        
        # 测试设置新的嵌套配置项
        self.config_manager.set("new_section.new_key", "new_nested_value")
        self.assertEqual(self.config_manager.get("new_section.new_key"), "new_nested_value")
    
    def test_save_config(self):
        """测试保存配置"""
        # 修改配置
        self.config_manager.set("app_name", "SavedApp")
        
        # 保存配置
        result = self.config_manager.save_config()
        self.assertTrue(result)
        
        # 创建新的配置管理器实例验证保存结果
        new_config_manager = ConfigManager(self.config_file)
        self.assertEqual(new_config_manager.get("app_name"), "SavedApp")
    
    def test_validate_config(self):
        """测试配置验证"""
        # 测试有效配置
        self.assertTrue(self.config_manager.validate_config())
        
        # 测试无效配置 - 缺少必需字段
        self.config_manager.config.pop("app_name", None)
        self.assertFalse(self.config_manager.validate_config())
        
        # 测试无效配置 - 无效的窗口宽度
        self.config_manager.set("window.width", -1)
        self.assertFalse(self.config_manager.validate_config())


if __name__ == "__main__":
    unittest.main()