# CausaMem - Nedensel Bellek Sistemi

> AI Agentinize ömür boyu bellek verin | AI Ajanları için Nedensel Bellek Sistemi

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Türkçe](README_tr.md)

---

## Arka Plan

CausaMem, AI Ajanları için bağımsız bir bellek sistemidir. Geliştirme tamamlandıktan sonra, [Claude-Mem](https://github.com/thedotmack/claude-mem) referans aldık ve çekirdek **AI yapılandırılmış sıkıştırma** işlevini uyguladık, **nedensel akıl yürütme** ile genişlettik.

## Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 4 katmanlı bellek | Olaylar → Zaman Çizelgesi → İlişkiler → Özetler |
| AI yapılandırılmış sıkıştırma | decided/learned/completed/next_steps otomatik çıkarma |
| Nedensel akıl yürütme | cause (neden) / effect (sonuç) çıkarımı |
| 3 motorlu arama | Vektör + FTS5 + Nedensel Zincir |
| Okunabilir Wiki | Obsidian Wiki formatı |
| Tür etiketleri | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Hızlı Başlangıç

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Bellek sistemini tartıştık, 4 katmanlı yapı kullanmaya karar verdik"
python gbrain.py causal "bellek"
```

## Teşekkürler

[Claude-Mem](https://github.com/thedotmack/claude-mem) ilham kaynağı olmuştur.

## Lisans

MIT License
