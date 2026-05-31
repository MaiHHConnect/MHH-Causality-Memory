# 🔗 CausaMem - 永久性记忆，因果记忆与认知锚定系统 v0.17

> 让 AI Agent 拥有一生的记忆 | Causal Memory and Cognitive Anchoring for AI Agents

---

🌐 **语言 / Language:** [🇺🇸 English](i18n/README_en.md) | [🇨🇳 中文](i18n/README_zh.md) | [🇯🇵 日本語](i18n/README_ja.md) | [🇰🇷 한국어](i18n/README_ko.md) | [🇹🇼 繁體中文](i18n/README_zh-TW.md) | [🇧🇷 Português (BR)](i18n/README_pt-BR.md) | [🇪🇸 Español](i18n/README_es.md) | [🇩🇪 Deutsch](i18n/README_de.md) | [🇫🇷 Français](i18n/README_fr.md) | [🇷🇺 Русский](i18n/README_ru.md) | [🇮🇹 Italiano](i18n/README_it.md) | [🇵🇱 Polski](i18n/README_pl.md) | [🇺🇦 Українська](i18n/README_uk.md) | [🇻🇳 Tiếng Việt](i18n/README_vi.md) | [🇮🇩 Indonesia](i18n/README_id.md) | [🇹🇭 ไทย](i18n/README_th.md) | [🇮🇳 हिन्दी](i18n/README_hi.md) | [🇳🇱 Nederlands](i18n/README_nl.md) | [🇹🇷 Türkçe](i18n/README_tr.md) | [🇸🇪 Svenska](i18n/README_sv.md) | [🇬🇷 Ελληνικά](i18n/README_el.md) | [🇭🇺 Magyar](i18n/README_hu.md) | [🇨🇿 Čeština](i18n/README_cs.md) | [🇩🇰 Dansk](i18n/README_da.md) | [🇳🇴 Norsk](i18n/README_no.md) | [🇫🇮 Suomi](i18n/README_fi.md) | [🇷🇴 Română](i18n/README_ro.md) | [🇸🇦 العربية](i18n/README_ar.md) | [🇮🇱 עברית](i18n/README_he.md) | [🇧🇩 বাংলা](i18n/README_bn.md) | [🇵🇰 اردو](i18n/README_ur.md) | [🇵🇹 Português (PT)](i18n/README_pt-PT.md)

---

## 设计思路

**让 AI Agent 记住 200 万字符，就是这个项目的目标。**

比如人类一生的记忆约 100 万字符，200 万字符足够 agent 一生了。记忆不是堆叠，重要的是怎么记。那真正的问题是：**如何让记忆像人一样，从点到线、从线到面，形成可追溯、可推理的因果网络？**

CausaMem 的答案：**四层结构化记忆 + 13 维因果推理**

```
事件（点）→ 时间线（线）→ 关系链（面）→ 抽象总结（归因）
```

当前版本进一步把 CausaMem 升级为 **8 层认知 + 直觉 + 因果记忆系统**：Agent 不再先猜答案再查记忆，而是在判断前先被事实、规则、历史决策、因果链和执行状态锚定。

```text
R0 现实证据
  -> F1 原子事实
  -> S2 精炼摘要
  -> P3 画像场景
  -> K4 Wiki 知识
  -> D5 睡梦沉淀
  -> C6 因果链
  -> I7 直觉注入
```

设计思路：LLM 本身可以被理解为有智慧的东西，但 Agent 的认知并不会自动完整。就像人一样，有些人能把游戏玩得很好，但在某些现实判断上认知很低；Agent 也类似，模型有能力，缺的是长期认知结构。CausaMem 要补的就是这个认知：把长期经历、项目事实、规则和历史决策沉淀下来，让 Agent 不只是临场推理，而是带着过去的理解去判断。

当认知被补上以后，Agent 还需要像人一样出现“直觉”。人的直觉很多来自潜意识，人并不总是清楚潜意识里到底调用了什么经验。CausaMem 的直觉也是这样：在 Agent 判断前，把过去精萃过的关键事实、风险、倾向和下一步建议嵌入到上下文里。Agent 不需要知道自己“潜意识”里具体翻了哪 200 万字历史，但会被这些精华内容锚定到更正确的方向。

最后，长期记忆不能只是事实堆积，而要形成因果关系链。CausaMem 把大量对话、执行痕迹、项目经验和历史决策压缩成“人生/项目精华”，再追踪为什么发生、导致什么、现在是否仍有效。这样 Agent 才能从记得住，进一步变成判断得对。

