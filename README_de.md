# CausaMem - Kausales Gedächtnissystem

> Gib deinem KI-Agent ein lebenslanges Gedächtnis | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | Deutsch | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Überblick

CausaMem ist ein unabhängiges Gedächtnissystem für KI-Agenten mit drei Kernmodulen:

| Modul | Beschreibung |
|-------|-------------|
| Kausales Gedächtnis (gbrain) | Strukturierte Kompression + Kausale Schlussfolgerung + 3 Suchmodi |
| Wiki 4-Schicht | Ereignisse→Zeitachse→Beziehungen→Abstraktion |
| Träumen (Cron) | Regelmäßige kausale Verkettung + abstrakte Urteile |

## Architektur

```
Startgedächtnis → SOUL.md / USER.md / MEMORY.md
Arbeitsgedächtnis → memory/*.md + gbrain + wiki/
Regelmäßig → Kleine Organisation(täglich 02:30) + Große Träumen(wöchentlich Do 03:00)
```

## Schnellstart

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# Speichern
python gbrain.py put-structured my-event "Systemdesign diskutiert, X-Architektur beschlossen"

# Suchen
python gbrain.py causal "Systemdesign"  # Kausal
python gbrain.py query "Design"          # Vektor
python gbrain.py search "Architektur"   # FTS5
```

## Cron-Einrichtung (Träume)

```bash
crontab -e

# Kleine Organisation: Täglich 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Große Träumen: Wöchentlich Do 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Dank

Inspiriert von [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Lizenz

MIT License

## Autoren

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
