#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 项目初始化工具
提供项目快速搭建、配置和环境设置功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
import tempfile

class ProjectInitializer:
    """项目初始化器"""
    
    def __init__(self, project_root: str = None):
        """初始化项目初始化器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 模板和配置路径
        self.templates_dir = self.project_root / "templates"
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.tools_dir = self.project_root / "tools"
        
        # 项目模板配置
        self.project_templates = {
            'basic': {
                'name': '基础项目',
                'description': '包含基本目录结构和配置文件',
                'directories': [
                    'src', 'docs', 'config', 'tests', 'logs', 'temp',
                    'tools', 'scripts', 'data', 'output'
                ],
                'files': {
                    'README.md': 'basic_readme_template.md',
                    'requirements.txt': 'basic_requirements.txt',
                    'config/config.yaml': 'basic_config.yaml',
                    '.gitignore': 'python_gitignore.txt'
                }
            },
            'ai_agent': {
                'name': 'AI Agent项目',
                'description': '适用于AI Agent开发的项目结构',
                'directories': [
                    'agents', 'prompts', 'tools', 'models', 'data',
                    'config', 'logs', 'tests', 'docs', 'scripts',
                    'output', 'temp', 'workflows'
                ],
                'files': {
                    'README.md': 'ai_agent_readme_template.md',
                    'requirements.txt': 'ai_agent_requirements.txt',
                    'config/agent_config.yaml': 'agent_config.yaml',
                    'config/model_config.yaml': 'model_config.yaml',
                    'agents/__init__.py': 'empty_file.txt',
                    'tools/__init__.py': 'empty_file.txt',
                    '.gitignore': 'python_gitignore.txt'
                }
            },
            'web_app': {
                'name': 'Web应用项目',
                'description': '适用于Web应用开发的项目结构',
                'directories': [
                    'frontend', 'backend', 'database', 'config',
                    'docs', 'tests', 'logs', 'scripts', 'static',
                    'templates', 'migrations', 'temp'
                ],
                'files': {
                    'README.md': 'web_app_readme_template.md',
                    'requirements.txt': 'web_app_requirements.txt',
                    'config/app_config.yaml': 'app_config.yaml',
                    'config/database_config.yaml': 'database_config.yaml',
                    'backend/__init__.py': 'empty_file.txt',
                    'frontend/package.json': 'package_json_template.json',
                    '.gitignore': 'web_app_gitignore.txt'
                }
            },
            'data_science': {
                'name': '数据科学项目',
                'description': '适用于数据科学和机器学习项目',
                'directories': [
                    'data/raw', 'data/processed', 'data/external',
                    'notebooks', 'src', 'models', 'reports',
                    'config', 'tests', 'docs', 'scripts', 'output'
                ],
                'files': {
                    'README.md': 'data_science_readme_template.md',
                    'requirements.txt': 'data_science_requirements.txt',
                    'config/data_config.yaml': 'data_config.yaml',
                    'config/model_config.yaml': 'ml_model_config.yaml',
                    'src/__init__.py': 'empty_file.txt',
                    'notebooks/.gitkeep': 'empty_file.txt',
                    '.gitignore': 'data_science_gitignore.txt'
                }
            }
        }
        
        # 初始化模板目录
        self.init_templates()
    
    def init_templates(self):
        """初始化模板目录和文件"""
        self.templates_dir.mkdir(exist_ok=True)
        
        # 创建基础模板文件
        templates = {
            'basic_readme_template.md': self._get_basic_readme_template(),
            'ai_agent_readme_template.md': self._get_ai_agent_readme_template(),
            'web_app_readme_template.md': self._get_web_app_readme_template(),
            'data_science_readme_template.md': self._get_data_science_readme_template(),
            'basic_requirements.txt': self._get_basic_requirements(),
            'ai_agent_requirements.txt': self._get_ai_agent_requirements(),
            'web_app_requirements.txt': self._get_web_app_requirements(),
            'data_science_requirements.txt': self._get_data_science_requirements(),
            'basic_config.yaml': self._get_basic_config(),
            'agent_config.yaml': self._get_agent_config(),
            'model_config.yaml': self._get_model_config(),
            'app_config.yaml': self._get_app_config(),
            'database_config.yaml': self._get_database_config(),
            'data_config.yaml': self._get_data_config(),
            'ml_model_config.yaml': self._get_ml_model_config(),
            'package_json_template.json': self._get_package_json_template(),
            'python_gitignore.txt': self._get_python_gitignore(),
            'web_app_gitignore.txt': self._get_web_app_gitignore(),
            'data_science_gitignore.txt': self._get_data_science_gitignore(),
            'empty_file.txt': ''
        }
        
        for filename, content in templates.items():
            template_file = self.templates_dir / filename
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def create_project(self, project_path: str, template_name: str = 'basic', 
                      project_name: str = None, **kwargs) -> bool:
        """创建新项目"""
        try:
            project_path = Path(project_path)
            
            if project_path.exists() and any(project_path.iterdir()):
                print(f"❌ 目录不为空: {project_path}")
                return False
            
            if template_name not in self.project_templates:
                print(f"❌ 未知的项目模板: {template_name}")
                print(f"可用模板: {', '.join(self.project_templates.keys())}")
                return False
            
            template = self.project_templates[template_name]
            
            if project_name is None:
                project_name = project_path.name
            
            print(f"🚀 创建项目: {project_name}")
            print(f"📁 项目路径: {project_path}")
            print(f"📋 使用模板: {template['name']}")
            
            # 创建项目根目录
            project_path.mkdir(parents=True, exist_ok=True)
            
            # 创建目录结构
            print("📂 创建目录结构...")
            for directory in template['directories']:
                dir_path = project_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ {directory}/")
            
            # 创建文件
            print("📄 创建项目文件...")
            for file_path, template_file in template['files'].items():
                self._create_file_from_template(
                    project_path / file_path,
                    template_file,
                    project_name=project_name,
                    **kwargs
                )
                print(f"  ✅ {file_path}")
            
            # 初始化Git仓库
            if kwargs.get('init_git', True):
                self._init_git_repository(project_path)
            
            # 创建虚拟环境
            if kwargs.get('create_venv', False):
                self._create_virtual_environment(project_path)
            
            # 安装依赖
            if kwargs.get('install_deps', False):
                self._install_dependencies(project_path)
            
            print(f"✅ 项目创建成功: {project_name}")
            print(f"📍 项目位置: {project_path.absolute()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建项目失败: {e}")
            return False
    
    def _create_file_from_template(self, file_path: Path, template_file: str, **kwargs):
        """从模板创建文件"""
        template_path = self.templates_dir / template_file
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if template_path.exists():
            # 读取模板内容
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换模板变量
            content = self._replace_template_variables(content, **kwargs)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            # 创建空文件
            file_path.touch()
    
    def _replace_template_variables(self, content: str, **kwargs) -> str:
        """替换模板变量"""
        variables = {
            'PROJECT_NAME': kwargs.get('project_name', 'YDS-Lab Project'),
            'AUTHOR': kwargs.get('author', 'YDS-Lab Team'),
            'EMAIL': kwargs.get('email', 'team@yds-lab.com'),
            'DESCRIPTION': kwargs.get('description', 'A YDS-Lab project'),
            'VERSION': kwargs.get('version', '1.0.0'),
            'DATE': datetime.now().strftime('%Y-%m-%d'),
            'YEAR': str(datetime.now().year)
        }
        
        for var, value in variables.items():
            content = content.replace(f'{{{{{var}}}}}', str(value))
        
        return content
    
    def _init_git_repository(self, project_path: Path) -> bool:
        """初始化Git仓库"""
        try:
            print("🔧 初始化Git仓库...")
            
            # 检查Git是否可用
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, cwd=project_path)
            
            if result.returncode != 0:
                print("⚠️ Git未安装，跳过Git初始化")
                return False
            
            # 初始化仓库
            subprocess.run(['git', 'init'], cwd=project_path, check=True)
            
            # 添加所有文件
            subprocess.run(['git', 'add', '.'], cwd=project_path, check=True)
            
            # 初始提交
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                         cwd=project_path, check=True)
            
            print("  ✅ Git仓库初始化完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git初始化失败: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Git初始化异常: {e}")
            return False
    
    def _create_virtual_environment(self, project_path: Path) -> bool:
        """创建虚拟环境"""
        try:
            print("🐍 创建Python虚拟环境...")
            
            venv_path = project_path / '.venv'
            
            # 创建虚拟环境
            subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], 
                         cwd=project_path, check=True)
            
            print(f"  ✅ 虚拟环境创建完成: {venv_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 虚拟环境创建失败: {e}")
            return False
        except Exception as e:
            print(f"⚠️ 虚拟环境创建异常: {e}")
            return False
    
    def _install_dependencies(self, project_path: Path) -> bool:
        """安装项目依赖"""
        try:
            requirements_file = project_path / 'requirements.txt'
            
            if not requirements_file.exists():
                print("⚠️ 未找到requirements.txt文件")
                return False
            
            print("📦 安装项目依赖...")
            
            # 确定Python可执行文件
            venv_path = project_path / '.venv'
            if venv_path.exists():
                if os.name == 'nt':  # Windows
                    python_exe = venv_path / 'Scripts' / 'python.exe'
                else:  # Unix-like
                    python_exe = venv_path / 'bin' / 'python'
            else:
                python_exe = sys.executable
            
            # 安装依赖
            subprocess.run([str(python_exe), '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         cwd=project_path, check=True)
            
            print("  ✅ 依赖安装完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 依赖安装失败: {e}")
            return False
        except Exception as e:
            print(f"⚠️ 依赖安装异常: {e}")
            return False
    
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """列出可用的项目模板"""
        return self.project_templates
    
    def add_custom_template(self, template_name: str, template_config: Dict[str, Any]) -> bool:
        """添加自定义项目模板"""
        try:
            # 验证模板配置
            required_keys = ['name', 'description', 'directories', 'files']
            for key in required_keys:
                if key not in template_config:
                    print(f"❌ 模板配置缺少必需字段: {key}")
                    return False
            
            # 添加模板
            self.project_templates[template_name] = template_config
            
            # 保存模板配置
            templates_config_file = self.config_dir / 'project_templates.json'
            self.config_dir.mkdir(exist_ok=True)
            
            with open(templates_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_templates, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 自定义模板已添加: {template_name}")
            return True
            
        except Exception as e:
            print(f"❌ 添加自定义模板失败: {e}")
            return False
    
    def remove_custom_template(self, template_name: str) -> bool:
        """移除自定义项目模板"""
        try:
            if template_name not in self.project_templates:
                print(f"❌ 模板不存在: {template_name}")
                return False
            
            # 不允许删除内置模板
            builtin_templates = ['basic', 'ai_agent', 'web_app', 'data_science']
            if template_name in builtin_templates:
                print(f"❌ 不能删除内置模板: {template_name}")
                return False
            
            # 删除模板
            del self.project_templates[template_name]
            
            # 保存模板配置
            templates_config_file = self.config_dir / 'project_templates.json'
            
            with open(templates_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_templates, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 自定义模板已移除: {template_name}")
            return True
            
        except Exception as e:
            print(f"❌ 移除自定义模板失败: {e}")
            return False
    
    def clone_project_template(self, source_path: str, template_name: str) -> bool:
        """从现有项目创建模板"""
        try:
            source_path = Path(source_path)
            
            if not source_path.exists():
                print(f"❌ 源项目路径不存在: {source_path}")
                return False
            
            print(f"📋 从项目创建模板: {template_name}")
            
            # 扫描项目结构
            directories = []
            files = {}
            
            for root, dirs, filenames in os.walk(source_path):
                root_path = Path(root)
                relative_root = root_path.relative_to(source_path)
                
                # 跳过某些目录
                skip_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', 
                           '.pytest_cache', '.mypy_cache', 'logs', 'temp'}
                
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                # 添加目录
                if str(relative_root) != '.':
                    directories.append(str(relative_root))
                
                # 添加文件
                for filename in filenames:
                    file_path = root_path / filename
                    relative_file = file_path.relative_to(source_path)
                    
                    # 跳过某些文件
                    skip_files = {'.DS_Store', 'Thumbs.db', '*.pyc', '*.log'}
                    if any(file_path.match(pattern) for pattern in skip_files):
                        continue
                    
                    # 创建模板文件
                    template_filename = f"custom_{template_name}_{filename}"
                    template_path = self.templates_dir / template_filename
                    
                    # 复制文件内容
                    shutil.copy2(file_path, template_path)
                    
                    files[str(relative_file)] = template_filename
            
            # 创建模板配置
            template_config = {
                'name': f'自定义模板: {template_name}',
                'description': f'从项目 {source_path.name} 创建的模板',
                'directories': sorted(directories),
                'files': files
            }
            
            # 添加模板
            success = self.add_custom_template(template_name, template_config)
            
            if success:
                print(f"✅ 项目模板创建成功: {template_name}")
                print(f"📂 包含 {len(directories)} 个目录")
                print(f"📄 包含 {len(files)} 个文件")
            
            return success
            
        except Exception as e:
            print(f"❌ 创建项目模板失败: {e}")
            return False
    
    def update_project_structure(self, project_path: str, template_name: str) -> bool:
        """更新现有项目结构"""
        try:
            project_path = Path(project_path)
            
            if not project_path.exists():
                print(f"❌ 项目路径不存在: {project_path}")
                return False
            
            if template_name not in self.project_templates:
                print(f"❌ 未知的项目模板: {template_name}")
                return False
            
            template = self.project_templates[template_name]
            
            print(f"🔄 更新项目结构: {project_path.name}")
            print(f"📋 使用模板: {template['name']}")
            
            # 创建缺失的目录
            print("📂 检查目录结构...")
            for directory in template['directories']:
                dir_path = project_path / directory
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"  ✅ 创建目录: {directory}/")
                else:
                    print(f"  ⏭️ 目录已存在: {directory}/")
            
            # 创建缺失的文件（不覆盖现有文件）
            print("📄 检查项目文件...")
            for file_path, template_file in template['files'].items():
                target_file = project_path / file_path
                
                if not target_file.exists():
                    self._create_file_from_template(
                        target_file,
                        template_file,
                        project_name=project_path.name
                    )
                    print(f"  ✅ 创建文件: {file_path}")
                else:
                    print(f"  ⏭️ 文件已存在: {file_path}")
            
            print(f"✅ 项目结构更新完成")
            return True
            
        except Exception as e:
            print(f"❌ 更新项目结构失败: {e}")
            return False
    
    # 模板内容生成方法
    def _get_basic_readme_template(self) -> str:
        return """# {{PROJECT_NAME}}

