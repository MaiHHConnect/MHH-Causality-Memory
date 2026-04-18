# CausaMem - Kauzální Paměťový Systém

> Dejte svému AI Agentovi celoživotní paměť | Kauzální paměťový systém pro AI Agenty

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Čeština](README_cs.md)

---

## Kontext

CausaMem je nezávislý paměťový systém pro AI Agenty. Po dokončení vývoje jsme se inspirovali [Claude-Mem](https://github.com/thedotmack/claude-mem) a implementovali jsme jeho klíčovou funkci **AI-strukturované komprese**, rozšířenou o **kauzální uvažování**.

## Hlavní Funkce

| Funkce | Popis |
|--------|--------|
| 4vrstvá paměť | Události → Časová osa → Vztahy → Souhrny |
| AI-strukturovaná komprese | Automaticky extrahuje decided/learned/completed/next_steps |
| Kauzální uvažování | Odvozuje cause (příčina) / effect (důsledek) |
| 3-motoroé vyhledávání | Vektor + FTS5 + Kauzální řetěz |
| Čitelná Wiki | Formát Obsidian Wiki |
| Typové tagy | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Rychlý Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Diskutovali jsme paměťový systém, rozhodli se pro 4vrstvou strukturu"
python gbrain.py causal "pamet"
```

## Poděkování

Inspirace od [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licence

MIT License