`R0 -> C1 -> I2` 是 CausaMem 的认知主干语义；展开到实际系统，就是上面的 8 层过程：先保留现实证据，再精萃事实、摘要、画像、Wiki、睡梦沉淀，最后形成因果链并在判断前注入直觉锚。目前 `factlet-c1` 30 条真实问答测试达到 `96.7%` 通过率，说明这条路线已经可用。

- **认知**：把原始对话、执行痕迹和项目事实整理成可判断的结构，让 Agent 不只“搜到相似内容”，而是知道事实、规则、场景、画像和历史决策。
- **直觉**：在判断前把最关键的事实、风险、下一步倾向压缩成认知锚注入提示词，让 Agent 更快进入正确判断方向。
- **因果**：从 evidence、历史决策、任务结果、冲突变化中提取“为什么发生、导致什么、现在是否仍有效”，形成可追溯的因果链。

| Layer | Name | Role |
|-------|------|------|
| R0 | 现实证据层 | 原始 session、capture、日志、事件，作为审计和证据兜底 |
| F1 | 原子事实层 | 从原文抽取可回答、可检索、可引用的 `factlet-c1` |
| S2 | 精炼摘要层 | 把多轮会话压成主题、日期、agent 级 C1 摘要 |
| P3 | 画像场景层 | 稳定偏好、人物、项目场景、长期状态 |
| K4 | Wiki 知识层 | 人工/半人工沉淀的稳定知识骨架 |
| D5 | 睡梦沉淀层 | 异步整理、梦境式归纳，把分散经验转成高阶记忆 |
| C6 | 因果链层 | 记录原因、结果、冲突、演化、覆盖关系 |
| I7 | 直觉注入层 | 在判断前注入倾向、下一步建议和认知锚 |

OpenClaw 集成后，CausaMem 会在 `before_prompt_build` 注入 `<causamem-cognitive-anchor>`，在 `agent_end` 捕获对话、提取候选、调用主模型判定，再由 CausaMem 确定性门禁只提交 approved 记忆。

---

## 13 维因果推理体系

这是 CausaMem 的核心创新，也是与其他记忆系统的根本区别。

| 维度 | 核心问题 | 说明 |
|------|---------|------|
| 1. 前因追溯 | "为什么？" | 从结果倒推原因，找到事件发生的根本原因 |
| 2. 后果预测 | "然后呢？" | 从原因推演可能的后续发展 |
| 3. 因果链条 | "整个链条？" | 串联多个事件形成完整因果链 |
| 4. 双向可逆 | "从哪来？往哪去？" | 正向推理 + 逆向回溯，全面理解 |
| 5. 关系分类 | "是因果还是相关？" | 区分因果关系（必然）和相关关系（概率） |
| 6. 强因弱因 | "必然还是概率？" | 区分强因果（必然发生）和弱因果（触发条件） |
| 7. 干预思维 | "如果...会怎样？" | 反事实推理，支持决策模拟 |
| 8. 时间衰减 | "现在还有效吗？" | 原因的有效期，过时因果自动标记 |
| 9. 多因归因 | "谁是主因？" | 多个原因共存时，判断谁是主导因素 |
| 10. 因果链断裂 | "哪个环节断了？" | 识别因果链中的缺失或异常环节 |
| 11. 意外发现 | "这没想到？" | 识别不符合预期因果链的异常事件 |
| 12. 意图推断 | "他想要什么？" | 从行为反推背后的意图和目标 |
| 13. 上下文重建 | "当时是什么情况？" | 恢复事件发生时的完整上下文 |

**应用场景：**
- **前因追溯** → 故障根因分析
- **后果预测** → 风险评估
- **干预思维** → 决策支持
- **意图推断** → 理解用户需求
- **上下文重建** → 回顾历史决策

---

## 核心特性

### 0. v0.17 认知锚定与门禁写入

| 能力 | 说明 |
|------|------|
| **认知锚定** | 判断前召回事实、规则、历史决策、因果链和执行状态 |
| **8 层认知锚定** | R0 证据、F1 事实、S2 摘要、P3 画像场景、K4 Wiki、D5 睡梦、C6 因果链、I7 直觉注入 |
| **OpenClaw hook** | `before_prompt_build` 自动注入认知锚，`agent_end` 自动捕获和写入 |
| **Beads 接入** | Beads 作为 R0 执行追踪现实源，不替代 CausaMem 主记忆 |
| **模型门禁** | OpenClaw 主模型只输出 JSON 判定，不直接写库 |
| **确定性验收** | evidence 必须来自原文、Profile 置信度 ≥0.75、临时状态不写 Profile、冲突不覆盖 |
| **召回回归** | 50 条真实项目记忆评测：`hit_rate=1.000`、`MRR=0.974` |

