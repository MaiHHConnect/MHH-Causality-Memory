# CausaMem - Причинная Система Памяти

> Дайте вашему ИИ-агенту пожизненную память | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | Русский | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## Обзор

CausaMem — независимая система памяти для ИИ-агентов с тремя основными модулями:

| Модуль | Описание |
|--------|---------|
| Причинная память (gbrain) | Структурированное сжатие + Причинное рассуждение + 3 режима поиска |
| Wiki 4 слоя | События→Временная шкала→Отношения→Абстракции |
| Сны (Cron) | Периодическая причинная цепочка + Абстрактные суждения |

## Архитектура

```
Память запуска → SOUL.md / USER.md / MEMORY.md
Рабочая память → memory/*.md + gbrain + wiki/
Периодическое выполнение → Малая организация(ежедневно 02:30) + Большой сон(еженедельно чт 03:00)
```

## Быстрый старт

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# Сохранить
python gbrain.py put-structured my-event "Обсудили дизайн системы, решили использовать архитектуру X"

# Искать
python gbrain.py causal "дизайн системы"  # Причинный
python gbrain.py query "дизайн"           # Вектор
python gbrain.py search "архитектура"    # FTS5
```

## Настройка Cron (Сны)

```bash
crontab -e

# Малая организация: Ежедневно 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# Большой сон: Еженедельно чт 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## Благодарности

Вдохновлено [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Лицензия

MIT License

## Авторы

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
