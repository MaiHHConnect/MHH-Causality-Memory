# 🔗 CausaMem - 因果记忆系统

> 让 AI Agent 拥有一生的记忆 | Causal Memory System for AI Agents

[English](README_en.md) | 中文 | [日本語](README_ja.md) | [한국어](README_ko.md)

---

## 项目背景

CausaMem 是独立的 AI Agent 记忆系统。在开发完成后，我们参考了 [Claude-Mem](https://github.com/thedotmack/claude-mem)，借鉴并实现了其核心的 **AI 结构化压缩** 功能，并在此基础上扩展了 **因果推理** 能力。

## 核心特性

| 特性 | 说明 |
|------|------|
| 四层记忆结构 | 事件 → 时间线 → 关系链 → 抽象总结 |
| AI 结构化压缩 | 自动提取 decided/learned/completed/next_steps |
| 因果推理 | 自动推断 cause（前因）/ effect（后果） |
| 双引擎检索 | 向量语义搜索 + FTS5 全文搜索 + 因果链搜索 |
| Wiki 人类可读 | Obsidian Wiki 格式，可直接阅读修改 |
| 类型标签 | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## 架构图

```
┌─────────────────────────────────────────┐
│         Context (Limited Space)           │
│  ┌─────────────────────────────────┐   │
│  │ SOUL.md     - Identity/Soul        │   │
│  │ USER.md     - User Info            │   │
│  │ MEMORY.md   - Index + Pointers    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                    ↓ Load on demand
┌─────────────────────────────────────────┐
│         External Memory (Unlimited)       │
│  ┌─────────────────────────────────┐   │
│  │ events/    - Event Layer          │   │
│  │ timeline/  - Timeline Layer       │   │
│  │ relations/ - Relationship Layer   │   │
│  │ abstracts/ - Abstract Layer        │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
```

### 2. 安装依赖

```bash
# Python 依赖
pip install requests

# 向量模型 (可选，向量搜索用)
# 需要 SiliconFlow API Key
```

### 3. 配置 API Key

```bash
export MINIMAX_API_KEY="your-minimax-key"
export SILICONFLOW_API_KEY="your-siliconflow-key"
```

### 4. 初始化

```bash
cd scripts/gbrain
python gbrain.py init
```

### 5. 使用

```bash
# 写入带结构化压缩的记忆
python gbrain.py put-structured memory-2026-04 "我们讨论了记忆系统，决定采用四层结构"

# AI 压缩观测（查看结构化输出）
python gbrain.py compress "你的观测内容"

# 向量语义搜索
python gbrain.py query "记忆系统"

# FTS5 全文搜索
python gbrain.py search "四层结构"

# 因果链搜索
python gbrain.py causal "记忆系统"
```

## 借鉴说明

本项目在开发过程中参考了 [Claude-Mem](https://github.com/thedotmack/claude-mem)：

| 借鉴内容 | 来源 | 说明 |
|----------|------|------|
| AI 结构化压缩 | Claude-Mem Session Summary | 将自由文本压缩为结构化字段 |
| 字段设计 | Claude-Mem | learned / completed / next_steps 等字段 |
| 类型标签系统 | Claude-Mem | 按类型组织观测记录 |

> Claude-Mem 是 TheDotMack 开发的高级 Claude Code 记忆插件，采用 SQLite + Chroma 向量库架构。本项目在其基础上独立实现了因果推理和 Wiki 格式存储。

## 目录结构

```
MHH-Causality-Memory/
├── README.md
├── README_en.md           # English
├── README_ja.md           # 日本語
├── README_ko.md           # 한국어
├── docs/                  # 文档
│   ├── 01_记忆系统架构说明.md
│   └── 安装指南.md
├── scripts/
│   ├── setup.sh           # 一键安装脚本
│   └── gbrain/
│       ├── gbrain.py      # 核心脚本（含 AI 压缩）
│       ├── search.py       # 搜索脚本
│       ├── ingest.py       # 批量导入
│       ├── stats.py        # 统计
│       ├── init.py         # 初始化
│       └── brain.db.placeholder
└── wiki/                  # Wiki 模板
    └── templates/
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

---

*Built for AI Agents that remember.*
