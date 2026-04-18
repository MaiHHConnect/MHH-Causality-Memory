# CausaMem - Sistema de Memoria Causal

> Dale a tu Agente de IA una memoria de por vida | Sistema de Memoria Causal para Agentes de IA

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Español](README_es.md)

---

## Antecedentes

CausaMem es un sistema de memoria independiente para Agentes de IA. Tras completar el desarrollo, tomamos como referencia [Claude-Mem](https://github.com/thedotmack/claude-mem) e implementamos su funcionalidad principal de **compresión estructurada con IA**, ampliándola con **razonamiento causal**.

## Funcionalidades Principales

| Recurso | Descripción |
|---------|-------------|
| Memoria de 4 capas | Eventos → Línea de Tiempo → Relaciones → Resúmenes |
| Compresión Estructurada con IA | Extrae decided/learned/completed/next_steps |
| Razonamiento Causal | Infiere cause (causa) / effect (consecuencia) |
| Búsqueda de 3 motores | Vector + FTS5 + Cadena Causal |
| Wiki Legible | Formato Obsidian Wiki |
| Etiquetas de Tipo | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Inicio Rápido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Discutimos el sistema de memoria, decidimos usar estructura de 4 capas"
python gbrain.py causal "memoria"
```

## Créditos

Inspirado en [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licencia

MIT License
