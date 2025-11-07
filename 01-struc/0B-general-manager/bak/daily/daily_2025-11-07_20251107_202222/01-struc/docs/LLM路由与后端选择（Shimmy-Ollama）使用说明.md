# LLM 路由与后端选择（Shimmy / Ollama）使用说明 — 草案

本说明文档用于指导在本项目中使用统一的模型路由接口，通过 Shimmy 与 Ollama 两个后端进行模型调用与自动选择，并解释相关配置、基准测试与故障回退机制。

## 一、目标与范围
- 为现有模型服务增加统一的调用入口，支持自动选择后端与故障回退。
- 外部化配置，避免硬编码端口与主机地址，便于维护与升级。
- 不影响现有 UI 与上层调用（保留原有 `get_llm_response` 接口）。
- 与项目架构设计文档对齐：服务分层、配置外置、受控改动、关注点分离。

## 二、相关文件与变更
- models/services/llm_router.py
  - 新增：
    - OpenAI 兼容 HTTP 调用（/v1/chat/completions）。部分 Shimmy 构建亦可能提供 /api/generate（返回内容为简化版，指标字段不保证）；路由入口默认使用 /v1/chat；性能基准工具会优先尝试 /api/generate 获取统一指标，失败时回退 /v1/chat。
    - `/api/generate` 端点调用（仅用于 Ollama 的失败回退）。
    - `route_chat(model, messages=None, prompt=None, options=None) -> str`：统一入口，读取 router_preference 并自动选择后端；按顺序回退（Ollama：/v1/chat → /api/generate；Shimmy：仅 /v1/chat）。
  - 保留：原生 Ollama Python 客户端调用路径。
- models/config/external_models.json
  - 示例：
    - Shimmy：`{"name": "shimmy", "host": "http://127.0.0.1:11435"}`（建议不带 `/v1`，由路由器自动补齐）。
    - Ollama：`environment_variables.OLLAMA_HOST = "http://127.0.0.1:11434"`；如在 models 内部配置了 `/v1`，路由器会统一处理。
- models/config/router_preference.json
  - 示例（当前草案数据）：
    ```json
    {
      "deepseek-1.5b-chat-q4_0": "shimmy",
      "tinyllama:latest": "ollama"
    }
    ```
- tools/performance/performance_analyzer.py
  - 基准测试脚本，统一向 `/api/generate` 发起请求，统计 `total_duration_ms`、`response_len`，并在可用时统计 `eval_count`、`eval_duration_ms` 等。
- 输出文件：01-struc/0B-general-manager/logs/bench_local_llm.json
  - 新增：健康预热（/health）与重试机制；若 `/api/generate` 多次失败（如 502），自动回退到 `/v1/chat/completions` 并标注 `endpoint` 字段（`generate` 或 `chat`）。

## 三、配置规范
- 外部服务地址
  - 推荐在 `external_models.json` 中为每个服务配置根地址（不带 `/v1`），例如：
    - Shimmy: `http://127.0.0.1:11436`（注意：常见错误是误填 11435 导致 404）
    - Ollama: `http://127.0.0.1:11434`
  - 路由器会自动将 OpenAI 兼容调用指向 `<host>/v1/...`；仅在 Ollama 下失败时回退到 `<host>/api/generate`。
- 模型命名与偏好
  - `router_preference.json` 使用模型名到后端名的映射（例如：`"qwen2:0.5b" -> "ollama"`）。
  - 若同名模型在两个后端都存在，可基于基准测试结果自动或手动更新偏好。

## 四、统一调用入口：route_chat
- 函数签名（简化）：
  - `route_chat(model: str, messages: List[dict] = None, prompt: Optional[str] = None, options: Optional[dict] = None) -> str`
