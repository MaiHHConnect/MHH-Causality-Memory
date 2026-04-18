# CausaMem - Kausalt Minnesystem

> Gi din AI Agent et livslangt minne | Kausalt minnesystem for AI Agenter

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Norsk](README_no.md)

---

## Bakgrunn

CausaMem er et uavhengig minnesystem for AI Agenter. Etter utviklingen refererte vi til [Claude-Mem](https://github.com/thedotmack/claude-mem) og implementerte dets kjernefunksjon **AI-strukturert komprimering**, utvidet med **kausal resonnering**.

## Hovedfunksjoner

| Funksjon | Beskrivelse |
|----------|-------------|
| 4-lags minne | Hendelser → Tidslinje → Relasjoner → Sammendrag |
| AI-strukturert komprimering | Trekker ut decided/learned/completed/next_steps automatisk |
| Kausal resonnering | Utleder cause (årsak) / effect (virkning) |
| 3-motors søk | Vektor + FTS5 + Kausal lenke |
| Lesbar Wiki | Obsidian Wiki format |
| Type tags | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Hurtigstart

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Vi diskuterte minnesystemet, bestemte oss for 4-lags struktur"
python gbrain.py causal "minne"
```

## Erkjennelse

Inspirert av [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Lisens

MIT License
