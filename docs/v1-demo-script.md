# V1 Demo Script: eKitEngine S380 Onboarding Diagnosis

> 这份脚本用于设计 V1 的主线演示剧情。目标不是模拟一个完美客服，而是让开发者清楚看到 Agentic Workflow 如何在“华为坤灵 APP 开局中的 eKitEngine S380 故障诊断”场景里一步步发生。

## 演示目标

主线案例选择 **eKitEngine S380 在华为坤灵 APP 开局时无法上线**。

这个案例比传统设备硬件故障更适合当前项目，因为它天然包含：

```text
用户自然语言描述
开局流程上下文
设备型号和拓扑信息
APP 状态
网络连通性
设备上线状态
历史相似案例
处置反馈闭环
```

这个案例要完整展示：

```text
1. 现象理解
2. 信息缺口识别
3. 追问用户
4. 用户补充现场信息
5. 工具选择
6. 证据汇总
7. 自我反思
8. 输出建议
9. 用户反馈
10. 再诊断闭环
11. Langfuse 观测
12. DeepEval 评测
```

## 设计原则

不要在第一轮把所有证据都喂给 Agent。问题要故意保留信息缺口，让 Agent 有机会展示：

```text
我理解到了什么
我还缺什么
我为什么要追问
我为什么选择这些工具
工具结果如何改变判断
我如何检查自己的结论是否可靠
```

同时要注意：这份脚本描述的是 **预期演示路径**，不是要求运行时完全 mock 一段固定对话。

V1 可以使用小型、可控的示例数据，但 Agent 的每一步反馈都应该有依据：

```text
现象理解来自用户输入
追问来自 missing_info
工具选择来自 current_state 和 next_action
工具结果来自轻量知识库、案例库、设备状态或 APP 日志数据
诊断来自 evidence 汇总
反思来自 checklist
评测来自 evaluation case 和 metric
```

不要硬编码：

```text
用户一问就直接吐出完整答案
无论输入什么都走同一套工具
工具调用只是假装显示，不影响 State
Reflection 永远通过
Eval Score 固定写死
```

推荐实现方式：

```text
用少量真实 fixture 数据支撑演示
每一次工具调用都返回可解释证据
每一步都把输入、输出和 State 摘要展示出来
最终回答由证据拼装和 LLM/规则共同生成
Langfuse 记录真实节点路径
DeepEval 基于真实输出计算分数
```

也就是说，前端展示可以教程化，但后端流程要真正跑过一遍：

```text
scripted scenario
  != hardcoded answer

controlled demo data
  = evidence-grounded agent flow
```

## 剧情可替换原则

eKitEngine S380 开局故障诊断是 V1 的主线剧情，但它不应该被写死进框架代码。

原则上，剧情变化时：

```text
Agent 框架代码不变
LangGraph 节点结构不变
Tool 接口不变
前端流程布局不变
```

变化的是周边依赖：

```text
demo_cases
fixture 数据
基础排查知识
历史案例
设备状态样例
APP 日志样例
评测集
页面展示文案
```

例如从“eKitEngine S380 开局无法上线”切换到“园区 Wi-Fi 终端无法接入”，不应该重写 `understand_symptom`、`decide_next_action`、`reflect_node` 这些核心流程，而应该替换：

```text
输入剧情：Wi-Fi 终端无法接入
知识条目：无线接入基础排查知识
案例数据：SSID 配置、认证失败、射频覆盖案例
状态数据：AP 在线状态、SSID 状态、认证日志
评测标准：现象覆盖、证据使用、可执行步骤、升级条件
```

这能体现这个项目不是为某一个故障写死的 demo，而是一个可复用的 Agentic Workflow 教程框架。

## 主线剧情

### Turn 1: 用户描述 S380 开局故障

用户输入：

```text
我们在新门店用华为坤灵 APP 开局，扫码添加 eKitEngine S380 后一直显示设备未上线，AP 也没有出现在拓扑里。现场说网线都插好了，帮我判断一下先查什么？
```

这一轮故意只给定性现象，不给网络拓扑、指示灯、APP 报错、设备是否能访问外网、是否获取 DHCP 地址等关键信息。

