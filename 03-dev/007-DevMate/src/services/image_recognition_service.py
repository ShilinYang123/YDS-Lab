"""
图像识别服务模块
负责屏幕截图、模板匹配和图像识别
"""
import os
import sys
import cv2
import numpy as np
import pyautogui
from typing import Tuple, Optional, List
from src.data.log_manager import LogManager


class ImageRecognitionService:
    """图像识别服务，负责屏幕截图和模板匹配"""
    
    def __init__(self, scale_factor: float = 1.0, threshold: float = 0.8):
        """
        初始化图像识别服务
        
        Args:
            scale_factor: 图像缩放因子
            threshold: 模板匹配阈值
        """
        self.scale_factor = scale_factor
        self.threshold = threshold
        self.logger = LogManager()
        self._resource_path = self._get_resource_path()
    
    def _get_resource_path(self) -> str:
        """获取资源文件路径"""
        # 兼容PyInstaller打包路径
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, 'handler_btn')
        return os.path.join(os.path.dirname(__file__), '..', '..', 'handler_btn')
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        捕获屏幕截图
        
        Returns:
            屏幕截图的numpy数组，失败时返回None
        """
        try:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            self.logger.debug("屏幕截图成功")
            return screenshot
        except Exception as e:
            self.logger.error(f"屏幕截图失败: {e}")
            return None
    
    def match_template(self, image: np.ndarray, template_path: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        在图像中匹配模板
        
        Args:
            image: 源图像
            template_path: 模板图像路径
            
        Returns:
            (是否匹配成功, 位置坐标)，匹配失败时位置为None
        """
        try:
            # 读取模板图像
            template = cv2.imread(template_path)
            if template is None:
                self.logger.error(f"无法读取模板图像: {template_path}")
                return False, None
            
            # 应用缩放因子
            if self.scale_factor != 1.0:
                image = cv2.resize(image, None, fx=self.scale_factor, fy=self.scale_factor)
                template = cv2.resize(template, None, fx=self.scale_factor, fy=self.scale_factor)
            
            # 执行模板匹配
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 检查是否超过阈值
            if max_val >= self.threshold:
                # 计算中心点位置
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                # 如果应用了缩放，需要还原坐标
                if self.scale_factor != 1.0:
                    center_x = int(center_x / self.scale_factor)
                    center_y = int(center_y / self.scale_factor)
                
                self.logger.debug(f"模板匹配成功: {template_path}, 位置: ({center_x}, {center_y}), 相似度: {max_val:.2f}")
                return True, (center_x, center_y)
            else:
                self.logger.debug(f"模板匹配失败: {template_path}, 最高相似度: {max_val:.2f}")
                return False, None
                
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return False, None
    
    def find_button(self, button_name: str) -> Optional[Tuple[int, int]]:
        """
        查找指定按钮
        
        Args:
            button_name: 按钮名称（不带扩展名）
            
        Returns:
            按钮位置坐标，未找到时返回None
        """
        # 构建模板路径
        template_path = os.path.join(self._resource_path, f"{button_name}.png")
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            self.logger.warning(f"按钮模板文件不存在: {template_path}")
            return None
        
        # 捕获屏幕
        screen = self.capture_screen()
        if screen is None:
            return None
        
        # 匹配模板
        found, position = self.match_template(screen, template_path)
        return position if found else None
    
    def find_main_button(self) -> Optional[Tuple[int, int]]:
        """
        查找主按钮
        
        Returns:
            主按钮位置坐标，未找到时返回None
        """
        return self.find_button("main")
    
    def find_handler_buttons(self) -> List[Tuple[int, int]]:
        """
        查找所有处理项按钮
        
        Returns:
            处理项按钮位置坐标列表
        """
        positions = []
        
        # 获取资源目录中的所有PNG文件
        if os.path.exists(self._resource_path):
            for filename in os.listdir(self._resource_path):
                if filename.endswith('.png') and filename.startswith('handler_btn_'):
                    button_name = os.path.splitext(filename)[0]
                    position = self.find_button(button_name)
                    if position:
                        positions.append(position)
        
        return positions
    
    def set_scale_factor(self, scale_factor: float) -> None:
        """
        设置图像缩放因子
        
        Args:
            scale_factor: 新的缩放因子
        """
        self.scale_factor = scale_factor
        self.logger.info(f"图像缩放因子已更新为: {scale_factor}")
    
    def set_threshold(self, threshold: float) -> None:
        """
        设置模板匹配阈值
        
        Args:
            threshold: 新的阈值
        """
        self.threshold = threshold
        self.logger.info(f"模板匹配阈值已更新为: {threshold}")