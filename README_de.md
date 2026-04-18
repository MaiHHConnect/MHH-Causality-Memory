# CausaMem - Kausales Gedächtnissystem

> Gib deinem KI-Agent ein lebenslanges Gedächtnis | Kausales Gedächtnissystem für KI-Agenten

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Deutsch](README_de.md)

---

## Hintergrund

CausaMem ist ein unabhängiges Gedächtnissystem für KI-Agenten. Nach der Entwicklung haben wir uns auf [Claude-Mem](https://github.com/thedotmack/claude-mem) bezogen und deren Kernfunktion der **KI-gestützten strukturierten Kompression** implementiert und um **kausales Schließen** erweitert.

## Hauptfunktionen

| Funktion | Beschreibung |
|----------|---------------|
| 4-Schicht-Gedächtnis | Ereignisse → Zeitachse → Beziehungen → Zusammenfassungen |
| KI-gestützte Kompression | Extrahiert decided/learned/completed/next_steps |
| Kausales Schließen | Leitet cause (Ursache) / effect (Wirkung) ab |
| 3-Motor-Suche | Vektor + FTS5 + Kausalkette |
| Lesbares Wiki | Obsidian Wiki Format |
| Typ-Tags | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Schnellstart

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Wir diskutierten das Gedächtnissystem, beschlossen die 4-Schicht-Struktur"
python gbrain.py causal "gedaechtnis"
```

## Danksagung

Inspiriert von [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Lizenz

MIT License