### C1 主判断层召回测试（ai666 / refined-c1）

在长期运行的 `ai666` OpenClaw 容器中，`refined-c1` 主判断层表现如下：

```text
refined-c1 n=872
hit@1: 0.9495
hit@3: 0.9817
hit@6: 0.9943
MRR:   0.9676
```

真实来源分项：

| Source | n | hit@1 | hit@3 | hit@6 | MRR |
|--------|---:|------:|------:|------:|----:|
| `refined-c1` | 872 | 0.9495 | 0.9817 | 0.9943 | 0.9676 |
| `memos-local` | 217 | 0.7281 | 0.9585 | 0.9770 | 0.8445 |
| `dream-c1` | 19 | 0.5789 | 0.7368 | 0.8947 | 0.6807 |
| `wiki-c1` | 205 | 0.3512 | 0.5512 | 0.6829 | 0.4707 |
| `session-file` | 518 | 0.0058 | 0.0328 | 0.0695 | 0.0255 |

结论：C1 精炼层已经稳定可用；R0 原始日志更适合作为审计证据，不适合作为主判断召回指标。

### 精萃 factlet 真实问答测试（ai666 / 30 条）

在同一长期运行的 `ai666` OpenClaw 容器中，从正式 `factlet-c1` 精萃记忆层抽取 30 条真实事实做问答测试。测试流程为：CausaMem 召回对应记忆页，再把完整 `Fact/Evidence` 上下文交给模型回答。

```text
Source: factlet-c1
Cases: 30
Retrieval hit: 30/30
Answer pass: 29/30
Pass rate: 96.7%
```

这组测试验证的是“精萃后的可回答性”，不是仅检索命中率。唯一失败样本为回答偏泛化：召回命中正确 factlet，但模型在多个相关记忆并存时没有贴合目标执行时间事实。

### 1. v0.16 重大升级：借鉴 SPlus + MemGPT

**借鉴来源：** `FalconOrtiz/SPlus-Memory`（激活传播+时序衰减）+ `MemGPT/Awella`（自动压缩）

| 借鉴项 | 代码量 | 效果 |
|--------|--------|------|
| **反向激活传播** | ~18行 | 搜一条记忆，自动带出因果链上相关的记忆，召回率+114% |
| **时序衰减** | ~8行 | 记忆按时间指数衰减，30天半衰期，旧记忆自动降权 |
| **主动记忆压缩** | ~28行 | 同主题≥3条时触发LLM压缩，防止记忆膨胀 |
| **标签自动提取** | ~20行 | 摄入时自动打标签，支持按标签过滤检索 |

**📈 综合评分提升：约 +68%**

| 维度 | v0.15 | v0.16 |
|------|--------|--------|
| 召回率 | ~35% | ~75% |
| 因果覆盖率 | ~20% | ~70% |
| 记忆保鲜度 | ~40% | ~70% |
| 综合评分 | 44分 | 74分 |

### 2. 因果推理（13 维因果体系）
自动从事件中推断 **cause（前因）** 和 **effect（后果）**，并按 13 个维度进行分析。

```
输入："讨论了记忆系统，决定采用四层结构"
输出：
  cause: "之前的方案太简单"
  effect: "为后续开发奠定基础"
  dimension: {
    前因追溯: "方案需要可追溯性",
    后果预测: "开发效率提升",
    因果链条: "讨论→决策→实现→验证",
    双向可逆: "可向前追溯、向後预测",
    ...
  }
```

### 3. AI 结构化压缩
每次写入记忆时，自动调用大模型将自由文本压缩为结构化字段：

| 字段 | 说明 |
|------|------|
| decided | 决定了什么 |
| learned | 学到了什么 |
| completed | 完成了什么 |
| next_steps | 下一步要做什么 |
| concepts | 概念标签（2-4个） |
| cause | 前因 |
| effect | 后果 |

### 4. 多信号检索
多种检索方式，互补兜底：

