"""
自动点击服务模块
负责执行鼠标点击操作，包含错误处理和重试机制
"""
import time
import pyautogui
from typing import Optional, Tuple
from src.data.log_manager import LogManager


class AutoClickService:
    """自动点击服务，负责执行鼠标点击操作"""
    
    def __init__(self, retry_count: int = 3, retry_delay: float = 0.5):
        """
        初始化自动点击服务
        
        Args:
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.logger = LogManager()
        
        # 设置pyautogui安全措施
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def click_position(self, x: int, y: int, button: str = "left", clicks: int = 1) -> bool:
        """
        点击指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            button: 鼠标按钮 ("left", "right", "middle")
            clicks: 点击次数
            
        Returns:
            是否点击成功
        """
        for attempt in range(self.retry_count):
            try:
                self.logger.debug(f"尝试点击位置 ({x}, {y}), 尝试次数: {attempt + 1}")
                pyautogui.click(x, y, button=button, clicks=clicks)
                self.logger.info(f"成功点击位置 ({x}, {y})")
                return True
            except Exception as e:
                self.logger.warning(f"点击失败 (尝试 {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        self.logger.error(f"点击位置 ({x}, {y}) 失败，已达到最大重试次数")
        return False
    
    def click_with_offset(self, position: Tuple[int, int], offset_x: int = 0, offset_y: int = 0, 
                          button: str = "left", clicks: int = 1) -> bool:
        """
        点击带偏移的位置
        
        Args:
            position: 原始位置 (x, y)
            offset_x: X轴偏移量
            offset_y: Y轴偏移量
            button: 鼠标按钮
            clicks: 点击次数
            
        Returns:
            是否点击成功
        """
        x, y = position
        return self.click_position(x + offset_x, y + offset_y, button, clicks)
    
    def double_click(self, x: int, y: int) -> bool:
        """
        双击指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            是否双击成功
        """
        return self.click_position(x, y, clicks=2)
    
    def right_click(self, x: int, y: int) -> bool:
        """
        右键点击指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            是否右键点击成功
        """
        return self.click_position(x, y, button="right")
    
    def drag_to(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                duration: float = 0.5) -> bool:
        """
        拖拽操作
        
        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 拖拽持续时间（秒）
            
        Returns:
            是否拖拽成功
        """
        for attempt in range(self.retry_count):
            try:
                self.logger.debug(f"尝试拖拽 ({start_x}, {start_y}) -> ({end_x}, {end_y}), 尝试次数: {attempt + 1}")
                pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
                self.logger.info(f"成功拖拽 ({start_x}, {start_y}) -> ({end_x}, {end_y})")
                return True
            except Exception as e:
                self.logger.warning(f"拖拽失败 (尝试 {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        self.logger.error(f"拖拽 ({start_x}, {start_y}) -> ({end_x}, {end_y}) 失败，已达到最大重试次数")
        return False
    
    def scroll(self, x: int, y: int, clicks: int, direction: str = "down") -> bool:
        """
        在指定位置滚动鼠标滚轮
        
        Args:
            x: X坐标
            y: Y坐标
            clicks: 滚动点击次数
            direction: 滚动方向 ("up" 或 "down")
            
        Returns:
            是否滚动成功
        """
        for attempt in range(self.retry_count):
            try:
                self.logger.debug(f"尝试在 ({x}, {y}) 位置滚动 {direction} {clicks} 次, 尝试次数: {attempt + 1}")
                
                # 移动鼠标到指定位置
                pyautogui.moveTo(x, y)
                
                # 执行滚动
                scroll_value = -clicks if direction == "up" else clicks
                pyautogui.scroll(scroll_value)
                
                self.logger.info(f"成功在 ({x}, {y}) 位置滚动 {direction} {clicks} 次")
                return True
            except Exception as e:
                self.logger.warning(f"滚动失败 (尝试 {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        self.logger.error(f"在 ({x}, {y}) 位置滚动 {direction} {clicks} 次失败，已达到最大重试次数")
        return False
    
    def set_retry_params(self, retry_count: int, retry_delay: float) -> None:
        """
        设置重试参数
        
        Args:
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.logger.info(f"重试参数已更新: 次数={retry_count}, 延迟={retry_delay}秒")
    
    def update_config(self, config: dict) -> None:
        """
        更新服务配置
        
        Args:
            config: 配置字典，包含retry_count和retry_delay等参数
        """
        if "retry_count" in config:
            self.retry_count = config["retry_count"]
        
        if "retry_delay" in config:
            self.retry_delay = config["retry_delay"]
            
        # 更新pyautogui设置
        if "pause" in config:
            pyautogui.PAUSE = config["pause"]
            
        self.logger.info(f"AutoClickService配置已更新: {config}")