# CausaMem - 인과 기억 시스템

> AI Agent에게 평생의 기억을 | Causal Memory System for AI Agents

---

## 프로젝트 개요

CausaMem은 **독립 개발**된 AI Agent 기억 시스템입니다. 7가지 핵심 기능:

| 기능 | 설명 |
|------|------|
| 인과 추론 | cause(전인)/effect(결과) 자동 추정 |
| AI 구조화 압축 | decided/learned/completed/next_steps/concepts 자동 추출 |
| 듀얼 엔진 검색 | 벡터 + FTS5 + 인과 체인 |
| Wiki 4층 구조 | events/timeline/relations/_dream |
|做梦 추상 총화 | Cron 정기(매일 2:30/매주 목 3:00) |
| 타입 태그 | DECISION/INSIGHT/BUG/FEATURE/CHANGE/DAILY |
| 멀티Agent 공유 | 파일시스템 공유 |

## 빠른 시작

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init
python gbrain.py put-structured my-event "시스템 설계 논의"
python gbrain.py causal "시스템 설계"
```

## Cron설정

```bash
crontab -e
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## 라이선스

MIT License

## 작성자

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
