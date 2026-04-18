# CausaMem - Sistem Memori Kausal

> Berikan Agent AI Anda ingatan seumur hidup | Sistem Memori Kausal untuk Agent AI

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Indonesia](README_id.md)

---

## Latar Belakang

CausaMem adalah sistem memori independen untuk Agent AI. Setelah pengembangan selesai, kami mereferensikan [Claude-Mem](https://github.com/thedotmack/claude-mem) dan mengimplementasikan fungsi inti **kompresi terstruktur AI**, diperluas dengan **penalaran kausal**.

## Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| Memori 4 lapisan | Peristiwa → Linimasa → Hubungan → Ringkasan |
| Kompresi Terstruktur AI | Ekstrak decided/learned/completed/next_steps |
| Penalaran Kausal | Menyimpulkan cause (penyebab) / effect (akibat) |
| Pencarian 3 mesin | Vektor + FTS5 + Rantai Kausal |
| Wiki Terbaca | Format Obsidian Wiki |
| Tag Jenis | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Mulai Cepat

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Kami membahas sistem memori, memutuskan menggunakan struktur 4 lapisan"
python gbrain.py causal "memori"
```

## Kredit

Terinspirasi oleh [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Lisensi

MIT License
