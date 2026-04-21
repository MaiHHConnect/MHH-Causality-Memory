# 🔗 CausaMem - 永久性记忆，因果记忆系统 v0.16

> 让 AI Agent 拥有一生的记忆 | Causal Memory System for AI Agents

---

🌐 **语言 / Language:** [🇺🇸 English](README_en.md) | [🇨🇳 中文](README_zh.md) | [🇯🇵 日本語](README_ja.md) | [🇰🇷 한국어](README_ko.md) | [🇹🇼 繁體中文](README_zh-TW.md) | [🇧🇷 Português (BR)](README_pt-BR.md) | [🇪🇸 Español](README_es.md) | [🇩🇪 Deutsch](README_de.md) | [🇫🇷 Français](README_fr.md) | [🇷🇺 Русский](README_ru.md) | [🇮🇹 Italiano](README_it.md) | [🇵🇱 Polski](README_pl.md) | [🇺🇦 Українська](README_uk.md) | [🇻🇳 Tiếng Việt](README_vi.md) | [🇮🇩 Indonesia](README_id.md) | [🇹🇭 ไทย](README_th.md) | [🇮🇳 हिन्दी](README_hi.md) | [🇳🇱 Nederlands](README_nl.md) | [🇹🇷 Türkçe](README_tr.md) | [🇸🇪 Svenska](README_sv.md) | [🇬🇷 Ελληνικά](README_el.md) | [🇭🇺 Magyar](README_hu.md) | [🇨🇿 Čeština](README_cs.md) | [🇩🇰 Dansk](README_da.md) | [🇳🇴 Norsk](README_no.md) | [🇫🇮 Suomi](README_fi.md) | [🇷🇴 Română](README_ro.md) | [🇸🇦 العربية](README_ar.md) | [🇮🇱 עברית](README_he.md) | [🇧🇩 বাংলা](README_bn.md) | [🇵🇰 اردو](README_ur.md) | [🇵🇹 Português (PT)](README_pt-PT.md)

---

## 设计思路

**让 AI Agent 记住 200 万字符，就是这个项目的目标。**

比如人类一生的记忆约 100 万字符，200 万字符足够 agent 一生了。记忆不是堆叠，重要的是怎么记。那真正的问题是：**如何让记忆像人一样，从点到线、从线到面，形成可追溯、可推理的因果网络？**

CausaMem 的答案：**四层结构化记忆 + 13 维因果推理**

```
事件（点）→ 时间线（线）→ 关系链（面）→ 抽象总结（归因）
```

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

### 0. v0.16 重大升级：借鉴 SPlus + MemGPT

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

### 1. 因果推理（13 维因果体系）
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

### 2. AI 结构化压缩
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

### 3. 双引擎检索
三种检索方式，互补兜底：

| 引擎 | 命令 | 适用场景 |
|------|------|---------|
| 向量语义 | `gbrain.py query` | 语义相近但表述不同 |
| 因果链 | `gbrain.py causal` | 搜索前因/后果 |

### 4. Wiki 四层结构
人类可读、可编辑的结构化知识库：

```
wiki/
├── events/           # 事件层：谁+做了什么+结果+情绪
├── timeline/         # 时间线层：按年/月串联
├── relations/        # 关系链层：事件间的因果/相关
└── _dream/          # 抽象层：定期做梦输出
```

### 5. 做梦抽象总结（Cron）
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

### 6. 类型标签系统
按类型组织记忆，方便筛选：

`DECISION` | `INSIGHT` | `BUG` | `FEATURE` | `CHANGE` | `DAILY`

### 7. 多 Agent 共享
记忆存储在文件系统，多个 Agent 可以同时访问、互不影响。

### 8. AI 情绪模块
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
- **向量搜索**: SiliconFlow Qwen3-Embedding-8B
- **AI 压缩**: MiniMax API / OpenAI Compatible
- **格式**: Obsidian Wiki (Markdown)

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

CausaMem v0.15 配套两个增强 Skill，通过 OpenClaw 的 clawhub 安装：

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
CausaMem（因果记忆）←→ self-improving（执行质量）←→ proactivity（前瞻行为）
     ↓                        ↓                        ↓
  知识触发                    教训固化                行动驱动
  被动唤醒                    被动写入                主动驱动
```

**联动机制：**
- CausaMem 负责"这件事和之前的因果关联"
- self-improving 负责"这件事教会了我什么"
- proactivity 负责"接下来应该主动做什么"

三套系统保持独立，通过 OpenClaw 的 AGENTS.md 路由层自然串联，无需手动干预。

---

*Built for AI Agents that remember.*