{{DESCRIPTION}}

## 项目信息

- **作者**: {{AUTHOR}}
- **邮箱**: {{EMAIL}}
- **版本**: {{VERSION}}
- **创建日期**: {{DATE}}

## 项目结构

```
{{PROJECT_NAME}}/
├── src/                # 源代码
├── docs/               # 文档
├── config/             # 配置文件
├── tests/              # 测试文件
├── logs/               # 日志文件
├── temp/               # 临时文件
├── tools/              # 工具脚本
├── scripts/            # 脚本文件
├── data/               # 数据文件
├── output/             # 输出文件
├── requirements.txt    # Python依赖
└── README.md          # 项目说明
```

## 安装和使用

1. 克隆项目
```bash
git clone <repository-url>
cd {{PROJECT_NAME}}
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行项目
```bash
python src/main.py
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

Copyright (c) {{YEAR}} {{AUTHOR}}
"""
    
    def _get_ai_agent_readme_template(self) -> str:
        return """# {{PROJECT_NAME}}

{{DESCRIPTION}}

一个基于AI Agent的智能项目，提供自动化和智能化解决方案。

## 项目信息

- **作者**: {{AUTHOR}}
- **邮箱**: {{EMAIL}}
- **版本**: {{VERSION}}
- **创建日期**: {{DATE}}