- 行为：
  1. 读取 `router_preference.json`，确定首选后端；若未配置，按模型名猜测（包含 `:` 视为 Ollama，否则 Shimmy）。
  2. 调用顺序：
     - Ollama：原生 Python 客户端 → OpenAI 兼容 `/v1/chat/completions` → 回退 `/api/generate`。
     - Shimmy：OpenAI 兼容 `/v1/chat/completions`（不支持 `/api/generate` 回退）。
  3. 返回字符串内容（失败时返回以方括号开头的错误信息）。
- 示例：
  ```python
  from models.services.llm_router import route_chat

  messages = [
      {"role": "system", "content": "你是一个有帮助的助手"},
      {"role": "user", "content": "请用一句话介绍自己"}
  ]
  print(route_chat("tinyllama:latest", messages))
  ```

## 五、基准测试与偏好生成
- 目的：为同名模型（例如 `qwen2:0.5b`）在 Shimmy 与 Ollama 间选择更优后端。
- 使用：
  - 先确保两个后端均可加载同名模型（Shimmy 使用 GGUF 文件；Ollama 使用其自有格式）。
  - 运行脚本（示例）：
    ```powershell
    python tools\performance\performance_analyzer.py `
      --shimmy-url http://127.0.0.1:11436 `
      --shimmy-model qwen2-0_5b-instruct-q4_0 `
      --ollama-url http://127.0.0.1:11434 `
      --ollama-model qwen2:0.5b `
      --prompt "请用两句中文写一首秋天的短诗。" `
      --out "S:\\YDS-Lab\\01-struc\\Log\\bench_local_llm.json" `
      --write-preference
    ```
  - 说明：
    - 初次调用将进行 `/health` 预热与重试；若 Ollama 的 `/api/generate` 或 `/v1/chat` 失败，将相互回退；结果中的 `endpoint` 字段标记实际使用端点。
    - 当两端模型名不同（如 `qwen2-0_5b-instruct-q4_0` vs `qwen2:0.5b`）时，将跳过自动写入 `router_preference.json`。
- 指标解读：
  - `total_duration_ms`：总耗时（请求到返回）。
  - `eval_count`、`eval_duration_ms`（若可用）：可用于估算 TPS 等。
  - `response_len`：返回文本长度（便于比较质量与速度）。

## 六、治理与审批
- 所有路由策略调整（更新 `router_preference.json`、修改 `external_models.json`）需走代码评审或文档审批流程。
- 文档层新增章节：
  - models/README.md：新增“LLM 路由与后端选择”小节（待批准后正式提交）。
  - 项目架构设计.md：新增“模型路由与后端选择策略”附录（待批准后正式提交）。

## 七、已知问题与建议
- Shimmy 的 OpenAI 兼容 `/v1` 端点在部分环境可能返回 502；请首先确认端口为 11436（误用 11435 会导致 404）。目前路由与基准脚本均已提供在 Ollama 下的失败回退，不影响整体功能。
- 基准测试中 Shimmy 的 `eval_count`、`eval_duration_ms` 可能为空，这会影响 TPS 的精确计算；建议以 `total_duration_ms` 和响应质量作为首要依据。
- 如需同名模型对比，请准备 Shimmy 对应的 GGUF 文件路径（例如 `qwen2:0.5b` 的 GGUF），并在 Ollama 端确保该模型已拉取。

## 八、后续工作（建议）
- 若批准：
  1. 在 models/README.md 与 项目架构设计.md 正式增加路由章节（以本草案为基础浓缩整理）。
  2. 启动第二个 Shimmy 实例（不同端口，如 11436），加载与 Ollama 相同的模型（如 `qwen2:0.5b`），完成对比基准并更新 router_preference。
  3. 调查并修复 Shimmy `/v1` 端点 502 问题（可在后续版本中逐步完善）。

## 九、调试与诊断（Echo 优先 + 非交互请求）

为避免 PowerShell 将 `curl` 解析为 `Invoke-WebRequest` 别名而进入交互等待（提示需要 `-Uri`），并提升日志可读性，建议采用“echo 先行 + 非交互请求”的操作准则。

