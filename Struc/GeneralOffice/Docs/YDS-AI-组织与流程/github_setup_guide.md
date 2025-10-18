# YDS-Lab GitHub仓库设置指南

## 当前状态
- ✅ 本地Git仓库已初始化
- ✅ Git配置已完成
- ✅ 代码已准备就绪
- ❌ GitHub仓库需要手动创建
- ❌ GitHub Token认证问题

## 步骤1: 在GitHub上创建仓库

1. 访问 GitHub: https://github.com/
2. 登录您的账户 (ShilinYang123)
3. 点击右上角的 "+" 按钮，选择 "New repository"
4. 填写仓库信息:
   - **Repository name**: `YDS-Lab`
   - **Description**: `YDS-Lab AI智能协作系统 - 企业级AI开发与协作平台`
   - **Visibility**: Public (公开)
   - **不要勾选** "Add a README file"
   - **不要勾选** "Add .gitignore"
   - **不要勾选** "Choose a license"
5. 点击 "Create repository"

## 步骤2: 推送代码到GitHub

创建仓库后，运行以下命令之一：

### 选项A: 使用Python脚本 (推荐)
```bash
python push_to_github.py
```

### 选项B: 手动Git命令
```bash
# 使用完整路径的Git
& "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe" remote add origin https://github.com/ShilinYang123/YDS-Lab.git
& "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe" add .
& "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe" commit -m "Initial commit: YDS-Lab AI智能协作系统"
& "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe" branch -M main
& "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe" push -u origin main
```

## 当前文件状态
- 已修改: `tools2/.github_config.json` (更新为YDS-Lab仓库信息)
- 新文件: `.gitignore`, `create_yds_lab_repo.py`, `manual_github_setup.py`, `push_to_github.py`
- 子模块变更: 多个MCP工具子模块有修改

## 故障排除

### 如果推送失败:
1. **认证问题**: 可能需要配置GitHub Personal Access Token
2. **仓库不存在**: 确保已在GitHub上创建仓库
3. **网络问题**: 检查网络连接

### GitHub Token配置 (如果需要):
```bash
# 设置环境变量
$env:GITHUB_TOKEN = "your_token_here"
```

## 验证推送成功
推送成功后，访问: https://github.com/ShilinYang123/YDS-Lab
应该能看到所有项目文件。

## 后续步骤
1. 配置GitHub Pages (如果需要)
2. 设置分支保护规则
3. 配置CI/CD工作流
4. 更新项目README.md