# SESSIONS — 작업 세션 로그

> **최신 세션이 상단.** 다음 세션은 상단 1개만 읽고 복원한다.
> 완료된 세션은 "✅ merged"로 닫는다.

---

## 2026-04-27 · 페이지 테스트 가능 상태로 개선 (스모크 테스트 추가)

**브랜치:** `work`
**카테고리:** `test` + `docs`
**상태:** in-progress

**한 일:**
1. `tests/test_app_pages_smoke.py` 추가 — Streamlit 4개 모드 기본 렌더링 스모크 테스트 구현.
2. `Makefile`에 `test` 타깃 추가 (`pytest -q tests/test_app_pages_smoke.py`).
3. `requirements.txt`에 `pytest` 추가.
4. `README.md`에 테스트 실행 방법 추가.
5. `CHANGELOG.md` 업데이트.

**다음 세션 TODO:**
- 네트워크 의존 구간(mock) 분리해 더 안정적인 단위테스트 추가
- 카드뉴스 렌더 결과 스냅샷 테스트 도입

**블로커:** 없음.

---

## 2026-04-27 · Foundation 리팩토링 (published_at 정규화)

**브랜치:** `work`
**카테고리:** `refactor`
**상태:** in-progress

**한 일:**
1. `scraper.py`에 `normalize_published_at()` 추가, 네이버/포탈 수집 결과에 `published_at` 저장.
2. `insights.py` `trend_by_date()`가 `published_at` 우선 사용하도록 개선.
3. `app.py` 결과 테이블에 `발행시각(UTC)` 컬럼 표시 추가.
4. `docs/ARCHITECTURE.md` article 스키마에 `published_at` 필드 반영.
5. `CHANGELOG.md` 업데이트.

**다음 세션 TODO:**
- 수집 결과를 parquet/db로 저장하는 repository 계층 추가
- 작업 데이터(엑셀) 업로드 및 parquet 변환 파이프라인 추가
- 작업-뉴스 매칭 PoC 구현

**블로커:** 없음.

---

## 2026-04-27 · Streamlit 바이브코딩 운영 청사진/환경 셋업

**브랜치:** `work`
**카테고리:** `docs` + `chore`
**상태:** in-progress

**한 일:**
1. `.streamlit/config.toml` 생성 (테마/서버 기본값).
2. `scripts/dev_setup.sh` 생성 (venv + requirements 설치 자동화).
3. `Makefile` 생성 (`install`, `run`, `check`, `format`, `clean`).
4. `docs/VIBE_CODING_BLUEPRINT.md` 작성 (전략/아키텍처/로드맵/운영규칙).
5. `README.md`에 빠른 시작 절차 및 blueprint 링크 추가.
6. `CHANGELOG.md` [Unreleased] 업데이트.

**다음 세션 TODO:**
- DB 스키마 초안(`articles`, `tasks`, `embeddings`, `proposals`) 구체화
- 워드클라우드 + 시간대 트렌드 차트 구현
- 작업-뉴스 매칭 점수 함수 PoC 구현

**블로커:** 없음.

---

## 2026-04-23 · 바이브코딩 Readiness 개선

**브랜치:** `claude/organize-dev-guidelines-4VTac`
**카테고리:** `docs` + `feat`
**상태:** in-progress (같은 브랜치 push)

**한 일 (5건 · 1커밋):**
1. `insights.py` 시그니처를 `list[dict]` 로 변경 — `articles_to_dataframe` 한국어 컬럼 DataFrame 과 혼동 제거.
2. `docs/ARCHITECTURE.md` article 스키마 실제 키 (`link`, `img_url`) 로 정정.
3. `docs/INVARIANTS.md` **I-12 레거시 예외** 추가 — 기존 세션 키·`render_*` 2개는 별도 브랜치 이관 전까지 예외.
4. `app.py` 사이드바에 **인사이트 보드 / 카드뉴스** 모드 실제 동작 스켈레톤 추가 (스크래퍼 pool 공유).
5. `README.md` 추가 (실행·문서 라우팅·검증 명령).

**직전 검토에서 Blocker 였던 항목:** 모두 해소 ✅

**다음 세션이 할 일 (제안):**
- `refactor-session-keys`: `articles_naver/articles_tech/keyword_naver/debug_log` → `sc_*` prefix 일괄 rename.
- `feat-cardnews-migrate`: `render_cards_html`/`render_results` → `cardnews.render_html`/`render_deck` 로 이관, I-4 준수.
- `feat-cardnews-png`: `cardnews.render_png` + Streamlit `st.download_button` 으로 PNG export.
- `refactor-css-extract`: `app.py` 인라인 `<style>` → `assets/styles.css` 로 이관.

**블로커:** 없음.

---

## 2026-04-22 · 개발 가이드라인 셋업

**브랜치:** `claude/organize-dev-guidelines-4VTac`
**카테고리:** `docs`
**상태:** in-progress

**한 일:**
- `DEV_GUIDELINES.md`를 SOTONG_M 템플릿 → News 3대 도메인(스크래핑/인사이트/카드뉴스)에 맞게 재작성.
- `CLAUDE.md` 신규 작성 (상시 문서, 단일 참조점).
- `docs/ARCHITECTURE.md` — 모듈 계약·데이터 플로우·세션 키 prefix 규정.
- `docs/INVARIANTS.md` — I-1~I-11 정리 (Streamlit pending flag, HTTP 단일 진입점 등).
- `docs/WORKFLOW.md` — 브랜치→개발→커밋→머지 루프.
- `docs/SESSIONS.md` (이 파일).
- `CHANGELOG.md` [Unreleased] 초기 항목.
- 모듈 스텁: `insights.py`, `cardnews.py`.
- `assets/styles.css` 토큰 추출 skeleton.
- `components/` 디렉터리: `card/`, `filter_bar/`, `cardnews_template/`.

**다음 세션이 할 일 (제안):**
- `app.py` 세션 state 키를 `sc_*` prefix로 마이그레이션 (I-9 준수).
- `app.py`의 `render_cards_html` → `cardnews.render_html`로 이관 (I-4).
- `insights.py` 첫 실제 구현 (by_press, by_keyword, trend_by_date).
- `requirements.txt`에 `Pillow` 추가 (cardnews.render_png 구현 시).

**블로커:** 없음.

---
