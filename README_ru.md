# CausaMem - Причинная Система Памяти

> Дайте вашему ИИ-агенту пожизненную память | Причинная система памяти для ИИ-агентов

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Русский](README_ru.md)

---

## Контекст

CausaMem — независимая система памяти для ИИ-агентов. После разработки мы обратились к [Claude-Mem](https://github.com/thedotmack/claude-mem) и реализовали его основную функцию **ИИ-структурированного сжатия**, расширив возможностями **причинного рассуждения**.

## Основные функции

| Функция | Описание |
|---------|----------|
| 4-слойная память | События → Временная шкала → Отношения → Аннотации |
| ИИ-структурированное сжатие | Автоизвлечение decided/learned/completed/next_steps |
| Причинное рассуждение | Выводит cause (причина) / effect (следствие) |
| 3-движковый поиск | Вектор + FTS5 + Причинная цепь |
| Читаемое Wiki | Формат Obsidian Wiki |
| Типовые теги | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Быстрый старт

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Мы обсудили систему памяти, решили использовать 4-слойную структуру"
python gbrain.py causal "память"
```

## Благодарности

Вдохновлено [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Лицензия

MIT License