## 项目结构

```
{{PROJECT_NAME}}/
├── agents/             # AI Agent模块
├── prompts/            # 提示词模板
├── tools/              # 工具函数
├── models/             # 模型配置
├── data/               # 数据文件
├── config/             # 配置文件
├── logs/               # 日志文件
├── tests/              # 测试文件
├── docs/               # 文档
├── scripts/            # 脚本文件
├── output/             # 输出文件
├── temp/               # 临时文件
├── workflows/          # 工作流配置
├── requirements.txt    # Python依赖
└── README.md          # 项目说明
```

## 功能特性

- 🤖 智能AI Agent
- 🔧 丰富的工具集
- 📝 灵活的提示词系统
- 🔄 自动化工作流
- 📊 数据处理和分析
- 🎯 任务调度和管理

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境
```bash
cp config/agent_config.yaml.example config/agent_config.yaml
# 编辑配置文件
```

3. 运行Agent
```bash
python agents/main_agent.py
```

## 配置说明

- `config/agent_config.yaml`: Agent基础配置
- `config/model_config.yaml`: 模型配置
- `prompts/`: 提示词模板目录

## 许可证

Copyright (c) {{YEAR}} {{AUTHOR}}
"""
    
    def _get_web_app_readme_template(self) -> str:
        return """# {{PROJECT_NAME}}

