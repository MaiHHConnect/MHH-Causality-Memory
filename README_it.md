# CausaMem - Sistema di Memoria Causale

> Dai al tuo Agente IA una memoria per tutta la vita | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | Italiano | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Panoramica

CausaMem è un sistema di memoria indipendente per Agenti IA con tre moduli principali:

| Modulo | Descrizione |
|--------|------------|
| Memoria Causale (gbrain) | Compressione strutturata + Ragionamento causale + 3 modi di ricerca |
| Wiki 4 livelli | Eventi→Timeline→Relazioni→Astrazioni |
| Sognare (Cron) | Concatenamento causale periodico + Giudizi astratti |

## Architettura

```
Memoria di avvio → SOUL.md / USER.md / MEMORY.md
Memoria di lavoro → memory/*.md + gbrain + wiki/
Esecuzione periodica → Piccola organizzazione(ogni giorno 02:30) + Grande sogno(ogni gio 03:00)
```

## Avvio rapido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init
python gbrain.py put-structured my-event "Discusso design sistema, deciso usare architettura X"
python gbrain.py causal "design sistema"
```

## Configurazione Cron (Sogni)

```bash
crontab -e
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Crediti


## Licenza

MIT License