- 原则：
  - 执行任何 HTTP 请求前，先打印目标 URL（Echo First），便于回溯与排查。
  - 优先使用不触发别名的命令（明确 `curl.exe`），或在使用 IWR 时显式提供 `-Uri` 并展开内容。

- 推荐用法：
  - Echo URL（示例）：
    - `Write-Output "http://127.0.0.1:11434/api/tags"`
    - `Write-Output "http://127.0.0.1:11436/health"`
  - 使用 curl.exe（非交互、直接输出）：
    - `curl.exe -sS http://127.0.0.1:11434/api/tags`
    - `curl.exe -sS http://127.0.0.1:11436/health`
  - 使用 Invoke-WebRequest（PowerShell 原生命令）时：
    - 必须显式提供 `-Uri` 参数，并且建议展开内容：
    - `Invoke-WebRequest -Uri http://127.0.0.1:11434/api/tags -UseBasicParsing | Select-Object -ExpandProperty Content`
    - `Invoke-WebRequest -Uri http://127.0.0.1:11436/health -UseBasicParsing | Select-Object -ExpandProperty Content`

- 快速检查示例：
  - Ollama 模型列表：
    - `Write-Output "http://127.0.0.1:11434/api/tags"`
    - `curl.exe -sS http://127.0.0.1:11434/api/tags`
  - Shimmy 健康检查：
    - `Write-Output "http://127.0.0.1:11436/health"`
    - `curl.exe -sS http://127.0.0.1:11436/health`

- 常见陷阱与规避：
  - PowerShell 将 `curl` 作为 `Invoke-WebRequest` 的别名，若未提供 `-Uri` 会等待交互输入；请明确调用 `curl.exe`。
  - 未进行 Echo 导致日志难以定位具体请求；请在每次网络请求前先输出 URL。
  - IWR 未加 `-UseBasicParsing`（PS 5.x 环境）可能引发解析问题；建议加上并展开 `Content`。

- 终止卡住的命令（一般方法）：
  - 按 Ctrl+C 中断前台请求。
  - 若使用 `Start-Job` 启动后台作业：`Get-Job` 查看状态，`Stop-Job -Id <jobId>` 停止。
  - 无法恢复时，关闭当前 PowerShell 终端窗口以重启会话。

- 文档层新增章节：
  - models/README.md：新增“LLM 路由与后端选择”小节（待批准后正式提交）。
  - 项目架构设计.md：新增“模型路由与后端选择策略”附录（待批准后正式提交）。

## 十、质量指标与分组聚合说明（套件输出）
- 质量指标（每任务分别对 Shimmy 与 Ollama 计算并在套件中聚合）：
  - length_penalty：长度相对期望的惩罚（越小越好）。
  - conciseness：简洁度（越大越好）。
  - format_compliance：格式符合率（越大越好）。
  - overall：综合质量分（越大越好）。
- 套件聚合字段（bench_suite_local_llm.json）：
  - aggregate.quality：所有任务的质量平均与胜率（win_rate、tie_rate、comparisons）。
  - aggregate.aligned_subset.quality：仅统计 `aligned=true` 的任务子集。
  - aggregate.pair_groups.<family>.<quantization>.quality：按家族+量化分组的质量平均与胜率。
- 数值含义：
  - avg_length_penalty / avg_conciseness / avg_format_compliance / avg_overall：在分组范围内的平均值。
  - count：该分组内任务数。
  - win_rate：按 `overall` 对比的胜率（Shimmy vs Ollama）；tie_rate：平局占比；comparisons：对比总数。
- 示例：当 family=qwen2、quantization=Q4_0，输出键为 `pair_groups.qwen2.Q4_0.quality`。

