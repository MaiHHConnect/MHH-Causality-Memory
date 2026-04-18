# CausaMem - Causal Memory System for AI Agents

> Give your AI Agent a lifetime of memory | 让 AI Agent 拥有一生的记忆

---

🌐 **Language:** [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Background

CausaMem is an **independently developed** AI Agent memory system created by Vinson and AI Agent 牛马2号.

Core philosophy: Give AI agents human-like memory capabilities.

## Core Features

### 1. Causal Reasoning (Core Innovation)
Automatically infer **cause** and **effect** from events, turning isolated facts into traceable causal chains.

```
Input: "Discussed memory system, decided to use four-layer structure"
Output:
  cause: "Previous architecture was too simple"
  effect: "Laid foundation for subsequent development"
```

### 2. AI Structured Compression
Each memory write automatically compresses free text into structured fields:

| Field | Description |
|-------|-------------|
| decided | What was decided |
| learned | What was learned |
| completed | What was completed |
| next_steps | Next steps |
| concepts | Concept tags (2-4) |
| cause | Cause |
| effect | Effect |

### 3. Dual-Engine Search
Three complementary search modes:

| Engine | Command | Best For |
|--------|---------|----------|
| Vector | `gbrain.py query` | Semantic similarity |
| FTS5 | `gbrain.py search` | Exact keyword |
| Causal | `gbrain.py causal` | Cause/Effect search |

### 4. Wiki Four-Layer Structure
Human-readable, editable structured knowledge base:

```
wiki/
├── events/        # Event layer: who+what+result+emotion
├── timeline/      # Timeline layer: chronological
├── relations/     # Relation layer: causal/correlated
└── _dream/      # Abstract layer: dream output
```

### 5. Dream Abstraction (Cron)
Periodic tasks for causal chains and abstract judgments:

| Type | Schedule | Content |
|------|----------|---------|
| Small | Daily 02:30 | Filter important events |
| Big | Weekly Thu 03:00 | Causal chains + phase analysis |

### 6. Type Tag System
Organize memories by type: `DECISION` | `INSIGHT` | `BUG` | `FEATURE` | `CHANGE` | `DAILY`

### 7. Multi-Agent Sharing
Filesystem-based storage, multiple agents can access simultaneously.

## Architecture

```
AI Agent
  ├── SOUL.md / USER.md / MEMORY.md  (startup)
  ├── memory/YYYY-MM-DD.md            (daily raw)
  ├── gbrain.db                       (vector+FTS5)
  ├── wiki/                           (4-layer wiki)
  └── Dream Cron                      (causal abstraction)
```

## Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
export MINIMAX_API_KEY="your-key"
export SILICONFLOW_API_KEY="your-key"
cd scripts/gbrain
python gbrain.py init

# Write memory (auto compression + causal inference)
python gbrain.py put-structured my-event "Discussed system design"

# Three search modes
python gbrain.py causal "system design"
python gbrain.py query "design"
python gbrain.py search "architecture"
```

## Cron Setup

```bash
crontab -e

# Small Dream: Daily 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Big Dream: Weekly Thu 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Project Structure

```
MHH-Causality-Memory/
├── README.md
├── docs/
│   ├── 01_记忆系统架构说明.md
│   └── 安装指南.md
├── scripts/
│   ├── setup.sh
│   ├── dream.py
│   └── gbrain/
│       ├── gbrain.py
│       └── ...
└── wiki/
    ├── _dream/
    ├── events/
    ├── timeline/
    └── relations/
```

## License

MIT License

## Authors

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)