Agent 预期行为：

```text
1. 识别场景：华为坤灵 APP 开局
2. 识别对象：eKitEngine S380
3. 识别现象：S380 未上线、AP 未出现在拓扑
4. 初步风险：开局无法完成，可能影响门店网络交付
5. 判断信息不足
6. 追问关键现场信息
```

预期节点路径：

```text
understand_symptom
  ↓
update_state
  ↓
decide_next_action
  ↓
ask_clarifying_question
  ↓
END_THIS_TURN
```

Agent 可以这样回复：

```text
我先按“华为坤灵 APP 开局 + eKitEngine S380 未上线 + AP 未出现在拓扑”来理解。

这类问题通常需要先区分是 APP/项目侧问题、设备注册上线问题、上行网络问题，还是本地接线/供电问题。

在给出处置建议前，需要先确认几个关键信息：
1. S380 上联到哪里？是门店路由器、光猫，还是其他网关设备？
2. S380 的电源灯和上联口指示灯状态如何？
3. AP 接在哪个下联口？是否有供电或链路灯？
4. APP 里显示的是“未上线”“添加失败”，还是没有发现设备？
5. 现场网络是否能访问互联网？是否使用 DHCP 自动分配地址？
```

右侧流程教学卡片：

```text
当前学习点：Information Gap Detection

Agent 做了什么：
把自然语言故障现象结构化为开局场景、S380 设备对象和关键症状。

为什么没有直接下结论：
缺少拓扑、指示灯、APP 状态、网络连通性、DHCP 等信息，证据不足。

下一步：
追问用户补充现场开局信息。
```

State 摘要：

```json
{
  "scenario": "华为坤灵 APP 开局",
  "recognized_equipment": ["eKitEngine S380", "AP"],
  "symptoms": ["S380 未上线", "AP 未出现在拓扑"],
  "risk_signals": ["开局无法完成", "门店网络交付受阻"],
  "missing_info": ["网络拓扑", "指示灯状态", "APP 状态", "网络连通性", "DHCP 状态", "AP 接入口"],
  "next_action": "ask_clarifying_question"
}
```

## Turn 2: 用户补充现场信息

用户输入：

```text
S380 上联到门店路由器 LAN 口，电源灯常亮，上联口有灯闪。AP 接在 S380 下面。APP 里扫码能添加设备，但是一直显示未上线。现场电脑接到 S380 下面能上网，路由器开了 DHCP。
```

这一轮补充了足够触发工具查询的证据。

Agent 预期行为：

```text
1. 更新 State
2. 识别关键事实：S380 上联有链路、下联电脑可上网、DHCP 已开、APP 可扫码添加但等待上线
3. 判断本地基础连通性可能正常
4. 决定调用工具，而不是继续泛泛追问
5. 查询开局基础排查知识
6. 查询历史相似案例
7. 查询设备状态或 APP 侧日志样例
8. 汇总证据
9. 生成初步诊断
10. 进入 reflect_node 自我检查
11. 检查通过后输出处置建议
```

预期节点路径：

```text
update_symptom_state
  ↓
decide_next_action
  ↓
runbook_search
  ↓
case_search
  ↓
device_status_query
  ↓
app_log_search
  ↓
update_state
  ↓
diagnose
  ↓
reflect
  ↓
final_answer
  ↓
record_trace
  ↓
run_evaluation
```

工具选择预期：

| Tool | 为什么调用 |
|---|---|
| `runbook_search` | 查询“eKitEngine S380 开局未上线”的基础排查路径 |
| `case_search` | 查找相似开局失败案例 |
| `device_status_query` | 查看示例设备注册、上线、云连接状态 |
| `app_log_search` | 查看 APP 添加设备或项目绑定相关日志 |

工具返回证据示例。注意这些字段应来自工具查询结果，而不是前端静态写死：

