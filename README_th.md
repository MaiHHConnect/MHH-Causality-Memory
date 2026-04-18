# CausaMem - ระบบความจำเชิงสาเหตุ

> มอบความจำตลอดชีวิตให้ AI Agent ของคุณ | ระบบความจำเชิงสาเหตุสำหรับ AI Agent

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [ไทย](README_th.md)

---

## ภูมิหลัง

CausaMem เป็นระบบความจำอิสระสำหรับ AI Agent หลังจากพัฒนาเสร็จ เราได้อ้างอิง [Claude-Mem](https://github.com/thedotmack/claude-mem) และนำฟีเจอร์หลัก **การบีบอัดแบบมีโครงสร้างด้วย AI** มาใช้ พร้อมขยายด้วย **การให้เหตุผลเชิงสาเหตุ**

## ฟีเจอร์หลัก

| ฟีเจอร์ | คำอธิบาย |
|---------|----------|
| ความจำ 4 ชั้น | เหตุการณ์ → ไทม์ไลน์ → ความสัมพันธ์ → สรุป |
| การบีบอัดแบบมีโครงสร้าง AI | แยก decided/learned/completed/next_steps อัตโนมัติ |
| การให้เหตุผลเชิงสาเหตุ | อนุมาน cause (สาเหตุ) / effect (ผลลัพธ์) |
| การค้นหา 3 เครื่องมือ | เวกเตอร์ + FTS5 + สายเชิงสาเหตุ |
| Wiki ที่อ่านได้ | รูปแบบ Obsidian Wiki |
| แท็กประเภท | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## เริ่มต้นอย่างรวดเร็ว

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "เราถกเถียงเรื่องระบบความจำ ตัดสินใจใช้โครงสร้าง 4 ชั้น"
python gbrain.py causal "ความจำ"
```

## เครดิต

ได้รับแรงบันดาลใจจาก [Claude-Mem](https://github.com/thedotmack/claude-mem).

## สิทธิ์การใช้งาน

MIT License
