# CausaMem - Sistema de Memória Causal

> Dê ao seu Agente de IA uma memória para toda a vida | Sistema de Memória Causal para Agentes de IA

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Português](README_pt-PT.md)

---

## Enquadramento

CausaMem é um sistema de memória independente para Agentes de IA. Após completar o desenvolvimento, referenciamos o [Claude-Mem](https://github.com/thedotmack/claude-mem) e implementamos a sua funcionalidade principal de **compressão estruturada por IA**, expandida com **raciocínio causal**.

## Funcionalidades Principais

| Funcionalidade | Descrição |
|----------------|-----------|
| Memória de 4 camadas | Eventos → Cronologia → Relações → Resumos |
| Compressão Estruturada por IA | Extrai automaticamente decided/learned/completed/next_steps |
| Raciocínio Causal | Infere cause (causa) / effect (consequência) |
| Pesquisa de 3 motores | Vetor + FTS5 + Cadeia Causal |
| Wiki Legível | Formato Obsidian Wiki |
| Etiquetas de Tipo | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Início Rápido

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Discutimos o sistema de memória, decidimos usar estrutura de 4 camadas"
python gbrain.py causal "memória"
```

## Créditos

Inspirado pelo [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licença

MIT License
