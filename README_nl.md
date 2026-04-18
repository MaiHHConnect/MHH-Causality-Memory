# CausaMem - Causaal Geheugensysteem

> Geef je AI Agent een levenlang geheugen | Causaal Geheugensysteem voor AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Nederlands](README_nl.md)

---

## Achtergrond

CausaMem is een onafhankelijk geheugensysteem voor AI Agents. Na de ontwikkeling hebben we ons gebaseerd op [Claude-Mem](https://github.com/thedotmack/claude-mem) en de kernfunctie van **AI-gestructureerde compressie** geïmplementeerd, uitgebreid met **causale redenering**.

## Belangrijkste Functies

| Functie | Beschrijving |
|---------|-------------|
| 4-laags geheugen | Gebeurtenissen → Tijdlijn → Relaties → Samenvattingen |
| AI-gestructureerde compressie | Extraheer decided/learned/completed/next_steps |
| Causale redenering | Leidt cause (oorzaak) / effect (gevolg) af |
| 3-motor zoeken | Vector + FTS5 + Causale keten |
| Leesbare Wiki | Obsidian Wiki formaat |
| Type tags | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Snelle Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "We bespraken het geheugensysteem, besloten 4-laags structuur te gebruiken"
python gbrain.py causal "geheugen"
```

## Dank

Geïnspireerd door [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licentie

MIT License
