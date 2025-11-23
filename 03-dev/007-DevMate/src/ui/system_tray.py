"""
系统托盘组件
负责系统托盘图标和菜单
"""
import os
import sys
import threading
from typing import Callable, Optional, List
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from src.data.log_manager import LogManager


class SystemTray:
    """系统托盘组件，管理托盘图标和菜单"""
    
    def __init__(self, app_name: str = "TraeMate"):
        """
        初始化系统托盘
        
        Args:
            app_name: 应用程序名称
        """
        self.app_name = app_name
        self.logger = LogManager()
        self.icon = None
        self.icon_thread = None
        self.is_running = False
        
        # 回调函数
        self.on_show_callback = None
        self.on_hide_callback = None
        self.on_start_callback = None
        self.on_stop_callback = None
        self.on_exit_callback = None
        self.on_configure_callback = None
        self.on_logs_callback = None
    
    def _create_icon_image(self, color: str = "#2c3553", size: int = 64) -> Image.Image:
        """
        创建托盘图标图像
        
        Args:
            color: 图标颜色
            size: 图标大小
            
        Returns:
            PIL图像对象
        """
        # 创建一个正方形图像
        image = Image.new('RGB', (size, size), color)
        draw = ImageDraw.Draw(image)
        
        # 绘制一个简单的圆形指示器
        padding = size // 8
        draw.ellipse([padding, padding, size-padding, size-padding], fill="#00ff00")
        
        return image
    
    def _get_icon_path(self) -> str:
        """获取图标文件路径"""
        # 兼容PyInstaller打包路径
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, 'icon.ico')
        return os.path.join(os.path.dirname(__file__), '..', '..', 'icon.ico')
    
    def _setup_menu(self) -> List[item]:
        """
        设置托盘菜单
        
        Returns:
            菜单项列表
        """
        menu_items = [
            item('显示', self._on_show, default=True),
            item('隐藏', self._on_hide),
            item('开始监控', self._on_start),
            item('停止监控', self._on_stop),
            item('配置', self._on_configure),
            item('日志', self._on_logs),
            item('退出', self._on_exit)
        ]
        return menu_items
    
    def _on_show(self, icon=None, item=None) -> None:
        """显示窗口回调"""
        if self.on_show_callback:
            self.on_show_callback()
        self.logger.debug("通过托盘菜单显示窗口")
    
    def _on_hide(self, icon=None, item=None) -> None:
        """隐藏窗口回调"""
        if self.on_hide_callback:
            self.on_hide_callback()
        self.logger.debug("通过托盘菜单隐藏窗口")
    
    def _on_start(self, icon=None, item=None) -> None:
        """开始监控回调"""
        if self.on_start_callback:
            self.on_start_callback()
        self.logger.debug("通过托盘菜单开始监控")
    
    def _on_stop(self, icon=None, item=None) -> None:
        """停止监控回调"""
        if self.on_stop_callback:
            self.on_stop_callback()
        self.logger.debug("通过托盘菜单停止监控")
    
    def _on_configure(self, icon=None, item=None) -> None:
        """配置回调"""
        if self.on_configure_callback:
            self.on_configure_callback()
        self.logger.debug("通过托盘菜单打开配置")
    
    def _on_logs(self, icon=None, item=None) -> None:
        """日志回调"""
        if self.on_logs_callback:
            self.on_logs_callback()
        self.logger.debug("通过托盘菜单打开日志")
    
    def _on_exit(self, icon=None, item=None) -> None:
        """退出回调"""
        if self.on_exit_callback:
            self.on_exit_callback()
        self.logger.debug("通过托盘菜单退出应用")
        self.stop()
    
    def start(self) -> None:
        """启动系统托盘"""
        if self.is_running:
            self.logger.warning("系统托盘已在运行")
            return
        
        try:
            # 尝试加载图标文件
            icon_path = self._get_icon_path()
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
            else:
                # 如果图标文件不存在，创建默认图标
                icon_image = self._create_icon_image()
                self.logger.warning(f"图标文件不存在: {icon_path}，使用默认图标")
            
            # 创建托盘图标
            self.icon = pystray.Icon(
                self.app_name,
                icon_image,
                self.app_name,
                menu=pystray.Menu(*self._setup_menu())
            )
            
            # 在单独线程中运行托盘
            self.icon_thread = threading.Thread(target=self.icon.run, daemon=True)
            self.icon_thread.start()
            self.is_running = True
            self.logger.info("系统托盘已启动")
            
        except Exception as e:
            self.logger.error(f"启动系统托盘失败: {e}")
            self.is_running = False
    
    def stop(self) -> None:
        """停止系统托盘"""
        if not self.is_running:
            return
        
        try:
            if self.icon:
                self.icon.stop()
            self.is_running = False
            self.logger.info("系统托盘已停止")
        except Exception as e:
            self.logger.error(f"停止系统托盘失败: {e}")
    
    def update_icon(self, color: str = None) -> None:
        """
        更新托盘图标
        
        Args:
            color: 新的图标颜色，如果为None则使用默认颜色
        """
        if not self.icon:
            return
        
        try:
            if color:
                icon_image = self._create_icon_image(color)
            else:
                # 尝试加载图标文件
                icon_path = self._get_icon_path()
                if os.path.exists(icon_path):
                    icon_image = Image.open(icon_path)
                else:
                    icon_image = self._create_icon_image()
            
            self.icon.icon = icon_image
            self.logger.debug("托盘图标已更新")
        except Exception as e:
            self.logger.error(f"更新托盘图标失败: {e}")
    
    def update_tooltip(self, tooltip: str) -> None:
        """
        更新托盘提示文本
        
        Args:
            tooltip: 新的提示文本
        """
        if not self.icon:
            return
        
        try:
            self.icon.title = tooltip
            self.logger.debug(f"托盘提示已更新: {tooltip}")
        except Exception as e:
            self.logger.error(f"更新托盘提示失败: {e}")
    
    def set_on_show_callback(self, callback: Callable) -> None:
        """
        设置显示窗口回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_show_callback = callback
    
    def set_on_hide_callback(self, callback: Callable) -> None:
        """
        设置隐藏窗口回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_hide_callback = callback
    
    def set_on_start_callback(self, callback: Callable) -> None:
        """
        设置开始监控回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_start_callback = callback
    
    def set_on_stop_callback(self, callback: Callable) -> None:
        """
        设置停止监控回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_stop_callback = callback
    
    def set_on_configure_callback(self, callback: Callable) -> None:
        """
        设置配置回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_configure_callback = callback
    
    def set_on_logs_callback(self, callback: Callable) -> None:
        """
        设置日志回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_logs_callback = callback
    
    def set_on_exit_callback(self, callback: Callable) -> None:
        """
        设置退出回调函数
        
        Args:
            callback: 回调函数
        """
        self.on_exit_callback = callback