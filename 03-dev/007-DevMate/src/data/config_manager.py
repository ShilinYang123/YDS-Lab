"""
配置管理模块
负责加载、保存和验证应用程序配置
"""
import json
import os
import sys
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器，负责配置的加载、保存和验证"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 兼容PyInstaller打包路径
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, 'config.json')
        return os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 验证和补充默认值
            return self._validate_and_fill_defaults(config)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"配置文件加载失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _validate_and_fill_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置并填充默认值"""
        default_config = self._get_default_config()
        
        # 递归合并配置，确保所有必需字段都存在
        def merge_dict(default: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            result = default.copy()
            for key, value in current.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dict(default_config, config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app_name": "TraeMate",
            "author": "杨世林 3AI",
            "window": {
                "width": 420,
                "height": 32,
                "bg_color": "#2c3553",
                "alpha": 0.7,
                "corner_radius": 12
            },
            "indicator": {
                "color_active": "#00ff00",
                "color_inactive": "#888888",
                "blink_interval": 1.0,
                "size": 14
            },
            "monitor": {
                "interval_seconds": 2.0,
                "cooldown_seconds": 30,
                "process_names": ["trae", "cursor"],
                "skip_process_check": False
            },
            "detection": {
                "scale_factor": 1.0,
                "threshold_main": 0.6,
                "threshold_handlers": 0.85
            },
            "custom_handlers": []
        }
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，支持点号分隔的嵌套键，如 "window.width" 或 "custom_handlers.0.name"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return default
            else:
                return default
                
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，支持点号分隔的嵌套键，如 "window.width"
            value: 配置值
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
            
        config[keys[-1]] = value
    
    def add_custom_handler(self, handler: Dict[str, Any]) -> None:
        """添加自定义处理项"""
        if 'custom_handlers' not in self.config:
            self.config['custom_handlers'] = []
        self.config['custom_handlers'].append(handler)
    
    def remove_custom_handler(self, index: int) -> bool:
        """删除自定义处理项"""
        if 'custom_handlers' in self.config and 0 <= index < len(self.config['custom_handlers']):
            self.config['custom_handlers'].pop(index)
            return True
        return False
    
    def get_custom_handlers(self) -> list:
        """获取所有自定义处理项"""
        return self.config.get('custom_handlers', [])
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        try:
            # 检查必需的顶级字段
            required_fields = ['app_name', 'window', 'monitor', 'detection']
            for field in required_fields:
                if field not in self.config:
                    return False
            
            # 检查窗口配置
            window_config = self.config.get('window', {})
            if not isinstance(window_config.get('width'), int) or window_config.get('width') <= 0:
                return False
            if not isinstance(window_config.get('height'), int) or window_config.get('height') <= 0:
                return False
            
            # 检查监控配置
            monitor_config = self.config.get('monitor', {})
            if not isinstance(monitor_config.get('interval_seconds'), (int, float)) or monitor_config.get('interval_seconds') <= 0:
                return False
            if not isinstance(monitor_config.get('cooldown_seconds'), (int, float)) or monitor_config.get('cooldown_seconds') < 0:
                return False
            
            # 检查检测配置
            detection_config = self.config.get('detection', {})
            if not isinstance(detection_config.get('scale_factor'), (int, float)) or detection_config.get('scale_factor') <= 0:
                return False
            if not isinstance(detection_config.get('threshold_main'), (int, float)) or not (0 <= detection_config.get('threshold_main') <= 1):
                return False
            if not isinstance(detection_config.get('threshold_handlers'), (int, float)) or not (0 <= detection_config.get('threshold_handlers') <= 1):
                return False
            
            return True
        except Exception:
            return False