# CausaMem - 因果記憶システム

> AI Agentに生涯の記憶を | Causal Memory System for AI Agents

---

## プロジェクト概要

CausaMemは**独立開発**のAI Agent記憶システム。7つのコア機能：

| 機能 | 説明 |
|------|------|
| 因果推論 | cause（前因）/ effect（后果）を自動推断 |
| AI構造化圧縮 | decided/learned/completed/next_steps/concepts自動抽出 |
| 双エンジン検索 | 向量 + FTS5 + 因果チェーン |
| Wiki 4層構造 | events/timeline/relations/_dream |
| 做夢抽象总结 | Cron定期（毎日2:30/毎週木3:00）|
| タイプタグ | DECISION/INSIGHT/BUG/FEATURE/CHANGE/DAILY |
| マルチAgent共有 | ファイルシステム共有 |

## クイックスタート

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init
python gbrain.py put-structured my-event "システム設計について議論"
python gbrain.py causal "システム設計"
```

## Cron設定

```bash
crontab -e
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## ライセンス

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
