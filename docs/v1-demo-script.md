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
工具结果来自轻量知识库、案例库或设备状态样例；开局动作核对结果来自用户现场回填
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
用少量受控 fixture 数据和用户核对项支撑演示
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

## 案例片段与技术设计对应关系

剧情的教学价值不在于“答案是什么”，而在于学习者能看出每个案例片段在架构中的位置。实现时应把剧情拆成场景依赖，而不是写死在 Agent 框架里。

| 剧情片段 | 要教会什么 | 架构落点 | 前端展示 |
|---|---|---|---|
| Turn 1 用户只描述 S380 未上线、AP 不进拓扑 | 自然语言如何变成可运行状态 | `understand_symptom` 写入 `recognized_equipment`、`symptoms`、`risk_signals` | State 摘要卡展示“识别到了什么” |
| Turn 1 信息不完整 | Agent 为什么先追问而不是直接给答案 | `missing_info` 驱动 `decide_next_action -> ask_clarifying_question` | 教学卡展示缺失信息和追问原因 |
| Turn 2 用户补充上联、DHCP、电脑可上网 | 现场证据如何改变下一步动作 | `conversation_turns`、`evidence` 更新，`next_action` 从追问切到工具查询 | Timeline 展示 State 变化 |
| APP 扫码能添加但等待上线 | Agent 如何把官方排查路径转成用户核对项 | `ask_onboarding_action_check` 生成现场核对清单，用户回填结果进入 State | 核对卡展示待确认动作和用户回填结果 |
| 查询 S380 状态 | 业务工具如何进入 Agent Loop | `device_status_query` 返回状态摘要，写入 `tool_calls` 和 `evidence` | 工具调用摘要展示返回字段 |
| 查询基础排查知识 | 官方约束和 runbook 如何支撑回答 | `runbook_search` 返回检查项、来源和适用条件 | 证据卡展示命中的知识条目 |
| 查询相似历史案例 | 案例检索如何影响原因排序 | `case_search` 更新 `case_hits` 和 `possible_causes` | 可能原因卡展示排序依据 |
| 输出前的自我检查 | 为什么需要 reflection 闭环 | `reflect_node` 读取 State 和 evidence，决定 `ready` 或继续查证 | Reflection Checklist 展示通过/未通过项 |
| 用户反馈 S380 已上线但 AP 仍缺失 | 执行反馈如何触发再诊断 | `feedback_history` 和 `remaining_risks` 更新，下一轮聚焦 AP | 闭环卡展示“已缓解”和“剩余问题” |
| Langfuse 与 DeepEval | 工程化系统如何观测和评测 | Langfuse 记录真实节点路径，DeepEval 基于真实输出评分 | 观测/评测区展示 trace 和 score |

这张表也定义了“剧情可替换”的边界：核心节点、State 字段语义、Tool 接口和 UI 布局保持稳定；变化的是场景输入、知识条目、历史案例、开局动作核对模板、fixture 数据、评测集和页面文案。

## 关键步骤输入/输出

这部分要固化到教程实例里。页面不是只告诉学习者“Agent 做了什么”，还要明确每个关节步骤吃进去什么、吐出来什么，以及这些输出如何成为下一步的输入。

