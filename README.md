# 因果记忆 CausaMem

**Causal Memory — 为跨越一生的 AI Agent 而设计 / Built for AI agents that live across a lifetime**

---

## �🇨 中文 · Chinese

### 它是什么

人一生的记忆大约 100 万字符。给 AI Agent 200 万字符，它需要全部想起来吗？

**不需要。**

真正的记忆，不是仓库的堆叠，而是**因果之网**。每一个"果"都指向它的"因"，每一个"因"都通向它的"果"。当你触摸这张网的任意一个节点，整条因果链条就会自然浮现。

MHH-Causality Memory 就是这张网。

### 核心概念：因果关联

> **果的因，因的果。**

```
Event A（因）
    ↓ creates
Event B（果）
    ↓ explains
Event C（果的果）→ ...形成联想链条
```

记忆不是"记了什么"，而是**"什么导致了什么"**。

### 架构

```
SURFACE LAYER（热层）        ← 当前上下文直接可读
CAUSAL LAYER（因果层）       ← 果→因，因→果，权重=因果强度×时间衰减
SEMANTIC LAYER（语义层）     ← FTS5 精确 + 向量语义兜底
STRUCTURAL LAYER（结构层）   ← Wiki 四层：事件/时间线/关系链/抽象
```

### 核心特性

| 特性 | 说明 |
|------|------|
| 🔗 因果关联 | 记忆之间以因果链条存储，不是孤立事实 |
| 🔄 因果反向关联 | 结果可反向追溯原因，触发整条链条回忆 |
| ⏱️ 因果强度衰减 | 随时间自然衰减，强因果（如人生重大决策）保留更久 |
| 🎯 双引擎兜底 | FTS5 + 向量语义，命中<2条自动触发兜底 |
| 📚 Wiki 四层结构 | 事件/时间线/关系链/抽象，可用 Obsidian 浏览 |
| 🤝 跨 Agent 共享 | OpenClaw + Hermes 共用 Wiki，因果链跨 agent |
| 🧠 一生记忆容量 | 200万字符上下文，按因果权重自动调度 |
| ⚡ 零外部依赖 | 本地存储，可离线运行 |

### 记忆容量

| 触发方式 | 加载范围 |
|---------|---------|
| 精确问答 | 相关因果链（1-5 个节点） |
| 主题联想 | 整条因果链（10-20 个节点） |
| 深度回顾 | 全量扫描 + 权重排序（50-100 个节点） |

### 适用场景

- **个人 AI Agent** — 一生的记忆，跨 agent 共享
- **团队记忆系统** — 多 agent 协作，因果脉络不丢失
- **长期项目** — 记录"为什么这么做"，而不只是"做了什么"
- **知识沉淀** — Wiki + 因果关联，可用 Obsidian 直接维护

### 快速开始

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
mkdir -p wiki/main/{events,timeline,relationships,abstracts}
# 配置 OpenClaw memory_search 后即可使用
```

### 文件结构

```
MHH-Causality-Memory/
├── README.md          ← 说明文档
├── templates/         ← Wiki 层模板
└── wiki/main/        ← Wiki 主目录
    ├── events/       ← 事件层
    ├── timeline/    ← 时间线层
    ├── relationships/ ← 关系链层
    └── abstracts/   ← 抽象总结层
```

---

## 🇺🇸 English

### What It Is

A human's lifetime memory is roughly 1 million characters. Give an AI agent 2 million characters — does it need to recall all of it?

**No.**

Real memory is not a warehouse. It is a **causal web**. Every "effect" points to its "cause". Every "cause" leads to its "effect". When you touch any node of this web, the entire causal chain naturally emerges.

MHH-Causality Memory is this web.

### Core Concept: Causality Links

> **The cause of the effect. The effect of the cause.**

```
Event A (cause)
    ↓ creates
Event B (effect)
    ↓ explains
Event C (effect of effect) → ...forming associative chains
```

Memory is not "what was stored" — it is **"what caused what"**.

### Architecture

```
SURFACE LAYER          ← Directly readable in current context
CAUSAL LAYER          ← effect→cause, cause→effect; weight = causal_strength × decay
SEMANTIC LAYER        ← FTS5 exact + vector semantic fallback
STRUCTURAL LAYER      ← Wiki 4-layer: Events / Timeline / Relationships / Abstracts
```

### Key Features

| Feature | Description |
|---------|-------------|
| 🔗 Causality Links | Memory stored as causal chains, not isolated facts |
| 🔄 Reverse Causation | Effects trace back to causes, triggering the whole chain |
| ⏱️ Causal Decay | Causal strength decays over time; strong causes last longer |
| 🎯 Dual-Engine Fallback | FTS5 exact + vector semantic; auto-fallback on <2 hits |
| 📚 Wiki 4-Layer | Events / Timeline / Relationships / Abstracts — Obsidian-ready |
| 🤝 Cross-Agent Shared | OpenClaw + Hermes share Wiki; causal chains cross agents |
| 🧠 Lifetime Capacity | 2M char context; auto-scheduled by causal weight |
| ⚡ Zero Dependencies | Local storage; works fully offline |

### Memory Capacity

| Trigger Type | Loaded Scope |
|-------------|-------------|
| Precise Q&A | Related causal chain (1–5 nodes) |
| Thematic Association | Full causal chain (10–20 nodes) |
| Deep Reflection | Full scan + weight sort (50–100 nodes) |

### Use Cases

- **Personal AI Agent** — Lifetime memory, shared across agents
- **Team Memory Systems** — Multi-agent collaboration; causal threads never lost
- **Long-Term Projects** — Chains record "why it was done"
- **Knowledge Management** — Wiki + causal links; maintainable in Obsidian

### Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
mkdir -p wiki/main/{events,timeline,relationships,abstracts}
# Configure OpenClaw memory_search to start using
```

---

## License

**MIT License**

- ✅ Personal / open-source use: free
- ❌ Commercial use: requires permission

Contact: 3871169@qq.com

---

**Authors: Vinson & 牛马2号 (Niuma2)**
