# 部署指南

## 系统要求

- Python 3.8+
- 8GB RAM
- 10GB 可用磁盘空间

## 安装步骤

1. **环境准备**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置系统**
   ```bash
   python ch.py --setup
   ```

4. **启动服务**
   ```bash
   python ch.py --start
   ```

## 验证部署

访问 `http://localhost:8080` 验证系统是否正常运行。

## 故障排除

查看日志文件 `logs/system.log` 获取详细的错误信息。

---
*本文档由自动化工具生成*