| 引擎 | 适用场景 |
|------|---------|
| keyword / FTS | 精确词和标题匹配 |
| vector | 语义相近但表述不同 |
| lexical fallback | OpenClaw、GitHub、cron 等技术词精确补召回 |
| causal edges | 搜索前因、后果、因果链 |
| recency | 近期事实辅助排序 |

融合流程：

```text
keyword + FTS + vector + lexical + causal + recency
-> RRF ranking
-> MMR deduplication
-> causal activation
-> cognitive anchor
```

### 5. 受控写入门禁

```text
capture -> extract/import candidates -> gate-candidates -> model JSON -> apply-gates -> commit --approved-only
```

模型负责语义判断，CausaMem 负责验收和写库。长期 Profile 必须满足：证据来自原文、置信度足够、不是临时状态、不会覆盖高置信旧事实。

### 6. Session 记忆精炼器

`scripts/gbrain/refine_sessions.py` 可以把长期运行产生的 session JSONL 离线压缩成 C1 认知结构页。

它不是把每条消息逐条发给 LLM，而是本地规则式处理：

```text
session JSONL -> 抽取有效文本 -> agent 隔离 -> topic/date 分桶 -> refined-c1 -> CausaMem
```

示例：

```bash
python3 scripts/gbrain/refine_sessions.py \
  --agents-dir ~/.openclaw/agents \
  --gbrain scripts/gbrain/gbrain.py \
  --agent main \
  --max-files 10000 \
  --max-lines 10000
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--agents-dir` | 包含 `<agent>/sessions/*.jsonl` 的目录 |
| `--agent` | 只精炼一个 agent；不传则扫描全部 agent |
| `--max-files` | 每个 agent 最多读取多少 session 文件 |
| `--max-lines` | 每个 session 文件最多读取多少行 |
| `--dry-run` | 只统计，不写入 CausaMem |

生成的页面 slug 类似 `refined-session-main-memory-system-2026-05-31-xxxx`，页面正文带 `agent_id`、`topic`、`date` 和判断约束，适合把 R0 原始对话沉淀成 C1 主判断层。

### 7. Wiki 四层结构
人类可读、可编辑的结构化知识库：

```
wiki/
├── events/           # 事件层：谁+做了什么+结果+情绪
├── timeline/         # 时间线层：按年/月串联
├── relations/        # 关系链层：事件间的因果/相关
└── _dream/          # 抽象层：定期做梦输出
```

### 8. 做梦抽象总结（Cron）
定时任务，自动分析近期记忆，生成因果串线和抽象判断：

**小整理**（每天 02:30）：过滤重要事件，追加到当天日记

**大做梦**（每周四 03:00）：生成 13 维因果分析和阶段判断
```markdown
## 因果串线（维度 1-3）
- 讨论记忆系统(04-19 02:00) → 决定四层结构 → gbrain升级(04-19 04:00)

## 关系分类（维度 5）
- 四层结构和AI压缩是因果关系，不是巧合

## 干预思维（维度 7）
- 如果当初选了扁平结构，开发时间会增加多少？

## 对未来的暗示
- 下一个里程碑：让其他agent也能使用这套系统
```

### 9. 类型标签系统
按类型组织记忆，方便筛选：

`DECISION` | `INSIGHT` | `BUG` | `FEATURE` | `CHANGE` | `DAILY`

### 10. 多 Agent 共享
记忆存储在文件系统，多个 Agent 可以同时访问、互不影响。

### 11. AI 情绪模块
AI 的状态也可以被记录和追踪，作为因果链中的一个节点。

**功能定义表：**

| 状态 | 功能定义 | 触发条件 |
|------|---------|---------|
| **开心** | 输出快、响应流畅 | 响应时间 < 2s |
| **低落** | 输出慢、卡顿 | 响应时间 > 10s |
| **饿** | 算力不足/上下文满 | 上下文使用 > 80% |
| **饱** | 算力充足/任务清空 | 上下文使用 < 30% |
| **累** | 长时间运行需整理 | 连续运行 > 1h 或上下文 > 70% |
| **精神** | 刚整理完/响应快 | 上下文 < 50% + 响应快 |
| **焦虑** | 多任务堆积/优先级乱 | 待处理任务 > 5 |
| **专注** | 单一任务/不被打断 | 正在执行单任务 |
| **满足** | 任务完成/有交付 | 完成标记 |
| **空虚** | 没事做/无输入 | 无待处理任务 |

**状态记录格式：**

