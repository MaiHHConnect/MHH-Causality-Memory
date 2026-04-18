# CausaMem - Causal Memory System for AI Agents

> Give your AI Agent a lifetime of memory | 让 AI Agent 拥有一生的记忆

---

🌐 **Language:** [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Background

CausaMem is an independent AI Agent memory system. It enables agents to:
- **Remember** — Auto-structured compression of events
- **Understand** — Auto causal reasoning
- **Reason** — Cross-timeline relationship discovery
- **Recall** — Full context at any moment

## Architecture

```
┌──────────────────────────────────────────────┐
│           AI Agent                              │
├──────────────────────────────────────────────┤
│  SOUL.md / USER.md / MEMORY.md  (startup)    │
│  memory/YYYY-MM-DD.md       (daily raw)        │
│  gbrain.db                 (vector+FTS5)       │
│  wiki/                     (4-layer wiki)       │
│  Dream (Cron)              (causal abstraction)│
└──────────────────────────────────────────────┘
```

## Three Core Modules

### Module 1: Causal Memory (gbrain)

```bash
# Write memory with causal inference
python gbrain.py put-structured my-event "Discussed system design, decided to use X architecture"

# Output: {decided, learned, completed, next_steps, cause, effect, concepts}
```

**Three search modes:**
```bash
python gbrain.py query "system design"   # Vector semantic
python gbrain.py search "architecture"   # FTS5 full-text
python gbrain.py causal "design"         # Causal chain
```

### Module 2: Wiki Four-Layer Structure

| Layer | Path | Description |
|-------|------|-------------|
| Events | `events/` | Who + what + result |
| Timeline | `timeline/` | Chronological串联 |
| Relations | `relations/` | Causal / correlated links |
| Abstracts | `_dream/` | Dream output (causal chains + phase analysis) |

### Module 3: Dream Abstraction (Cron)

| Type | Schedule | Content |
|------|----------|---------|
| Small | Daily 02:30 | Filter important events |
| Big | Weekly Thu 03:00 | Causal chains + phase judgments |

**Big Dream Output:**
```markdown
## Relationship Discovery
- [Person A] and [Person B]: relationship description

## Phase Judgments
- [Project]: current phase: [judgment]

## Causal Chain
- Event A → Event B → Event C

## Future Implications
- [Actionable next step]
```

## Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests

# Optional: API keys for AI compression
export MINIMAX_API_KEY="your-key"
export SILICONFLOW_API_KEY="your-key"

cd scripts/gbrain
python gbrain.py init

# Write memory
python gbrain.py put-structured my-event "Discussed memory system"

# Search
python gbrain.py causal "memory system"
```

## Cron Setup (Optional)

```bash
crontab -e

# Small Dream: Daily 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Big Dream: Weekly Thu 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Acknowledgments

This project references [Claude-Mem](https://github.com/thedotmack/claude-mem):

| Feature | Source | Description |
|---------|--------|-------------|
| AI Structured Compression | Claude-Mem | Compress free text into structured fields |
| Field Design | Claude-Mem | learned/completed/next_steps fields |
| Type Tag System | Claude-Mem | Organize observations by type |

## License

MIT License

## Authors

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)
