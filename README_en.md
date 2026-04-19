# CausaMem v0.15 - Causal Memory System for AI Agents

> 让 AI Agent 拥有一生的记忆 | Permanent Memory for Life | 一记记一生

---

## Design Philosophy

**The goal of this project: Make AI agents remember 2 million characters.**

For example, a human's lifetime memory is roughly 1 million characters. 2 million characters is sufficient for an agent's lifetime. Memory is not about accumulation—it's about how you remember. The real question is: How do you make memory work like a human's—connecting dots into lines, lines into planes, forming a traceable, reasoning-enabled causal network?

CausaMem's answer: Four-Layer Structured Memory + 13-Dimensional Causal Reasoning

**Core promise: 记忆永久性存在，一记记一生 (Permanent memory, remember for a lifetime)**

---

## 13-Dimensional Causal Reasoning

| # | Question | Description |
|---|----------|-------------|
| 1 | Why? | Cause tracing |
| 2 | What then? | Effect prediction |
| 3 | Full chain? | Causal chains |
| 4 | Where from/to? | Bidirectional reasoning |
| 5 | Causal or correlated? | Relation classification |
| 6 | Necessary or probabilistic? | Strong/weak cause |
| 7 | What if? | Intervention thinking |
| 8 | Still valid? | Temporal decay |
| 9 | Who was main cause? | Multi-cause attribution |
| 10 | Which link broke? | Chain breakage |
| 11 | Unexpected? | Anomaly discovery |
| 12 | What did they want? | Intent inference |
| 13 | What was situation? | Context reconstruction |

---

## Core Features (8 Total)

1. **13-Dimensional Causal Reasoning** - Auto cause/effect inference
2. **AI Structured Compression** - decided/learned/completed/next_steps/concepts/cause/effect
3. **Dual-Engine Search** - Vector + FTS5 + Causal chain
4. **Wiki Four-Layer (Human-Readable)** - events/timeline/relations/_dream
5. **Dream Abstraction (Cron)** - Daily 02:30 + Weekly Thu 03:00
6. **Type Tag System** - DECISION/INSIGHT/BUG/FEATURE/CHANGE/DAILY
7. **Multi-Agent Sharing** - Filesystem based
8. **AI Emotion Module** - Track AI state as causal chain node (happy/sad/hungry/sated/tired/energetic/anxious/focused/satisfied/empty)

---

## Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init
python gbrain.py put-structured my-event "Discussed system design"
python gbrain.py causal "system design"
```

## Cron Setup

```bash
30 2 * * * python scripts/dream.py small
0 3 * * 4 python scripts/dream.py big
```

---

## Agent Skill Ecosystem (v0.15)

CausaMem v0.15 ships with two complementary Skills for OpenClaw:

### [self-improving](https://github.com/clawhub/clawhub/tree/main/skills/self-improving) — Execution Quality

> After each task: what went well? What can be improved? What will I do differently next time?

```bash
clawhub install self-improving
```

**CausaMem联动:** When causal memory triggers a domain, automatically read the corresponding domain file to chain execution lessons into the causal network.

---

### [proactivity](https://github.com/clawhub/clawhub/tree/main/skills/proactivity) — Proactive Behavior

> Not just reactive—anticipate missing steps, keep momentum, recover from interruptions.

```bash
clawhub install proactivity
```

**CausaMem联动:** When driving proactive behavior, proactively link to relevant cases and lessons from causal memory as decision references.

---

### Three-System Memory Architecture

```
CausaMem (Causal Memory) ←→ self-improving (Execution Quality) ←→ proactivity (Proactive Behavior)
     ↓                          ↓                          ↓
  Knowledge Trigger         Lesson Consolidation       Action Driver
  Passive Wake-up           Passive Write-in           Active Drive
```

**Linkage:**
- CausaMem: "How is this related to past events因果?"
- self-improving: "What did this teach me?"
- proactivity: "What should I do next proactively?"

Three systems remain independent, naturally chained via OpenClaw's AGENTS.md routing layer—no manual intervention required.

---

## License

**CC BY-NC 4.0** - Commercial use requires permission.

Contact: 3871169@qq.com

---

## Authors

- Vinson
- 牛马2号 (AI Agent)
