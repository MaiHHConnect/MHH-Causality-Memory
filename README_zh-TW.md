# CausaMem - 因果記憶系統

> 讓 AI Agent 擁有一生的記憶 | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | 繁體中文 | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## 專案背景

CausaMem 是獨立的 AI Agent 記憶系統，包含三大模組：

| 模組 | 說明 |
|------|------|
| 因果記憶(gbrain) | 結構化壓縮 + 因果推論 + 3種檢索 |
| Wiki 4層結構 | 事件→時間線→關係→抽象 |
| 做夢(定時) | 定期因果串線 + 抽象判斷 |

## 架構

```
啟動記憶 → SOUL.md / USER.md / MEMORY.md
工作記憶 → memory/*.md + gbrain + wiki/
定時執行 → 小整理(每日2:30) + 大做夢(每週四3:00)
```

## 快速開始

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# 寫入記憶
python gbrain.py put-structured my-event "討論系統設計，決定採用X架構"

# 檢索
python gbrain.py causal "系統設計"  # 因果鏈
python gbrain.py query "設計"       # 向量
python gbrain.py search "架構"     # FTS5
```

## Cron設定（做夢）

```bash
crontab -e

# 小整理：每日 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# 大做夢：每週四 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```
## 授權

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2號](https://github.com/openclaw) (AI Agent)
