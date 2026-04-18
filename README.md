# 🔗 CausaMem - 因果记忆系统

> 让 AI Agent 拥有一生的记忆 | Causal Memory System for AI Agents

---

🌐 **语言 / Language:** [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

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
pip install requests
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
python gbrain.py put-structured memory-2026 "讨论记忆系统，决定采用四层结构"

# AI 压缩观测
python gbrain.py compress "你的观测内容"

# 向量语义搜索
python gbrain.py query "记忆系统"

# FTS5 全文搜索
python gbrain.py search "四层结构"

# 因果链搜索
python gbrain.py causal "记忆系统"
```

## 借鉴说明

本项目参考了 [Claude-Mem](https://github.com/thedotmack/claude-mem)：

| 借鉴内容 | 来源 | 说明 |
|----------|------|------|
| AI 结构化压缩 | Claude-Mem | 将自由文本压缩为结构化字段 |
| 字段设计 | Claude-Mem | learned / completed / next_steps 字段 |
| 类型标签系统 | Claude-Mem | 按类型组织观测记录 |

> Claude-Mem 是 TheDotMack 开发的高级 Claude Code 记忆插件。本项目在其基础上独立实现了因果推理和 Wiki 格式存储。

## 技术栈

- **存储**: SQLite
- **向量搜索**: SiliconFlow Qwen3-Embedding-8B
- **AI 压缩**: MiniMax API
- **格式**: Obsidian Wiki (Markdown)

## License

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)

---

*Built for AI Agents that remember.*
