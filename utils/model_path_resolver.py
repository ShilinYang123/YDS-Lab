"""
模型路径解析器 - 支持外部模型目录配置
支持将模型存储在S:\LLm等外部目录，同时保持项目兼容性
"""

import os
import json
from typing import Optional, Dict, Any

class ModelPathResolver:
    """模型路径解析器"""
    
    def __init__(self):
        self.project_root = self._get_project_root()
        self.config = self._load_external_config()
    
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, ".."))
    
    def _load_external_config(self) -> Dict[str, Any]:
        """加载外部模型配置"""
        config_path = os.path.join(self.project_root, "models", "config", "external_models.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：无法加载外部模型配置: {e}")
        
        return {}
    
    def get_shimmy_path(self) -> str:
        """获取Shimmy可执行文件路径"""
        # 优先使用外部配置
        if self.config and "external_models_config" in self.config:
            shimmy_config = self.config["external_models_config"]["models"]["shimmy"]
            if shimmy_config.get("enabled", False):
                shimmy_path = shimmy_config["executable_path"]
                if os.path.exists(shimmy_path):
                    return shimmy_path
        
        # 环境变量备选
        shimmy_home = os.environ.get("SHIMMY_HOME")
        if shimmy_home:
            shimmy_path = os.path.join(shimmy_home, "shimmy.exe")
            if os.path.exists(shimmy_path):
                return shimmy_path
        
        # 新的统一模型路径（S:\LLm\models）
        unified_shimmy_path = os.path.join("S:", "LLm", "models", "shimmy", "shimmy.exe")
        if os.path.exists(unified_shimmy_path):
            return unified_shimmy_path
        
        # 项目本地路径（兜底）
        local_path = os.path.join(self.project_root, "models", "shimmy", "shimmy.exe")
        return local_path
    
    def get_model_path(self, model_name: str) -> str:
        """获取指定模型的路径"""
        # 优先使用外部配置
        if self.config and "external_models_config" in self.config:
            models_config = self.config["external_models_config"]["models"]
            if model_name in models_config and models_config[model_name].get("enabled", False):
                model_path = models_config[model_name]["model_path"]
                if os.path.exists(model_path):
                    return model_path
        
        # 环境变量备选
        models_root = os.environ.get("MODELS_PATH")
        if models_root:
            model_path = os.path.join(models_root, model_name)
            if os.path.exists(model_path):
                return model_path
        
        # 新的统一模型路径（S:\LLm\models）
        unified_model_path = os.path.join("S:", "LLm", "models", model_name)
        if os.path.exists(unified_model_path):
            return unified_model_path
        
        # 项目本地路径（兜底）
        local_path = os.path.join(self.project_root, "models", model_name)
        return local_path
    
    def get_lama_model_path(self) -> str:
        """获取LaMa模型文件路径"""
        lama_dir = self.get_model_path("lama")
        
        # 检查外部配置中的具体文件名
        if self.config and "external_models_config" in self.config:
            lama_config = self.config["external_models_config"]["models"]["lama"]
            if lama_config.get("enabled", False):
                model_file = lama_config.get("model_file", "lama_256.pth")
                return os.path.join(lama_dir, model_file)
        
        # 默认文件名
        return os.path.join(lama_dir, "lama_256.pth")
    
    def get_output_dir(self) -> str:
        """获取输出目录"""
        return os.path.join(self.project_root, "output")
    
    def create_symlinks(self) -> bool:
        """创建符号链接（需要管理员权限）"""
        try:
            if not self.config or "external_models_config" not in self.config:
                return False
            
            llm_root = self.config["external_models_config"]["llm_root"]
            if not os.path.exists(llm_root):
                print(f"外部LLM目录不存在: {llm_root}")
                return False
            
            # 创建项目内的符号链接目录
            project_models_dir = os.path.join(self.project_root, "models")
            os.makedirs(project_models_dir, exist_ok=True)
            
            # 为每个模型创建符号链接
            for model_name, model_config in self.config["external_models_config"]["models"].items():
                if not model_config.get("enabled", False):
                    continue
                
                external_path = model_config["model_path"]
                local_link = os.path.join(project_models_dir, model_name)
                
                # 如果链接已存在，跳过
                if os.path.exists(local_link):
                    continue
                
                # 创建符号链接（Windows需要管理员权限）
                try:
                    os.symlink(external_path, local_link, target_is_directory=True)
                    print(f"创建符号链接: {local_link} -> {external_path}")
                except OSError as e:
                    print(f"创建符号链接失败 (可能需要管理员权限): {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"创建符号链接时出错: {e}")
            return False

# 全局实例
resolver = ModelPathResolver()

# 便捷函数
def get_shimmy_path() -> str:
    return resolver.get_shimmy_path()

def get_model_path(model_name: str) -> str:
    return resolver.get_model_path(model_name)

def get_lama_model_path() -> str:
    return resolver.get_lama_model_path()

def get_output_dir() -> str:
    return resolver.get_output_dir()