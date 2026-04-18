# CausaMem - কারণ মেমোরি সিস্টেম

> আপনার AI এজেন্টকে আজীবন স্মৃতি দিন | AI এজেন্টদের জন্য কারণ মেমোরি সিস্টেম

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [বাংলা](README_bn.md)

---

## প্রেক্ষাপট

CausaMem হল AI এজেন্টদের জন্য একটি স্বাধীন মেমোরি সিস্টেম। উন্নয়ন সম্পন্ন করার পরে, আমরা [Claude-Mem](https://github.com/thedotmack/claude-mem) কে রেফারেন্স করেছি এবং এর মূল **AI-স্ট্রাকচার্ড কম্প্রেশন** ফিচার বাস্তবায়ন করেছি, **কারণ-যুক্তি** দিয়ে প্রসারিত।

## মূল বৈশিষ্ট্য

| বৈশিষ্ট্য | বিবরণ |
|---------|--------|
| 4-স্তর মেমোরি | ইভেন্ট → টাইমলাইন → সম্পর্ক → সারসংক্ষেপ |
| AI-স্ট্রাকচার্ড কম্প্রেশন | decided/learned/completed/next_steps স্বয়ংক্রিয়ভাবে বের করে |
| কারণ-যুক্তি | cause (কারণ) / effect (প্রভাব) অনুমান করে |
| 3-ইঞ্জিন সার্চ | ভেক্টর + FTS5 + কারণ শৃঙ্খল |
| পাঠযোগ্য Wiki | Obsidian Wiki ফরম্যাট |
| টাইপ ট্যাগ | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## দ্রুত শুরু

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "আমরা মেমোরি সিস্টেম নিয়ে আলোচনা করেছি, 4-স্তর কাঠামো ব্যবহার করার সিদ্ধান্ত নিয়েছি"
python gbrain.py causal "স্মৃতি"
```

## স্বীকৃতি

[Claude-Mem](https://github.com/thedotmack/claude-mem) থেকে অনুপ্রাণিত।

## লাইসেন্স

MIT License
