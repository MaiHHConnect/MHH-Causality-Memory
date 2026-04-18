# CausaMem - Causal Memory System

> Give your AI Agent a lifetime of memory

---

## Overview

CausaMem is an **independently developed** AI Agent memory system with 7 core features:

| Feature | Description |
|---------|-------------|
| Causal Reasoning | Auto infer cause/effect |
| AI Compression | Structured fields: decided/learned/completed/next_steps/concepts/cause/effect |
| Dual Search | Vector + FTS5 + Causal chain |
| Wiki 4-Layer | events/timeline/relations/_dream |
| Dream Cron | Periodic causal abstraction (daily 02:30 / weekly Thu 03:00) |
| Type Tags | DECISION/INSIGHT/BUG/FEATURE/CHANGE/DAILY |
| Multi-Agent | Filesystem-based sharing |

## Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init
python gbrain.py put-structured my-event "Discussed design"
python gbrain.py causal "design"
```

## Cron Setup

```bash
crontab -e
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## License

MIT License

## Authors

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)