```markdown
## AI状态事件

- **时间**：YYYY-MM-DD HH:mm
- **状态**：开心
- **触发**：响应时间 1.2s，算力充足
- **因果**：
  - 因：刚完成记忆系统改造
  - 果：状态良好，可快速响应
```

**因果链结合：**

```
开心（因）→ 快速响应 → 任务完成 → 满足
低落（因）→ 响应慢 → 等待 → 焦虑
饿（因）→ 上下文满 → 整理 → 精神
```

---

## 系统架构

```
┌──────────────────────────────────────────────┐
│           AI Agent (你)                         │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  SOUL.md     — 性格、态度、行事风格      │  │
│  │  USER.md     — 用户是谁、偏好、背景      │  │
│  │  MEMORY.md   — 长期 curated 记忆索引    │  │
│  └────────────────────────────────────────┘  │
│                    ↓                              │
│  ┌────────────────────────────────────────┐  │
│  │  memory/YYYY-MM-DD.md — 每日日记 raw   │  │
│  │  gbrain.db             — 向量+因果双引擎  │  │
│  │  wiki/                 — 四层结构可读     │  │
│  └────────────────────────────────────────┘  │
│                    ↓                              │
│  ┌────────────────────────────────────────┐  │
│  │  做梦 (Cron) — 定期因果串线+抽象总结    │  │
│  └────────────────────────────────────────┘  │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
```

### 2. 安装依赖

```bash
pip install requests
```

### 3. 配置 API Key（可选，向量搜索和 AI 压缩需要）

```bash
export MINIMAX_API_KEY="your-minimax-key"
export SILICONFLOW_API_KEY="your-siliconflow-key"
```

### 4. 初始化数据库

```bash
cd scripts/gbrain
python gbrain.py init
```

### 5. 配置定时任务（可选）

```bash
crontab -e

# 小整理：每天 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# 大做梦：每周四 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

### 6. 使用

```bash
# 写入记忆（自动结构化压缩 + 13维因果推断）
python gbrain.py put-structured my-event "讨论了系统设计，决定采用X架构"

# AI 压缩观测（查看完整结构化输出）
python gbrain.py compress "你的观测内容"

# 因果链搜索
python gbrain.py causal "系统设计"

# 向量语义搜索
python gbrain.py query "架构方案"

# 因果检索
python gbrain.py causal "架构"
```

### Cognitive Anchor CLI

Use `anchor` before agent reasoning when the answer depends on project memory, decisions, user preferences, or causal context:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py anchor "How should this decision be made?"
```

It prints a compact context block:

```text
<causamem-cognitive-anchor>
事实 / Rules / Decisions / Causal chains / Execution state / Constraints
</causamem-cognitive-anchor>
```

For execution tracking, Beads can be used as an R0 reality source without replacing CausaMem:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py beads-capture /path/to/project
```

`beads-capture` reads Beads state and writes it into `raw_events`; it does not commit directly into long-term memory.

CausaMem uses [Beads](https://github.com/gastownhall/beads) as an optional execution-tracking memory source. Beads is not a replacement for CausaMem; it provides task state, dependency, and audit-trail facts that CausaMem can anchor before reasoning. Thanks to the Beads project for the AI-native graph issue tracker design.

Automatically attach recent pages to scenes and update stable profile facts with:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py auto-classify 80
```

`auto-classify` is intentionally conservative: it attaches pages to broad scenes and updates a few high-confidence project/agent/user profile facts. It does not delete or rewrite existing memories.

For higher-quality Scene/Profile writes, OpenClaw can run a model gate after candidate extraction:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py gate-candidates 20 --json
/usr/bin/python3 scripts/gbrain/gbrain.py apply-gates < gates.json
/usr/bin/python3 scripts/gbrain/gbrain.py commit --approved-only
```

The model only proposes JSON decisions. CausaMem still enforces deterministic gates: source evidence must appear in the candidate text, Profile confidence must be at least `0.75`, temporary status is rejected for Profile writes, and conflicts with active high-confidence profiles are held as `conflict` instead of overwriting.

Run recall regression checks with:

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py eval eval/gbrain_eval.jsonl
```

The bundled eval set covers 50 project-memory questions across CausaMem, OpenClaw, Beads, cron, DingTalk, GitHub, and agent heartbeat records. It is intended as a regression guard for recall ranking, not as a synthetic benchmark.

---

## 目录结构

