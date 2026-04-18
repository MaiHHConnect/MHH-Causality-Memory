# CausaMem - Causal Memory System

> Give your AI Agent a lifetime of memory

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Türkçe](README_tr.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Overview

CausaMem - Independent AI Agent memory system with three core modules:

| Module | Description |
|--------|-------------|
| Causal Memory (gbrain) | Structured compression + Causal reasoning + 3 search modes |
| Wiki 4-Layer | Events→Timeline→Relations→Abstractions |
| Dream (Cron) | Periodic causal chains + Abstract judgments |

## Architecture

```
Startup Memory → SOUL.md / USER.md / MEMORY.md
Working Memory → memory/*.md + gbrain + wiki/
Periodic → Small(daily 02:30) + Big Dream(weekly Thu 03:00)
```

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
crontab -e
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Acknowledgments

Inspired by [Claude-Mem](https://github.com/thedotmack/claude-mem).

## License

MIT License
