"""
处理项管理器
负责管理自定义处理项的增删改查
"""
import os
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.data.config_manager import ConfigManager
from src.data.log_manager import LogManager


class HandlerManager:
    """处理项管理器"""
    
    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        """
        初始化处理项管理器
        
        Args:
            config_manager: 配置管理器
            log_manager: 日志管理器
        """
        self.config_manager = config_manager
        self.log_manager = log_manager
        
        # 处理项图像目录
        self.handlers_dir = Path("resources/handlers")
        self._ensure_handlers_dir()
    
    def _ensure_handlers_dir(self) -> None:
        """确保处理项图像目录存在"""
        if not self.handlers_dir.exists():
            self.handlers_dir.mkdir(parents=True, exist_ok=True)
            self.log_manager.info(f"创建处理项目录: {self.handlers_dir}")
    
    def get_handlers(self) -> List[Dict[str, Any]]:
        """
        获取所有处理项
        
        Returns:
            List[Dict[str, Any]]: 处理项列表
        """
        config = self.config_manager.get_config()
        return config.get("custom_handlers", [])
    
    def get_handler(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取处理项
        
        Args:
            name: 处理项名称
            
        Returns:
            Optional[Dict[str, Any]]: 处理项，如果不存在则为None
        """
        handlers = self.get_handlers()
        for handler in handlers:
            if handler.get("name") == name:
                return handler.copy()
        return None
    
    def add_handler(self, handler: Dict[str, Any]) -> bool:
        """
        添加处理项
        
        Args:
            handler: 处理项信息
            
        Returns:
            bool: 是否成功添加
        """
        # 验证处理项
        if not self._validate_handler(handler):
            return False
        
        # 复制图像文件到处理项目录
        if not self._copy_handler_image(handler):
            return False
        
        # 添加到配置
        config = self.config_manager.get_config()
        handlers = config.setdefault("custom_handlers", [])
        handlers.append(handler)
        
        # 保存配置
        if self.config_manager.save_config():
            self.log_manager.info(f"添加处理项: {handler.get('name')}")
            return True
        
        return False
    
    def update_handler(self, name: str, updated_handler: Dict[str, Any]) -> bool:
        """
        更新处理项
        
        Args:
            name: 原处理项名称
            updated_handler: 更新后的处理项信息
            
        Returns:
            bool: 是否成功更新
        """
        # 验证处理项
        if not self._validate_handler(updated_handler):
            return False
        
        # 复制图像文件到处理项目录
        if not self._copy_handler_image(updated_handler):
            return False
        
        # 更新配置
        config = self.config_manager.get_config()
        handlers = config.get("custom_handlers", [])
        
        for i, handler in enumerate(handlers):
            if handler.get("name") == name:
                # 删除旧图像文件
                self._remove_handler_image(handler)
                
                # 更新处理项
                handlers[i] = updated_handler
                
                # 保存配置
                if self.config_manager.save_config():
                    self.log_manager.info(f"更新处理项: {name} -> {updated_handler.get('name')}")
                    return True
        
        self.log_manager.warning(f"未找到处理项: {name}")
        return False
    
    def delete_handler(self, name: str) -> bool:
        """
        删除处理项
        
        Args:
            name: 处理项名称
            
        Returns:
            bool: 是否成功删除
        """
        # 从配置中删除
        config = self.config_manager.get_config()
        handlers = config.get("custom_handlers", [])
        
        for i, handler in enumerate(handlers):
            if handler.get("name") == name:
                # 删除图像文件
                self._remove_handler_image(handler)
                
                # 从列表中删除
                del handlers[i]
                
                # 保存配置
                if self.config_manager.save_config():
                    self.log_manager.info(f"删除处理项: {name}")
                    return True
        
        self.log_manager.warning(f"未找到处理项: {name}")
        return False
    
    def _validate_handler(self, handler: Dict[str, Any]) -> bool:
        """
        验证处理项信息
        
        Args:
            handler: 处理项信息
            
        Returns:
            bool: 是否有效
        """
        # 检查必需字段
        if not handler.get("name"):
            self.log_manager.error("处理项名称不能为空")
            return False
        
        if not handler.get("image_file"):
            self.log_manager.error("处理项图像文件不能为空")
            return False
        
        # 检查图像文件是否存在
        image_path = Path(handler.get("image_file"))
        if not image_path.exists():
            self.log_manager.error(f"图像文件不存在: {image_path}")
            return False
        
        # 检查名称是否重复（新增时）
        if "name" not in handler or handler.get("name") not in [h.get("name") for h in self.get_handlers()]:
            return True
        
        self.log_manager.error(f"处理项名称已存在: {handler.get('name')}")
        return False
    
    def _copy_handler_image(self, handler: Dict[str, Any]) -> bool:
        """
        复制处理项图像文件到处理项目录
        
        Args:
            handler: 处理项信息
            
        Returns:
            bool: 是否成功复制
        """
        try:
            source_path = Path(handler.get("image_file"))
            if not source_path.exists():
                self.log_manager.error(f"源图像文件不存在: {source_path}")
                return False
            
            # 生成目标文件名
            handler_name = handler.get("name", "").replace(" ", "_").lower()
            file_ext = source_path.suffix
            target_filename = f"{handler_name}{file_ext}"
            target_path = self.handlers_dir / target_filename
            
            # 如果文件已存在，生成唯一文件名
            counter = 1
            while target_path.exists():
                target_filename = f"{handler_name}_{counter}{file_ext}"
                target_path = self.handlers_dir / target_filename
                counter += 1
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            # 更新处理项中的图像路径
            handler["image_file"] = str(target_path)
            
            self.log_manager.debug(f"复制图像文件: {source_path} -> {target_path}")
            return True
        
        except Exception as e:
            self.log_manager.error(f"复制图像文件失败: {e}")
            return False
    
    def _remove_handler_image(self, handler: Dict[str, Any]) -> bool:
        """
        删除处理项图像文件
        
        Args:
            handler: 处理项信息
            
        Returns:
            bool: 是否成功删除
        """
        try:
            image_path = Path(handler.get("image_file"))
            if image_path.exists() and image_path.parent == self.handlers_dir:
                os.remove(image_path)
                self.log_manager.debug(f"删除图像文件: {image_path}")
            return True
        
        except Exception as e:
            self.log_manager.error(f"删除图像文件失败: {e}")
            return False
    
    def import_handlers(self, file_path: str) -> bool:
        """
        从文件导入处理项
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            bool: 是否成功导入
        """
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                handlers_data = json.load(f)
            
            if not isinstance(handlers_data, list):
                self.log_manager.error("导入文件格式错误，应为处理项列表")
                return False
            
            # 验证并添加处理项
            success_count = 0
            for handler in handlers_data:
                if self.add_handler(handler):
                    success_count += 1
            
            self.log_manager.info(f"成功导入 {success_count}/{len(handlers_data)} 个处理项")
            return success_count > 0
        
        except Exception as e:
            self.log_manager.error(f"导入处理项失败: {e}")
            return False
    
    def export_handlers(self, file_path: str, handler_names: List[str] = None) -> bool:
        """
        导出处理项到文件
        
        Args:
            file_path: 导出文件路径
            handler_names: 要导出的处理项名称列表，如果为None则导出所有
            
        Returns:
            bool: 是否成功导出
        """
        try:
            import json
            
            # 获取要导出的处理项
            handlers = self.get_handlers()
            if handler_names:
                handlers = [h for h in handlers if h.get("name") in handler_names]
            
            # 导出到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(handlers, f, ensure_ascii=False, indent=2)
            
            self.log_manager.info(f"成功导出 {len(handlers)} 个处理项到: {file_path}")
            return True
        
        except Exception as e:
            self.log_manager.error(f"导出处理项失败: {e}")
            return False
    
    def get_available_images(self) -> List[str]:
        """
        获取处理项目录中可用的图像文件
        
        Returns:
            List[str]: 图像文件路径列表
        """
        if not self.handlers_dir.exists():
            return []
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.handlers_dir.glob(f"*{ext}"))
        
        return [str(path) for path in image_files]