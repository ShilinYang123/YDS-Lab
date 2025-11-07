# Trae平台API参考文档

## 智能体API

### CEO智能体API

#### 获取智能体状态
```http
GET /api/agents/ceo/status
```

**响应示例**:
```json
{
  "status": "active",
  "current_tasks": ["strategic_planning", "team_coordination"],
  "performance_metrics": {
    "decisions_made": 15,
    "meetings_conducted": 3,
    "success_rate": 0.95
  }
}
```

#### 创建决策任务
```http
POST /api/agents/ceo/decisions
Content-Type: application/json

{
  "decision_type": "strategic",
  "context": "项目优先级调整",
  "stakeholders": ["dev_team", "resource_admin"],
  "deadline": "2024-11-02T10:00:00Z"
}
```

### DevTeamLead智能体API

#### 获取开发任务
```http
GET /api/agents/devteam/tasks
```

#### 创建代码审查
```http
POST /api/agents/devteam/code-review
Content-Type: application/json

{
  "repository": "project-repo",
  "pull_request": 123,
  "reviewers": ["senior_dev", "tech_lead"],
  "priority": "high"
}
```

### ResourceAdmin智能体API

#### 获取系统资源
```http
GET /api/agents/resource/system-status
```

#### 配置环境
```http
POST /api/agents/resource/environment
Content-Type: application/json

{
  "environment": "production",
  "configuration": {
    "cpu_limit": "4",
    "memory_limit": "8Gi",
    "storage": "100Gi"
  }
}
```

## MCP工具API

### GitHub MCP API

#### 创建仓库
```http
POST /api/mcp/github/repositories
Content-Type: application/json

{
  "name": "new-project",
  "description": "项目描述",
  "private": true,
  "auto_init": true
}
```

#### 获取提交历史
```http
GET /api/mcp/github/repositories/{repo}/commits
```

### Excel MCP API

#### 处理Excel文件
```http
POST /api/mcp/excel/process
Content-Type: multipart/form-data

file: [Excel文件]
operations: ["read", "analyze", "report"]
```

#### 生成报表
```http
POST /api/mcp/excel/generate-report
Content-Type: application/json

{
  "data_source": "sales_data.xlsx",
  "report_type": "monthly_summary",
  "output_format": "xlsx"
}
```

## 协作工作流API

### 创建工作流
```http
POST /api/workflows
Content-Type: application/json

{
  "name": "项目开发流程",
  "type": "project_development",
  "participants": ["ceo", "devteam", "resource_admin"],
  "steps": [
    {
      "name": "需求分析",
      "assignee": "ceo",
      "duration": "2h"
    },
    {
      "name": "技术设计",
      "assignee": "devteam",
      "duration": "4h"
    }
  ]
}
```

### 获取工作流状态
```http
GET /api/workflows/{workflow_id}/status
```

## 错误代码

| 代码 | 描述 | 解决方案 |
|------|------|----------|
| 1001 | 智能体未响应 | 检查智能体状态，重启服务 |
| 1002 | MCP服务不可用 | 检查MCP集群状态 |
| 1003 | 权限不足 | 验证API密钥和权限 |
| 1004 | 配置错误 | 检查配置文件格式 |
| 1005 | 资源不足 | 检查系统资源使用情况 |

## 认证和授权

### API密钥认证
```http
Authorization: Bearer YOUR_API_KEY
```

### 权限级别
- **admin**: 完全访问权限
- **operator**: 操作权限
- **viewer**: 只读权限

---
*API文档版本: v2.0*
*最后更新: {datetime.now().strftime('%Y-%m-%d')}*
