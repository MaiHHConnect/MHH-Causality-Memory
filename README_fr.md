# CausaMem - Système de Mémoire Causale

> Donnez à votre Agent IA une mémoire à vie | Système de Mémoire Causale pour Agents IA

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

---

## Contexte

CausaMem est un système de mémoire indépendant pour Agents IA. Après développement, nous avons référencé [Claude-Mem](https://github.com/thedotmack/claude-mem) et implémenté sa fonctionnalité principale de **compression structurée par IA**, étendue avec le **raisonnement causal**.

## Fonctionnalités Principales

| Fonctionnalité | Description |
|-----------------|-------------|
| Mémoire à 4 couches | Événements → Chronologie → Relations → Résumés |
| Compression Structurée par IA | Extrait decided/learned/completed/next_steps |
| Raisonnement Causale | Induit cause (cause) / effect (conséquence) |
| Recherche à 3 moteurs | Vecteur + FTS5 + Chaîne Causale |
| Wiki Lisible | Format Obsidian Wiki |
| Tags de Type | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Démarrage Rapide

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Nous avons discuté du système de mémoire, décidé d'utiliser une structure à 4 couches"
python gbrain.py causal "memoire"
```

## Crédits

Inspiré par [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licence

MIT License
