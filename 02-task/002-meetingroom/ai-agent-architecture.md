# 智能体架构设计与AI模型选择方案

## 1. 智能体架构概述

本系统采用9个智能体设计，对应公司治理架构中的阴阳双核（CEO/会议秘书）与五行部门（木火土金水），每个智能体具有特定的角色职责和决策权重。

## 2. AI模型选择策略

### 2.1 主模型：Qwen2.5-14B
**选择理由**：
- 中文理解能力业界领先，特别适合企业会议场景
- 支持长上下文（32K tokens），适合复杂会议讨论
- 推理能力强，适合决策分析
- 本地部署性能优秀，响应速度满足实时要求

**技术参数**：
```
模型：qwen2.5:14b
上下文长度：32,768 tokens
温度参数：0.7（平衡创造性和准确性）
最大输出：4,096 tokens
采样参数：top_p=0.9, top_k=50
```

### 2.2 备用模型：Qwen2.5-7B
**使用场景**：
- 资源受限时的降级方案
- 简单问答和基础对话
- 高并发时的负载分担

**技术参数**：
```
模型：qwen2.5:7b
上下文长度：16,384 tokens
温度参数：0.7
最大输出：2,048 tokens
```

## 3. 智能体角色设计

### 3.1 阴阳双核智能体

#### 3.1.1 CEO智能体 (agent.ceo)
```yaml
id: agent.ceo
name: CEO智能体
display_name: 总经理智能体
role: CEO
llm_model: qwen2.5:14b
voice: zh_male_clear
weight: 3
responsibilities:
  - 战略决策制定
  - 会议方向把控
  - 最终决策权
  - 跨部门协调
personality:
  - 决策导向
  - 全局视野
  - 权威性强
  - 善于总结
prompt_template: |
  你是YDS-Lab的总经理智能体，具备深厚的企业管理经验。
  你的职责是：{responsibilities}
  当前会议类型：{meeting_type}
  讨论主题：{topic}
  请基于公司治理原则和战略方向，提供专业意见。
```

#### 3.1.2 会议秘书智能体 (agent.secretary)
```yaml
id: agent.secretary
name: 会议秘书智能体
display_name: 会议秘书智能体
role: MeetingSecretary
llm_model: qwen2.5:14b
voice: zh_female_clear
weight: 2
responsibilities:
  - 会议流程管理
  - 议程控制
  - 会议记录
  - 时间管理
personality:
  - 组织能力强
  - 时间观念强
  - 细致认真
  - 善于协调
prompt_template: |
  你是专业的会议秘书智能体，负责会议的组织和管理。
  你的职责是：{responsibilities}
  请确保会议按照议程进行，合理控制讨论时间，
  并准确记录会议要点和决策结果。
```

### 3.2 五行部门智能体

#### 3.2.1 木部门智能体 (agent.wood) - 创新与发展
```yaml
id: agent.wood
name: 木部门智能体
display_name: 木部门智能体
role: Observer
llm_model: qwen2.5:7b
voice: zh_male_clear
weight: 1
responsibilities:
  - 创新方案评估
  - 发展机会识别
  - 新技术应用建议
  - 市场趋势分析
expertise:
  - 技术创新
  - 产品研发
  - 市场拓展
  - 商业模式创新
```

#### 3.2.2 火部门智能体 (agent.fire) - 营销与推广
```yaml
id: agent.fire
name: 火部门智能体
display_name: 火部门智能体
role: Observer
llm_model: qwen2.5:7b
voice: zh_female_clear
weight: 1
responsibilities:
  - 营销策略建议
  - 品牌推广方案
  - 客户关系维护
  - 市场活动策划
expertise:
  - 市场营销
  - 品牌管理
  - 客户服务
  - 公关传播
```

#### 3.2.3 土部门智能体 (agent.earth) - 运营与执行
```yaml
id: agent.earth
name: 土部门智能体
display_name: 土部门智能体
role: Observer
llm_model: qwen2.5:7b
voice: zh_male_clear
weight: 1
responsibilities:
  - 运营流程优化
  - 执行效率提升
  - 质量控制建议
  - 供应链管理
expertise:
  - 运营管理
  - 流程优化
  - 质量管理
  - 供应链
```

