# CLAUDE.md — News 프로젝트 작업 규칙

> 이 파일은 Claude가 News 레포에서 작업할 때 가장 먼저 읽는 **유일한** 상시 문서다.
> 나머지 docs/는 필요할 때만 선택적으로 읽는다. (→ [`DEV_GUIDELINES.md`](./DEV_GUIDELINES.md))

## 도메인

뉴스 스크래퍼를 기반으로 한 3대 도메인을 개발한다:

1. **뉴스 스크래핑** (`scraper.py`) — 네이버 뉴스 + 사이트별 최신 기사 수집, 본문 enrich, 키워드 추출.
2. **인사이트 보드** (`insights.py`) — 수집 기사 집계·트렌드·언론사별 랭킹·키워드 클러스터.
3. **카드뉴스** (`cardnews.py`) — 기사 요약을 카드형 이미지/HTML로 렌더, 썸네일·export.

## 절대 규칙 (반드시 지킬 것)

1. **토큰 절약**: 수정 대상 파일만 읽어라. `app.py` 수정 요청에 `scraper.py`를 읽지 마라. (`DEV_GUIDELINES.md` §1)
2. **평탄 스크립트**: `app.py`는 위→아래 실행 흐름. 마크업/state 헬퍼는 도메인 모듈(`cardnews.py` 등)로 빼라.
3. **on_click 금지**: `if st.button():` → `_do_*` pending flag → `st.rerun()` 패턴만.
4. **HTTP 단일 진입점**: `scraper._build_session()` 외의 `requests.get/Session()` 금지.
5. **XSS 방어**: 세션에 들어가거나 `st.markdown(unsafe_allow_html=True)`로 나가는 모든 사용자/외부 문자열은 `html.escape()`.
6. **네임스페이스 분리**: `sc_*` (scraper), `ins_*` (insights), `cn_*` (cardnews), pending은 `_` prefix.
7. **main 직push 금지**: 모든 변경은 작업 브랜치 → PR → 머지.

## 읽기 라우팅 (작업별 최소 파일)

| 작업 | 읽을 파일 |
|---|---|
| 스크래핑 버그 | `scraper.py` |
| 인사이트 차트/집계 | `insights.py` |
| 카드뉴스 레이아웃/이미지 | `cardnews.py` (+ `assets/styles.css`) |
| UI/탭/상태 | `app.py` (+ `docs/INVARIANTS.md`) |
| CSS만 | `assets/styles.css` |
| 아키텍처 파악 | `docs/ARCHITECTURE.md` |

전체 라우팅 표는 [`DEV_GUIDELINES.md §3`](./DEV_GUIDELINES.md#3-라우팅-표).

## 커밋 전 체크리스트

```bash
python -m py_compile app.py scraper.py insights.py cardnews.py
grep -nE 'on_click\s*=' app.py                                 # 0
grep -nE 'requests\.(get|post|Session)\(' scraper.py           # 0 (ㅡ _build_session 내부는 예외)
```

커밋에는 다음이 함께 포함되어야 한다:
- `CHANGELOG.md` [Unreleased] 항목 추가
- `docs/SESSIONS.md` 상단 세션 기록
- 새 invariant 발생 시 `docs/INVARIANTS.md` 갱신

## 브랜치 네이밍

`<카테고리>-<설명>` — 슬래시 금지, 하이픈 구분.
카테고리: `fix`, `feat`, `refactor`, `style`, `docs`, `chore`.

예: `feat-insight-trend`, `fix-scraper-selector`, `style-cardnews-typography`.
