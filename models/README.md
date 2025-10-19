# 模型配置目录

本目录管理 YDS-Lab 系统的AI模型配置和服务。

## 📁 目录结构

### 🔧 config - 配置管理
- `api_keys.json` - API密钥配置 (生产环境)
- `api_keys.example.json` - API密钥配置模板
- `secret_vars.local.json` - 本地敏感变量 (不提交Git)

### 🚀 services - 服务模块
- `llm_router.py` - 大语言模型路由服务

## 🔐 安全配置

### API密钥管理
1. **生产环境**: 使用 `api_keys.json`
2. **开发环境**: 复制 `api_keys.example.json` 为 `api_keys.json` 并填入真实密钥
3. **本地测试**: 使用 `secret_vars.local.json` 存储临时配置

### 文件安全级别
- 🔴 `*.local.*` - 本地文件，不提交Git
- 🟡 `api_keys.json` - 生产密钥，谨慎管理
- 🟢 `*.example.*` - 模板文件，可安全提交

## 🤖 模型服务

### LLM路由服务
`llm_router.py` 提供统一的大语言模型访问接口：
- 支持多个AI服务提供商
- 自动负载均衡和故障转移
- 统一的API调用格式

### 使用示例
```python
from models.services.llm_router import LLMRouter

# 初始化路由器
router = LLMRouter()

# 发送请求
response = router.chat("你好，请介绍一下YDS-Lab项目")
```

## ⚙️ 配置说明

### API密钥配置格式
```json
{
  "openai": {
    "api_key": "your-openai-key",
    "base_url": "https://api.openai.com/v1"
  },
  "anthropic": {
    "api_key": "your-anthropic-key"
  }
}
```

### 环境变量支持
系统支持通过环境变量覆盖配置：
- `OPENAI_API_KEY` - OpenAI API密钥
- `ANTHROPIC_API_KEY` - Anthropic API密钥

## 🔄 配置更新流程

1. **开发环境**:
   - 修改 `api_keys.example.json` 模板
   - 更新本地 `api_keys.json` 配置

2. **生产环境**:
   - 通过安全渠道更新 `api_keys.json`
   - 重启相关服务使配置生效

## 📝 最佳实践

- 定期轮换API密钥
- 监控API使用量和成本
- 备份重要配置文件
- 使用环境变量管理敏感信息
- 及时更新模型服务版本