# Agent Engineering Learning Demo

> 面向初学者的故障运维 Agent 教程项目，重点展示 Agent 如何理解故障现象、自主选择工具、查询轻量运维知识与案例、完成自我反思，并通过 Langfuse 和 DeepEval 观察与评估整个过程。

本项目不是通用聊天机器人，也不是完整工单系统。它是一个 **Agent Engineering 教学沙盘**，用一个足够真实但可控的故障运维场景，讲清楚现代 Agent 系统的核心工程结构。学习者不只是看到最终答案，还能看到 Agent 每一步为什么这样判断、为什么选择这个工具、证据如何进入 State、最终回答如何被观测和评测。

## 核心场景

用户入口不是告警编号，也不是工单编号，而是一个自然语言描述的故障现象。

示例输入：

```text
冷却水泵声音变大，出水流量下降，泵体温度也偏高，可能是什么问题？
```

Agent 需要自行判断：

```text
这是什么设备？
有哪些故障现象？
当前风险高不高？
应该先查基础排查知识、指标、日志、历史案例，还是先追问用户？
查到的信息是否足够形成处置建议？
```

交互过程应该是多轮的。Agent 不应该在信息不足时硬给结论，而是边理解、边查询、边追问。

示例互动：

```text
用户：
冷却水泵声音变大，出水流量下降，泵体温度也偏高，可能是什么问题？

Agent：
我先按“冷却水泵 + 异响 + 流量下降 + 温度升高”理解。
这类现象可能和入口堵塞、阀门开度、轴承异常或空转有关。
我需要先确认两个信息：
1. 温度大概升到多少？
2. 现场振动是否明显变大？

用户：
温度 92 度，振动也比平时明显。

Agent：
这已经接近高风险信号。我会优先查基础排查知识和相似历史案例，
同时查看泵的温度、流量、振动阈值。

Agent 调用工具：
- runbook_search
- case_search
- metric_query

Agent：
结合证据，最可能原因是入口过滤器堵塞或轴承异常。
建议先切换备用泵，再隔离检查过滤器和轴承状态。
```

最终输出面向一线运维人员：

```text
1. 现象理解
2. 风险判断
3. 可能原因排序
4. 建议补充确认的信息
5. 排查步骤
6. 临时处置建议
7. 命中的基础知识或历史案例
8. 何时升级、停机或转人工
```

## 教学目标

这个项目要让初学者一眼看懂：

- Agent 和普通流程编排的区别
- LangGraph 如何表达 State / Node / Edge / Router
- Agent 如何根据上下文选择工具，而不是固定查一遍所有系统
- 轻量知识库和案例库如何辅助 Agent 做判断
- 如何把运行过程展示成可观察的教学界面
- V1 如何接入 Langfuse 做链路观测，接入 DeepEval 做效果评测
- 2.0 版本如何接入设备文档和维保知识导入

## Agentic 主线

推荐的 V1 工作流要突出 Agentic 过程：

```text
START
  ↓
understand_symptom
  ↓
decide_next_action
  ├── ask_clarifying_question
  ├── search_basic_runbook
  ├── search_historical_cases
  ├── query_metric_thresholds
  ├── search_logs
  ├── reflect
  ├── generate_response
  ├── record_trace
  └── run_evaluation
```

关键点是：**工具选择由 Agent 根据故障现象决定**。

多轮互动时，工作流不是一次性结束，而是随着用户补充信息继续更新 State：

```text
用户补充信息
  ↓
update_symptom_state
  ↓
decide_next_action
  ↓
tool_or_question_or_final
```

学习者在这个主线里看到的不是“代码跑完了”，而是：

| 阶段 | 学习者看到什么 | 学到什么 |
|---|---|---|
| understand_symptom | Agent 把用户原话结构化成设备、现象、风险信号 | State 是如何从自然语言产生的 |
| decide_next_action | Agent 解释下一步是追问、查知识、查案例、查指标还是查日志 | Agentic 决策不是固定 if-else 流程 |
| call_tool | 页面展示工具输入、输出和命中证据 | Tool Calling 如何接入业务数据 |
| update_state | 证据被写回 `AgentState` | Agent 如何积累上下文 |
| reflect | Agent 检查证据是否足够、步骤是否安全 | 自我反思如何提升可靠性 |
| observe | Langfuse 展示节点、工具、耗时、token 和 trace | 可观测性如何帮助调试 Agent |
| evaluate | DeepEval 对回答进行质量评测 | Agent 输出如何被量化和回归测试 |

