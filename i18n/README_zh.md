# CausaMem - 因果记忆与认知锚定系统

> 让 AI Agent 拥有跨越长期项目的一生记忆。
> 在 Agent 判断前，先用事实、规则、历史决策、因果链和执行状态把它锚定住。

[返回主 README](../README.md)

## 它是什么

CausaMem 不是普通向量记忆库。

普通记忆系统通常是：

```text
用户提问 -> 向量搜索 -> 返回相似文本
```

CausaMem 是：

```text
捕获现实证据
-> 提取候选记忆
-> 大模型语义判断
-> CausaMem 确定性门禁
-> 写入长期因果记忆
-> 在 Agent 判断前注入认知锚
```

它的目标不是“搜到相似内容”，而是让 Agent 在回答前先知道发生过什么、为什么发生、过去怎么决定、现在执行状态如何、哪些规则不能违背。

## 三层认知锚定

```text
R0 现实证据层
  raw_events、Beads 执行状态、真实观测

C1 认知结构层
  memory_candidates、pages、causal_edges、scenes、profiles

I2 直觉注入层
  在 OpenClaw 判断前注入 causamem-cognitive-anchor
```

## 为什么比普通记忆强

普通向量记忆只看语义相似，容易出现旧日志抢排名、精确词漏召回、临时状态污染长期记忆、无法解释为什么这样判断。

CausaMem 同时使用：

```text
keyword
FTS
vector
lexical fallback
causal edges
recency
RRF 融合排序
MMR 去重
因果激活
```

当前 50 条真实项目记忆回归集：

```text
hit_rate: 1.000
MRR: 0.974
```

长期运行的 `ai666` OpenClaw 容器真实记忆库 2000 条召回测试：

```text
真实可评测 page: 3265
本次抽样: 2000
Overall hit@1: 0.5465
Overall hit@3: 0.6215
Overall hit@6: 0.6555
Overall MRR:   0.5888
```

总分包含大量 R0 原始日志、历史 Hy-Memory L0 和 OpenClaw 原始 capture，因此会被审计层噪声拉低。主判断层 `refined-c1` 的表现更能代表 CausaMem 0.17 的实际使用质量：

```text
refined-c1 n=872
hit@1: 0.9495
hit@3: 0.9817
hit@6: 0.9943
MRR:   0.9676
```

真实来源分项：

| Source | n | hit@1 | hit@3 | hit@6 | MRR |
|--------|---:|------:|------:|------:|----:|
| `refined-c1` | 872 | 0.9495 | 0.9817 | 0.9943 | 0.9676 |
| `memos-local` | 217 | 0.7281 | 0.9585 | 0.9770 | 0.8445 |
| `dream-c1` | 19 | 0.5789 | 0.7368 | 0.8947 | 0.6807 |
| `wiki-c1` | 205 | 0.3512 | 0.5512 | 0.6829 | 0.4707 |
| `session-file` | 518 | 0.0058 | 0.0328 | 0.0695 | 0.0255 |

结论：C1 精炼层已经稳定可用；R0 原始日志更适合作为审计证据，不适合作为主判断召回指标。

## OpenClaw 集成

CausaMem 通过两个 hook 接入 OpenClaw：

```text
before_prompt_build
  判断前自动召回并注入认知锚

agent_end
  自动捕获对话
  提取候选记忆
  调用 OpenClaw 主模型做门禁判断
  由 CausaMem 确定性验收
  只提交 approved 记忆
```

## Beads 边界

Beads 是执行追踪现实源，不是主记忆系统。

```text
Beads 负责：任务状态、依赖、审计轨迹
CausaMem 负责：长期因果记忆、认知锚定、判断前注入
```

## 写入门禁

大模型不能直接写库。它只输出 JSON 判断：

```text
approve
reject
scene
profile
conflict
```

CausaMem 再检查：

```text
证据必须来自原文
Profile 置信度 >= 0.75
临时状态不能写 Profile
冲突旧 Profile 时不覆盖
```

## 快速开始

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
/usr/bin/python3 scripts/gbrain/gbrain.py init
/usr/bin/python3 scripts/gbrain/gbrain.py doctor
```

生成认知锚：

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py anchor "回答前应该知道什么？"
```

运行回归评测：

```bash
/usr/bin/python3 scripts/gbrain/gbrain.py eval eval/gbrain_eval.jsonl
```

## Session 记忆精炼器

`scripts/gbrain/refine_sessions.py` 可以把长期运行产生的 session JSONL 离线压缩成 C1 认知结构页。

它不是把每条消息逐条发给 LLM，而是在本地规则式处理：

```text
session JSONL -> 抽取有效文本 -> agent 隔离 -> topic/date 分桶 -> refined-c1 -> CausaMem
```

示例：

```bash
python3 scripts/gbrain/refine_sessions.py \
  --agents-dir ~/.openclaw/agents \
  --gbrain scripts/gbrain/gbrain.py \
  --agent main \
  --max-files 10000 \
  --max-lines 10000
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--agents-dir` | 包含 `<agent>/sessions/*.jsonl` 的目录 |
| `--agent` | 只精炼一个 agent；不传则扫描全部 agent |
| `--max-files` | 每个 agent 最多读取多少 session 文件 |
| `--max-lines` | 每个 session 文件最多读取多少行 |
| `--dry-run` | 只统计，不写入 CausaMem |

生成的页面 slug 类似 `refined-session-main-memory-system-2026-05-31-xxxx`，页面正文带 `agent_id`、`topic`、`date` 和判断约束，适合把 R0 原始对话沉淀成 C1 主判断层。

## 安全说明

不要提交 API Key、GitHub Token、本地数据库、Beads runtime 数据或任何 credential。

使用环境变量：

```bash
export SILICONFLOW_API_KEY="..."
export MINIMAX_API_KEY="..."
```

## 一句话

CausaMem 是 Agent 的因果大脑：先看现实，再看历史，再看因果，再做判断。