- 查看输出路径与示例：
  - 文件路径：`S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json`
  - 快速查看 pair_groups 示例（PowerShell）：
    - `Get-Content S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json | Select-String '"qwen2.Q4_0"' -Context 0,50`
    - `Get-Content S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json | Select-String '"deepseek.Q4_0"' -Context 0,50`
    - `Get-Content S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json | Select-String '"tinyllama.Q4_0"' -Context 0,50`
  - 快速查看顶层 quality 示例（PowerShell）：
    - `Get-Content S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json | Select-String '"aggregate"' -Context 0,50 | Select-String '"quality"'`

## 十一、任务级 URL 覆盖（多实例并行）
- 目的：在同一套件中同时指向不同的 Shimmy/Ollama 实例（例如 Shimmy:11436 运行 qwen2，Shimmy:11435 运行 deepseek）。
- 用法：在 tools/performance/benchmark_suite.json 中的单个任务内加入：
  - shimmy_url: 指向对应 Shimmy 实例（例如 `http://127.0.0.1:11435`）。
  - ollama_url: 指向对应 Ollama 实例（通常 `http://127.0.0.1:11434`）。
- 说明：未设置时使用顶层默认 `shimmy_url` / `ollama_url`；设置后将覆盖该任务的后端地址。
- 注意：`shimmy_model` / `ollama_model` 字段用于记录模型名并写入偏好文件，Shimmy 实例实际加载的模型由服务器进程决定（需提前在相应端口启动对应模型）。
- 示例：
  - Echo URL（示例）：
    - `Write-Output "http://127.0.0.1:11434/api/tags"`
    - `Write-Output "http://127.0.0.1:11436/health"`
  - 使用 curl.exe（非交互、直接输出）：
    - `curl.exe -sS http://127.0.0.1:11434/api/tags`
    - `curl.exe -sS http://127.0.0.1:11436/health`
  - 使用 Invoke-WebRequest（PowerShell 原生命令）时：
    - 必须显式提供 `-Uri` 参数，并且建议展开内容：
    - `Invoke-WebRequest -Uri http://127.0.0.1:11434/api/tags -UseBasicParsing | Select-Object -ExpandProperty Content`
    - `Invoke-WebRequest -Uri http://127.0.0.1:11436/health -UseBasicParsing | Select-Object -ExpandProperty Content`

- 快速检查示例：
  - Ollama 模型列表：
    - `Write-Output "http://127.0.0.1:11434/api/tags"`
    - `curl.exe -sS http://127.0.0.1:11434/api/tags`
  - Shimmy 健康检查：
    - `Write-Output "http://127.0.0.1:11436/health"`
    - `curl.exe -sS http://127.0.0.1:11436/health`

- 常见陷阱与规避：
  - PowerShell 将 `curl` 作为 `Invoke-WebRequest` 的别名，若未提供 `-Uri` 会等待交互输入；请明确调用 `curl.exe`。
  - 未进行 Echo 导致日志难以定位具体请求；请在每次网络请求前先输出 URL。
  - IWR 未加 `-UseBasicParsing`（PS 5.x 环境）可能引发解析问题；建议加上并展开 `Content`。

- 终止卡住的命令（一般方法）：
  - 按 Ctrl+C 中断前台请求。
  - 若使用 `Start-Job` 启动后台作业：`Get-Job` 查看状态，`Stop-Job -Id <jobId>` 停止。
  - 无法恢复时，关闭当前 PowerShell 终端窗口以重启会话。

- 文档层新增章节：
  - models/README.md：新增“LLM 路由与后端选择”小节（待批准后正式提交）。
  - 项目架构设计.md：新增“模型路由与后端选择策略”附录（待批准后正式提交）。

## 十二、TinyLlama（1.1B Chat v1.0, Q4_0）对齐说明与示例

[更新：2025-10-27] TinyLlama Q4_0 vs Q4_K_M 对比摘要（以当前一次套件输出为例，数值以日志为准）
- pair_groups.tinyllama.Q4_0.quality：
  - Shimmy：avg_overall≈0.624，win_rate≈0.667；conciseness≈0.677，length_penalty≈0.758，format≈0.483。
  - Ollama：avg_overall≈0.499，win_rate≈0.333；conciseness≈0.210，length_penalty≈0.420，format≈0.767。
