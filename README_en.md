# 🔗 CausaMem - Causal Memory System for AI Agents

> Give your AI Agent a lifetime of memory | 让 AI Agent 拥有一生的记忆

---

🌐 **Language:** [English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Background

CausaMem is an independent AI Agent memory system. After completing development, we referenced [Claude-Mem](https://github.com/thedotmack/claude-mem) and implemented its core **AI-powered structured compression** feature, extended with **causal reasoning**.

## Core Features

| Feature | Description |
|---------|-------------|
| Four-Layer Memory | Events → Timeline → Relations → Abstracts |
| AI Structured Compression | Auto-extract decided/learned/completed/next_steps |
| Causal Reasoning | Auto-infer cause / effect |
| Dual-Engine Search | Vector + FTS5 + Causal Chain |
| Human-Readable Wiki | Obsidian Wiki format |
| Type Tags | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Quick Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
export MINIMAX_API_KEY="your-key"
export SILICONFLOW_API_KEY="your-key"
cd scripts/gbrain
python gbrain.py init
python gbrain.py put-structured memory-2026 "Discussed memory system, decided to use four-layer structure"
python gbrain.py causal "memory"
```

## Acknowledgments

This project references [Claude-Mem](https://github.com/thedotmack/claude-mem) for its AI structured compression design.

## License

MIT License

## Authors

- [Vinson](https://github.com/MaiHHConnect)
- [牛马2号](https://github.com/openclaw) (AI Agent)
