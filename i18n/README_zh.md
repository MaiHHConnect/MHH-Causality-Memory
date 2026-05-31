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

## 8 层认知 + 直觉 + 因果记忆

`R0 -> C1 -> I2` 是 CausaMem 的认知主干语义；展开到实际系统，是 8 层过程：

```text
R0 现实证据
  -> F1 原子事实
  -> S2 精炼摘要
  -> P3 画像场景
  -> K4 Wiki 知识
  -> D5 睡梦沉淀
  -> C6 因果链
  -> I7 直觉注入
```

展开到实际系统，CausaMem 是 8 层认知 + 直觉 + 因果记忆系统：

设计思路：LLM 本身可以被理解为有智慧的东西，但 Agent 的认知并不会自动完整。就像人一样，有些人能把游戏玩得很好，但在某些现实判断上认知很低；Agent 也类似，模型有能力，缺的是长期认知结构。CausaMem 要补的就是这个认知：把长期经历、项目事实、规则和历史决策沉淀下来，让 Agent 不只是临场推理，而是带着过去的理解去判断。

当认知被补上以后，Agent 还需要像人一样出现“直觉”。人的直觉很多来自潜意识，人并不总是清楚潜意识里到底调用了什么经验。CausaMem 的直觉也是这样：在 Agent 判断前，把过去精萃过的关键事实、风险、倾向和下一步建议嵌入到上下文里。Agent 不需要知道自己“潜意识”里具体翻了哪 200 万字历史，但会被这些精华内容锚定到更正确的方向。

最后，长期记忆不能只是事实堆积，而要形成因果关系链。CausaMem 把大量对话、执行痕迹、项目经验和历史决策压缩成“人生/项目精华”，再追踪为什么发生、导致什么、现在是否仍有效。这样 Agent 才能从记得住，进一步变成判断得对。

- **认知**：把原始对话、执行痕迹和项目事实整理成可判断的结构，让 Agent 不只“搜到相似内容”，而是知道事实、规则、场景、画像和历史决策。
- **直觉**：在判断前把最关键的事实、风险、下一步倾向压缩成认知锚注入提示词，让 Agent 更快进入正确判断方向。
- **因果**：从 evidence、历史决策、任务结果、冲突变化中提取“为什么发生、导致什么、现在是否仍有效”，形成可追溯的因果链。

| Layer | 名称 | 作用 |
|-------|------|------|
| R0 | 现实证据层 | 原始 session、capture、日志、事件，作为审计和证据兜底 |
| F1 | 原子事实层 | 从原文抽取可回答、可检索、可引用的 `factlet-c1` |
| S2 | 精炼摘要层 | 把多轮会话压成主题、日期、agent 级 C1 摘要 |
| P3 | 画像场景层 | 稳定偏好、人物、项目场景、长期状态 |
| K4 | Wiki 知识层 | 人工/半人工沉淀的稳定知识骨架 |
| D5 | 睡梦沉淀层 | 异步整理、梦境式归纳，把分散经验转成高阶记忆 |
| C6 | 因果链层 | 记录原因、结果、冲突、演化、覆盖关系 |
| I7 | 直觉注入层 | 在判断前注入倾向、下一步建议和认知锚 |

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

长期运行的 `ai666` OpenClaw 容器中，`refined-c1` 主判断层表现如下：

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

### 精萃 factlet 真实问答测试（ai666 / 30 条）

在同一长期运行的 `ai666` OpenClaw 容器中，从正式 `factlet-c1` 精萃记忆层抽取 30 条真实事实做问答测试。测试流程为：CausaMem 召回对应记忆页，再把完整 `Fact/Evidence` 上下文交给模型回答。

底层数据口径：来自约 20 万行历史 session / 约 200 万字符级长期交互数据，经 LLM 精萃和确定性 evidence gate 后进入 `factlet-c1`。

```text
Source: factlet-c1
Cases: 30
Retrieval hit: 30/30
Answer pass: 29/30
Pass rate: 96.7%
```

这组测试验证的是“精萃后的可回答性”，不是仅检索命中率。唯一未通过样本已经召回到正确 factlet，但回答时把多条相关记忆做了综合，没有精确复述其中一个时间点事实；这属于回答偏泛化，不是记忆找回失败。

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