- pair_groups.tinyllama.Q4_K_M.quality：
  - Shimmy：avg_overall≈0.760，win_rate≈0.667；conciseness≈1.000，length_penalty≈1.000，format≈0.400。
  - Ollama：avg_overall≈0.540，win_rate≈0.333；conciseness≈0.244，length_penalty≈0.468，format≈0.817。
- aligned_subset（对齐任务子集）：
  - Shimmy：avg_overall≈0.589，win_rate≈0.5；conciseness≈0.604；length_penalty≈0.729；format≈0.472；速度更快次数=4。
  - Ollama：avg_overall≈0.539，win_rate≈0.5；conciseness≈0.210；length_penalty≈0.519；format≈0.800；速度更快次数=8。

选型建议（TinyLlama 家族）：
- 质量优先（更短更简洁）：建议使用 Shimmy + Q4_K_M；如需严格格式遵循（结构化/模板化），可考虑 Q4_0 或 Ollama。
- 速度优先：Ollama 通常更快（在 aligned_subset 中 8 次快于 4 次）。
- 路由建议示例（偏好文件 router_preference.json）：
  {
    "tinyllama:latest": "shimmy"
  }
  具体场景可按需覆盖（例如对速度优先的任务临时路由到 Ollama）。

本章节记录 TinyLlama 在 Shimmy 与 Ollama 的对齐与使用示例，便于在低资源环境下快速验证路由质量与性能。

- Shimmy 实例与模型
  - 端口：11437
  - 模型名（Shimmy）：tinyllama-1.1b-chat-q4_0
  - 健康检查与模型列表（Echo 先行）：
    - `Write-Output "http://127.0.0.1:11437/health"`
    - `curl.exe -sS http://127.0.0.1:11437/health`
    - `Write-Output "http://127.0.0.1:11437/v1/models"`
    - `curl.exe -sS http://127.0.0.1:11437/v1/models`

- 套件配置（tools/performance/benchmark_suite.json 已对齐）
  - tl_* 任务均设置：
    - `aligned: true`
    - `shimmy_url: http://127.0.0.1:11437`
    - `shimmy_model: tinyllama-1.1b-chat-q4_0`

## 十三、Shimmy 模型 ID 解析与 per-model 端口映射示例

为便于在同一台机器上运行多个 Shimmy 实例（每个实例加载不同模型/端口），这里给出模型 ID 的解析规则与“按模型覆盖端口”的配置示例。

### 1) 模型 ID 解析规则（约定）
- Ollama：形如 `family:tag`，例如 `qwen2:0.5b`、`tinyllama:latest`。
  - 路由器默认将包含冒号的 ID 视为 Ollama。
- Shimmy：使用 GGUF 模型文件名的语义化片段，常见示例：
  - `qwen2-0_5b-instruct-q4_0`
  - `deepseek-r1-distill-q4_0`
  - `tinyllama-1.1b-chat-q4_0`
  - 解析提示：
    - `family`：第一个连字符前的词根（如 qwen2 / deepseek / tinyllama）。
    - `size`：`x.yb` 或 `x_yb` 形式（如 0_5b / 1.1b）。
    - `variant`：`instruct` / `chat` 等。
    - `quantization`：`q4_0`、`q4_k_m` 等。

> 注：解析只用于文档说明与人类理解；路由器以完整字符串匹配 `router_preference.json`，不做正则拆解。

### 2) per-model 端口映射（覆盖示例）
当需要为不同 Shimmy 模型指定不同端口，可在不改动代码的前提下通过“覆盖文件”进行配置。推荐方案：

