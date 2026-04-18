# CausaMem - 인과 기억 시스템

> AI Agent에게 평생의 기억을 | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | 한국어

---

## 프로젝트 배경

CausaMem은 독립적으로 개발된 AI Agent 기억 시스템입니다. 개발 완료 후 [Claude-Mem](https://github.com/thedotmack/claude-mem)을 참고하여 핵심 **AI 구조화 압축** 기능을 구현하고, **인과 추론** 능력을 확장했습니다.

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 4층 기억 구조 | 이벤트 → 타임라인 → 관계 체인 → 추상 요약 |
| AI 구조화 압축 | decided/learned/completed/next_steps 자동 추출 |
| 인과 추론 | cause(전인)/effect(결과) 자동 추정 |
| 듀얼 엔진 검색 | 벡터 + FTS5 전체문서 + 인과 체인 |
| 인간이 읽을 수 있는 Wiki | Obsidian Wiki 형식, 직접 읽기·수정 가능 |
| 타입 태그 | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## 빠른 시작

### 1. 클론

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
```

### 2. 의존성 설치

```bash
pip install requests
```

### 3. API Key 설정

```bash
export MINIMAX_API_KEY="your-minimax-key"
export SILICONFLOW_API_KEY="your-siliconflow-key"
```

### 4. 초기화

```bash
cd scripts/gbrain
python gbrain.py init
```

### 5. 사용법

```bash
# 구조화 압축과 함께 기억 쓰기
python gbrain.py put-structured memory-2026-04 "기억 시스템에 대해 논의하고 4층 구조를 채택하기로 했다"

# AI 압축 (구조화 출력 확인)
python gbrain.py compress "관찰 내용"

# 벡터 의미 검색
python gbrain.py query "기억 시스템"

# FTS5 전체문서 검색
python gbrain.py search "4층"

# 인과 체인 검색
python gbrain.py causal "기억 시스템"
```

## 감사 인사

본 프로젝트는 개발 과정에서 [Claude-Mem](https://github.com/thedotmack/claude-mem)을 참고했습니다:

| 기능 | 출처 | 설명 |
|------|------|------|
| AI 구조화 압축 | Claude-Mem | 자유 텍스트를 구조화 필드로 압축 |
| 필드 설계 | Claude-Mem | learned/completed/next_steps 필드 |
| 타입 태그 시스템 | Claude-Mem | 타입별 관찰 기록 정리 |

## 프로젝트 구조

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

## 라이선스

MIT License

## 작성자

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)

---

*기억을 가진 AI Agent를 위해 만들어졌습니다.*