{{DESCRIPTION}}

一个现代化的Web应用项目，提供完整的前后端解决方案。

## 项目信息

- **作者**: {{AUTHOR}}
- **邮箱**: {{EMAIL}}
- **版本**: {{VERSION}}
- **创建日期**: {{DATE}}

## 项目结构

```
{{PROJECT_NAME}}/
├── frontend/           # 前端代码
├── backend/            # 后端代码
├── database/           # 数据库脚本
├── config/             # 配置文件
├── docs/               # 文档
├── tests/              # 测试文件
├── logs/               # 日志文件
├── scripts/            # 脚本文件
├── static/             # 静态资源
├── templates/          # 模板文件
├── migrations/         # 数据库迁移
├── temp/               # 临时文件
├── requirements.txt    # Python依赖
└── README.md          # 项目说明
```

## 技术栈

- **前端**: HTML5, CSS3, JavaScript, React/Vue
- **后端**: Python, Flask/Django
- **数据库**: PostgreSQL/MySQL/SQLite
- **缓存**: Redis
- **部署**: Docker, Nginx

## 快速开始

1. 安装后端依赖
```bash
pip install -r requirements.txt
```

2. 安装前端依赖
```bash
cd frontend
npm install
```

3. 配置数据库
```bash
# 编辑数据库配置
cp config/database_config.yaml.example config/database_config.yaml
```