## Agent Loop 设计

本项目需要明确展示一个 Agent Loop，而不是一次性问答。

Agent Loop 的核心过程：

```text
用户输入或补充现场信息
  ↓
理解当前信息
  ↓
更新 Agent State
  ↓
判断下一步动作
  ├── 信息不足 → 追问用户，结束当前轮
  ├── 需要证据 → 调用工具查询
  ├── 证据不足 → 继续选择工具或追问
  └── 信息足够 → 生成诊断和处置建议
```

伪代码：

```python
while not final_answer:
    understand_symptom()
    update_state()
    decide_next_action()

    if next_action == "ask_user":
        return question_to_user

    if next_action == "call_tool":
        tool_result = run_tool()
        add_evidence(tool_result)
        continue

    if next_action == "final":
        return final_answer
```

在 LangGraph 中可以表达为：

```text
START
  ↓
understand_symptom
  ↓
decide_next_action
  ├── ask_user → END_THIS_TURN
  ├── call_tool → tool_node → update_state → decide_next_action
  └── draft_answer → reflect → final_or_continue
```

这里的关键点是：`ask_user` 不是整个任务结束，而是当前轮结束。用户补充信息后，下一轮继续带着之前的 `AgentState` 进入 loop。

为了让教程安全、清楚，V1 建议做受控循环：

```text
max_steps = 5
每轮最多调用 1 个或一组相关工具
如果连续两轮没有新增证据，就追问用户或给出保守结论
涉及高风险信号时，优先输出保护性建议
```

页面右侧应展示每一步 loop：

```text
Loop 1:
- action: ask_user
- reason: 缺少温度数值和振动信息

Loop 2:
- action: call_tool
- tools: runbook_search, metric_query
- reason: 已获得温度和振动信息，需要查询阈值和基础排查知识

Loop 3:
- action: final
- reason: 证据足够形成排查建议
```

## 自我反思与闭环

故障运维场景里，Agent 不应该查到一点信息就直接给最终结论。V1 可以增加一个轻量 `reflect_node`，在最终回答前做自我检查。

自我反思闭环：

```text
生成初步诊断
  ↓
reflect_node 自我检查
  ├── 证据不足 → 回到 decide_next_action
  ├── 缺少关键信息 → 追问用户
  ├── 操作风险过高 → 加入升级/停机/人工确认建议
  └── 检查通过 → 输出最终建议
```

反思节点重点检查：

| 检查项 | 说明 |
|---|---|
| 设备是否明确 | 是否识别出冷却水泵、UPS、空压机等设备 |
| 现象是否完整 | 是否覆盖用户描述的温度、压力、流量、声音、振动等现象 |
| 证据是否足够 | 是否有基础知识、历史案例、指标或日志支撑判断 |
| 风险是否处理 | 是否识别高温、剧烈振动、烟雾、漏液、供电风险等信号 |
| 步骤是否安全 | 是否避免直接建议危险操作 |
| 升级条件是否明确 | 是否说明何时转人工、停机或升级处理 |

V1 反思可以先做成 checklist，不需要复杂多 Agent：

```python
reflection = {
    "has_equipment": True,
    "has_symptoms": True,
    "has_evidence": True,
    "has_risk_control": True,
    "has_escalation_condition": True,
    "decision": "ready"
}
```

如果 `decision` 不是 `ready`，Agent Loop 继续运行。

除了回答前的自我反思，还应该支持运维处置闭环。用户执行建议后，可以继续反馈结果：

```text
Agent：
建议先切换备用泵，并观察温度和振动是否下降。

用户：
已经切到备用泵了，温度开始下降，但振动还是高。

Agent：
温度下降说明过热风险缓解，但振动仍高，下一步应重点检查轴承和联轴器。
我会继续查询相似案例和振动阈值。
```

处置反馈闭环：

