# CausaMem - Kausalt Minnessystem

> Ge din AI-agent ett livslångt minne | Kausalt minnessystem för AI-agenter

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Svenska](README_sv.md)

---

## Bakgrund

CausaMem är ett oberoende minnessystem för AI-agenter. Efter utvecklingen refererade vi till [Claude-Mem](https://github.com/thedotmack/claude-mem) och implementerade dess kärnfunktion **AI-strukturerad komprimering**, utökad med **kausal resonemang**.

## Huvudfunktioner

| Funktion | Beskrivning |
|---------|-------------|
| 4-lagers minne | Händelser → Tidslinje → Relationer → Sammanfattningar |
| AI-strukturerad komprimering | Extrahera decided/learned/completed/next_steps |
| Kausal resonemang | Härled cause (orsak) / effect (verkan) |
| 3-motorsökning | Vektor + FTS5 + Kausalkedja |
| Läsbar Wiki | Obsidian Wiki-format |
| Typ-taggar | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Snabbstart

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Vi diskuterade minnessystemet, beslutade använda 4-lagers struktur"
python gbrain.py causal "minne"
```

## Erkännande

Inspirerad av [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licens

MIT License