4. 运行应用
```bash
# 启动后端
python backend/app.py

# 启动前端
cd frontend
npm start
```

## API文档

访问 `http://localhost:5000/docs` 查看API文档

## 许可证

Copyright (c) {{YEAR}} {{AUTHOR}}
"""
    
    def _get_data_science_readme_template(self) -> str:
        return """# {{PROJECT_NAME}}

{{DESCRIPTION}}

一个数据科学和机器学习项目，提供完整的数据分析和建模解决方案。

## 项目信息

- **作者**: {{AUTHOR}}
- **邮箱**: {{EMAIL}}
- **版本**: {{VERSION}}
- **创建日期**: {{DATE}}

## 项目结构

```
{{PROJECT_NAME}}/
├── data/
│   ├── raw/            # 原始数据
│   ├── processed/      # 处理后的数据
│   └── external/       # 外部数据
├── notebooks/          # Jupyter笔记本
├── src/                # 源代码
├── models/             # 训练好的模型
├── reports/            # 分析报告
├── config/             # 配置文件
├── tests/              # 测试文件
├── docs/               # 文档
├── scripts/            # 脚本文件
├── output/             # 输出文件
├── requirements.txt    # Python依赖
└── README.md          # 项目说明
```

## 技术栈

- **数据处理**: Pandas, NumPy
- **机器学习**: Scikit-learn, XGBoost, LightGBM
- **深度学习**: TensorFlow, PyTorch
- **可视化**: Matplotlib, Seaborn, Plotly
- **笔记本**: Jupyter Lab

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动Jupyter Lab
```bash
jupyter lab
```

3. 运行数据处理
```bash
python src/data_processing.py
```

4. 训练模型
```bash
python src/train_model.py
```

## 数据说明

- `data/raw/`: 存放原始数据文件
- `data/processed/`: 存放清洗和预处理后的数据
- `data/external/`: 存放外部数据源

## 模型说明

- `models/`: 存放训练好的模型文件
- `config/model_config.yaml`: 模型配置参数

## 许可证

Copyright (c) {{YEAR}} {{AUTHOR}}
"""
    
    def _get_basic_requirements(self) -> str:
        return """# 基础Python依赖
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=0.19.0
click>=8.0.0
rich>=12.0.0
"""
    
    def _get_ai_agent_requirements(self) -> str:
        return """# AI Agent项目依赖
