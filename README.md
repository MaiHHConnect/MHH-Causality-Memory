# 🔗 CausaMem - 因果记忆系统

> 让 AI Agent 拥有一生的记忆 | Causal Memory System for AI Agents

---

🌐 **语言 / Language:** [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## 项目背景

CausaMem（因果记忆）是一套完整的 AI Agent 记忆系统，让 Agent 能够：
- **记住** — 事件自动结构化压缩
- **理解** — 因果关系自动推理
- **推理** — 跨时间线关联发现
- **回顾** — 任意时刻召回完整上下文

系统包含三个核心模块：**因果记忆（gbrain）** + **Wiki 四层结构** + **做梦抽象总结**，三者协同实现「像人一样记忆」。

## 系统架构

```
┌──────────────────────────────────────────────┐
│           AI Agent (你)                         │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  SOUL.md     — 性格、态度、行事风格       │  │
│  │  USER.md     — 用户是谁、偏好、背景       │  │
│  │  MEMORY.md   — 长期 curated 记忆索引     │  │
│  └────────────────────────────────────────┘  │
│                    ↓ 工作记忆                    │
│  ┌────────────────────────────────────────┐  │
│  │  memory/YYYY-MM-DD.md — 每日日记 raw    │  │
│  │  gbrain.db             — 向量+FTS5 双引擎│  │
│  │  wiki/                 — 四层结构可读   │  │
│  └────────────────────────────────────────┘  │
│                    ↓ 被动触发                    │
│  ┌────────────────────────────────────────┐  │
│  │  memory_search() — 搜 → 触发关联        │  │
│  └────────────────────────────────────────┘  │
│                    ↓ 主动触发                    │
│  ┌────────────────────────────────────────┐  │
│  │  做梦 (Cron) — 定期因果串线+抽象总结     │  │
│  └────────────────────────────────────────┘  │
│                                              │
└──────────────────────────────────────────────┘
```

## 三大模块

### 模块一：因果记忆（gbrain）

核心数据库，自动完成 AI 结构化压缩 + 因果推理。

```bash
# 写入记忆（自动压缩 + 因果推断）
python gbrain.py put-structured memory-2026 "讨论记忆系统，决定采用四层结构"

# 输出结构化 JSON：
# {
#   "decided": "采用四层记忆结构",
#   "learned": "四层比三层更清晰",
#   "completed": "确定架构方案",
#   "next_steps": "实现向量压缩",
#   "cause": "之前的方案太简单",
#   "effect": "为后续开发奠定基础",
#   "concepts": ["四层结构", "记忆系统", "架构"]
# }
```

**三种检索方式：**
```bash
python gbrain.py query "记忆系统"      # 向量语义搜索
python gbrain.py search "四层结构"     # FTS5 全文搜索
python gbrain.py causal "记忆系统"     # 因果链搜索
```

### 模块二：Wiki 四层结构

人类可读、可编辑的结构化知识库。

| 层级 | 路径 | 说明 |
|------|------|------|
| 事件层 | `events/` | 最小记忆单元：谁+做了什么+结果 |
| 时间线层 | `timeline/` | 按时间串联事件 |
| 关系链层 | `relations/` | 事件间的因果/引出/相关 |
| 抽象层 | `_dream/` | 定期做梦生成的因果串线+阶段判断 |

### 模块三：做梦抽象总结（Cron）

定时任务，自动分析近期记忆，生成因果串线和抽象判断。

**两种做梦：**

| 类型 | 频率 | 内容 |
|------|------|------|
| 小整理 | 每天 2:30 | 过滤重要事件，追加到当天日记 |
| 大做梦 | 每周四 3:00 | 因果串线 + 关系发现 + 阶段判断 |

**大做梦输出示例：**
```markdown
## 关系发现
- 浩哥 和 牛马2号：通过钉钉协作，决策-执行模式

## 性格倾向
- 浩哥：偏向快速决策，不纠结方案B

## 阶段判断
- CausaMem：v1.0 完成，核心功能落地

## 因果串线
- 讨论记忆系统(04-19 02:00) → 决定四层结构 → gbrain升级(04-19 04:00) → GitHub发布(04-19 04:30)

## 对未来的暗示
- 下一个里程碑：让其他agent也能使用这套系统
```

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

### 3. 配置 API Key（可选，向量搜索需要）

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
# 添加到 crontab
crontab -e

# 小整理：每天 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/gbrain/gbrain.py put-structured "daily-$(date +\%Y-\%m-\%d)" "$(cat ~/.openclaw/workspace-main/memory/$(date +\%Y-\%m-\%d).md 2>/dev/null || echo 'no memory')"

# 大做梦：每周四 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py --big
```

### 6. 开始使用

```bash
# 写入记忆
python gbrain.py put-structured my-event "我们讨论了系统设计，决定采用X方案"

# 搜索
python gbrain.py causal "系统设计"    # 因果链
python gbrain.py query "系统设计"     # 向量
python gbrain.py search "方案"       # 全文
```
## 目录结构

```
MHH-Causality-Memory/
├── README.md              # 本文档
├── docs/
│   ├── 01_记忆系统架构说明.md   # 完整架构文档
│   └── 安装指南.md          # 详细安装说明
├── scripts/
│   ├── setup.sh           # 一键安装脚本
│   ├── gbrain/
│   │   ├── gbrain.py     # 核心脚本（压缩+检索）
│   │   ├── search.py      # 向量搜索入口
│   │   ├── ingest.py      # 批量导入
│   │   ├── stats.py       # 状态统计
│   │   ├── init.py        # 初始化
│   │   └── brain.db.placeholder
│   └── wiki/
│       └── templates/      # Wiki 模板
└── wiki/                  # Wiki 空白结构
    ├── _dream/           # 抽象总结
    ├── events/           # 事件层
    ├── timeline/         # 时间线层
    └── relations/        # 关系链层
```

## 技术栈

- **存储**: SQLite
- **向量搜索**: SiliconFlow Qwen3-Embedding-8B
- **AI 压缩**: MiniMax API / OpenAI Compatible
- **格式**: Obsidian Wiki (Markdown)

## License

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)
