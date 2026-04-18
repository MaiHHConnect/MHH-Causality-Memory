# CausaMem — 因果记忆 | Causal Memory for AI Agents

**让 OpenClaw 和 Hermes 建立一生的记忆**
*Build lifelong memory for AI Agents — A causal memory system based on causal chains*

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/MaiHHConnect/MHH-Causality-Memory?style=social)](https://github.com/MaiHHConnect/MHH-Causality-Memory)
[![GitHub forks](https://img.shields.io/github/forks/MaiHHConnect/MHH-Causality-Memory?style=social)](https://github.com/MaiHHConnect/MHH-Causality-Memory)

---

## 🌐 Languages / 语言

> **English** (default) | [中文介绍](#-中文介绍)

---

## What It Is

A human's lifetime memory is roughly **1 million characters**. Give an AI agent **2 million characters** of context — does it need to recall all of it?

**No.**

Real memory is not a warehouse. It is a **causal web**. Every "effect" points to its "cause". Every "cause" leads to its "effect". When you touch any node of this web, the entire causal chain naturally emerges.

**CausaMem** is this web — a causal memory system for AI agents that live across a lifetime.

---

## Core Concept: Causality Links

> **The cause of the effect. The effect of the cause.**

```
Event A (cause)
    ↓ creates
Event B (effect)
    ↓ explains
Event C (effect of effect) → ...forming associative chains
```

Memory is not "what was stored" — it is **"what caused what"**.

When two agents (OpenClaw + Hermes) converse, Agent A's memory fragments can trigger Agent B's causal chain. The chain ripples outward — memory is **recalled**, not searched.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  SURFACE LAYER                                               │
│  Directly readable in current context                         │
├─────────────────────────────────────────────────────────────┤
│  CAUSAL LAYER                                               │
│  effect→cause, cause→effect                                 │
│  Edge weight = causal_strength × temporal_decay              │
├─────────────────────────────────────────────────────────────┤
│  SEMANTIC LAYER                                             │
│  FTS5 exact match + vector semantic search fallback          │
├─────────────────────────────────────────────────────────────┤
│  STRUCTURAL LAYER — Wiki 4-Layer                           │
│  Events / Timeline / Relationships / Abstracts               │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

| | Feature | Description |
|--|---------|-------------|
| 🔗 | **Causality Links** | Memory stored as causal chains, not isolated facts |
| 🔄 | **Reverse Causation** | Effects trace back to causes, triggering the whole chain |
| ⏱️ | **Causal Decay** | Causal strength decays over time; strong causes last longer |
| 🎯 | **Dual-Engine Fallback** | FTS5 exact + vector semantic; auto-fallback on <2 hits |
| 📚 | **Wiki 4-Layer** | Events / Timeline / Relationships / Abstracts — Obsidian-ready |
| 🤝 | **Cross-Agent Shared** | OpenClaw + Hermes share Wiki; causal chains cross agents |
| 🧠 | **Lifetime Capacity** | 2M char context; auto-scheduled by causal weight + decay |
| ⚡ | **Zero Dependencies** | Local storage; works fully offline |

---

## Memory Capacity: 1M vs 2M Characters

| Trigger Type | Loaded Scope |
|-------------|-------------|
| Precise Q&A | Related causal chain (1–5 nodes) |
| Thematic Association | Full causal chain (10–20 nodes) |
| Deep Reflection | Full scan + weight sort (50–100 nodes) |

You don't load everything. You load **the triggered node + its causal chain**.

---

## Comparison

| | KV Store | OpenClaw Default | S+Memory | CausaMem |
|--|:--------:|:---------------:|:--------:|:--------:|
| **Storage** | KV pairs | Text files | Vector facts | Causal chains |
| **Association** | None | None | Co-occurrence | Causal strength |
| **Recall** | Exact match | File read | Semantic search | Causal traversal |
| **Cross-Agent** | ❌ | Difficult | ✅ | ✅ Wiki-shared |
| **Explainability** | Low | Medium | Medium | High (clear chains) |

---

## Quick Start

```bash
# Clone
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory

# Initialize
bash scripts/setup.sh

# Configure OpenClaw memory_search to point to scripts/gbrain/search.py
```

---

## File Structure

```
MHH-Causality-Memory/
├── README.md              ← This file
├── preview.html           ← Bilingual preview (with tab switching, for local use)
├── scripts/
│   ├── setup.sh          ← One-time initialization
│   ├── gbrain/           ← Vector search engine
│   │   ├── search.py     ← Search entry point
│   │   ├── ingest.py     ← Batch import
│   │   ├── init.py       ← DB initialization
│   │   └── stats.py      ← Status check
│   └── wiki/templates/   ← Wiki layer templates
├── wiki/main/             ← Wiki directory (empty, ready to use)
│   ├── events/           ← Event layer
│   ├── timeline/         ← Timeline layer
│   ├── relationships/    ← Relationship layer
│   └── abstracts/        ← Abstract layer
└── docs/
    └── 安装指南.md        ← Installation guide (Chinese)
```

---

## Use Cases

- **Personal AI Agent** — Lifetime memory shared across OpenClaw / Hermes / other agents
- **Team Memory** — Multi-agent collaboration; causal threads never lost
- **Long-Term Projects** — Chains record "why it was done", not just "what was done"
- **Knowledge Management** — Wiki 4-layer + causal links; maintainable in Obsidian

---

## License

**MIT License** — Free for personal/open-source use · Commercial use requires permission

Contact: **3871169@qq.com**

---

**Authors: Vinson & 牛马2号 (Niuma2)**

---

## 🇨🇳 中文介绍

人一生的记忆大约 **100 万字符**。给 AI Agent **200 万字符**，它需要全部想起来吗？

**不需要。**

真正的记忆，不是仓库的堆叠，而是**因果之网**。每一个"果"都指向它的"因"，每一个"因"都通向它的"果"。当你触摸这张网的任意一个节点，整条因果链条就会自然浮现。

**因果记忆 CausaMem** 就是这张网。

### 核心理念

> **果的因，因的果。**

记忆不是"记了什么"，而是**"什么导致了什么"**。

### 架构

| 层级 | 说明 |
|------|------|
| Surface Layer（热层） | 当前上下文直接可读 |
| Causal Layer（因果层） | 果→因，因→果，权重=因果强度×时间衰减 |
| Semantic Layer（语义层） | FTS5 精确 + 向量语义兜底 |
| Structural Layer（结构层） | Wiki 四层：事件/时间线/关系链/抽象 |

### 安装

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
bash scripts/setup.sh
```

详细安装指南见 `docs/安装指南.md`
