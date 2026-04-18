# CausaMem - Sistema de Memória Causal

> Dê ao seu Agente de IA uma memória vitalícia | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | Português (BR) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Visão Geral

CausaMem é um sistema de memória independente para Agentes de IA com três módulos principais:

| Módulo | Descrição |
|--------|-----------|
| Memória Causal (gbrain) | Compressão estruturada + Raciocínio causal + 3 modos de busca |
| Wiki 4 camadas | Eventos→Linha do tempo→Relações→Abstrações |
| Sonhar (Cron) | Encadeamento causal periódico + Julgamentos abstratos |

## Arquitetura

```
Memória de inicialização → SOUL.md / USER.md / MEMORY.md
Memória de trabalho → memory/*.md + gbrain + wiki/
Execução periódica → Pequena organização(diário 02:30) + Grande sonho(semanal qui 03:00)
```

## Início rápido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# Salvar
python gbrain.py put-structured my-event "Discutiu o design do sistema, decidiu usar a arquitetura X"

# Buscar
python gbrain.py causal "design sistema"  # Causal
python gbrain.py query "design"           # Vetor
python gbrain.py search "arquitetura"    # FTS5
```

## Configuração Cron (Sonhos)

```bash
crontab -e

# Pequena organização: Diário 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Grande sonho: Semanal qui 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Créditos

Inspirado em [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licença

MIT License

## Autores

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
