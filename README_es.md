# CausaMem - Sistema de Memoria Causal

> Dale a tu Agente de IA una memoria de por vida | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | Español | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Descripción

CausaMem es un sistema de memoria independiente para Agentes de IA con tres módulos principales:

| Módulo | Descripción |
|--------|-------------|
| Memoria Causal (gbrain) | Compresión estructurada + Razonamiento causal + 3 modos de búsqueda |
| Wiki 4 capas | Eventos→Línea de tiempo→Relaciones→Abstracciones |
| Soñar (Cron) | Encadenamiento causal periódico + Juicios abstractos |

## Arquitectura

```
Memoria de inicio → SOUL.md / USER.md / MEMORY.md
Memoria de trabajo → memory/*.md + gbrain + wiki/
Ejecución periódica → Pequeña organización(diario 02:30) + Gran sueño(semanal jue 03:00)
```

## Inicio rápido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# Guardar
python gbrain.py put-structured my-event "Discutió el diseño del sistema, decidió usar la arquitectura X"

# Buscar
python gbrain.py causal "diseño sistema"  # Causal
python gbrain.py query "diseño"           # Vector
python gbrain.py search "arquitectura"   # FTS5
```

## Configuración Cron (Soñar)

```bash
crontab -e

# Pequeña organización: Diario 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Gran sueño: Semanal jue 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Créditos

Inspirado por [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licencia

MIT License

## Autores

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