```text
给出处置建议
  ↓
用户反馈执行结果
  ↓
Agent 更新 State
  ↓
判断是否缓解
  ├── 已缓解 → 给出观察和收尾建议
  ├── 部分缓解 → 聚焦剩余异常继续排查
  └── 未缓解或恶化 → 升级风险等级并切换排查方向
```

这让系统不只是“给答案”，而是能展示：

```text
Diagnosis
→ Reflection
→ Action
→ Feedback
→ Re-diagnosis
```

## V1 观测与评测

Langfuse 和 DeepEval 需要进入 V1，因为这个项目的核心是 Agent Engineering 教程，而不只是 Agent Demo。

### Langfuse Observability

V1 要把每次 Agent Loop 记录成 trace：

```text
Trace
  ├── user_input
  ├── understand_symptom span
  ├── decide_next_action span
  ├── tool_call span
  │   ├── tool name
  │   ├── tool input
  │   └── tool output
  ├── reflect span
  └── final_answer
```

学习者应该能在页面或 Langfuse 控制台看到：

| 观测项 | 学习意义 |
|---|---|
| 每个节点耗时 | 哪一步慢，为什么慢 |
| Tool Call 输入输出 | Agent 到底查了什么 |
| State 快照 | 每一轮上下文如何变化 |
| Trace Timeline | Agent Loop 的完整路径 |
| Token / Latency | LLM 调用成本和延迟 |

### DeepEval Evaluation

V1 也要提供最小评测集，用来评估故障回答是否合格。

示例评测维度：

| Metric | 检查内容 |
|---|---|
| Symptom Coverage | 是否覆盖用户描述的关键现象 |
| Evidence Usage | 是否引用了工具或案例证据 |
| Risk Awareness | 是否识别高风险信号 |
| Actionability | 排查步骤是否可执行 |
| Escalation Condition | 是否说明何时升级或转人工 |

V1 不需要一开始就做复杂评测平台，但要有一个可运行的 evaluation pipeline：

```text
demo_cases
  ↓
run_agent
  ↓
collect_answer_and_trace
  ↓
run_deepeval_metrics
  ↓
show_eval_result
```

页面里可以用一个 “Evaluation” 区块展示：

```text
case_id: pump-overheat-001
score: 0.82
passed: true
missing:
- 缺少明确升级条件
```

不是固定流程：

```text
查知识库 → 查案例 → 查指标 → 查日志
```

而是动态决策：

| 用户描述 | Agent 倾向动作 |
|---|---|
| 设备明确，现象明确 | 检索内置基础排查知识 |
| 提到温度、压力、流量、振动 | 查询指标阈值或历史趋势 |
| 提到错误码、告警文本、日志关键字 | 搜索日志或告警案例 |
| 描述和历史案例相似 | 搜索历史故障案例 |
| 只说“设备坏了” | 先追问设备类型和具体现象 |
| 涉及安全风险 | 优先给出保护性建议和升级条件 |

## 多轮互动设计

V1 要体现一个简单但真实的互动过程：

```text
1. 用户描述故障现象
2. Agent 结构化理解
3. Agent 判断信息是否足够
4. 信息不足时追问用户
5. 信息足够时选择工具查询
6. Agent 汇总证据
7. 必要时继续追问
8. 最终输出诊断和处置建议
```

Agent 的中间回复不必每次都很长，重点是告诉用户：

```text
我理解到了什么
我还缺什么
我下一步准备查什么
为什么要查这个
```

推荐的追问类型：

| 缺失信息 | 追问示例 |
|---|---|
| 设备不明确 | “这是哪类设备？水泵、UPS、空压机，还是其他设备？” |
| 现象太泛 | “主要异常是温度、压力、流量、声音、振动，还是报警灯？” |
| 缺少严重度 | “异常持续多久了？是否已经影响业务或生产？” |
| 缺少量化指标 | “温度、压力或流量大概是多少？和平时相比变化多大？” |
| 涉及安全风险 | “现场是否有异味、烟雾、漏液、剧烈振动或人员风险？” |

页面右侧应该展示互动过程中的 State 变化：

