# GitHub认证问题修复指南

## 问题诊断结果

❌ **待修复**: 环境变量GITHUB_TOKEN未设置
- 当前状态: 未设置或为空
- 需要: 设置有效的GitHub Personal Access Token

✅ **配置正确**: 用户名配置
- 用户名: `ShilinYang123`
- 仓库URL: `https://github.com/ShilinYang123/YDS-Lab.git`

## 立即修复步骤

### 1. 生成新的GitHub Personal Access Token

1. 访问 GitHub Settings: https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置Token名称: `YDS-Lab-Token`
4. 选择过期时间: 建议90天或自定义
5. **重要**: 选择以下权限:
   ```
   ✅ repo (完整仓库访问权限)
   ✅ workflow (GitHub Actions权限)
   ✅ write:packages (包写入权限)
   ✅ delete:packages (包删除权限)
   ✅ admin:repo_hook (仓库钩子管理)
   ```
6. 点击 "Generate token"
7. **立即复制Token** (只显示一次!)

### 2. 设置环境变量

#### 方法1: PowerShell临时设置 (当前会话)
```powershell
$env:GITHUB_TOKEN = "你的_token_这里"
```

#### 方法2: 永久设置 (推荐)
```powershell
# 设置用户级环境变量
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "你的_token_这里", "User")

# 重启PowerShell或重新加载环境变量
$env:GITHUB_TOKEN = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")
```

#### 方法3: 通过系统设置
1. 按 `Win + R`，输入 `sysdm.cpl`
2. 点击 "环境变量"
3. 在 "用户变量" 中点击 "新建"
4. 变量名: `GITHUB_TOKEN`
5. 变量值: 你的Token
6. 确定并重启应用

### 3. 验证配置

```powershell
# 检查环境变量
echo $env:GITHUB_TOKEN

# 测试GitHub API连接
curl -H "Authorization: token $env:GITHUB_TOKEN" https://api.github.com/user
```

### 4. 重新尝试推送

配置完成后，可以重新尝试使用MCP GitHub工具:

```powershell
# 或者使用Git命令行
git remote set-url origin https://$env:GITHUB_TOKEN@github.com/ShiinWang123/YDS-Lab.git
git push -u origin main
```

## 安全注意事项

⚠️ **重要安全提醒**:
1. **永远不要**将Token提交到代码仓库
2. **定期轮换**Token (建议每90天)
3. **最小权限原则**: 只授予必要的权限
4. **监控使用**: 定期检查Token使用情况
5. **泄露处理**: 如果Token泄露，立即撤销并重新生成

## 常见问题排查

### Token验证失败
```bash
# 测试Token有效性
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### 权限不足
- 确保Token具有 `repo` 权限
- 检查仓库是否为私有 (需要相应权限)

### 网络问题
```bash
# 测试GitHub连接
ping github.com
nslookup api.github.com
```

### MCP工具问题
- 重启Trae AI
- 清除MCP缓存
- 检查MCP服务器状态

## 验证成功标志

✅ 环境变量正确设置
✅ Token权限充足
✅ API连接测试成功
✅ MCP工具认证通过
✅ 文件推送成功

## 如果问题仍然存在

1. 查看详细错误日志
2. 使用 `github_issue_report.md` 向相关项目报告
3. 考虑使用GitHub CLI作为替代方案
4. 联系技术支持

---

**修复完成后，请删除此文件以避免安全信息泄露。**