openai>=1.0.0
anthropic>=0.3.0
langchain>=0.1.0
langchain-community>=0.0.10
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=0.19.0
click>=8.0.0
rich>=12.0.0
pydantic>=2.0.0
asyncio>=3.4.3
aiohttp>=3.8.0
tiktoken>=0.5.0
numpy>=1.24.0
pandas>=2.0.0
"""
    
    def _get_web_app_requirements(self) -> str:
        return """# Web应用项目依赖
flask>=2.3.0
flask-sqlalchemy>=3.0.0
flask-migrate>=4.0.0
flask-cors>=4.0.0
gunicorn>=21.0.0
psycopg2-binary>=2.9.0
redis>=4.5.0
celery>=5.3.0
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=0.19.0
click>=8.0.0
rich>=12.0.0
pydantic>=2.0.0
"""
    
    def _get_data_science_requirements(self) -> str:
        return """# 数据科学项目依赖
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0
scikit-learn>=1.3.0
xgboost>=1.7.0
lightgbm>=4.0.0
jupyter>=1.0.0
jupyterlab>=4.0.0
ipykernel>=6.25.0
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=0.19.0
click>=8.0.0
rich>=12.0.0
"""
    
    def _get_basic_config(self) -> str:
        return """# 基础项目配置
project:
  name: "{{PROJECT_NAME}}"
  version: "{{VERSION}}"
  author: "{{AUTHOR}}"
  description: "{{DESCRIPTION}}"

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"

paths:
  data: "data"
  output: "output"
  temp: "temp"
  logs: "logs"
"""
    
    def _get_agent_config(self) -> str:
        return """# AI Agent配置
agent:
  name: "{{PROJECT_NAME}}_Agent"
  version: "{{VERSION}}"
  description: "{{DESCRIPTION}}"
  
  # 模型配置
  model:
    provider: "openai"  # openai, anthropic, local
    model_name: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    
  # 工具配置
  tools:
    enabled: true
    max_tools: 10
    timeout: 30
    
  # 记忆配置
  memory:
    type: "conversation"  # conversation, vector, graph
    max_history: 100
    
  # 任务配置
  tasks:
    max_concurrent: 5
    timeout: 300
    retry_count: 3

# 环境配置
environment:
  openai_api_key: "${OPENAI_API_KEY}"
  anthropic_api_key: "${ANTHROPIC_API_KEY}"
  
# 日志配置
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/agent.log"
"""
    
    def _get_model_config(self) -> str:
        return """# 模型配置
models:
  # OpenAI模型
  openai:
    gpt-4:
      max_tokens: 4096
      temperature: 0.7
      top_p: 1.0
      frequency_penalty: 0.0
      presence_penalty: 0.0
    gpt-3.5-turbo:
      max_tokens: 2048
      temperature: 0.7
      top_p: 1.0
      
  # Anthropic模型
  anthropic:
    claude-3-opus:
      max_tokens: 4096
      temperature: 0.7
    claude-3-sonnet:
      max_tokens: 2048
      temperature: 0.7
      
# 提示词配置
prompts:
  system_prompt: |
    你是一个专业的AI助手，能够帮助用户完成各种任务。
    请始终保持专业、准确和有帮助的态度。
    
  user_prompt_template: |
    用户请求: {user_input}
    上下文: {context}
    
# 输出配置
output:
  format: "json"  # json, text, markdown
  include_metadata: true
  save_to_file: true
"""
    
    def _get_app_config(self) -> str:
        return """# Web应用配置
app:
  name: "{{PROJECT_NAME}}"
  version: "{{VERSION}}"
  debug: false
  secret_key: "${SECRET_KEY}"
  
  # 服务器配置
  host: "0.0.0.0"
  port: 5000
  
  # 数据库配置
  database:
    url: "${DATABASE_URL}"
    pool_size: 10
    max_overflow: 20
    
  # Redis配置
  redis:
    url: "${REDIS_URL}"
    decode_responses: true
    
  # 文件上传配置
  upload:
    max_file_size: 16777216  # 16MB
    allowed_extensions: ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt']
    upload_folder: "uploads"
    
# 安全配置
security:
  cors:
    origins: ["http://localhost:3000"]
    methods: ["GET", "POST", "PUT", "DELETE"]
    headers: ["Content-Type", "Authorization"]
    
  jwt:
    secret_key: "${JWT_SECRET_KEY}"
    algorithm: "HS256"
    expiration: 3600  # 1小时
    
