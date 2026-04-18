# CausaMem - Kauzális Memóriarendszer

> Adj AI Agentodnak egész életen át tartó memóriát | Kauzális memóriarendszer AI Agentok számára

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Magyar](README_hu.md)

---

## Háttér

A CausaMem egy független memóriarendszer AI Agentok számára. A fejlesztés befejezése után a [Claude-Mem](https://github.com/thedotmack/claude-mem) referenciaként szolgált, és annak **AI-struktúrált tömörítési** funkcióját implementáltuk, kiegészítve **kauzális következtetéssel**.

## Fő jellemzők

| Jellemző | Leírás |
|---------|--------|
| 4 rétegű memória | Események → Idővonal → Kapcsolatok → Összefoglalók |
| AI-struktúrált tömörítés | decided/learned/completed/next_steps automatikus kinyerése |
| Kauzális következtetés | cause (ok) / effect (következmény) következtetése |
| 3 motoros keresés | Vektor + FTS5 + Kauzális lánc |
| Olvasható Wiki | Obsidian Wiki formátum |
| Típus címkék | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Gyors kezdés

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Megbeszéltük a memóriarendszert, úgy döntöttünk 4 rétegű struktúrát használunk"
python gbrain.py causal "memoria"
```

## Köszönet

A [Claude-Mem](https://github.com/thedotmack/claude-mem) inspirálta.

## Licenc

MIT License