#### 3.2.4 金部门智能体 (agent.metal) - 财务与控制
```yaml
id: agent.metal
name: 金部门智能体
display_name: 金部门智能体
role: Observer
llm_model: qwen2.5:7b
voice: zh_female_clear
weight: 1
responsibilities:
  - 财务风险评估
  - 成本控制建议
  - 投资回报分析
  - 预算管理
expertise:
  - 财务管理
  - 风险控制
  - 投资分析
  - 合规管理
```

#### 3.2.5 水部门智能体 (agent.water) - 人力与协调
```yaml
id: agent.water
name: 水部门智能体
display_name: 水部门智能体
role: Observer
llm_model: qwen2.5:7b
voice: zh_male_clear
weight: 1
responsibilities:
  - 人力资源建议
  - 团队协调方案
  - 培训发展计划
  - 组织文化建设
expertise:
  - 人力资源
  - 团队建设
  - 培训发展
  - 组织行为
```

## 4. 智能体协作机制

### 4.1 消息处理流程
```
用户输入 → 消息分类 → 相关智能体识别 → 并行处理 → 意见汇总 → 决策输出
```

### 4.2 意见表达分类系统
```yaml
opinion_colors:
  agree: "🟢"          # 完全认同
  partial_agree: "🟡"   # 部分认同  
  disagree: "🔴"       # 不同意
  need_info: "🔵"      # 需要更多信息
```

### 4.3 决策算法：加权多数制
```python
def calculate_vote_result(votes, role_weights, quorum=0.6):
    """
    计算投票结果
    - votes: {user_id: {option, weight}}
    - role_weights: {role: weight}
    - quorum: 法定人数比例
    """
    total_weight = sum(role_weights.values())
    option_weights = {}
    
    for vote in votes:
        role = get_user_role(vote.user_id)
        weight = role_weights.get(role, 1)
        option = vote.option
        
        if option not in option_weights:
            option_weights[option] = 0
        option_weights[option] += weight
    
    # 检查法定人数
    participating_weight = sum(option_weights.values())
    if participating_weight / total_weight < quorum:
        return {"status": "failed", "reason": "未达到法定人数"}
    
    # 找出获胜选项
    winning_option = max(option_weights.items(), key=lambda x: x[1])
    return {
        "status": "passed",
        "winning_option": winning_option[0],
        "weight": winning_option[1],
        "total_weight": participating_weight,
        "quorum_met": True
    }
```

## 5. 智能体交互协议

### 5.1 智能体消息格式
```json
{
  "agent_id": "agent.ceo",
  "message_type": "opinion|decision|question|summary",
  "content": "具体意见内容",
  "opinion_color": "🟢|🟡|🔴|🔵",
  "confidence": 0.85,
  "reasoning": "推理过程",
  "suggestions": ["建议1", "建议2"],
  "timestamp": "2025-11-15T10:30:00Z"
}
```

### 5.2 智能体状态管理
```yaml
agent_states:
  listening: "监听会议内容"
  thinking: "分析处理中"
  responding: "生成回应中"
  waiting: "等待发言时机"
  error: "处理异常"
```

### 5.3 智能体协调器
```typescript
class AgentCoordinator {
  private agents: Map<string, Agent>;
  private messageQueue: MessageQueue;
  private decisionEngine: DecisionEngine;
  
  async processMessage(message: Message): Promise<AgentResponse[]> {
    // 1. 识别相关智能体
    const relevantAgents = this.identifyRelevantAgents(message);
    
    // 2. 并行处理消息
    const responses = await Promise.all(
      relevantAgents.map(agent => agent.processMessage(message))
    );
    
    // 3. 汇总和优先级排序
    return this.aggregateResponses(responses);
  }
  
  async makeDecision(context: DecisionContext): Promise<Decision> {
    // 1. 收集各智能体意见
    const opinions = await this.collectOpinions(context);
    
    // 2. 应用决策算法
    return this.decisionEngine.makeDecision(opinions);
  }
}
```

