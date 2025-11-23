"""
状态栏UI组件
负责显示监控状态和指示器
"""
import tkinter as tk
from tkinter import Canvas
import threading
import time
from typing import Callable, Optional
from src.data.log_manager import LogManager


class StatusBar:
    """状态栏组件，显示监控状态和指示器"""
    
    def __init__(self, parent, width: int = 420, height: int = 32, 
                 bg_color: str = "#2c3553", alpha: float = 0.7):
        """
        初始化状态栏
        
        Args:
            parent: 父窗口
            width: 状态栏宽度
            height: 状态栏高度
            bg_color: 背景颜色
            alpha: 透明度
        """
        self.parent = parent
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.alpha = alpha
        self.logger = LogManager()
        
        # 状态变量
        self.is_monitoring = False
        self.indicator_blinking = False
        self.blink_thread = None
        self.blink_interval = 1.0
        self.indicator_color_active = "#00ff00"
        self.indicator_color_inactive = "#888888"
        
        # 创建UI组件
        self._create_ui()
    
    def _create_ui(self) -> None:
        """创建UI组件"""
        # 创建主框架
        self.frame = tk.Frame(
            self.parent,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布用于绘制指示器
        self.canvas = Canvas(
            self.frame,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绘制初始指示器
        self._draw_indicator(self.indicator_color_inactive)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
    
    def _draw_indicator(self, color: str) -> None:
        """
        绘制指示器
        
        Args:
            color: 指示器颜色
        """
        self.canvas.delete("indicator")
        indicator_size = 14
        center_x = self.width // 2
        center_y = self.height // 2
        
        self.canvas.create_oval(
            center_x - indicator_size,
            center_y - indicator_size,
            center_x + indicator_size,
            center_y + indicator_size,
            fill=color,
            outline="",
            tags="indicator"
        )
    
    def _blink_indicator(self) -> None:
        """闪烁指示器"""
        while self.indicator_blinking:
            if self.is_monitoring:
                self._draw_indicator(self.indicator_color_active)
            else:
                self._draw_indicator(self.indicator_color_inactive)
            time.sleep(self.blink_interval)
            
            if self.is_monitoring:
                self._draw_indicator(self.indicator_color_inactive)
            else:
                self._draw_indicator(self.indicator_color_active)
            time.sleep(self.blink_interval)
    
    def start_blinking(self) -> None:
        """开始指示器闪烁"""
        if not self.indicator_blinking:
            self.indicator_blinking = True
            self.blink_thread = threading.Thread(target=self._blink_indicator, daemon=True)
            self.blink_thread.start()
            self.logger.debug("指示器闪烁已开始")
    
    def stop_blinking(self) -> None:
        """停止指示器闪烁"""
        self.indicator_blinking = False
        if self.is_monitoring:
            self._draw_indicator(self.indicator_color_active)
        else:
            self._draw_indicator(self.indicator_color_inactive)
        self.logger.debug("指示器闪烁已停止")
    
    def set_monitoring_status(self, is_monitoring: bool) -> None:
        """
        设置监控状态
        
        Args:
            is_monitoring: 是否正在监控
        """
        self.is_monitoring = is_monitoring
        if not self.indicator_blinking:
            color = self.indicator_color_active if is_monitoring else self.indicator_color_inactive
            self._draw_indicator(color)
        self.logger.debug(f"监控状态已更新: {'监控中' if is_monitoring else '未监控'}")
    
    def set_blink_interval(self, interval: float) -> None:
        """
        设置闪烁间隔
        
        Args:
            interval: 闪烁间隔（秒）
        """
        self.blink_interval = interval
        self.logger.debug(f"指示器闪烁间隔已更新为: {interval}秒")
    
    def set_indicator_colors(self, active: str, inactive: str) -> None:
        """
        设置指示器颜色
        
        Args:
            active: 激活状态颜色
            inactive: 非激活状态颜色
        """
        self.indicator_color_active = active
        self.indicator_color_inactive = inactive
        
        # 更新当前指示器颜色
        if not self.indicator_blinking:
            color = self.indicator_color_active if self.is_monitoring else self.indicator_color_inactive
            self._draw_indicator(color)
        
        self.logger.debug(f"指示器颜色已更新: 激活={active}, 非激活={inactive}")
    
    def set_on_click_callback(self, callback: Callable) -> None:
        """
        设置点击回调函数
        
        Args:
            callback: 点击回调函数
        """
        self.on_click_callback = callback
    
    def set_on_right_click_callback(self, callback: Callable) -> None:
        """
        设置右键点击回调函数
        
        Args:
            callback: 右键点击回调函数
        """
        self.on_right_click_callback = callback
    
    def _on_click(self, event) -> None:
        """处理点击事件"""
        if hasattr(self, 'on_click_callback'):
            self.on_click_callback(event)
    
    def _on_right_click(self, event) -> None:
        """处理右键点击事件"""
        if hasattr(self, 'on_right_click_callback'):
            self.on_right_click_callback(event)
    
    def _on_drag(self, event) -> None:
        """处理拖拽事件"""
        # 获取窗口当前位置
        x = self.parent.winfo_x() + event.x
        y = self.parent.winfo_y() + event.y
        
        # 移动窗口
        self.parent.geometry(f"+{x - self.width // 2}+{y - self.height // 2}")
    
    def set_transparency(self, alpha: float) -> None:
        """
        设置窗口透明度
        
        Args:
            alpha: 透明度值 (0.0-1.0)
        """
        self.alpha = alpha
        self.parent.attributes('-alpha', alpha)
        self.logger.debug(f"窗口透明度已更新为: {alpha}")
    
    def get_size(self) -> tuple:
        """
        获取状态栏大小
        
        Returns:
            (宽度, 高度)
        """
        return (self.width, self.height)