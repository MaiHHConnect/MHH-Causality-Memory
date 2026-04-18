# CausaMem - Sistema di Memoria Causale

> Dai al tuo Agente IA una memoria per tutta la vita | Sistema di Memoria Causale per Agenti IA

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Italiano](README_it.md)

---

## Contesto

CausaMem è un sistema di memoria indipendente per Agenti IA. Dopo lo sviluppo, abbiamo fatto riferimento a [Claude-Mem](https://github.com/thedotmack/claude-mem) e implementato la sua funzionalità principale di **compressione strutturata IA**, estendendola con il **ragionamento causale**.

## Funzionalità Principali

| Funzionalità | Descrizione |
|--------------|-------------|
| Memoria a 4 livelli | Eventi → Timeline → Relazioni → Riassunti |
| Compressione Strutturata IA | Estrae decided/learned/completed/next_steps |
| Ragionamento Causale | Deduce cause (causa) / effect (effetto) |
| Ricerca a 3 motori | Vettore + FTS5 + Catena Causale |
| Wiki Leggibile | Formato Obsidian Wiki |
| Tag di Tipo | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Avvio Rapido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Abbiamo discusso il sistema di memoria, deciso di usare struttura a 4 livelli"
python gbrain.py causal "memoria"
```

## Crediti

Ispirato da [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licenza

MIT License
