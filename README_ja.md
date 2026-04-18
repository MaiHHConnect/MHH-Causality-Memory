# CausaMem - 因果記憶システム

> AI Agentに生涯の記憶を | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | 日本語 | [한국어](README_ko.md) | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## プロジェクト概要

CausaMemは独立したAI Agent記憶システム。3つのコアモジュールで構成：

| モジュール | 説明 |
|-----------|------|
| 因果記憶(gbrain) | 構造化圧縮 + 因果推論 + 3種検索 |
| Wiki 4層構造 | イベント→タイムライン→関係→抽象 |
| 做梦(クロン) | 定期因果串線 + 抽象判断 |

## 3層アーキテクチャ

```
起動記憶 → SOUL.md / USER.md / MEMORY.md
作業記憶 → memory/*.md + gbrain + wiki/
定期実行 → 小整理(毎日2:30) + 大做梦(毎週木3:00)
```

## クイックスタート

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# 記憶の書き込み
python gbrain.py put-structured my-event "システム設計について議論、Xアーキテクチャ採用を決定"

# 検索
python gbrain.py causal "システム設計"  # 因果検索
python gbrain.py query "設計"          # ベクター
python gbrain.py search "アーキテクチャ" # FTS5
```

## Cron設定（做梦）

```bash
crontab -e

# 小整理：毎日 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# 大做梦：毎週木曜 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## 謝辞


## ライセンス

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