# 日志配置
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
"""
    
    def _get_database_config(self) -> str:
        return """# 数据库配置
database:
  # 主数据库
  primary:
    engine: "postgresql"  # postgresql, mysql, sqlite
    host: "${DB_HOST}"
    port: 5432
    name: "${DB_NAME}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
    
  # 连接池配置
  pool:
    size: 10
    max_overflow: 20
    timeout: 30
    recycle: 3600
    
  # 迁移配置
  migration:
    directory: "migrations"
    auto_upgrade: false
    
# Redis配置
redis:
  host: "${REDIS_HOST}"
  port: 6379
  db: 0
  password: "${REDIS_PASSWORD}"
  
# 备份配置
backup:
  enabled: true
  schedule: "0 2 * * *"  # 每天凌晨2点
  retention_days: 30
  storage_path: "backups"
"""
    
    def _get_data_config(self) -> str:
        return """# 数据配置
data:
  # 数据源配置
  sources:
    local:
      path: "data/raw"
      formats: [".csv", ".json", ".xlsx", ".parquet"]
    
    database:
      enabled: false
      connection_string: "${DATABASE_URL}"
      
    api:
      enabled: false
      base_url: "${API_BASE_URL}"
      api_key: "${API_KEY}"
      
  # 数据处理配置
  processing:
    chunk_size: 10000
    parallel: true
    max_workers: 4
    
    # 数据清洗
    cleaning:
      remove_duplicates: true
      handle_missing: "drop"  # drop, fill, interpolate
      outlier_detection: true
      
  # 数据验证
  validation:
    enabled: true
    schema_file: "config/data_schema.json"
    
# 输出配置
output:
  processed_data_path: "data/processed"
  reports_path: "reports"
  models_path: "models"
  
# 日志配置
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/data.log"
"""
    
    def _get_ml_model_config(self) -> str:
        return """# 机器学习模型配置
models:
  # 分类模型
  classification:
    random_forest:
      n_estimators: 100
      max_depth: 10
      random_state: 42
      
    xgboost:
      n_estimators: 100
      learning_rate: 0.1
      max_depth: 6
      random_state: 42
      
    lightgbm:
      n_estimators: 100
      learning_rate: 0.1
      max_depth: 6
      random_state: 42
      
  # 回归模型
  regression:
    linear_regression:
      fit_intercept: true
      
    ridge:
      alpha: 1.0
      random_state: 42
      
    lasso:
      alpha: 1.0
      random_state: 42
      
# 训练配置
training:
  # 数据分割
  test_size: 0.2
  validation_size: 0.2
  random_state: 42
  stratify: true
  
  # 交叉验证
  cross_validation:
    enabled: true
    cv_folds: 5
    scoring: "accuracy"  # accuracy, f1, roc_auc, etc.
    
  # 超参数优化
  hyperparameter_tuning:
    enabled: false
    method: "grid_search"  # grid_search, random_search, bayesian
    cv_folds: 3
    
# 评估配置
evaluation:
  metrics:
    classification: ["accuracy", "precision", "recall", "f1", "roc_auc"]
    regression: ["mse", "rmse", "mae", "r2"]
    
  # 模型保存
  save_models: true
  model_format: "pickle"  # pickle, joblib, onnx
  
# 预测配置
prediction:
  batch_size: 1000
  output_format: "csv"  # csv, json, parquet
  include_probabilities: true
"""
    
    def _get_package_json_template(self) -> str:
        return """{
  "name": "{{PROJECT_NAME}}",
  "version": "{{VERSION}}",
  "description": "{{DESCRIPTION}}",
  "main": "src/index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "dev": "npm start",
    "lint": "eslint src/",
    "format": "prettier --write src/"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.4.0",
    "react-router-dom": "^6.14.0"
  },
  "devDependencies": {
    "eslint": "^8.44.0",
    "prettier": "^3.0.0"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "author": "{{AUTHOR}}",
  "license": "MIT"
}"""
    
    def _get_python_gitignore(self) -> str:
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
temp/
.cache/

# Database
*.db
*.sqlite
*.sqlite3

# Configuration
.env.local
.env.production
config/local_*
"""
    
    def _get_web_app_gitignore(self) -> str:
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Frontend build
frontend/build/
frontend/dist/

