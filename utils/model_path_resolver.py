"""
模型路径解析器 - 支持外部模型目录配置
优先使用 S:\\LLM 外部目录（兼容历史 S:\\LLm 兜底路径），同时保持项目兼容性
"""

import os
import json
from typing import Optional, Dict, Any, List

class ModelPathResolver:
    """模型路径解析器"""
    
    def __init__(self):
        self.project_root = self._get_project_root()
        self.config = self._load_external_config()
        # 智能体目录根路径（统一）
        self.agents_root = os.path.join(self.project_root, "01-struc", "Agents")
    
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, ".."))
    
    def _load_external_config(self) -> Dict[str, Any]:
        """加载外部模型配置（统一读取新路径，不再回退到 GeneralOffice）"""
        candidate_paths = [
            # 新路径优先：01-struc/0B-general-manager/config
            os.path.join(self.project_root, "01-struc", "0B-general-manager", "config", "external_models.json"),
            # 历史路径（项目级 models/config），仅作为补充来源，不涉及 GeneralOffice
            os.path.join(self.project_root, "models", "config", "external_models.json"),
        ]
        for config_path in candidate_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"警告：无法加载外部模型配置({config_path}): {e}")
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

        # 新的统一模型路径（优先 S:\\LLM\models，兼容 S:\\LLm\models）
        unified_shimmy_path_primary = os.path.join("S:", "LLM", "models", "shimmy", "shimmy.exe")
        if os.path.exists(unified_shimmy_path_primary):
            return unified_shimmy_path_primary
        unified_shimmy_path_legacy = os.path.join("S:", "LLm", "models", "shimmy", "shimmy.exe")
        if os.path.exists(unified_shimmy_path_legacy):
            return unified_shimmy_path_legacy
        
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
        
        # 新的统一模型路径（优先 S:\\LLM\models，兼容 S:\\LLm\models）
        unified_model_path_primary = os.path.join("S:", "LLM", "models", model_name)
        if os.path.exists(unified_model_path_primary):
            return unified_model_path_primary
        unified_model_path_legacy = os.path.join("S:", "LLm", "models", model_name)
        if os.path.exists(unified_model_path_legacy):
            return unified_model_path_legacy
        
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

    # ====== 新增：智能体目录解析工具 ======
    def list_agents(self) -> List[str]:
        """列出所有智能体目录名（两位编号前缀）"""
        if not os.path.isdir(self.agents_root):
            return []
        agents = []
        for name in os.listdir(self.agents_root):
            agent_path = os.path.join(self.agents_root, name)
            if os.path.isdir(agent_path) and len(name) >= 3:
                prefix = name[:2]
                if prefix.isdigit():
                    agents.append(name)
        return sorted(agents)

    def normalize_agent_name(self, name: str) -> str:
        """规范化智能体目录名（保持原样或修复常见误写）"""
        # 已带编号则直接返回
        if len(name) >= 3 and name[:2].isdigit():
            return name
        # 常见误写修复（示例：marketing_director → 07-marketing_director）
        mapping = {
            "ceo": "01-ceo",
            "chair_assistant": "02-chair_assistant",
            "planning_director": "03-planning_director",
            "finance_director": "04-finance_director",
            "resource_admin": "05-resource_admin",
            "dev_team": "06-dev_team",
            "marketing_director": "07-marketing_director",
        }
        return mapping.get(name, name)

    def resolve_agent_path(self, name: str, must_exist: bool = True) -> str:
        """解析智能体目录的绝对路径
        :param name: 智能体目录名（推荐格式：07-marketing_director）
        :param must_exist: 若为 True 且不存在则抛出异常
        :return: 绝对路径字符串
        """
        normalized = self.normalize_agent_name(name)
        path = os.path.join(self.agents_root, normalized)
        if must_exist and not os.path.isdir(path):
            raise FileNotFoundError(f"智能体目录不存在: {normalized} -> {path}")
        return path
    
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

# 新增便捷函数（智能体目录）
def list_agents() -> List[str]:
    return resolver.list_agents()

def resolve_agent_path(name: str, must_exist: bool = True) -> str:
    return resolver.resolve_agent_path(name, must_exist)