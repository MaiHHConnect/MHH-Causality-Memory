# CausaMem - Sistem de Memorie Causal

> Oferă agentului tău AI o memorie pe viață | Sistem de memorie cauzal pentru agenți AI

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Română](README_ro.md)

---

## Context

CausaMem este un sistem de memorie independent pentru agenți AI. După finalizarea dezvoltării, am făcut referință la [Claude-Mem](https://github.com/thedotmack/claude-mem) și am implementat funcția sa de bază **compresie structurată AI**, extinsă cu **raționament cauzal**.

## Funcționalități Principale

| Funcționalitate | Descriere |
|----------------|-----------|
| Memorie pe 4 niveluri | Evenimente → Cronologie → Relații → Rezumate |
| Compresie Structurată AI | Extrage automat decided/learned/completed/next_steps |
| Raționament Cauzal | Inferă cause (cauză) / effect (efect) |
| Căutare pe 3 motoare | Vector + FTS5 + Lanț Cauzal |
| Wiki Lizibil | Format Obsidian Wiki |
| Etichete de tip | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Start Rapid

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Am discutat despre sistemul de memorie, am decis să folosim structura pe 4 niveluri"
python gbrain.py causal "memorie"
```

## Mulțumiri

Inspirat de [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licență

MIT License