| 步骤 | 输入 | 输出 | S380 剧情里的体现 |
|---|---|---|---|
| `understand_symptom` | 用户本轮输入、上一轮 `AgentState`、GLM 结构化结果或本地规则 | `scenario`、`recognized_equipment`、`symptoms`、`observations`、`missing_info`、初始 `next_action` | 从“APP 里显示未上线”识别出华为坤灵 APP 开局、eKitEngine S380 未上线、AP 未进拓扑，并记录还缺上联、指示灯、DHCP、现场连通性等信息 |
| `decide_next_action` | 已识别场景、设备、现象、现场观察、缺失信息、用户反馈历史 | `next_action`、规划理由、`loop_history` | 第一轮因为缺少现场信息而选择 `ask_user`；第二轮信息足够后选择 `investigate`；用户反馈 S380 已上线但 AP 仍缺失时，转为 `investigate_remaining_risk` |
| `ask_clarifying_question` | `missing_info`、缺失字段到自然语言问题的映射 | 本轮追问文本、追问原因 | 追问 S380 上联到哪里、上联口/电源灯状态、APP 具体状态、电脑接入 S380 是否能上网、路由器是否开启 DHCP |
| `collect_evidence` | 用户输入、场景、设备、现象、现场观察 | `runbook_hits`、`case_hits`、`device_status`、`onboarding_action_checks`、统一 `evidence`、`tool_calls` | 查询 S380 开局知识、相似历史案例、示例设备状态，并生成“核对项目归属、SN、WAN 地址、重新部署动作”的现场核对项 |
| `diagnose` | 知识库命中、案例命中、设备状态、核对项、用户反馈 | `diagnosis`、`possible_causes`、`recommended_actions`、`llm.diagnosis` | 把原因排序到项目归属、WAN 地址获取、云端上线、整网自动发现、AP 接入等路径，并给出低风险排查顺序 |
| `reflect` | 设备/现象是否明确、证据是否充足、建议动作是否安全、是否有升级条件 | `reflection` checklist、`reflection.decision` | 检查回答是否避免一开始恢复出厂，是否要求先核对项目归属和连通性，是否说明需要升级处理的边界 |
| `final` | 诊断结论、原因排序、建议动作、证据、现场核对项 | 面向一线人员的 `final_answer` | 最终回答要包含当前判断、优先排查顺序、用户现场要核对的动作和下一轮反馈方式 |
| `evaluate` | `final_answer`、完整 `AgentState`、工具和 trace 摘要 | `evaluation`、`trace` | DeepEval 风格指标检查回答是否覆盖现象、引用证据、可执行、安全；Langfuse 风格 trace 展示节点路径和工具调用 |

这张表的教学重点是数据流：`understand_symptom` 的输出变成 `decide_next_action` 的输入，`collect_evidence` 的输出变成 `diagnose` 的输入，`reflect` 的结论决定能否进入 `final`。因此剧情可以换，但这套输入/输出契约不能随剧情散掉。

## 官方资料校准

这个案例必须基于官方资料做约束。当前 V1 剧情以华为官方支持文档中的 **Huawei eKit App 扫码开局、S380 上线、S380 整网自动发现** 为依据。

官方资料能支撑的事实：

| 事实 | 官方资料依据 |
|---|---|
| Huawei eKit App 支持通过扫描 SN/条码进行设备开局 | Huawei eKit App 的 Barcode Scanning-based Deployment 文档 |
| S380 可以作为示例设备通过扫码/SN 上线 | SN Scanning-based Deployment 文档以 S380 为示例 |
| S380 开局前需要保证 WAN 口地址获取模式和外网通信条件 | Barcode Scanning-based Deployment / Quick Start Guide |
| DHCP 是 S380 WAN 口地址获取的默认方式之一 | Barcode Scanning-based Deployment |
| S380 上线后可以自动发现整网设备，并在 APP 中添加发现到的设备 | SN Scanning-based Deployment / Quick Start Guide |
| 设备如果已被加入其他项目，官方流程中存在迁移到当前项目的处理 | SN Scanning-based Deployment / Barcode Scanning-based Deployment |
| 设备长时间未部署时，请求间隔可能变长，官方建议断电重启后重新部署 | Barcode Scanning-based Deployment |

官方资料链接：

```text
Huawei eKit App - SN Scanning-based Deployment:
https://support.huawei.com/enterprise/en/doc/EDOC1100396965/f32d2edd/sn-scanning-based-deployment-automatic-entire-network-discovery

Huawei eKit App - Barcode Scanning-based Deployment:
https://support.huawei.com/enterprise/en/doc/EDOC1100396965/3d4c76d9/barcode-scanning-based-deployment

SME Network Solution Quick Start Guide - Configuring Devices:
https://support.huawei.com/enterprise/en/doc/EDOC1100289274/1eaac1e1/configuring-devices

eKitEngine S380 product documentation entry:
https://support.huawei.com/enterprise/en/switches/ekitengine%20s380%20-pid-257690483
```