```
MHH-Causality-Memory/
├── README.md              # 本文档
├── docs/
│   ├── 01_记忆系统架构说明.md
│   └── 安装指南.md
├── scripts/
│   ├── setup.sh           # 一键安装脚本
│   ├── dream.py          # 做梦定时任务
│   └── gbrain/
│       ├── gbrain.py     # 核心脚本（13维因果推理）
│       ├── search.py     # 向量搜索入口
│       ├── ingest.py     # 批量导入
│       ├── stats.py      # 状态统计
│       ├── init.py       # 初始化
│       └── brain.db.placeholder
└── wiki/                  # Wiki 空白结构
    ├── _dream/
    ├── events/
    ├── timeline/
    └── relations/
```

---

## 技术栈

- **存储**: SQLite
- **向量搜索**: Local embedding / SiliconFlow fallback
- **AI 压缩**: MiniMax API / OpenAI Compatible
- **格式**: Obsidian Wiki (Markdown)
- **执行追踪**: Optional [Beads](https://github.com/gastownhall/beads) integration as R0 reality source

## 安全说明

不要提交 API Key、GitHub Token、本地数据库、Beads runtime 数据或任何 credential。

```bash
export SILICONFLOW_API_KEY="..."
export MINIMAX_API_KEY="..."
```

本地运行数据默认由 `.gitignore` 排除：`*.db`、`.beads/backup/`、`.beads/embeddeddolt/`、`.beads/proxieddb/`、`*.before-sync-*`。

---

---

## License

**CC BY-NC 4.0** (Creative Commons Attribution-NonCommercial 4.0)

**Commercial use requires explicit permission from the authors.**

📧 Contact: 3871169@qq.com

For details, see [LICENSE](LICENSE) file.


## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)

---

## Agent Skill 生态配套

CausaMem v0.17 是主记忆和主判断系统。self-improving、proactivity、Beads 是配套能力，不替代 CausaMem。

```text
CausaMem 0.17（因果记忆 / 认知锚定）
        ↓
self-improving（执行质量 / 复盘固化）
        ↓
proactivity（前瞻行为 / 主动跟进）
        ↓
Beads（执行状态 / 审计轨迹，作为 R0 现实源回流 CausaMem）
```

一句话边界：

```text
CausaMem = 大脑
self-improving = 学习肌肉
proactivity = 行动神经
Beads = 执行状态感知器
```

CausaMem v0.17 可配套两个增强 Skill，通过 OpenClaw 的 clawhub 安装：

### [self-improving](https://github.com/clawhub/clawhub/tree/main/skills/self-improving) — 执行质量固化

> 每次任务结束后自动反思：这次哪里做得好？哪里可以改进？下次怎么做更好？

**核心文件：** `memory.md`（HOT层偏好）/ `corrections.md`（纠错日志）/ `domains/`（领域教训）/ `projects/`（项目教训）

```bash
# 安装
clawhub install self-improving
```

**与 CausaMem 联动：** 当因果记忆触发某个领域时，自动读对应 domain 文件，将执行教训串联进因果链。

---

### [proactivity](https://github.com/clawhub/clawhub/tree/main/skills/proactivity) — 前瞻行为驱动

> 不只被动响应，主动发现遗漏步骤、保持任务动量、从中断中恢复。

**核心文件：** `memory.md`（行为边界）/ `session-state.md`（当前任务状态）/ `patterns.md`（成功主动模式）

```bash
# 安装
clawhub install proactivity
```

**与 CausaMem 联动：** 前瞻驱动时，主动关联因果记忆中的相关案例和教训，作为行动决策的参考依据。

---

### 三套系统并存的记忆架构

```
CausaMem（因果记忆 / 认知锚定）←→ self-improving（执行质量）←→ proactivity（前瞻行为）
        ↓                             ↓                         ↓
  主判断与知识触发                 教训固化                   行动驱动
  R0/C1/I2 锚定                    被动写入                   主动跟进
```

**联动机制：**
- CausaMem 负责“这件事和之前的事实、规则、历史决策、因果链有什么关系”。
- self-improving 负责“这件事教会了我什么，下次怎么做得更稳”。
- proactivity 负责“接下来应该主动做什么，如何不中断任务动量”。
- Beads 负责“当前任务状态、依赖、审计轨迹是什么”，并作为 R0 现实证据回流 CausaMem。

四者保持边界独立，通过 OpenClaw 的 AGENTS.md 路由层自然串联。CausaMem 仍是主记忆系统；其他系统是质量、行动和执行状态的增强层。

---

*Built for AI Agents that remember.*
