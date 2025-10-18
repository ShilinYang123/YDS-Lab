#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 文档生成工具
提供自动化文档生成、API文档、代码注释和文档管理功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import re
import ast
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import threading
import subprocess
from collections import defaultdict

try:
    import markdown
    import markdown.extensions.toc
    import markdown.extensions.codehilite
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

try:
    import sphinx
    SPHINX_AVAILABLE = True
except ImportError:
    SPHINX_AVAILABLE = False

@dataclass
class CodeElement:
    """代码元素"""
    name: str
    type: str  # class, function, method, variable, constant
    file_path: str
    line_number: int
    docstring: str = ''
    signature: str = ''
    parameters: List[Dict[str, Any]] = None
    return_type: str = ''
    decorators: List[str] = None
    parent: str = ''
    visibility: str = 'public'  # public, private, protected
    complexity: int = 0
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.decorators is None:
            self.decorators = []

@dataclass
class APIEndpoint:
    """API端点"""
    path: str
    method: str
    description: str = ''
    parameters: List[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = None
    tags: List[str] = None
    deprecated: bool = False
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.responses is None:
            self.responses = {}
        if self.tags is None:
            self.tags = []

@dataclass
class DocumentSection:
    """文档章节"""
    title: str
    content: str
    level: int = 1
    order: int = 0
    file_path: str = ''
    auto_generated: bool = False

class DocumentationGenerator:
    """文档生成器"""
    
    def __init__(self, project_root: str = None):
        """初始化文档生成器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.docs_dir = self.project_root / "docs"
        self.templates_dir = self.docs_dir / "templates"
        self.output_dir = self.docs_dir / "generated"
        self.logs_dir = self.project_root / "logs" / "documentation"
        
        # 创建目录
        for directory in [self.docs_dir, self.templates_dir, self.output_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化状态
        self.code_elements = {}
        self.api_endpoints = []
        self.document_sections = []
        
        # 设置日志
        self._setup_logging()
        
        # 初始化模板环境
        if JINJA2_AVAILABLE:
            self.template_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=True
            )
        else:
            self.template_env = None
        
        # 创建默认模板
        self._create_default_templates()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载文档配置"""
        config_file = self.config_dir / "documentation_config.yaml"
        
        default_config = {
            'project': {
                'name': 'YDS-Lab',
                'version': '1.0.0',
                'description': 'YDS-Lab AI Agent协作平台',
                'author': 'YDS-Lab Team',
                'license': 'MIT',
                'homepage': 'https://github.com/yds-lab/yds-lab'
            },
            'generation': {
                'include_patterns': [
                    '*.py',
                    '*.js',
                    '*.ts',
                    '*.jsx',
                    '*.tsx',
                    '*.java',
                    '*.cpp',
                    '*.c',
                    '*.h',
                    '*.hpp'
                ],
                'exclude_patterns': [
                    '__pycache__',
                    'node_modules',
                    '.git',
                    '*.pyc',
                    '*.pyo',
                    'venv',
                    'env',
                    '.venv'
                ],
                'exclude_dirs': [
                    'tests',
                    'test',
                    'docs',
                    'build',
                    'dist'
                ],
                'max_file_size': 1048576,  # 1MB
                'encoding': 'utf-8'
            },
            'output': {
                'formats': ['markdown', 'html', 'json'],
                'markdown': {
                    'extensions': ['toc', 'codehilite', 'tables', 'fenced_code'],
                    'toc_depth': 3
                },
                'html': {
                    'theme': 'default',
                    'syntax_highlighting': True,
                    'include_source': True
                },
                'api_doc': {
                    'format': 'openapi',
                    'version': '3.0.0',
                    'include_examples': True
                }
            },
            'analysis': {
                'include_private': False,
                'include_magic_methods': False,
                'calculate_complexity': True,
                'extract_todos': True,
                'extract_fixmes': True,
                'analyze_dependencies': True
            },
            'templates': {
                'use_custom': True,
                'auto_generate': True
            },
            'sphinx': {
                'enabled': False,
                'theme': 'sphinx_rtd_theme',
                'extensions': [
                    'sphinx.ext.autodoc',
                    'sphinx.ext.viewcode',
                    'sphinx.ext.napoleon'
                ]
            },
            'log_level': 'INFO'
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载文档配置失败: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"documentation_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _create_default_templates(self):
        """创建默认模板"""
        templates = {
            'readme.md.j2': '''# {{ project.name }}

{{ project.description }}

## 版本信息
- 版本: {{ project.version }}
- 作者: {{ project.author }}
- 许可证: {{ project.license }}

## 项目结构

```
{{ project_structure }}
```

## 安装说明

```bash
# 克隆项目
git clone {{ project.homepage }}

# 安装依赖
pip install -r requirements.txt
```

## 使用说明

详细使用说明请参考 [用户手册](docs/user_guide.md)

## API文档

API文档请参考 [API参考](docs/api_reference.md)

## 开发指南

开发指南请参考 [开发文档](docs/development.md)

## 更新日志

更新日志请参考 [CHANGELOG.md](CHANGELOG.md)
''',
            
            'api_reference.md.j2': '''# API参考文档

## 概述

{{ project.description }}

## 基础信息

- 基础URL: `{{ base_url | default('http://localhost:8000') }}`
- API版本: `{{ api_version | default('v1') }}`
- 认证方式: {{ auth_type | default('Bearer Token') }}

## 端点列表

{% for endpoint in endpoints %}
### {{ endpoint.method | upper }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**参数:**

{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}) - {{ param.description }}{% if param.required %} *必需*{% endif %}
{% endfor %}
{% endif %}

{% if endpoint.responses %}
**响应:**

{% for status, response in endpoint.responses.items() %}
- `{{ status }}`: {{ response.description }}
{% endfor %}
{% endif %}

---
{% endfor %}
''',
            
            'code_reference.md.j2': '''# 代码参考文档

## 概述

本文档包含项目中所有主要代码元素的详细信息。

## 模块列表

{% for file_path, elements in modules.items() %}
### {{ file_path }}

{% for element in elements %}
#### {{ element.name }}

**类型:** {{ element.type }}
**行号:** {{ element.line_number }}

{% if element.docstring %}
**说明:**
{{ element.docstring }}
{% endif %}

{% if element.signature %}
**签名:**
```python
{{ element.signature }}
```
{% endif %}

{% if element.parameters %}
**参数:**
{% for param in element.parameters %}
- `{{ param.name }}` ({{ param.type | default('Any') }}): {{ param.description | default('') }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endfor %}
''',
            
            'user_guide.md.j2': '''# 用户指南

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 基本使用

```python
# 示例代码
from yds_lab import YDSLab

# 初始化
lab = YDSLab()

# 使用功能
result = lab.process()
```

## 功能介绍

### 主要功能

1. **功能一**: 描述功能一的用途和使用方法
2. **功能二**: 描述功能二的用途和使用方法
3. **功能三**: 描述功能三的用途和使用方法

### 高级功能

详细介绍高级功能的使用方法。

## 配置说明

### 配置文件

配置文件位于 `config/` 目录下，包含以下文件：

- `config.yaml`: 主配置文件
- `database.yaml`: 数据库配置
- `api.yaml`: API配置

### 环境变量

支持以下环境变量：

- `YDS_LAB_ENV`: 运行环境 (development/production)
- `YDS_LAB_DEBUG`: 调试模式 (true/false)

## 故障排除

### 常见问题

1. **问题一**: 解决方案
2. **问题二**: 解决方案

### 日志查看

日志文件位于 `logs/` 目录下。
''',
            
            'development.md.j2': '''# 开发指南

## 开发环境设置

### 环境要求

- Python 3.8+
- Node.js 16+
- Git

### 开发安装

```bash
# 克隆项目
git clone {{ project.homepage }}
cd {{ project.name.lower() }}

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 安装开发依赖
pip install -r requirements-dev.txt
```

## 项目结构

```
{{ project_structure }}
```

## 编码规范

### Python代码规范

- 遵循 PEP 8 标准
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查

### 提交规范

提交信息格式：
```
<type>(<scope>): <description>

<body>

<footer>
```

类型说明：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_specific.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试规范

- 测试文件以 `test_` 开头
- 测试函数以 `test_` 开头
- 使用 pytest fixtures
- 保持测试覆盖率 > 80%

## 部署

### 开发环境部署

```bash
# 启动开发服务器
python manage.py runserver
```

### 生产环境部署

参考 [部署文档](deployment.md)

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request
'''
        }
        
        for template_name, content in templates.items():
            template_file = self.templates_dir / template_name
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def analyze_project(self) -> Dict[str, Any]:
        """分析项目结构和代码"""
        self.logger.info("开始分析项目")
        
        analysis_result = {
            'files_analyzed': 0,
            'code_elements': 0,
            'api_endpoints': 0,
            'todos': [],
            'fixmes': [],
            'dependencies': set(),
            'project_structure': self._get_project_structure()
        }
        
        # 分析代码文件
        for file_path in self._get_source_files():
            try:
                self._analyze_file(file_path)
                analysis_result['files_analyzed'] += 1
            except Exception as e:
                self.logger.error(f"分析文件失败 {file_path}: {e}")
        
        analysis_result['code_elements'] = len(self.code_elements)
        analysis_result['api_endpoints'] = len(self.api_endpoints)
        
        # 提取TODO和FIXME
        analysis_result['todos'], analysis_result['fixmes'] = self._extract_todos_fixmes()
        
        # 分析依赖
        if self.config['analysis']['analyze_dependencies']:
            analysis_result['dependencies'] = self._analyze_dependencies()
        
        self.logger.info(f"项目分析完成: {analysis_result['files_analyzed']} 个文件")
        return analysis_result
    
    def _get_source_files(self) -> List[Path]:
        """获取源代码文件列表"""
        source_files = []
        
        include_patterns = self.config['generation']['include_patterns']
        exclude_patterns = self.config['generation']['exclude_patterns']
        exclude_dirs = self.config['generation']['exclude_dirs']
        max_size = self.config['generation']['max_file_size']
        
        for pattern in include_patterns:
            for file_path in self.project_root.rglob(pattern):
                # 检查文件大小
                if file_path.stat().st_size > max_size:
                    continue
                
                # 检查排除目录
                if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                    continue
                
                # 检查排除模式
                if any(exclude_pattern in str(file_path) for exclude_pattern in exclude_patterns):
                    continue
                
                if file_path.is_file():
                    source_files.append(file_path)
        
        return source_files
    
    def _get_project_structure(self) -> str:
        """获取项目结构"""
        def build_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
            if current_depth >= max_depth:
                return ""
            
            items = []
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    
                    if item.name in ['__pycache__', 'node_modules', '.git']:
                        continue
                    
                    items.append(item)
            except PermissionError:
                return ""
            
            tree_str = ""
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree_str += f"{prefix}{current_prefix}{item.name}\n"
                
                if item.is_dir() and current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    tree_str += build_tree(item, next_prefix, max_depth, current_depth + 1)
            
            return tree_str
        
        return build_tree(self.project_root)
    
    def _analyze_file(self, file_path: Path):
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding=self.config['generation']['encoding']) as f:
                content = f.read()
        except Exception as e:
            self.logger.warning(f"读取文件失败 {file_path}: {e}")
            return
        
        # 根据文件类型分析
        if file_path.suffix == '.py':
            self._analyze_python_file(file_path, content)
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            self._analyze_javascript_file(file_path, content)
        elif file_path.suffix in ['.java']:
            self._analyze_java_file(file_path, content)
        elif file_path.suffix in ['.cpp', '.c', '.h', '.hpp']:
            self._analyze_cpp_file(file_path, content)
    
    def _analyze_python_file(self, file_path: Path, content: str):
        """分析Python文件"""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._extract_class_info(file_path, node, content)
                elif isinstance(node, ast.FunctionDef):
                    self._extract_function_info(file_path, node, content)
                elif isinstance(node, ast.AsyncFunctionDef):
                    self._extract_function_info(file_path, node, content, is_async=True)
        
        except SyntaxError as e:
            self.logger.warning(f"Python语法错误 {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"分析Python文件失败 {file_path}: {e}")
    
    def _extract_class_info(self, file_path: Path, node: ast.ClassDef, content: str):
        """提取类信息"""
        element_id = f"{file_path}:{node.name}"
        
        # 提取文档字符串
        docstring = ast.get_docstring(node) or ''
        
        # 提取装饰器
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # 计算复杂度
        complexity = self._calculate_complexity(node) if self.config['analysis']['calculate_complexity'] else 0
        
        element = CodeElement(
            name=node.name,
            type='class',
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=node.lineno,
            docstring=docstring,
            decorators=decorators,
            complexity=complexity
        )
        
        self.code_elements[element_id] = element
        
        # 分析类方法
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_method_info(file_path, item, content, node.name)
    
    def _extract_function_info(self, file_path: Path, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                              content: str, is_async: bool = False, parent: str = ''):
        """提取函数信息"""
        element_id = f"{file_path}:{parent}:{node.name}" if parent else f"{file_path}:{node.name}"
        
        # 检查是否包含私有方法
        if not self.config['analysis']['include_private'] and node.name.startswith('_'):
            if not (self.config['analysis']['include_magic_methods'] and node.name.startswith('__')):
                return
        
        # 提取文档字符串
        docstring = ast.get_docstring(node) or ''
        
        # 提取装饰器
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # 提取参数信息
        parameters = self._extract_parameters(node.args)
        
        # 提取返回类型
        return_type = ''
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        # 生成函数签名
        signature = self._generate_function_signature(node, is_async)
        
        # 计算复杂度
        complexity = self._calculate_complexity(node) if self.config['analysis']['calculate_complexity'] else 0
        
        # 确定可见性
        visibility = 'private' if node.name.startswith('_') else 'public'
        
        element = CodeElement(
            name=node.name,
            type='method' if parent else 'function',
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=node.lineno,
            docstring=docstring,
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            parent=parent,
            visibility=visibility,
            complexity=complexity
        )
        
        self.code_elements[element_id] = element
        
        # 检查是否为API端点
        self._check_api_endpoint(element, decorators, docstring)
    
    def _extract_method_info(self, file_path: Path, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                            content: str, class_name: str):
        """提取方法信息"""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        self._extract_function_info(file_path, node, content, is_async, class_name)
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return ast.unparse(decorator)
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return ast.unparse(decorator.func)
        
        return ast.unparse(decorator)
    
    def _extract_parameters(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """提取参数信息"""
        parameters = []
        
        # 位置参数
        for i, arg in enumerate(args.args):
            param_info = {
                'name': arg.arg,
                'type': ast.unparse(arg.annotation) if arg.annotation else 'Any',
                'default': None,
                'required': True
            }
            
            # 检查默认值
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default_index = i - defaults_offset
                param_info['default'] = ast.unparse(args.defaults[default_index])
                param_info['required'] = False
            
            parameters.append(param_info)
        
        # *args
        if args.vararg:
            parameters.append({
                'name': f"*{args.vararg.arg}",
                'type': 'Any',
                'default': None,
                'required': False
            })
        
        # **kwargs
        if args.kwarg:
            parameters.append({
                'name': f"**{args.kwarg.arg}",
                'type': 'Any',
                'default': None,
                'required': False
            })
        
        return parameters
    
    def _generate_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                                   is_async: bool = False) -> str:
        """生成函数签名"""
        prefix = "async def " if is_async else "def "
        
        # 参数列表
        args_str = []
        
        # 位置参数
        for i, arg in enumerate(node.args.args):
            arg_str = arg.arg
            
            # 类型注解
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            
            # 默认值
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset:
                default_index = i - defaults_offset
                arg_str += f" = {ast.unparse(node.args.defaults[default_index])}"
            
            args_str.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
            args_str.append(vararg_str)
        
        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
            args_str.append(kwarg_str)
        
        signature = f"{prefix}{node.name}({', '.join(args_str)})"
        
        # 返回类型
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"
        
        return signature
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _check_api_endpoint(self, element: CodeElement, decorators: List[str], docstring: str):
        """检查是否为API端点"""
        # 检查Flask路由装饰器
        flask_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        for decorator in decorators:
            if 'route' in decorator.lower():
                # 提取路由信息
                # 这里可以进一步解析装饰器参数
                endpoint = APIEndpoint(
                    path=f"/{element.name}",  # 简化处理
                    method='GET',  # 默认方法
                    description=docstring.split('\n')[0] if docstring else element.name
                )
                
                self.api_endpoints.append(endpoint)
                break
    
    def _analyze_javascript_file(self, file_path: Path, content: str):
        """分析JavaScript/TypeScript文件"""
        # 简化的JavaScript分析
        # 可以使用专门的JavaScript解析器如esprima
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查函数定义
            if re.match(r'(export\s+)?(async\s+)?function\s+\w+', line):
                func_match = re.search(r'function\s+(\w+)', line)
                if func_match:
                    func_name = func_match.group(1)
                    
                    element = CodeElement(
                        name=func_name,
                        type='function',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i,
                        signature=line
                    )
                    
                    element_id = f"{file_path}:{func_name}"
                    self.code_elements[element_id] = element
            
            # 检查类定义
            elif re.match(r'(export\s+)?(default\s+)?class\s+\w+', line):
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    class_name = class_match.group(1)
                    
                    element = CodeElement(
                        name=class_name,
                        type='class',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i,
                        signature=line
                    )
                    
                    element_id = f"{file_path}:{class_name}"
                    self.code_elements[element_id] = element
    
    def _analyze_java_file(self, file_path: Path, content: str):
        """分析Java文件"""
        # 简化的Java分析
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查类定义
            if re.match(r'(public\s+)?(abstract\s+)?(final\s+)?class\s+\w+', line):
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    class_name = class_match.group(1)
                    
                    element = CodeElement(
                        name=class_name,
                        type='class',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i,
                        signature=line
                    )
                    
                    element_id = f"{file_path}:{class_name}"
                    self.code_elements[element_id] = element
            
            # 检查方法定义
            elif re.match(r'(public|private|protected)\s+.*\s+\w+\s*\(', line):
                method_match = re.search(r'\s+(\w+)\s*\(', line)
                if method_match:
                    method_name = method_match.group(1)
                    
                    element = CodeElement(
                        name=method_name,
                        type='method',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i,
                        signature=line
                    )
                    
                    element_id = f"{file_path}:{method_name}"
                    self.code_elements[element_id] = element
    
    def _analyze_cpp_file(self, file_path: Path, content: str):
        """分析C++文件"""
        # 简化的C++分析
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查类定义
            if re.match(r'class\s+\w+', line):
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    class_name = class_match.group(1)
                    
                    element = CodeElement(
                        name=class_name,
                        type='class',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i,
                        signature=line
                    )
                    
                    element_id = f"{file_path}:{class_name}"
                    self.code_elements[element_id] = element
            
            # 检查函数定义
            elif re.match(r'\w+.*\w+\s*\(.*\)\s*{?', line) and not line.startswith('//'):
                func_match = re.search(r'(\w+)\s*\(', line)
                if func_match:
                    func_name = func_match.group(1)
                    
                    element = CodeElement(
                        name=func_name,
                        type='function',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i,
                        signature=line
                    )
                    
                    element_id = f"{file_path}:{func_name}"
                    self.code_elements[element_id] = element
    
    def _extract_todos_fixmes(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """提取TODO和FIXME注释"""
        todos = []
        fixmes = []
        
        if not (self.config['analysis']['extract_todos'] or self.config['analysis']['extract_fixmes']):
            return todos, fixmes
        
        for file_path in self._get_source_files():
            try:
                with open(file_path, 'r', encoding=self.config['generation']['encoding']) as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    if self.config['analysis']['extract_todos'] and 'todo' in line_lower:
                        todo_match = re.search(r'todo:?\s*(.*)', line_lower)
                        if todo_match:
                            todos.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': i,
                                'content': todo_match.group(1).strip(),
                                'full_line': line.strip()
                            })
                    
                    if self.config['analysis']['extract_fixmes'] and 'fixme' in line_lower:
                        fixme_match = re.search(r'fixme:?\s*(.*)', line_lower)
                        if fixme_match:
                            fixmes.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': i,
                                'content': fixme_match.group(1).strip(),
                                'full_line': line.strip()
                            })
            
            except Exception as e:
                self.logger.warning(f"提取TODO/FIXME失败 {file_path}: {e}")
        
        return todos, fixmes
    
    def _analyze_dependencies(self) -> Set[str]:
        """分析项目依赖"""
        dependencies = set()
        
        # Python依赖
        requirements_files = [
            'requirements.txt',
            'requirements-dev.txt',
            'Pipfile',
            'pyproject.toml'
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        if req_file.endswith('.txt'):
                            for line in content.split('\n'):
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    dep = line.split('==')[0].split('>=')[0].split('<=')[0]
                                    dependencies.add(dep)
                        
                        elif req_file == 'pyproject.toml':
                            # 简化的TOML解析
                            import re
                            deps = re.findall(r'"([^"]+)"', content)
                            dependencies.update(deps)
                
                except Exception as e:
                    self.logger.warning(f"分析依赖文件失败 {req_file}: {e}")
        
        # JavaScript依赖
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    
                    for dep_type in ['dependencies', 'devDependencies']:
                        if dep_type in package_data:
                            dependencies.update(package_data[dep_type].keys())
            
            except Exception as e:
                self.logger.warning(f"分析package.json失败: {e}")
        
        return dependencies
    
    def generate_documentation(self, formats: List[str] = None) -> Dict[str, str]:
        """生成文档"""
        if formats is None:
            formats = self.config['output']['formats']
        
        self.logger.info(f"开始生成文档，格式: {formats}")
        
        # 分析项目
        analysis_result = self.analyze_project()
        
        # 准备模板数据
        template_data = self._prepare_template_data(analysis_result)
        
        generated_files = {}
        
        for format_type in formats:
            if format_type == 'markdown':
                files = self._generate_markdown_docs(template_data)
                generated_files.update(files)
            elif format_type == 'html':
                files = self._generate_html_docs(template_data)
                generated_files.update(files)
            elif format_type == 'json':
                files = self._generate_json_docs(template_data)
                generated_files.update(files)
        
        self.logger.info(f"文档生成完成，共生成 {len(generated_files)} 个文件")
        return generated_files
    
    def _prepare_template_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """准备模板数据"""
        # 按文件分组代码元素
        modules = defaultdict(list)
        for element in self.code_elements.values():
            modules[element.file_path].append(element)
        
        # 排序
        for file_path in modules:
            modules[file_path].sort(key=lambda x: x.line_number)
        
        template_data = {
            'project': self.config['project'],
            'analysis': analysis_result,
            'modules': dict(modules),
            'endpoints': self.api_endpoints,
            'code_elements': self.code_elements,
            'project_structure': analysis_result['project_structure'],
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'todos': analysis_result['todos'],
            'fixmes': analysis_result['fixmes'],
            'dependencies': list(analysis_result['dependencies'])
        }
        
        return template_data
    
    def _generate_markdown_docs(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """生成Markdown文档"""
        generated_files = {}
        
        if not self.template_env:
            self.logger.warning("Jinja2不可用，跳过模板渲染")
            return generated_files
        
        # 生成各种文档
        docs_to_generate = [
            ('readme.md.j2', 'README.md'),
            ('api_reference.md.j2', 'api_reference.md'),
            ('code_reference.md.j2', 'code_reference.md'),
            ('user_guide.md.j2', 'user_guide.md'),
            ('development.md.j2', 'development.md')
        ]
        
        for template_name, output_name in docs_to_generate:
            try:
                template = self.template_env.get_template(template_name)
                content = template.render(**template_data)
                
                output_path = self.output_dir / output_name
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                generated_files[output_name] = str(output_path)
                self.logger.info(f"生成Markdown文档: {output_name}")
            
            except Exception as e:
                self.logger.error(f"生成Markdown文档失败 {output_name}: {e}")
        
        return generated_files
    
    def _generate_html_docs(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """生成HTML文档"""
        generated_files = {}
        
        if not MARKDOWN_AVAILABLE:
            self.logger.warning("markdown库不可用，跳过HTML生成")
            return generated_files
        
        # 首先生成Markdown文档
        md_files = self._generate_markdown_docs(template_data)
        
        # 配置Markdown扩展
        extensions = self.config['output']['markdown']['extensions']
        
        md = markdown.Markdown(extensions=extensions)
        
        # 转换为HTML
        for doc_name, md_path in md_files.items():
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                html_content = md.convert(md_content)
                
                # 包装在HTML模板中
                full_html = self._wrap_html(html_content, template_data['project']['name'])
                
                html_name = doc_name.replace('.md', '.html')
                html_path = self.output_dir / html_name
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                
                generated_files[html_name] = str(html_path)
                self.logger.info(f"生成HTML文档: {html_name}")
            
            except Exception as e:
                self.logger.error(f"生成HTML文档失败 {doc_name}: {e}")
        
        return generated_files
    
    def _wrap_html(self, content: str, title: str) -> str:
        """包装HTML内容"""
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 文档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        
        code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 1em 0;
            padding: 0 1em;
            color: #666;
        }}
        
        .toc {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 20px;
        }}
        
        .toc > ul {{
            padding-left: 0;
        }}
        
        .toc a {{
            text-decoration: none;
            color: #3498db;
        }}
        
        .toc a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""
        
        return html_template
    
    def _generate_json_docs(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """生成JSON文档"""
        generated_files = {}
        
        try:
            # 代码元素JSON
            elements_data = {}
            for element_id, element in self.code_elements.items():
                elements_data[element_id] = asdict(element)
            
            elements_json = self.output_dir / 'code_elements.json'
            with open(elements_json, 'w', encoding='utf-8') as f:
                json.dump(elements_data, f, indent=2, ensure_ascii=False)
            
            generated_files['code_elements.json'] = str(elements_json)
            
            # API端点JSON
            if self.api_endpoints:
                endpoints_data = [asdict(endpoint) for endpoint in self.api_endpoints]
                
                endpoints_json = self.output_dir / 'api_endpoints.json'
                with open(endpoints_json, 'w', encoding='utf-8') as f:
                    json.dump(endpoints_data, f, indent=2, ensure_ascii=False)
                
                generated_files['api_endpoints.json'] = str(endpoints_json)
            
            # 项目分析JSON
            analysis_json = self.output_dir / 'project_analysis.json'
            with open(analysis_json, 'w', encoding='utf-8') as f:
                # 转换set为list以便JSON序列化
                analysis_data = template_data['analysis'].copy()
                if 'dependencies' in analysis_data:
                    analysis_data['dependencies'] = list(analysis_data['dependencies'])
                
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            generated_files['project_analysis.json'] = str(analysis_json)
            
            self.logger.info("生成JSON文档完成")
        
        except Exception as e:
            self.logger.error(f"生成JSON文档失败: {e}")
        
        return generated_files
    
    def generate_api_documentation(self, format_type: str = 'openapi') -> str:
        """生成API文档"""
        if format_type == 'openapi':
            return self._generate_openapi_spec()
        else:
            raise ValueError(f"不支持的API文档格式: {format_type}")
    
    def _generate_openapi_spec(self) -> str:
        """生成OpenAPI规范"""
        spec = {
            'openapi': self.config['output']['api_doc']['version'],
            'info': {
                'title': self.config['project']['name'],
                'version': self.config['project']['version'],
                'description': self.config['project']['description']
            },
            'servers': [
                {
                    'url': 'http://localhost:8000',
                    'description': '开发服务器'
                }
            ],
            'paths': {},
            'components': {
                'schemas': {},
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer'
                    }
                }
            }
        }
        
        # 添加API端点
        for endpoint in self.api_endpoints:
            if endpoint.path not in spec['paths']:
                spec['paths'][endpoint.path] = {}
            
            method_spec = {
                'summary': endpoint.description,
                'description': endpoint.description,
                'tags': endpoint.tags,
                'deprecated': endpoint.deprecated
            }
            
            # 添加参数
            if endpoint.parameters:
                method_spec['parameters'] = endpoint.parameters
            
            # 添加响应
            if endpoint.responses:
                method_spec['responses'] = endpoint.responses
            else:
                method_spec['responses'] = {
                    '200': {
                        'description': '成功'
                    }
                }
            
            spec['paths'][endpoint.path][endpoint.method.lower()] = method_spec
        
        # 保存OpenAPI规范
        openapi_file = self.output_dir / 'openapi.json'
        with open(openapi_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"生成OpenAPI规范: {openapi_file}")
        return str(openapi_file)
    
    def generate_sphinx_docs(self) -> bool:
        """生成Sphinx文档"""
        if not SPHINX_AVAILABLE:
            self.logger.error("Sphinx不可用")
            return False
        
        if not self.config['sphinx']['enabled']:
            self.logger.info("Sphinx文档生成已禁用")
            return False
        
        try:
            sphinx_dir = self.docs_dir / 'sphinx'
            sphinx_dir.mkdir(exist_ok=True)
            
            # 创建Sphinx配置
            self._create_sphinx_config(sphinx_dir)
            
            # 运行sphinx-build
            cmd = [
                'sphinx-build',
                '-b', 'html',
                str(sphinx_dir),
                str(self.output_dir / 'sphinx')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Sphinx文档生成成功")
                return True
            else:
                self.logger.error(f"Sphinx文档生成失败: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Sphinx文档生成异常: {e}")
            return False
    
    def _create_sphinx_config(self, sphinx_dir: Path):
        """创建Sphinx配置"""
        conf_py = sphinx_dir / 'conf.py'
        
        config_content = f"""
import os
import sys
sys.path.insert(0, os.path.abspath('{self.project_root}'))

project = '{self.config['project']['name']}'
copyright = '2024, {self.config['project']['author']}'
author = '{self.config['project']['author']}'
version = '{self.config['project']['version']}'
release = '{self.config['project']['version']}'

extensions = {self.config['sphinx']['extensions']}

templates_path = ['_templates']
exclude_patterns = []

html_theme = '{self.config['sphinx']['theme']}'
html_static_path = ['_static']

language = 'zh_CN'
"""
        
        with open(conf_py, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # 创建index.rst
        index_rst = sphinx_dir / 'index.rst'
        
        index_content = f"""
{self.config['project']['name']}
{'=' * len(self.config['project']['name'])}

{self.config['project']['description']}

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   modules

索引和表格
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
        
        with open(index_rst, 'w', encoding='utf-8') as f:
            f.write(index_content)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 文档生成工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--analyze', action='store_true', help='分析项目结构')
    parser.add_argument('--generate', nargs='*', help='生成文档 (可选格式: markdown, html, json)')
    parser.add_argument('--api-doc', action='store_true', help='生成API文档')
    parser.add_argument('--sphinx', action='store_true', help='生成Sphinx文档')
    parser.add_argument('--output-dir', help='指定输出目录')
    
    args = parser.parse_args()
    
    generator = DocumentationGenerator(args.project_root)
    
    if args.output_dir:
        generator.output_dir = Path(args.output_dir)
        generator.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 分析项目
    if args.analyze:
        print("🔍 分析项目结构")
        analysis = generator.analyze_project()
        
        print("="*50)
        print(f"文件分析: {analysis['files_analyzed']} 个")
        print(f"代码元素: {analysis['code_elements']} 个")
        print(f"API端点: {analysis['api_endpoints']} 个")
        print(f"TODO项: {len(analysis['todos'])} 个")
        print(f"FIXME项: {len(analysis['fixmes'])} 个")
        print(f"依赖包: {len(analysis['dependencies'])} 个")
        
        return
    
    # 生成文档
    if args.generate is not None:
        formats = args.generate if args.generate else ['markdown', 'html', 'json']
        
        print(f"📝 生成文档，格式: {formats}")
        generated_files = generator.generate_documentation(formats)
        
        print("="*50)
        print("生成的文档文件:")
        for name, path in generated_files.items():
            print(f"  {name}: {path}")
        
        return
    
    # 生成API文档
    if args.api_doc:
        print("🔌 生成API文档")
        api_doc_path = generator.generate_api_documentation()
        print(f"✅ API文档已生成: {api_doc_path}")
        return
    
    # 生成Sphinx文档
    if args.sphinx:
        print("📚 生成Sphinx文档")
        if generator.generate_sphinx_docs():
            print("✅ Sphinx文档生成成功")
        else:
            print("❌ Sphinx文档生成失败")
        return
    
    # 默认显示状态
    print("📖 文档生成器状态")
    print("="*40)
    print(f"项目路径: {generator.project_root}")
    print(f"文档目录: {generator.docs_dir}")
    print(f"输出目录: {generator.output_dir}")
    print(f"模板目录: {generator.templates_dir}")

if __name__ == "__main__":
    main()