1. 在 `models/config/` 新增一个文件（示例命名）：`per_model_hosts.json`（可选，按需创建）。
2. 内容示例：
   ```json
   {
     "tinyllama-1.1b-chat-q4_0": "http://127.0.0.1:11437",
     "qwen2-0_5b-instruct-q4_0": "http://127.0.0.1:11436",
     "deepseek-r1-distill-q4_0": "http://127.0.0.1:11435"
   }
   ```
3. 路由器读取顺序（建议实现/对齐）：
   - 若 `per_model_hosts.json` 中存在该模型的主机地址，则优先使用该地址（并自动补齐 `/v1` 进行 OpenAI 兼容调用）。
   - 否则回退到 `external_models.json` 中的基础 `shimmy.host`。
   - 若仍未命中，按 `router_preference.json` 与模型 ID 规则决定走 Ollama 或报错。

> 提示：当前草案文档仅提供约定与示例；实际读取逻辑可在 `models/services/llm_router.py` 中按上述顺序实现，或在上层调用处进行覆盖传参（与“十一、任务级 URL 覆盖”一致）。

### 3) 关联文件与变更建议
- `models/config/external_models.json`：保持为系统级基础地址。
- `models/config/router_preference.json`：维护模型到后端的偏好映射。
- `models/config/per_model_hosts.json`（可选）：按模型覆盖 Shimmy 主机地址，用于一机多实例或性能分流。

### 4) 快速检查（Echo + 非交互）
- TinyLlama（11437）：
  - `Write-Output "http://127.0.0.1:11437/health"`
  - `curl.exe -sS http://127.0.0.1:11437/health`
- Qwen2-0.5b（11436）：
  - `Write-Output "http://127.0.0.1:11436/health"`
  - `curl.exe -sS http://127.0.0.1:11436/health`
- DeepSeek（11435）：
  - `Write-Output "http://127.0.0.1:11435/health"`
  - `curl.exe -sS http://127.0.0.1:11435/health`
    - `ollama_model: tinyllama:latest`

- 重跑套件（聚合输出）
  - 命令（Echo 先行）：
    - `Write-Output "python tools\\performance\\run_benchmark_suite.py"`
    - `python tools\performance\run_benchmark_suite.py`
  - 输出位置：`S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json`
  - 快速查看 TinyLlama 分组与对齐子集：
    - `Get-Content S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json | Select-String '"tinyllama.Q4_0"' -Context 0,60`
    - `Get-Content S:\YDS-Lab\Struc\GeneralOffice\logs\bench_suite_local_llm.json | Select-String '"aligned_subset"' -Context 0,40`

- 结果简述（以当前一次套件输出为例，数值以日志为准）
  - pair_groups.tinyllama.Q4_0.quality：
    - Shimmy 平均综合质量(avg_overall)≈0.76，胜率≈1.0（6/6）；
    - Ollama 平均综合质量(avg_overall)≈0.44，胜率≈0.0；
  - aligned_subset.quality（仅 tl_* 子集）：
    - Shimmy avg_overall≈0.57；
    - Ollama avg_overall≈0.48（示例值，实际以日志为准）。

- 常见诊断
  - 若 PowerShell 中 `curl` 提示需要 `-Uri`，请改用 `curl.exe` 或 `Invoke-WebRequest -Uri ... | Select-Object -ExpandProperty Content`；并遵循“Echo 先行”。
  - 若 TinyLlama GGUF 文件不可见但服务已运行，可能为文件在加载后被移动/删除的情况；服务仍能工作直至重启。请在重启前确认 `S:\LLM\models\shimmy\tinyllama-1.1b-chat-q4_0.gguf` 文件完整性（大小≈608MB）。
  - 下载 GGUF 建议（网络不稳定时）：
    - Hugging Face：`https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_0.gguf`
    - 镜像（可选）：`https://hf-mirror.com/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_0.gguf`

- 路由调用示例
  - Python：
    ```python
    from models.services.llm_router import route_chat
    messages = [
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "请用两句中文写一首秋天的短诗。"}
    ]
    print(route_chat("tinyllama:latest", messages))
    ```

// ... existing code ...