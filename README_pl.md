# CausaMem - Przyczynowy System Pamięci

> Daj swojemu Agentowi AI pamięć na całe życie | Przyczynowy System Pamięci dla Agentów AI

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Polski](README_pl.md)

---

## Kontekst

CausaMem to niezależny system pamięci dla Agentów AI. Po zakończeniu rozwoju, wzorowaliśmy się na [Claude-Mem](https://github.com/thedotmack/claude-mem) i zaimplementowaliśmy jego główną funkcję **AI-uporządkowanej kompresji strukturalnej**, rozszerzoną o **wnioskowanie przyczynowe**.

## Główne Funkcje

| Funkcja | Opis |
|---------|------|
| Pamięć 4-warstwowa | Zdarzenia → Oś czasu → Relacje → Podsumowania |
| Kompresja Strukturalna AI | Automatycznie wyodrębnia decided/learned/completed/next_steps |
| Wnioskowanie Przyczynowe | Wyprowadza cause (przyczyna) / effect (skutek) |
| Wyszukiwanie 3-silnikowe | Wektor + FTS5 + Łańcuch Przyczynowy |
| Wiki Czytelne | Format Obsidian Wiki |
| Tagi Typu | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Szybki Start

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Omówiliśmy system pamięci, postanowiliśmy użyć 4-warstwowej struktury"
python gbrain.py causal "pamiec"
```

## Podziękowania

Zainspirowane przez [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Licencja

MIT License
