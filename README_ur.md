# CausaMem - وجہی یادداشت نظام

> اپنے AI ایجنٹ کو زندگی بھر کی یاد دیں | AI ایجنٹس کے لیے وجہی یادداشت نظام

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [اردو](README_ur.md)

---

## پس منظر

CausaMem AI ایجنٹس کے لیے ایک آزاد یادداشت نظام ہے۔ ترقی مکمل ہونے کے بعد، ہم نے [Claude-Mem](https://github.com/thedotmack/claude-mem) کا حوالہ دیا اور اس کی بنیادی **AI-ساختہ کمپریشن** فنکشن نافذ کی، **وجہی استدلال** کے ساتھ وسعت دی۔

## اہم خصوصیات

| خصوصیت | وضاحت |
|--------|--------|
| 4-طبقہ یادداشت | واقعات → ٹائم لائن → تعلقات → خلاصے |
| AI-ساختہ کمپریشن | decided/learned/completed/next_steps خودکار نکالنا |
| وجہی استدلال | cause (وجہ) / effect (نتیجہ) اخذ کرنا |
| 3-انجن تلاش | ویکٹر + FTS5 + وجہی سلسلہ |
| قابل پڑھ Wiki | Obsidian Wiki فارمیٹ |
| قسم کے ٹیگز | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## تیز آغاز

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "ہم نے یادداشت نظام پر تبادلہ خیال کیا، 4-طبقہ ساخت استعمال کرنے کا فیصلہ کیا"
python gbrain.py causal "یادداشت"
```

## قدردانی

[Claude-Mem](https://github.com/thedotmack/claude-mem) سے متاثرہ۔

## لائسنس

MIT License
