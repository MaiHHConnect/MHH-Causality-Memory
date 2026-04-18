# MHH-Causality Memory

**因果记忆 — A memory system built on causal chains, designed for AI agents that live across a lifetime.**

人一生的记忆大约 100 万字符。给 AI Agent 200 万字符，它需要全部想起来吗？

不需要。

真正的记忆，不是仓库的堆叠，而是**因果之网**。每一个"果"都指向它的"因"，每一个"因"都通向它的"果"。当你触摸这张网的任意一个节点，整条因果链条就会自然浮现。

MHH-Causality Memory 就是这张网。

---

## What It Does

```
Session 1: Agent learns "浩哥 refactored the memory system on 2026-04-18"
Session 2: Agent asks "浩哥 最近在做什么？" → recalls the 04-18 refactor → traces back to
            the 04-13 Wiki restructure → connects to the first OpenClaw session on 04-08
            → understands the full evolution pattern without storing everything explicitly
```

普通的记忆系统是键值存储。MHH-Causality Memory 是因果之网。

---

## Core Concept: 因果关联（Causality Links）

**果的因，因的果。**

```
  Event A（因）
      ↓ creates
  Event B（果）
      ↓ explains
  Event C（果的果）→ ...形成联想链条
```

记忆不是"记了什么"，而是**"什么导致了什么"**。

当两个 agent（OpenClaw + Hermes）对话时：
- Agent A 的记忆碎片，可以触发 Agent B 的因果链
- Agent B 的因果链反向追溯，又激活 Agent A 的深层记忆
- 因果链条像涟漪一样扩散，记忆自动"想到"而不是被"搜到"

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  SURFACE LAYER（热层 — 当前上下文直接可读）              │
│  当前 session 激活的因果节点，Agent 直接使用              │
├─────────────────────────────────────────────────────────┤
│  CAUSAL LAYER（因果层 — 因果链条）                      │
│  果→因，因→果。每条边有权重：因果强度 + 时间距离          │
├─────────────────────────────────────────────────────────┤
│  SEMANTIC LAYER（语义层 — 向量 + FTS5）                │
│  兜底搜索：精确词 → FTS5，语义相似 → 向量               │
├─────────────────────────────────────────────────────────┤
│  STRUCTURAL LAYER（结构层 — Wiki 四层）                 │
│  事件层 / 时间线层 / 关系链层 / 抽象总结层               │
└─────────────────────────────────────────────────────────┘
```

**因果检索流程：**

```
触发节点 X
    ↓
沿因果边向外扩散（广度优先）
    ↓
按 权重 = 因果强度 × 时间衰减 排序
    ↓
截断至上下文上限（200万字符）
    ↓
返回因果链条，Agent 自然联想
```

---

## Key Features

- **因果关联** — 记忆之间不是孤立存储，而是因果链条，果的因、因的果，形成网络
- **因果反向关联** — 结果可以反向追溯原因，触发整条链条的回忆
- **因果强度衰减** — 因果关系随时间自然衰减，但强因果（如人生重大决策）保留更久
- **双引擎兜底** — FTS5 精确匹配 + 向量语义搜索，命中少于2条时自动兜底
- **Wiki 四层结构** — 事件 / 时间线 / 关系链 / 抽象总结，可直接用 Obsidian 浏览
- **跨 Agent 共享** — OpenClaw 和 Hermes 可以共同读写的 Wiki，因果链跨 agent 传递
- **一生记忆容量** — 200 万字符上下文，按因果权重 + 时间衰减自动调度，无需手动管理
- **零外部依赖** — 本地存储，可离线运行

---

## Quick Start

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/MHH-Causality-Memory.git
cd MHH-Causality-Memory

# 2. 初始化 Wiki 结构
mkdir -p wiki/main/{events,timeline,relationships,abstracts}
cp templates/* wiki/main/

# 3. 配置 OpenClaw memory_search
# 在 openclaw.json 中添加 gbrain 路径

# 4. 开始使用
# 每次 session 后自动沉淀事件到 wiki 层
# 向量索引自动更新
```

---

## Memory Capacity: 100 万字符 vs 200 万字符

人的一生记忆约 100 万字符。给 Agent 200 万字符，不意味着全部加载。

**调度策略：**

| 触发方式 | 加载范围 |
|---------|---------|
| 精确问答 | 相关因果链（约 1-5 个节点）|
| 主题联想 | 整条因果链（约 10-20 个节点）|
| 深度回顾 | 全量扫描 + 按权重排序（约 50-100 个节点）|

不需要全量加载，只需要**触发的节点 + 因果链条**。

---

## 因果记忆 vs 其他记忆系统

| | 传统键值 | OpenClaw 默认 | S+Memory | MHH-Causality |
|--|:-------:|:------------:|:--------:|:------------:|
| **存储形式** | KV 对 | 文本文件 | 向量事实 | 因果链条 |
| **关联方式** | 无 | 无 | 共现关系 | 因果强度 |
| **召回方式** | 精确匹配 | 读文件 | 语义搜索 | 因果扩散 |
| **跨 Agent** | ❌ | 困难 | ✅ | ✅ Wiki 共享 |
| **可解释性** | 低 | 中 | 中 | 高（因果链清晰）|

---

## 适用场景

- **个人 AI Agent** — 一生的记忆，跨 agent 共享（OpenClaw / Hermes / 其他）
- **团队记忆系统** — 多 agent 协作时，记忆的因果脉络不会丢失
- **长期项目** — 因果链条记录了"为什么这么做"，而不是"做了什么"
- **知识沉淀** — Wiki 四层结构 + 因果关联，可直接用 Obsidian 阅读和维护

---

## License

**开源协议：MIT**

- ✅ 个人使用：免费
- ✅ 开源项目：免费
- ❌ 商业使用：需联系授权

如需商业授权，请联系：[邮箱地址]

---

Built with ❤️ for AI agents that deserve a lifetime of memory.
