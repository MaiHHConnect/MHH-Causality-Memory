# CausaMem - Українська Причинна Система Пам'яті

> Дайте вашому AI-агенту пам'ять на все життя | Причинна система пам'яті для AI-агентів

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Українська](README_uk.md)

---

## Контекст

CausaMem — незалежна система пам'яті для AI-агентів. Після розробки ми звернулися до [Claude-Mem](https://github.com/thedotmack/claude-mem) та імплементували його основну функцію **AI-структурованого стиснення**, розширивши можливостями **причинного міркування**.

## Основні функції

| Функція | Опис |
|---------|------|
| 4-шарова пам'ять | Події → Часова шкала → Відносини → Підсумки |
| AI-структуроване стиснення | Автоматичне витягування decided/learned/completed/next_steps |
| Причинне міркування | Виводить cause (причина) / effect (наслідок) |
| 3-двигунний пошук | Вектор + FTS5 + Причинний ланцюг |
| Читабельна Wiki | Формат Obsidian Wiki |
| Теги типу | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Швидкий старт

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Ми обговорили систему пам'яті, вирішили використовувати 4-шарову структуру"
python gbrain.py causal "память"
```

## Подяки

Натхненно [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Ліцензія

MIT License
