# CausaMem - Sistema de Memória Causal

> Dê ao seu Agent de IA uma memória vitalícia | Sistema de Memória Causal para Agentes de IA

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Português](README_pt-BR.md)

---

## Fundo do Projeto

CausaMem é um sistema de memória independente para Agentes de IA. Após o desenvolvimento, referenciamos o [Claude-Mem](https://github.com/thedotmack/claude-mem) e implementamos sua principal funcionalidade de **compressão estruturada com IA**, estendendo com **raciocínio causal**.

## Funcionalidades Principais

| Recurso | Descrição |
|---------|-----------|
| Memória de 4 camadas | Eventos → Linha do Tempo → Relações → Resumos |
| Compressão Estruturada com IA | Extrai automaticamente decided/learned/completed/next_steps |
| Raciocínio Causal | Infere cause (causa) / effect (consequência) |
| Busca de 3 motores | Vetor + FTS5 + Cadeia Causal |
| Wiki Legível | Formato Obsidian Wiki |
| Tags de Tipo | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Início Rápido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Discutimos o sistema de memória, decidimos usar estrutura de 4 camadas"
python gbrain.py causal "memória"
```

## Créditos

Inspirado em [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licença

MIT License
