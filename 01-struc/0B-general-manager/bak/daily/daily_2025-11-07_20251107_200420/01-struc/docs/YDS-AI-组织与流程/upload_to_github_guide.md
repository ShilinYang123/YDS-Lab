# GitHub 网页上传指南

由于Token认证问题，我们可以使用GitHub网页界面直接上传项目文件。

## 方法1: 网页批量上传

1. **访问您的仓库**
   - 打开 https://github.com/ShilinYang123/YDS-Lab

2. **上传文件**
   - 点击 "uploading an existing file" 或 "Add file" → "Upload files"
   - 将整个项目文件夹拖拽到上传区域
   - 或者选择 "choose your files" 批量选择文件

3. **提交更改**
   - 在页面底部添加提交信息：`Initial commit: YDS-Lab project setup`
   - 点击 "Commit changes"

## 方法2: 创建README文件

1. 在仓库页面点击 "Add a README"
2. 添加项目描述
3. 提交后再上传其他文件

## 当前项目结构

需要上传的主要目录和文件：
- `Docs/` - 项目文档
- `ai/` - AI相关模块
- `tools/` - 工具集合
- `tools2/` - 扩展工具
- `projects/` - 项目文件
- `knowledge/` - 知识库
- `config/` - 配置文件
- `.gitignore` - Git忽略文件

## 注意事项

- 一次可以上传多个文件和文件夹
- 大文件（>100MB）需要使用Git LFS
- 上传后项目将立即可见

## 后续步骤

上传完成后，您可以：
1. 设置仓库描述和标签
2. 配置GitHub Pages（如需要）
3. 设置协作者权限
4. 创建Issues和Projects

---

**提示**: 网页上传是最简单的方法，不需要处理Token认证问题。