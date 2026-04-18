# CausaMem - 因果記憶システム

> AI Agentに生涯の記憶を | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | 日本語 | [한국어](README_ko.md)

---

## プロジェクト背景

CausaMemは independently 開発されたAI Agent記憶システムです。開発完了後、[Claude-Mem](https://github.com/thedotmack/claude-mem)を参考に、その中核となる**AI構造化圧縮**機能を実装し、さらに**因果推論**能力を拡張しました。

## コア機能

| 機能 | 説明 |
|------|------|
| 4層記憶構造 | イベント → タイムライン → 関係チェーン → 抽象サマリー |
| AI構造化圧縮 | decided/learned/completed/next_steps を自動抽出 |
| 因果推論 | cause（前因）/ effect（結果） を自動推定 |
| デュアルエンジン検索 | ベクター + FTS5全文 + 因果チェーン |
| 人間が読めるWiki | Obsidian Wiki形式、直接閲覧・編集可能 |
| タイプタグ | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## クイックスタート

### 1. クローン

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
```

### 2. 依存関係インストール

```bash
pip install requests
```

### 3. API Key設定

```bash
export MINIMAX_API_KEY="your-minimax-key"
export SILICONFLOW_API_KEY="your-siliconflow-key"
```

### 4. 初期化

```bash
cd scripts/gbrain
python gbrain.py init
```

### 5. 使用方法

```bash
# 構造化圧縮付きで記憶を書き込み
python gbrain.py put-structured memory-2026-04 "記憶システムについて議論し、4層構造を採用することにした"

# AI圧縮（構造化出力を確認）
python gbrain.py compress "あなたの観測内容"

# ベクター意味検索
python gbrain.py query "記憶システム"

# FTS5全文検索
python gbrain.py search "4層"

# 因果チェーン検索
python gbrain.py causal "記憶システム"
```

## 謝辞

本プロジェクトは開発中に[Claude-Mem](https://github.com/thedotmack/claude-mem)を参照しました：

| 機能 | ソース | 説明 |
|------|--------|------|
| AI構造化圧縮 | Claude-Mem | フリーテキストを構造化フィールドに圧縮 |
| フィールド設計 | Claude-Mem | learned/completed/next_steps フィールド |
| タイプタグシステム | Claude-Mem | タイプ別観測記録整理 |

## プロジェクト構造

```
MHH-Causality-Memory/
├── README.md
├── README_en.md
├── README_ja.md
├── README_ko.md
├── docs/
├── scripts/
│   ├── setup.sh
│   └── gbrain/
│       ├── gbrain.py
│       └── ...
└── wiki/
```

## ライセンス

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)

---

*記憶を持つAI Agentのために建造されました。*
