# Agent Engineering Starter Kit

> 基于 LangGraph + Langfuse + DeepEval 的现代 Agent 工程化教程框架

---

# 项目简介

本项目是一个：

```text
可运行
可观测
可评估
可扩展
```

的现代 Agent Engineering（Agent 工程化）教程级框架。

项目重点不是：

```text
聊天机器人 Demo
```

而是完整展示：

```text
Build
→ Observe
→ Evaluate
→ Optimize
```

的现代 Agent 开发生命周期。

---

# 项目目标

本项目旨在帮助开发者理解：

- 什么是现代 Agent Runtime
- Agent 如何进行 Tool Calling
- Agent Workflow 如何组织
- 如何观测 Agent 内部运行过程
- 如何评估 Agent 的效果
- 如何构建生产级 Agent 架构

---

# 为什么做这个项目

目前很多 Agent Demo 存在以下问题：

| 问题 | 描述 |
|---|---|
| 黑盒化 | Agent 内部过程不可见 |
| 缺乏观测 | 无法看到 Tool Call / Latency / Token |
| 缺乏评测 | 无法知道 Agent 是否真的有效 |
| 架构混乱 | Prompt、Tool、Workflow 耦合严重 |
| 不可扩展 | 难以演进成真实系统 |

本项目希望通过现代 Agent Engineering 架构解决这些问题。

---

# 技术栈

| 层 | 技术 | 职责 |
|---|---|---|
| Components | LangChain | 模型、Prompt、Tool 抽象 |
| Runtime | LangGraph | Agent 工作流与状态机 |
| Observability | Langfuse | Trace / Span / Token / Latency |
| Evaluation | DeepEval | Agent 自动评测 |
| Backend API | FastAPI | API 服务 |
| Frontend UI | Streamlit | 可视化交互界面 |

---

# 核心设计理念

本项目遵循：

# Agent Engineering

而不是：

```text
Chatbot Demo
```

因此系统重点包括：

- Runtime 可视化
- Workflow 编排
- State 管理
- Tool 调用
- Trace 观测
- Evaluation 评测
- 可扩展架构

---

# 为什么选择 LangGraph

传统 LangChain Agent：

```python
initialize_agent(...)
```

通常存在：

- 黑盒执行
- 不可控
- 难调试
- 难扩展
- 不适合复杂 Agent

因此本项目采用：

# LangGraph

作为核心 Agent Runtime。

LangGraph 的核心思想：

```text
Agent = State + Node + Edge
```

即：

- State：Agent 当前状态
- Node：执行节点
- Edge：状态流转关系

这种方式非常适合：

- Tool Calling
- 多步推理
- Workflow Orchestration
- 多 Agent
- Human-in-the-loop

---

# 为什么选择 Langfuse

如果 Agent 没有 Observability：

```text
≈ 无法调试
```

因此本项目采用：

# Langfuse

用于：

- Trace
- Span
- Tool Call
- Token Usage
- Latency
- Runtime Inspection

Langfuse 是整个 Agent 系统的观测层。

---

# 为什么选择 DeepEval

现代 Agent 系统不能只“能运行”。

还必须：

```text
可评估
可量化
可回归测试
```

因此本项目采用：

# DeepEval

用于：

- Answer Relevancy
- Faithfulness
- Task Completion
- Regression Testing

---

# Demo 场景设计

本项目采用：

# 智能数据分析 Agent

作为完整教程案例。

---

# 示例场景

用户输入：

```text
请帮我分析 2025 年第一季度销售数据，
统计各地区销售额，并生成趋势图。
```

Agent 自动：

```text
1. 理解任务
2. 规划执行步骤
3. 调用 Python Tool
4. 分析 CSV 数据
5. 生成统计图表
6. 输出分析报告
```

---

# 为什么选择这个案例

相比：

```text
天气查询 Demo
```

智能数据分析 Agent 更适合展示：

| 能力 | 是否体现 |
|---|---|
| Tool Calling | YES |
| 多步推理 | YES |
| Python Execution | YES |
| Workflow | YES |
| Structured Output | YES |
| Evaluation | YES |

同时：

```text
复杂度仍然可控
```

非常适合作为教程级 Agent 项目。

---

# V1 功能范围

V1 聚焦：

# 单 Agent Runtime

不做：

- Multi-Agent
- MCP
- Browser Agent
- RAG
- Long-term Memory

---

# V1 功能列表

## 1. Chat Agent

支持：

- 多轮对话
- Tool Calling
- Agent Loop
- Final Response

---

## 2. Python Analysis Tool

核心工具：

```python
python_exec(code)
```

用于：

- DataFrame 分析
- 图表生成
- 数据统计

---

## 3. Web Search Tool

用于：

- 外部知识获取
- 搜索补充信息