因此，V1 剧情里的诊断依据应该优先围绕：

```text
S380 是否完成扫码/添加
S380 WAN 口是否能获取地址
S380 是否能访问外网并完成自动上线
设备是否已在其他项目中
是否需要按官方提示迁移设备
S380 上线后是否发现下游设备
等待过久时是否需要断电重启后重新部署
```

目前仍属于 V1 fixture 的内容：

```text
device_status_query 返回的 onboarding_status / last_seen 等示例字段
ask_onboarding_action_check 生成的核对项和用户回填结果
DeepEval 示例分数
具体历史案例 ID
```

这些 fixture 可以用于教学，但不能伪装成真实 APP 接口或真实线上日志。页面上应标注为“示例状态数据”或“演示案例数据”。

需要避免的未经校准表达：

```text
不要把 DNS/NTP/HTTPS 出口受限写成已被官方明确列出的 S380 开局故障根因。
不要写成“直接解绑设备”，优先使用“按提示迁移到当前项目”或“核对项目归属”。
不要声称存在可查询的 APP 开局事件日志或官方 APP 事件接口。
不要将 AP 不进拓扑的具体根因写死，只能作为 S380 整网自动发现后的合理演示扩展。
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
开局动作核对模板
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

这类问题通常需要先区分是 APP/项目侧问题、设备自动上线问题、上行网络问题，还是本地接线/接入问题。

在给出处置建议前，需要先确认几个关键信息：
1. S380 上联到哪里？是门店路由器、光猫，还是其他网关设备？
2. S380 的电源灯和上联口指示灯状态如何？
3. AP 接在哪个下联口？下联口是否有链路状态？
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
7. 查询示例设备状态
8. 根据 runbook 和当前 State 生成开局动作核对项，让用户现场确认
9. 汇总证据和用户可核对项
10. 生成初步诊断
11. 进入 reflect_node 自我检查
12. 检查通过后输出处置建议
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
ask_onboarding_action_check
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

工具与动作选择预期：

| Tool / Action | 为什么调用 |
|---|---|
| `runbook_search` | 查询“eKitEngine S380 开局未上线”的基础排查路径 |
| `case_search` | 查找相似开局失败案例 |
| `device_status_query` | 查看示例设备地址获取、上线和整网发现状态 |
| `ask_onboarding_action_check` | 生成让用户核对的开局动作排查项，不代表真实 APP 接口查询 |

工具返回证据与核对项示例。注意工具结果应来自查询结果，核对项应由 Agent 根据 runbook 和当前 State 生成，而不是前端静态写死：

```json
{
  "runbook_hits": [
    {
      "title": "eKitEngine S380 开局未上线基础排查",
      "key_checks": ["项目/账号归属", "设备 SN 是否重复添加", "WAN 口地址获取模式", "外网通信", "DHCP 地址获取", "整网自动发现状态"]
    }
  ],
  "case_hits": [
    {
      "case_id": "CASE-KL-001",
      "symptom": "eKitEngine S380 扫码添加成功但设备长时间未上线",
      "root_cause": "设备已被其他项目添加，或 S380 无法完成外网通信和自动上线",
      "action": "按官方提示迁移到当前项目，确认 S380 WAN 口地址获取和外网通信条件"
    }
  ],
  "device_status": {
    "model": "S380",
    "local_connectivity": "ok",
    "dhcp": "ok",
    "onboarding_status": "waiting_online",
    "last_seen": null
  },
  "onboarding_action_checks": [
    "确认当前项目和门店是否选对",
    "核对 APP 中设备 SN 是否与机身 SN 一致",
    "确认 S380 是否曾加入其他项目，是否需要按提示迁移到当前项目",
    "确认 S380 WAN 口地址获取方式是否符合现场网络",
    "长时间等待上线时，确认是否按官方建议断电重启后重新部署"
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
| 步骤是否安全 | 通过，先核对项目归属和连通性，不建议盲目恢复出厂 |
| 升级条件是否明确 | 需要在最终回答中说明 |

Agent 可以这样回复：

```text
根据你补充的信息，现场基础链路不像是完全断开：

1. S380 上联口有灯闪，说明物理链路存在
2. 电脑接在 S380 下面能上网，说明上行网络和 DHCP 大概率可用
3. APP 扫码能添加设备，但一直等待上线，说明问题更可能出现在项目归属、WAN 地址获取、外网通信或自动上线环节

我查询了开局基础排查知识、相似案例和设备状态样例。优先建议按这个顺序排查：

1. 核对设备是否已经在其他项目或账号下，避免重复添加导致当前项目等待上线。
2. 确认 S380 WAN 口地址获取模式是否符合开局要求，默认 DHCP 时应保持默认设置。
3. 确认 S380 能与外部网络通信，因为扫码开局需要设备完成自动上线。
4. 在 APP 中确认当前项目、门店、设备 SN 是否一致。
5. 如果设备长时间未上线，按官方建议可以断电重启后重新执行部署观察。

不建议一开始就恢复出厂。应先核对项目归属、WAN 地址获取和外网通信条件，并保留现场配置记录。
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
  span: ask_onboarding_action_check
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
我们查了，S380 之前被另一个测试项目加过。按提示迁移到当前项目后，S380 已经上线了，但 AP 还是没有出现在拓扑里。
```

这一轮用于展示处置反馈闭环。

Agent 预期行为：

```text
1. 更新 feedback_history
2. 判断 S380 上线问题已缓解
3. 判断 AP 拓扑问题仍未解决
4. 缩小排查方向到 AP 接入链路、整网自动发现、AP 上线状态
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
S380 迁移到当前项目后已经上线，说明前一轮“设备已在其他项目中”这个方向是有效的。

现在剩余问题变成：AP 没有出现在拓扑里。下一步建议聚焦 AP 和交换机下联关系：

1. 确认 AP 是否接入 S380 下联网络，端口是否有链路状态。
2. 确认 AP 是否已被 S380 整网自动发现。
3. 查询 AP 是否已经上线但拓扑未刷新，还是 AP 本身未上线。
4. 如果 AP 未上线，继续检查 DHCP 地址获取和出口访问。
5. 如果 AP 已上线但拓扑不显示，等待拓扑刷新或检查拓扑发现相关配置。

当前不需要回退 S380 开局流程，问题焦点已经从 S380 上线转到 AP 接入和整网自动发现。
```

右侧流程教学卡片：

```text
当前学习点：Feedback Loop

Agent 做了什么：
把用户执行结果写入 State，判断“S380 已上线”表示主问题部分缓解，“AP 仍未进拓扑”表示剩余问题需要重新聚焦。

为什么没有重复原建议：
反馈信息改变了问题焦点，下一轮诊断应从 S380 上线切换到 AP 接入和整网自动发现。

下一步：
继续查询 AP 状态和下联端口证据。
```

State 摘要：

```json
{
  "feedback_history": [
    {
      "action_taken": "按提示迁移到当前项目并重新扫码",
      "switch_status": "online",
      "ap_topology": "missing"
    }
  ],
  "remaining_risks": ["AP 未出现在拓扑", "AP 可能未上线", "整网自动发现或拓扑刷新未完成"],
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
Onboarding Event Search
账号/项目/设备归属检查
```

预期 Agent 行为：

```text
1. 识别 APP 添加失败
2. 追问错误提示、设备 SN、项目和账号信息
3. 生成开局动作核对项，必要时查询添加失败案例
4. 优先检查设备是否已在其他项目中、SN 是否录入正确、账号权限是否正确
5. 给出升级条件：多账号复现、设备归属状态异常、APP 侧返回不可恢复错误
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