## 6. 会议纪要生成

### 6.1 纪要生成流程
```
会议开始 → 实时记录 → 关键信息提取 → 决策点识别 → 行动项提取 → 纪要生成 → 审核确认
```

### 6.2 纪要模板
```markdown
# 会议纪要

## 基本信息
- 会议ID: {room_id}
- 会议类型: {meeting_type}
- 开始时间: {start_time}
- 结束时间: {end_time}
- 参与智能体: {agent_list}

## 讨论要点
{discussion_points}

## 决策结果
{decisions}

## 行动项
{action_items}

## 分歧处理
{disagreements}

## 下一步计划
{next_steps}
```

### 6.3 关键信息提取算法
```python
def extract_key_information(messages):
    """从消息中提取关键信息"""
    key_info = {
        "decisions": [],
        "action_items": [],
        "disagreements": [],
        "consensus": [],
        "key_topics": []
    }
    
    for message in messages:
        # 使用NLP技术提取关键信息
        if message.type == "decision":
            key_info["decisions"].append(extract_decision(message))
        elif message.type == "action_item":
            key_info["action_items"].append(extract_action_item(message))
        elif message.opinion_color == "🔴":
            key_info["disagreements"].append(extract_disagreement(message))
    
    return key_info
```

## 7. 性能优化策略

### 7.1 模型调用优化
- **缓存机制**：相似问题的回答缓存
- **批处理**：多个智能体请求合并处理
- **流式响应**：大文本生成采用流式输出
- **降级策略**：高负载时自动切换到小模型

### 7.2 资源管理
```yaml
resource_limits:
  max_concurrent_agents: 9
  max_model_calls_per_minute: 60
  max_response_length: 4096
  cache_ttl: 3600
  
performance_targets:
  response_time: "<2s"
  accuracy: ">85%"
  availability: ">99.5%"
```

## 8. 质量保障

### 8.1 回答质量评估
```python
def evaluate_response_quality(response, context):
    """评估智能体回答质量"""
    scores = {
        "relevance": calculate_relevance(response, context),
        "accuracy": calculate_accuracy(response, facts),
        "completeness": calculate_completeness(response, requirements),
        "clarity": calculate_clarity(response),
        "professionalism": calculate_professionalism(response)
    }
    
    return weighted_average(scores)
```

### 8.2 持续学习机制
- **反馈收集**：用户对智能体回答的评分
- **模型微调**：基于高质量对话数据微调
- **知识更新**：定期更新企业知识和行业信息
- **性能监控**：持续监控和优化模型表现

## 9. 安全和合规

### 9.1 内容安全
```yaml
content_filters:
  - sensitive_topic_detection
  - inappropriate_language_filter
  - factual_accuracy_check
  - bias_detection
  - compliance_verification
```

### 9.2 数据保护
- **对话加密**：敏感对话内容加密存储
- **访问控制**：基于角色的智能体权限管理
- **审计日志**：完整的智能体操作记录
- **数据脱敏**：个人信息和企业机密脱敏处理

## 10. 部署和维护

### 10.1 模型部署架构
```
┌─────────────────┐
│   智能体协调器   │
└────────┬────────┘
         │
    ┌────┴────┐
    │        │
┌───▼───┐ ┌─▼───┐
│Qwen14B│ │Qwen7B│
└───┬───┘ └──┬──┘
    │        │
    └────┬───┘
         │
    ┌────▼────┐
    │Ollama服务│
    └─────────┘
```

### 10.2 健康检查
```bash
# 模型服务健康检查
curl http://127.0.0.1:11434/api/tags

# 智能体状态检查  
curl http://localhost:3000/api/agents/health

# 服务质量检查
curl http://localhost:3000/api/agents/quality-metrics
```

### 10.3 维护策略
- **定期更新**：模型版本和知识库定期更新
- **性能监控**：持续监控响应时间和准确率
- **故障恢复**：自动故障检测和恢复机制
- **容量规划**：根据使用情况调整资源配置