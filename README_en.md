# CausaMem - Causal Memory System for AI Agents

> Give your AI Agent a lifetime of memory | 让 AI Agent 拥有一生的记忆

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

---

## Background

CausaMem is an independent AI Agent memory system. After completing initial development, we referenced [Claude-Mem](https://github.com/thedotmack/claude-mem) and implemented its core **AI-powered structured compression** feature, then extended it with **causal reasoning** capabilities.

## Core Features

| Feature | Description |
|---------|-------------|
| Four-Layer Memory | Events → Timeline → Relations → Abstracts |
| AI Structured Compression | Auto-extract decided/learned/completed/next_steps |
| Causal Reasoning | Auto-infer cause / effect |
| Dual-Engine Search | Vector + FTS5 + Causal Chain |
| Human-Readable Wiki | Obsidian Wiki format, directly readable |
| Type Tags | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Architecture

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

## Quick Start

### 1. Clone

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
```

### 2. Install Dependencies

```bash
pip install requests
```

### 3. Configure API Key

```bash
export MINIMAX_API_KEY="your-minimax-key"
export SILICONFLOW_API_KEY="your-siliconflow-key"
```

### 4. Initialize

```bash
cd scripts/gbrain
python gbrain.py init
```

### 5. Usage

```bash
# Write memory with structured compression
python gbrain.py put-structured memory-2026-04 "We discussed memory system, decided to use four-layer structure"

# AI compress observation (view structured output)
python gbrain.py compress "Your observation content"

# Vector semantic search
python gbrain.py query "memory system"

# FTS5 full-text search
python gbrain.py search "four layer"

# Causal chain search
python gbrain.py causal "memory system"
```

## Acknowledgments

This project references [Claude-Mem](https://github.com/thedotmack/claude-mem) during development:

| Feature | Source | Description |
|---------|--------|-------------|
| AI Structured Compression | Claude-Mem Session Summary | Compress free text into structured fields |
| Field Design | Claude-Mem | learned / completed / next_steps fields |
| Type Tag System | Claude-Mem | Organize observations by type |

> Claude-Mem is an advanced memory plugin for Claude Code developed by TheDotMack, using SQLite + Chroma vector database architecture. This project independently implements causal reasoning and Wiki-format storage on top of similar concepts.

## Project Structure

```
MHH-Causality-Memory/
├── README.md
├── README_en.md           # English
├── README_ja.md           # 日本語
├── README_ko.md           # 한국어
├── docs/
│   ├── 01_记忆系统架构说明.md
│   └── 安装指南.md
├── scripts/
│   ├── setup.sh
│   └── gbrain/
│       ├── gbrain.py     # Core script (with AI compression)
│       ├── search.py
│       ├── ingest.py
│       ├── stats.py
│       ├── init.py
│       └── brain.db.placeholder
└── wiki/
    └── templates/
```

## Tech Stack

- **Storage**: SQLite
- **Vector Search**: SiliconFlow Qwen3-Embedding-8B
- **AI Compression**: MiniMax API / OpenAI Compatible
- **Format**: Obsidian Wiki (Markdown)

## License

MIT License

## Authors

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)

---

*Built for AI Agents that remember.*
