# CausaMem - نظام الذاكرة السببي

> امنح وكيل الذكاء الاصطناعي الخاص بك ذاكرة مدى الحياة | نظام الذاكرة السببي لوكلاء الذكاء الاصطناعي

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [العربية](README_ar.md)

---

## الخلفية

CausaMem هو نظام ذاكرة مستقل لوكلاء الذكاء الاصطناعي. بعد إكمال التطوير، استلهمنا من [Claude-Mem](https://github.com/thedotmack/claude-mem) ونفذنا وظيفة **الضغط الهيكلي المدعوم بالذكاء الاصطناعي** الأساسية، مع التوسع في **الاستدلال السببي**.

## الميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| ذاكرة من 4 طبقات | الأحداث → الجدول الزمني → العلاقات → الملخصات |
| ضغط هيكلي بالذكاء الاصطناعي | استخراج تلقائي لـ decided/learned/completed/next_steps |
| الاستدلال السببي | يستنتج cause (السبب) / effect (النتيجة) |
| بحث بـ 3 محركات | متجه + FTS5 + السلسلة السببية |
| ويكي مقروء | تنسيق Obsidian Wiki |
| علامات النوع | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## البدء السريع

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "ناقشنا نظام الذاكرة، قررنا استخدام هيكل من 4 طبقات"
python gbrain.py causal "الذاكرة"
```

## الشكر والتقدير

مستوحى من [Claude-Mem](https://github.com/thedotmack/claude-mem).

## الترخيص

MIT License
