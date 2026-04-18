# CausaMem - 인과 기억 시스템

> AI Agent에게 평생의 기억을 | Causal Memory System for AI Agents

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | 한국어 | [繁體中文](README_zh-TW.md) | [Português](README_pt-BR.md) | [Español](README_es.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Русский](README_ru.md) | [Italiano](README_it.md) | [Polski](README_pl.md) | [Українська](README_uk.md) | [Tiếng Việt](README_vi.md) | [Indonesia](README_id.md) | [ไทย](README_th.md) | [हिन्दी](README_hi.md) | [Nederlands](README_nl.md) | [Türkçe](README_tr.md) | [Svenska](README_sv.md) | [Ελληνικά](README_el.md) | [Magyar](README_hu.md) | [Čeština](README_cs.md) | [Dansk](README_da.md) | [Norsk](README_no.md) | [Suomi](README_fi.md) | [Română](README_ro.md) | [العربية](README_ar.md) | [עברית](README_he.md) | [বাংলা](README_bn.md) | [اردو](README_ur.md) | [Português PT](README_pt-PT.md)

---

## 프로젝트 개요

CausaMem은 독립적인 AI Agent 기억 시스템입니다. 3개의 핵심 모듈로 구성:

| 모듈 | 설명 |
|------|------|
| 인과 기억(gbrain) | 구조화 압축 + 인과 추론 + 3종 검색 |
| Wiki 4층 구조 | 이벤트→타임라인→관계→추상 |
|做梦(크론) | 정기 인과 سلسلة + 추상 판단 |

## 3단계 아키텍처

```
시동 기억 → SOUL.md / USER.md / MEMORY.md
작업 기억 → memory/*.md + gbrain + wiki/
정기 실행 → 소정리(매일 2:30) + 대做梦(매주 목 3:00)
```

## 빠른 시작

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
pip install requests
cd scripts/gbrain
python gbrain.py init

# 기억 쓰기
python gbrain.py put-structured my-event "시스템 설계 논의, X 아키텍처 채택 결정"

# 검색
python gbrain.py causal "시스템 설계"  # 인과 검색
python gbrain.py query "설계"          # 벡터
python gbrain.py search "아키텍처"     # FTS5
```

## Cron설정 (做梦)

```bash
crontab -e

# 소정리: 매일 02:30
30 2 * * * cd /path/to/MHH-Causality-Memory && python scripts/dream.py small

# 대做梦: 매주 목 03:00
0 3 * * 4 cd /path/to/MHH-Causality-Memory && python scripts/dream.py big
```

## 감사의 말

[Claude-Mem](https://github.com/thedotmack/claude-mem)의 AI 구조화 압축을 참고했습니다.

## 라이선스

MIT License

## 작성자

- [Vinson](https://github.com/MaiHHConnect)
- [牛馬2号](https://github.com/openclaw) (AI Agent)