---

## 4. Langfuse Trace

展示：

```text
LLM Call
→ Tool Call
→ Tool Result
→ Final Response
```

---

## 5. DeepEval

自动评测：

| Metric | 作用 |
|---|---|
| AnswerRelevancyMetric | 回答相关性 |
| FaithfulnessMetric | 幻觉检测 |
| TaskCompletionMetric | 任务完成度 |

---

# Agent Runtime 设计

Agent Workflow：

```text
START
  ↓
chatbot
  ↓
need_tool?
  ├── yes → tools
  │            ↓
  │         chatbot
  │
  └── no → END
```

这是：

# 标准 ReAct Workflow

---

# 系统架构

```text
                ┌────────────────┐
                │   Streamlit UI │
                └────────┬───────┘
                         ↓
                ┌────────────────┐
                │    FastAPI     │
                └────────┬───────┘
                         ↓
                ┌────────────────┐
                │   LangGraph    │
                │ Agent Runtime  │
                └────────┬───────┘
                         ↓
        ┌────────────────────────────────┐
        │                                │
        ↓                                ↓
┌──────────────┐               ┌────────────────┐
│ LangChain    │               │ Langfuse       │
│ Components   │               │ Observability  │
└──────┬───────┘               └────────────────┘
       ↓
┌──────────────┐
│ LLM + Tools  │
└──────────────┘

                         ↓
                ┌────────────────┐
                │   DeepEval     │
                │   Evaluation   │
                └────────────────┘
```

---

# 项目目录结构

```text
agent-engineering-starter/
│
├── app/
│
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── router.py
│   │   ├── prompts/
│   │   └── nodes/
│   │
│   ├── llm/
│   │   └── models.py
│   │
│   ├── tools/
│   │   ├── python_exec.py
│   │   └── web_search.py
│   │
│   ├── observability/
│   │   └── langfuse_config.py
│   │
│   ├── evaluation/
│   │   ├── dataset.py
│   │   ├── metrics.py
│   │   └── run_eval.py
│   │
│   ├── api/
│   │   └── main.py
│   │
│   └── ui/
│       └── streamlit_app.py
│
├── tests/
├── docker/
├── .env
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Agent State 设计

```python
class AgentState(TypedDict):
    messages: list
    current_step: str
    tool_result: str
    final_answer: str
```

State 是整个 LangGraph Runtime 的核心。

---

# Node 设计

V1 包含：

| Node | 作用 |
|---|---|
| chatbot_node | LLM 推理 |
| tools_node | Tool 调用 |
| router_node | 判断是否继续 |
| final_node | 输出整理 |

---

# LangChain 使用原则

本项目：

# 使用 LangChain Components

但：

# 不使用旧版 Agent 抽象

---

# 使用：

| 组件 | 是否使用 |
|---|---|
| ChatOpenAI | YES |
| PromptTemplate | YES |
| @tool | YES |
| OutputParser | YES |

---

# 不使用：

| 组件 | 原因 |
|---|---|
| initialize_agent | 黑盒 |
| AgentExecutor | 老架构 |
| old chains | 不适合现代 Agent |

---

# UI 设计

采用：

# Streamlit

布局：

```text
左侧：
- 模型选择
- Temperature
- System Prompt

中间：
- Chat Window

右侧：
- Agent State
- Tool Calls
- Trace Timeline
- Token Usage
- Latency
```

---

# Docker 部署

使用：

```text
docker-compose
```

包含：

| 服务 | 作用 |
|---|---|
| app | Agent 服务 |
| langfuse-web | Langfuse UI |
| langfuse-worker | Trace Worker |
| postgres | 数据存储 |
| clickhouse | Trace Analytics |

---

# Evaluation Pipeline

Evaluation Flow：

```text
Dataset
  ↓
Run Agent
  ↓
Collect Response
  ↓
DeepEval
  ↓
Generate Metrics
```

---

# V2 规划

后续可扩展：

| 功能 | 技术 |
|---|---|
| Memory | Redis |
| Multi-Agent | Supervisor Pattern |
| Reflection | Self-Refine |
| MCP | Model Context Protocol |
| Browser Tool | Playwright |
| RAG | Chroma |
| Persistence | PostgreSQL |

---

# 项目最终定位

本项目不是：

```text
聊天机器人 Demo
```

而是：

# Agent Engineering Starter Kit

用于：

- 学习现代 Agent 架构
- 理解 Agent Runtime
- 理解 Observability
- 理解 Evaluation
- 搭建生产级 Agent 基础设施

---

# 最终目标

通过本项目，开发者能够掌握：

```text
LangGraph Runtime
+
Langfuse Observability
+
DeepEval Evaluation
```

构成的现代 Agent Engineering 核心体系。
