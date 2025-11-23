"""
日志管理器测试
"""
import unittest
import os
import tempfile
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.log_manager import LogManager, LogLevel


class TestLogManager(unittest.TestCase):
    """日志管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时日志文件
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_log.txt")
        
        # 创建日志管理器实例，强制创建新实例
        self.log_manager = LogManager(self.log_file, force_new=True)
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)
    
    def test_write_log(self):
        """测试写入日志"""
        # 写入不同级别的日志
        self.log_manager.write_log(LogLevel.INFO, "测试信息日志")
        self.log_manager.write_log(LogLevel.WARNING, "测试警告日志")
        self.log_manager.write_log(LogLevel.ERROR, "测试错误日志")
        
        # 验证日志文件存在
        self.assertTrue(os.path.exists(self.log_file))
        
        # 读取日志内容
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 验证日志内容
        self.assertIn("测试信息日志", log_content)
        self.assertIn("测试警告日志", log_content)
        self.assertIn("测试错误日志", log_content)
        self.assertIn("[INFO]", log_content)
        self.assertIn("[WARNING]", log_content)
        self.assertIn("[ERROR]", log_content)
    
    def test_convenience_methods(self):
        """测试便捷方法"""
        # 使用便捷方法写入日志
        self.log_manager.info("测试信息")
        self.log_manager.warning("测试警告")
        self.log_manager.error("测试错误")
        
        # 读取日志内容
        logs = self.log_manager.read_logs()
        
        # 验证日志内容
        self.assertIn("测试信息", logs)
        self.assertIn("测试警告", logs)
        self.assertIn("测试错误", logs)
    
    def test_clear_logs(self):
        """测试清空日志"""
        # 写入日志
        self.log_manager.info("测试日志")
        
        # 验证日志存在
        logs_before = self.log_manager.read_logs()
        self.assertIn("测试日志", logs_before)
        
        # 清空日志
        result = self.log_manager.clear_logs()
        self.assertTrue(result)
        
        # 验证日志已清空
        logs_after = self.log_manager.read_logs()
        self.assertEqual(logs_after, "")
    
    def test_get_log_size(self):
        """测试获取日志大小"""
        # 初始大小应为0
        size_before = self.log_manager.get_log_size()
        self.assertEqual(size_before, 0)
        
        # 写入日志
        self.log_manager.info("测试日志内容")
        
        # 验证大小增加
        size_after = self.log_manager.get_log_size()
        self.assertGreater(size_after, size_before)
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 创建第二个日志管理器实例
        log_manager2 = LogManager(self.log_file)
        
        # 验证是同一个实例
        self.assertIs(self.log_manager, log_manager2)
        
        # 创建强制新实例
        log_manager3 = LogManager(self.log_file, force_new=True)
        
        # 验证不是同一个实例
        self.assertIsNot(self.log_manager, log_manager3)


if __name__ == "__main__":
    unittest.main()