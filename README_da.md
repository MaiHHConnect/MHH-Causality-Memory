# CausaMem - Kausalt Hukommelsessystem

> Giv din AI Agent en livslang hukommelse | Kausalt hukommelsessystem for AI Agenter

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Dansk](README_da.md)

---

## Baggrund

CausaMem er et uafhængigt hukommelsessystem for AI Agenter. Efter udviklingen reference vi til [Claude-Mem](https://github.com/thedotmack/claude-mem) og implementerede dets kernefunktion **AI-struktureret komprimering**, udvidet med **kausal ræsonnement**.

## Hovedfunktioner

| Funktion | Beskrivelse |
|----------|-------------|
| 4-lags hukommelse | Begivenheder → Tidslinje → Relationer → Resuméer |
| AI-struktureret komprimering | Udtrækker automatisk decided/learned/completed/next_steps |
| Kausalt ræsonnement | Udleder cause (årsag) / effect (virkning) |
| 3-motors søgning | Vektor + FTS5 + Kausal kæde |
| Læsbar Wiki | Obsidian Wiki format |
| Type tags | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Hurtig Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Vi diskuterede hukommelsessystemet, besluttede at bruge 4-lags struktur"
python gbrain.py causal "hukommelse"
```

## Anerkendelse

Inspireret af [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licens

MIT License
