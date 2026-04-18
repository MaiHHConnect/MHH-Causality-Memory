# CausaMem - 因果記憶系統

> 讓 AI Agent 擁有一生的記憶 | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | 繁體中文

---

## 專案背景

CausaMem 是獨立的 AI Agent 記憶系統。在開發完成後，我們參考了 [Claude-Mem](https://github.com/thedotmack/claude-mem)，借鑒並實現了其核心的 **AI 結構化壓縮** 功能，并在此基礎上擴展了 **因果推理** 能力。

## 核心特性

| 特性 | 說明 |
|------|------|
| 四層記憶結構 | 事件 → 時間線 → 關係鏈 → 抽象總結 |
| AI 結構化壓縮 | 自動提取 decided/learned/completed/next_steps |
| 因果推理 | 自動推斷 cause（前因）/ effect（後果） |
| 雙引擎檢索 | 向量語義搜索 + FTS5 全文搜索 + 因果鏈搜索 |
| Wiki 人類可讀 | Obsidian Wiki 格式，可直接閱讀修改 |
| 類型標籤 | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## 快速開始

```bash
# 克隆
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory

# 寫入帶結構化壓縮的記憶
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "討論記憶系統，決定採用四層結構"

# 因果鏈搜索
python gbrain.py causal "記憶系統"
```

## 借鑒說明

本專案參考了 [Claude-Mem](https://github.com/thedotmack/claude-mem) 的 AI 結構化壓縮設計。

## 授權

MIT License

## 作者

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2號](https://github.com/openclaw) (AI Agent)
