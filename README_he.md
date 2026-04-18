# CausaMem - מערכת זיכרון סיבתית

> תן לסוכן ה-AI שלך זיכרון לכל החיים | מערכת זיכרון סיבתית לסוכני AI

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [עברית](README_he.md)

---

## רקע

CausaMem הוא מערכת זיכרון עצמאית לסוכני AI. לאחר הפיתוח, התייחסנו אל [Claude-Mem](https://github.com/thedotmack/claude-mem) ויישמנו את הפונקציה המרכזית שלו **דחיסה מובנית עם AI**, עם הרחבה ל**הסקת סיבות**.

## תכ机ות עיקריות

| תכונה | תיאור |
|--------|--------|
| זיכרון 4 שכבות | אירועים → ציר זמן → יחסים → סיכומים |
| דחיסה מובנית AI | חילוץ אוטומטי של decided/learned/completed/next_steps |
| הסקת סיבות | מסיק cause (סיבה) / effect (תוצאה) |
| חיפוש 3 מנועים | וקטור + FTS5 + שרשרת סיבתית |
| Wiki קריא | פורמט Obsidian Wiki |
| תגיות סוג | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## התחלה מהירה

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "דנו על מערכת הזיכרון, החלטנו להשתמש במבנה 4 שכבות"
python gbrain.py causal "זיכרון"
```

## הוקרה

בהשראת [Claude-Mem](https://github.com/thedotmack/claude-mem).

## רישיון

MIT License