```json
{
  "runbook_hits": [
    {
      "title": "eKitEngine S380 开局未上线基础排查",
      "key_checks": ["项目/账号绑定", "设备 SN 是否重复添加", "设备云连接", "DNS/NTP/HTTPS 出口", "DHCP 地址获取", "拓扑接线"]
    }
  ],
  "case_hits": [
    {
      "case_id": "CASE-KL-001",
      "symptom": "eKitEngine S380 扫码添加成功但设备长时间未上线",
      "root_cause": "设备已被其他项目绑定或云连接受限",
      "action": "核对项目绑定关系，确认设备可访问云端服务"
    }
  ],
  "device_status": {
    "model": "S380",
    "local_connectivity": "ok",
    "dhcp": "ok",
    "cloud_register": "pending",
    "last_seen": null
  },
  "app_logs": [
    {
      "event": "device_add",
      "result": "accepted",
      "followup_status": "waiting_online"
    }
  ]
}
```

Reflection Checklist：

| 检查项 | 预期结果 |
|---|---|
| 场景是否明确 | 通过，华为坤灵 APP 开局 |
| 现象是否覆盖 | 通过，S380 未上线、AP 未进拓扑 |
| 证据是否足够 | 通过，有现场信息、基础知识、案例、状态样例 |
| 风险是否处理 | 通过，开局受阻但未直接影响运行中业务 |
| 步骤是否安全 | 通过，先核对绑定和连通性，不建议盲目恢复出厂 |
| 升级条件是否明确 | 需要在最终回答中说明 |

Agent 可以这样回复：

```text
根据你补充的信息，现场基础链路不像是完全断开：

1. S380 上联口有灯闪，说明物理链路存在
2. 电脑接在 S380 下面能上网，说明上行网络和 DHCP 大概率可用
3. APP 扫码能添加设备，但一直等待上线，说明问题更可能出现在设备云连接、项目绑定或上线注册环节

我查询了开局基础排查知识、相似案例和设备状态样例。优先建议按这个顺序排查：

1. 核对设备是否已经被其他项目或账号绑定，避免重复添加导致当前项目等待上线。
2. 检查门店出口是否限制 DNS、NTP 或 HTTPS 访问，设备能上网不等于能正常连接云端服务。
3. 确认设备时间是否正常，如果时间偏差过大，可能影响证书或云连接。
4. 在 APP 中确认当前项目、门店、设备 SN 是否一致。
5. 如果确认绑定和出口都正常，再考虑重启设备并观察是否重新上线。

不建议一开始就恢复出厂。恢复出厂应放在确认绑定、出口和项目配置无误之后，并且要保留现场配置记录。
```

右侧流程教学卡片：

```text
当前学习点：Tool Selection + Evidence Grounding

Agent 做了什么：
根据现场补充信息判断本地网络基本可用，因此优先查询开局知识、相似案例和设备云注册状态。

为什么不是继续追问：
已有信息足够排除一部分基础接线问题，可以进入证据查询。

为什么进入 reflect：
在输出建议前，需要检查是否避免了高风险操作，比如一上来就恢复出厂。
```

Langfuse Trace 预期：

```text
trace: s380-onboarding-offline-demo
  span: understand_symptom
  span: decide_next_action
  span: runbook_search
  span: case_search
  span: device_status_query
  span: app_log_search
  span: reflect
  span: final_answer
```

DeepEval 预期：

```json
{
  "case_id": "s380-onboarding-offline-001",
  "symptom_coverage": 1.0,
  "evidence_usage": 0.9,
  "risk_awareness": 0.8,
  "actionability": 0.9,
  "escalation_condition": 0.8,
  "passed": true
}
```

## Turn 3: 用户反馈处置结果

用户输入：

```text
我们查了，S380 之前被另一个测试项目加过。现在解绑后重新扫码，S380 已经上线了，但 AP 还是没有出现在拓扑里。
```

这一轮用于展示处置反馈闭环。

Agent 预期行为：

```text
1. 更新 feedback_history
2. 判断 S380 上线问题已缓解
3. 判断 AP 拓扑问题仍未解决
4. 缩小排查方向到 AP 供电、下联端口、LLDP/拓扑发现、AP 上线状态
5. 必要时继续查案例或设备状态
6. 给出下一步排查建议
```

预期节点路径：