```text
Turn 1:
- recognized_equipment: 冷却水泵
- symptoms: 异响、流量下降、温度升高
- missing_info: 温度数值、振动情况
- next_action: ask_clarifying_question

Turn 2:
- risk_signals: 高温、振动升高
- next_action: runbook_search + case_search + metric_query
- evidence: ...
```

## 示例设备与故障

V1 可以先围绕三类设备构建演示：

| 设备 | 示例故障现象 |
|---|---|
| 冷却水泵 | 温度高、流量下降、异响、振动变大 |
| UPS | 电池柜温度高、电压漂移、自检告警 |
| 空压机 | 压力上不去、频繁加载卸载、过滤器压差高 |

这些例子足够贴近真实运维，又不会让教程复杂到看不懂。

## V1 轻量知识库与案例

V1 不做设备文档导入，先准备几个简单案例和小型知识库，用来体现“Agent 根据现象自行决定去哪里查”。

建议准备三类数据：

```text
1. 基础排查知识
2. 历史故障案例
3. 示例指标与日志
```

### 基础排查知识

用于回答“这类现象一般先查什么”。

| 设备 | 现象 | 基础排查知识 |
|---|---|---|
| 冷却水泵 | 温度高、流量下降、异响 | 先查阀门开度、过滤器堵塞、轴承温度、振动趋势、备用泵状态 |
| UPS | 电池柜温度高、电压漂移 | 先查负载率、通风、单体电压差、自检结果、冗余状态 |
| 空压机 | 压力上不去、频繁加载卸载 | 先查用气量、进气滤芯压差、泄漏点、排水阀、设定压力 |

### 历史故障案例

用于体现相似案例检索。

| 案例 | 现象 | 最终原因 | 处置 |
|---|---|---|---|
| CASE-001 | 冷却水泵温度升高、流量下降 | 入口过滤器堵塞 | 切备用泵，隔离后清洗过滤器 |
| CASE-002 | UPS 电池柜温度高、电压漂移 | 电池柜风扇故障 | 恢复通风，安排电池巡检 |
| CASE-003 | 空压机压力下降、加载频繁 | 主管路泄漏 | 隔离泄漏支路，恢复压力 |

### 示例指标与日志

用于体现 Agent 会根据现象选择查指标或日志。

| 设备 | 指标 |
|---|---|
| 冷却水泵 | 温度、流量、振动、电机电流 |
| UPS | 电池电压漂移、柜内温度、负载率 |
| 空压机 | 出口压力、滤芯压差、电机电流、加载频率 |

## 用户界面

前端不是用户系统，不做登录、权限、个人中心。

页面应该是一个 **故障运维 Agent 教程控制台**：

```text
左侧：运行配置
- 模型选择
- Temperature
- System Prompt
- 示例故障现象

中间：交互区
- 用户输入故障现象
- Agent 追问关键信息
- 用户补充现场信息
- Agent 输出分析和处置建议

右侧：教学可视化
- Agent State
- 多轮对话 Turn 记录
- 当前 Workflow 节点
- Agent 决定调用的工具
- Tool Calls 输入输出
- 命中的基础知识或历史案例
- Langfuse Trace / Token / Latency
- DeepEval Evaluation Result
```

用户体验重点：

```text
用户只需要描述现象。
系统自己决定去哪里查。
页面把 Agent 的判断过程展示出来。
```

## 后台架构

推荐技术栈：

| 层 | 技术 | 职责 |
|---|---|---|
| UI | Streamlit | 教学控制台 |
| API | FastAPI | 对外 HTTP 接口 |
| Agent Runtime | LangGraph | 状态机、节点、路由、循环 |
| Components | LangChain | LLM、Prompt、Tool 抽象 |
| Knowledge | V1 内置轻量知识库，V2 升级文档导入/RAG | 基础排查知识与案例检索 |
| Observability | Langfuse | V1 记录 Trace / Span / Tool Call / Token / Latency |
| Evaluation | DeepEval | V1 运行故障回答质量评测 |

建议分层：

