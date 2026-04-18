# 🔗 CausaMem - 因果记忆系统

> 让 AI Agent 拥有一生的记忆 | Causal Memory System for AI Agents

---

🌐 **语言 / Language:** [🇺🇸 English](README_en.md) | [🇨🇳 中文](README_zh.md) | [🇯🇵 日本語](README_ja.md) | [🇰🇷 한국어](README_ko.md) | [🇹🇼 繁體中文](README_zh-TW.md) | [🇧🇷 Português (BR)](README_pt-BR.md) | [🇪🇸 Español](README_es.md) | [🇩🇪 Deutsch](README_de.md) | [🇫🇷 Français](README_fr.md) | [🇷🇺 Русский](README_ru.md) | [🇮🇹 Italiano](README_it.md) | [🇵🇱 Polski](README_pl.md) | [🇺🇦 Українська](README_uk.md) | [🇻🇳 Tiếng Việt](README_vi.md) | [🇮🇩 Indonesia](README_id.md) | [🇹🇭 ไทย](README_th.md) | [🇮🇳 हिन्दी](README_hi.md) | [🇳🇱 Nederlands](README_nl.md) | [🇹🇷 Türkçe](README_tr.md) | [🇸🇪 Svenska](README_sv.md) | [🇬🇷 Ελληνικά](README_el.md) | [🇭🇺 Magyar](README_hu.md) | [🇨🇿 Čeština](README_cs.md) | [🇩🇰 Dansk](README_da.md) | [🇳🇴 Norsk](README_no.md) | [🇫🇮 Suomi](README_fi.md) | [🇷🇴 Română](README_ro.md) | [🇸🇦 العربية](README_ar.md) | [🇮🇱 עברית](README_he.md) | [🇧🇩 বাংলা](README_bn.md) | [🇵🇰 اردو](README_ur.md) | [🇵🇹 Português (PT)](README_pt-PT.md)

---

## 设计思路

**记忆不是堆叠，重要的是怎么记。**

人类一生的记忆约 100 万字符，AI Agent 的上下文窗口更大（200 万字符），但堆叠信息不等于有效记忆。真正的问题是：**如何让记忆像人一样，从点到线、从线到面，形成可追溯、可推理的因果网络？**

CausaMem 的答案是：**四层结构化记忆 + 因果推理**

```
事件（点）→ 时间线（线）→ 关系链（面）→ 抽象总结（归因）
```

每一层都是对下一层的抽象和归因。不是堆数据，而是建立**从点到面的归因记忆体系**。

- **事件层**：最小记忆单元（谁+在哪里+做什么+结果+情绪）
- **时间线层**：按时间串联，保证记忆的连续感
- **关系链层**：事件之间的因果/引出/相关关系
- **抽象层**：定期做梦，自动生成因果串线和阶段判断

加上 **前因（cause）** 和 **后果（effect）** 的自动推断，让每个事件不再孤立，而是因果网络上的一环。

---

## 核心特性

### 1. 因果推理（核心首创）
自动从事件中推断**前因（cause）**和**后果（effect）**，让记忆不再是孤立的事实，而是可以追溯因果的链状结构。

```
输入："讨论了记忆系统，决定采用四层结构"
输出：
  cause: "之前的方案太简单"
  effect: "为后续开发奠定基础"
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
| FTS5 全文 | `gbrain.py search` | 精确关键词匹配 |
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

**大做梦**（每周四 03:00）：生成因果串线和阶段判断
```markdown
## 因果串线
- 讨论记忆系统(04-19 02:00) → 决定四层结构 → gbrain升级(04-19 04:00)

## 关系发现
- 浩哥 和 牛马2号：通过钉钉协作，决策-执行模式

## 对未来的暗示
- 下一个里程碑：让其他agent也能使用这套系统
```

### 6. 类型标签系统
按类型组织记忆，方便筛选：

`DECISION` | `INSIGHT` | `BUG` | `FEATURE` | `CHANGE` | `DAILY`

### 7. 多 Agent 共享
记忆存储在文件系统，多个 Agent 可以同时访问、互不影响。

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
│  │  gbrain.db             — 向量+FTS5 双引擎│  │
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
# 写入记忆（自动结构化压缩 + 因果推断）
python gbrain.py put-structured my-event "讨论了系统设计，决定采用X架构"

# AI 压缩观测（查看完整结构化输出）
python gbrain.py compress "你的观测内容"

# 因果链搜索
python gbrain.py causal "系统设计"

# 向量语义搜索
python gbrain.py query "架构方案"

# FTS5 全文搜索
python gbrain.py search "X架构"
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
│       ├── gbrain.py     # 核心脚本
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

## License

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)
