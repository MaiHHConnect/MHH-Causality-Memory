# CausaMem - Système de Mémoire Causale

> Donnez à votre Agent IA une mémoire à vie | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | Français | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Aperçu

CausaMem est un système de mémoire indépendant pour Agents IA avec trois modules principaux:

| Module | Description |
|--------|-------------|
| Mémoire Causale (gbrain) | Compression structurée + Raisonnement causal + 3 modes de recherche |
| Wiki 4 couches | Événements→Chronologie→Relations→Abstractions |
| Rêver (Cron) | Enchaînement causal périodique + Jugements abstraits |

## Architecture

```
Mémoire de démarrage → SOUL.md / USER.md / MEMORY.md
Mémoire de travail → memory/*.md + gbrain + wiki/
Exécution périodique → Petite organisation(quotidien 02:30) + Grand rêve(hebdo jeu 03:00)
```

## Démarrage rapide

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# Mémoriser
python gbrain.py put-structured my-event "A discuté du design système, décidé d'utiliser l'architecture X"

# Rechercher
python gbrain.py causal "design système"  # Causale
python gbrain.py query "design"           # Vecteur
python gbrain.py search "architecture"   # FTS5
```

## Configuration Cron (Rêves)

```bash
crontab -e

# Petite organisation: Quotidien 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Grand rêve: Hebdomadaire jeu 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```
## Licence

MIT License

## Auteurs

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