# Database
*.db
*.sqlite
*.sqlite3
migrations/versions/

# Uploads
uploads/
static/uploads/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Configuration
.env.local
.env.production
config/local_*

# Temporary files
*.tmp
*.temp
temp/
.cache/
"""
    
    def _get_data_science_gitignore(self) -> str:
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Jupyter Notebook
.ipynb_checkpoints

# Data files
data/raw/
data/external/
*.csv
*.xlsx
*.json
*.parquet
*.h5
*.hdf5

# Models
models/*.pkl
models/*.joblib
models/*.h5
models/*.pb

# Outputs
output/
reports/figures/
reports/plots/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Configuration
.env.local
.env.production
config/local_*

# Temporary files
*.tmp
*.temp
temp/
.cache/

# MLflow
mlruns/
mlartifacts/
"""

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 项目初始化工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建项目命令
    create_parser = subparsers.add_parser('create', help='创建新项目')
    create_parser.add_argument('path', help='项目路径')
    create_parser.add_argument('--template', default='basic', help='项目模板')
    create_parser.add_argument('--name', help='项目名称')
    create_parser.add_argument('--author', help='作者名称')
    create_parser.add_argument('--email', help='作者邮箱')
    create_parser.add_argument('--description', help='项目描述')
    create_parser.add_argument('--no-git', action='store_true', help='不初始化Git仓库')
    create_parser.add_argument('--create-venv', action='store_true', help='创建虚拟环境')
    create_parser.add_argument('--install-deps', action='store_true', help='安装依赖')
    
    # 列出模板命令
    subparsers.add_parser('templates', help='列出可用模板')
    
    # 更新项目命令
    update_parser = subparsers.add_parser('update', help='更新项目结构')
    update_parser.add_argument('path', help='项目路径')
    update_parser.add_argument('--template', required=True, help='项目模板')
    
    # 克隆模板命令
    clone_parser = subparsers.add_parser('clone', help='从现有项目创建模板')
    clone_parser.add_argument('source', help='源项目路径')
    clone_parser.add_argument('name', help='模板名称')
    
    # 添加自定义模板命令
    add_parser = subparsers.add_parser('add-template', help='添加自定义模板')
    add_parser.add_argument('config', help='模板配置文件路径')
    
    # 移除自定义模板命令
    remove_parser = subparsers.add_parser('remove-template', help='移除自定义模板')
    remove_parser.add_argument('name', help='模板名称')
    
    args = parser.parse_args()
    
    initializer = ProjectInitializer(args.project_root)
    
    if args.command == 'create':
        kwargs = {
            'init_git': not args.no_git,
            'create_venv': args.create_venv,
            'install_deps': args.install_deps
        }
        
        # 添加可选参数
        if args.author:
            kwargs['author'] = args.author
        if args.email:
            kwargs['email'] = args.email
        if args.description:
            kwargs['description'] = args.description
        
        success = initializer.create_project(
            args.path, 
            args.template, 
            args.name,
            **kwargs
        )
        
        if not success:
            sys.exit(1)
        
    elif args.command == 'templates':
        templates = initializer.list_templates()
        
        print("📋 可用项目模板:")
        print("=" * 50)
        
        for template_name, template_info in templates.items():
            print(f"🏗️  {template_name}")
            print(f"    名称: {template_info['name']}")
            print(f"    描述: {template_info['description']}")
            print(f"    目录数: {len(template_info['directories'])}")
            print(f"    文件数: {len(template_info['files'])}")
            print()
        
    elif args.command == 'update':
        success = initializer.update_project_structure(args.path, args.template)
        if not success:
            sys.exit(1)
        
    elif args.command == 'clone':
        success = initializer.clone_project_template(args.source, args.name)
        if not success:
            sys.exit(1)
        
    elif args.command == 'add-template':
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            template_name = Path(args.config).stem
            success = initializer.add_custom_template(template_name, template_config)
            
            if not success:
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ 读取模板配置失败: {e}")
            sys.exit(1)
        
    elif args.command == 'remove-template':
        success = initializer.remove_custom_template(args.name)
        if not success:
            sys.exit(1)
        
    else:
        # 默认显示帮助
        parser.print_help()

if __name__ == "__main__":
    main()