```text
update_feedback_state
  ↓
decide_next_action
  ↓
case_search
  ↓
device_status_query
  ↓
diagnose_remaining_risk
  ↓
reflect
  ↓
final_answer
```

Agent 可以这样回复：

```text
S380 解绑后重新扫码已经上线，说明前一轮“设备被其他项目绑定”这个方向是有效的。

现在剩余问题变成：AP 没有出现在拓扑里。下一步建议聚焦 AP 和交换机下联关系：

1. 确认 AP 是否正常供电，PoE 指示灯或 AP 指示灯是否正常。
2. 确认 AP 接入的是 S380 的下联口，并且端口有链路灯。
3. 查询 AP 是否已经上线但拓扑未刷新，还是 AP 本身未上线。
4. 如果 AP 未上线，继续检查 DHCP 地址获取和出口访问。
5. 如果 AP 已上线但拓扑不显示，等待拓扑刷新或检查拓扑发现相关配置。

当前不需要回退 S380 开局流程，问题焦点已经从 S380 云注册转到 AP 接入和拓扑发现。
```

右侧流程教学卡片：

```text
当前学习点：Feedback Loop

Agent 做了什么：
把用户执行结果写入 State，判断“S380 已上线”表示主问题部分缓解，“AP 仍未进拓扑”表示剩余问题需要重新聚焦。

为什么没有重复原建议：
反馈信息改变了问题焦点，下一轮诊断应从 S380 上线切换到 AP 接入和拓扑发现。

下一步：
继续查询 AP 状态和下联端口证据。
```

State 摘要：

```json
{
  "feedback_history": [
    {
      "action_taken": "解绑旧项目并重新扫码",
      "switch_status": "online",
      "ap_topology": "missing"
    }
  ],
  "remaining_risks": ["AP 未出现在拓扑", "AP 可能未上线", "拓扑发现未刷新"],
  "next_action": "diagnose_remaining_risk"
}
```

## 对照案例

### APP 扫码添加失败

用户输入：

```text
华为坤灵 APP 扫码添加设备时直接提示添加失败，现场换了手机也一样，应该先查哪里？
```

主要教学点：

```text
Information Gap Detection
App Log Search
账号/项目/设备绑定检查
```

预期 Agent 行为：

```text
1. 识别 APP 添加失败
2. 追问错误提示、设备 SN、项目和账号信息
3. 查询 APP 日志或添加失败案例
4. 优先检查设备是否已绑定、SN 是否录入正确、账号权限是否正确
5. 给出升级条件：多账号复现、设备绑定状态异常、APP 侧返回不可恢复错误
```

### AP 上电但终端搜不到 Wi-Fi

用户输入：

```text
门店开局后 AP 看起来已经上电了，但手机搜不到配置的 Wi-Fi，先从哪里查？
```

主要教学点：

```text
Tool Selection
Config Status Query
排查路径排序
```

预期 Agent 行为：

```text
1. 识别无线业务未生效
2. 查询 AP 在线状态和 SSID 配置状态
3. 查询相似案例
4. 优先区分 AP 未上线、SSID 未下发、射频未开启、终端侧过滤等路径
5. 给出先低风险、后高成本的排查顺序
```

## 前端展示重点

V1 前端不是复杂调试器，而是流程教学页面。每一轮都要让开发者看清楚：

```text
用户说了什么
Agent 理解成什么
Agent 为什么追问
Agent 为什么调用这些工具
工具返回了什么证据
证据如何改变 State
reflect_node 检查了什么
最终回答如何形成
Langfuse 记录了哪些节点
DeepEval 如何评分
```

推荐页面结构：

```text
左侧：自然交互
中间：流程步骤教学卡片
右侧：关键过程摘要
```

## 成功标准

这个演示剧情跑通后，学习者应该能说清楚：

```text
1. Agent Loop 为什么不是一次性问答
2. Agent 为什么需要追问用户
3. 工具选择如何由 State 决定
4. 证据如何进入下一轮判断
5. reflect_node 为什么重要
6. Langfuse 如何观察过程
7. DeepEval 如何评估答案
8. 用户反馈如何触发再诊断闭环
9. 剧情变化为什么不应该改 Agent 框架代码
```