```text
app/
  api/              # FastAPI 路由，只负责 HTTP
  services/         # 应用编排层
  agent/            # LangGraph 工作流核心
    state.py        # AgentState
    graph.py        # build_graph()
    router.py       # 工具选择和节点流转
    nodes/          # understand / decide / tool / diagnose / final
    prompts/        # 系统提示词
  tools/            # metric_query / log_search / runbook_search / case_search
  knowledge/        # V1 轻量知识库；V2 文档导入、解析、检索
  observability/    # Langfuse 封装
  evaluation/       # DeepEval 数据集与指标
  schemas/          # 请求响应模型
  ui/               # Streamlit 页面

data/
  demo/             # 示例指标、日志、历史案例、基础知识
```

分离原则：

```text
UI 不理解 LangGraph 内部实现。
API 不直接写 Agent 节点逻辑。
Graph 不关心 HTTP 和页面。
Tools 只负责查询能力，不负责最终诊断。
Knowledge 模块 V1 只保留轻量规则和案例检索边界，设备文档导入放到 2.0 版本。
```

## Agent State 设计

建议的核心 State：

```python
class AgentState(TypedDict, total=False):
    user_input: str
    recognized_equipment: str
    symptoms: list[str]
    risk_signals: list[str]
    missing_info: list[str]
    conversation_turns: list[dict]
    loop_history: list[dict]
    step_count: int
    max_steps: int
    next_action: str
    evidence: list[dict]
    tool_calls: list[dict]
    runbook_hits: list[dict]
    case_hits: list[dict]
    possible_causes: list[dict]
    recommended_actions: list[str]
    reflection: dict
    feedback_history: list[dict]
    final_answer: str
```

这个状态设计的重点是教学可读：

```text
用户说了什么
Agent 理解成什么
Agent 觉得缺什么
Agent 决定查什么
查到了什么证据
最后如何形成建议
```

## V1 最小闭环

第一版先做一个可运行闭环：

```text
用户输入故障现象
  ↓
进入 Agent Loop
  ↓
Agent 结构化理解设备和症状，并更新 State
  ↓
Agent 判断是否需要追问
  ↓
用户补充现场信息
  ↓
Agent 继续进入 Loop，决定调用 runbook_search / case_search / metric_query / log_search
  ↓
工具返回证据
  ↓
Agent 更新 State，并判断是否继续查、追问或结束
  ↓
Agent 生成初步诊断，并进入 reflect_node 自我检查
  ↓
检查不通过则继续追问或查证据；检查通过则输出建议
  ↓
Langfuse 记录完整 trace
  ↓
DeepEval 对回答做质量评测
  ↓
页面展示回答、状态、工具调用和证据命中
  ↓
用户反馈执行结果后，Agent 继续更新 State 并进入下一轮闭环
```

建议先不用做：

- 用户系统
- 多 Agent
- 完整 CMDB
- 复杂工单流
- 生产级权限
- 生产级向量数据库
- 设备文档导入
- 大规模评测平台

## 2.0 设备文档导入

设备文档、产品手册、维保指南放到 2.0 版本再做。

2.0 可以增加一个独立模块：

```text
Document Import
  ↓
Document Parse
  ↓
Chunk
  ↓
Embedding / Index
  ↓
document_search Tool
```

这样 V1 保持简单清楚，2.0 再展示完整知识导入和 RAG 能力。

## V2 扩展方向

后续可以逐层增加：

| 能力 | 说明 |
|---|---|
| 设备文档导入 | 支持用户准备的设备手册、维保指南、产品文档 |
| 向量 RAG | 让设备手册、维保指南、历史案例都能被语义检索 |
| 指标趋势分析 | 查询时间窗口内的温度、压力、流量、振动趋势 |
| 工单生成 | 将最终处置建议转成标准工单 |
| 评测集扩展 | 增加更多设备、更多故障现象和更严格指标 |
| Trace 分析 | 对 Langfuse trace 做批量分析和性能优化 |
| Human-in-the-loop | 高风险操作前请求人工确认 |

## 最终定位

本项目最终要表达的是：

```text
一个初学者能看懂、能运行、能扩展的故障运维 Agent 工程样板。
```

它的价值不在于“回答像不像客服”，而在于清楚展示：

```text
Reasoning
→ Tool Selection
→ Evidence Collection
→ Case / Knowledge Grounding
→ Action Planning
→ Observability
→ Evaluation
```
