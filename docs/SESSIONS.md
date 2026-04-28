# SESSIONS — 작업 세션 로그

> **최신 세션이 상단.** 다음 세션은 상단 1개만 읽고 복원한다.
> 완료된 세션은 "✅ merged"로 닫는다.

---

## 2026-04-28 · Refactor (후보/히스토리 로직 모듈화)

**브랜치:** `work`
**카테고리:** `refactor`
**상태:** in-progress

**한 일:**
1. `app_helpers.py` 추가 — 카드뉴스 후보 생성/중복체크/히스토리 JSON import/DataFrame 변환 유틸 분리.
2. `app.py`의 중복 로직(후보 추가, JSON import, 후보 테이블 생성)을 helper 호출로 치환.
3. `tests/test_app_helpers.py` 추가로 helper 함수 단위 검증.

**다음 세션 TODO:**
- `app.py` 화면별 renderer 함수 분리(모듈 단위)
- 제안 화면 상태관리 키(`pr_*`) prefix 표준화
- app 레이아웃/CSS 외부 파일 완전 분리

**블로커:** 없음.

---

## 2026-04-28 · Phase A 완료 정리 (MVP 완료)

**브랜치:** `work`
**카테고리:** `feat` + `docs`
**상태:** in-progress

**한 일:**
1. 카드뉴스 후보 관리 고도화(다중 삭제, 썸네일/발행일 표시).
2. 제안 히스토리 JSON에서 카드뉴스 후보 일괄 불러오기 기능 추가.
3. 제안 추천 데이터에 `img_url/date/published_at` 전달 필드 보강.
4. `docs/DEVELOPMENT_PHASES.md`에 Phase A 완료 상태를 명시.

**다음 세션 TODO (Phase B 시작):**
- 배치 스케줄링/재시도/실패로그 표준화
- 데이터 품질 지표(중복률/누락률) 대시보드
- 운영 관측성(수집 성공률/처리시간) 추가

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 8 (카드뉴스 후보 관리 UI)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. 카드뉴스 화면에 `카드뉴스 후보 관리` UI(목록/선택 삭제/전체 초기화) 추가.
2. 제안 연동 후보(`cardnews_candidates`)를 사용자 제어로 정리할 수 있게 개선.
3. 후보 목록을 테이블로 노출해 카드 제작 전 큐를 점검 가능하게 함.

**다음 세션 TODO:**
- 카드뉴스 후보에 썸네일/발행일 컬럼 추가
- 후보 선택 다중 삭제 지원
- 제안 히스토리에서 카드 후보 일괄 불러오기

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 7 (제안 → 카드뉴스 연동)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. 제안 화면에서 추천 기사별 `카드뉴스 후보로 추가` 액션 추가.
2. 세션 상태(`cardnews_candidates`)에 중복 제거하며 후보 적재.
3. 카드뉴스 화면이 제안 연동 후보 + 수집 기사 풀을 합쳐 렌더하도록 확장.
4. 카드뉴스 화면에 제안 연동 후보 건수 캡션 표시.

**다음 세션 TODO:**
- 카드뉴스 후보 목록 관리(삭제/초기화) UI 추가
- 제안 히스토리 상세 화면에서 카드 생성 바로가기 추가
- 추천 기사에 썸네일/발행일 보강

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 6 (최신성/출처 신뢰도 반영 + 이력 조회)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. `proposal_engine.py` 추천 점수에 최신성(`freshness_score`)과 출처 신뢰도(`source_score`) 반영.
2. 최종 기사 점수(`score`)를 relevance + freshness + source 가중합으로 계산.
3. `proposal_engine.py`에 최근 제안 아티팩트 목록 함수(`list_recent_proposal_artifacts`) 추가.
4. `app.py` 제안 화면 상세에 점수 분해(rel/fresh/src) 표시 및 최근 아티팩트 이력 테이블 추가.
5. `tests/test_proposal_engine.py`를 점수/이력 시나리오까지 확장.

**다음 세션 TODO:**
- 카드뉴스에서 제안 추천 기사 바로 선택 기능
- 제안 히스토리 상세 뷰(파일 열기/재사용) 추가
- 매칭 점수 설명 tooltip 개선

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 5 (우선순위 가중치 + 제안서 템플릿 분리)

**브랜치:** `main`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. `proposal_engine.py`에 작업 우선순위 점수(`priority_score`) 로직 추가(효과/위험/난이도 가중치).
2. 제안서 Markdown 템플릿을 `executive` / `execution` 2종으로 분리.
3. 제안 아티팩트 저장 시 JSON + 템플릿별 MD 2개를 함께 저장하도록 확장.
4. `app.py` 제안 화면에 우선순위 점수 컬럼/템플릿 선택 다운로드 UI 반영.
5. `tests/test_proposal_engine.py` 검증 시나리오 업데이트.

**다음 세션 TODO:**
- 카드뉴스 화면에서 제안서 추천 기사 바로 가져오기
- 추천 스코어에 기사 최신성/출처 신뢰도 반영
- 제안 결과 히스토리 조회(로컬 파일 목록) UI 추가

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 4 (제안서 아티팩트 저장/다운로드)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. `proposal_engine.py`에 `proposals_to_markdown`, `save_proposals_artifacts` 추가.
2. `app.py` 제안 화면에서 생성 결과를 세션에 보관하고 JSON/Markdown 다운로드 제공.
3. 생성 결과를 `data/artifacts/proposals/YYYY-MM-DD/`에 JSON/MD로 저장하고 경로 표시.
4. `tests/test_proposal_engine.py`에 아티팩트 저장/마크다운 렌더 검증 추가.

**다음 세션 TODO:**
- 추천 점수에 작업 난이도/효과 가중치 추가
- 제안서 템플릿(경영진 요약/현장 실행안) 2종으로 분리
- 카드뉴스 화면과 제안 화면 데이터 연동

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 3 (작업-뉴스 매칭 제안 화면)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. `proposal_engine.py` 추가 — 작업-뉴스 토큰 중첩 기반 스코어링/추천(`suggest_for_tasks`) 구현.
2. `shipyard_store.py`에 최신 작업 Parquet 로더(`load_latest_shipyard_tasks`) 추가.
3. `app.py`에 신규 모드 `🤝 자동화 과제 제안` 추가(요약표 + 작업별 추천 상세).
4. `tests/test_proposal_engine.py` 추가 및 `tests/test_app_pages_smoke.py` 신규 메뉴 옵션 반영.
5. `README.md`, `CHANGELOG.md` 업데이트.

**다음 세션 TODO:**
- 제안 결과를 파일(JSON/MD)로 저장하는 export 기능 추가
- 추천 스코어에 비용/난이도/효과 가중치 반영
- 카드뉴스와 제안서 연결(선택 기사로 카드 자동 생성)

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 Step 2 (조선소 작업 데이터 업로드 파이프라인)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. `shipyard_store.py` 추가 — Excel 업로드 raw 저장, 필수 컬럼 검증, Parquet 저장 파이프라인 구현.
2. `app.py`에 신규 모드 `🏭 조선소 작업 데이터` 추가 및 업로드 UI/검증 결과 표시 연결.
3. `tests/test_shipyard_store.py` 추가 — 성공/필수 컬럼 누락 케이스 검증.
4. `tests/test_app_pages_smoke.py`에 신규 메뉴 옵션 검증 추가.
5. 엑셀 엔진 미설치(openpyxl) 환경에서도 사용자 안내 에러를 반환하도록 처리.

**다음 세션 TODO:**
- 업로드된 조선소 데이터 미리보기/필터링 UI 추가
- 뉴스-작업 매칭 스코어링 함수(룰 기반) 1차 구현
- 제안서 생성 템플릿과 근거 링크 연결

**블로커:** 없음.

---

## 2026-04-28 · Phase 1 착수 (Local First 저장소 시작)

**브랜치:** `work`
**카테고리:** `feat`
**상태:** in-progress

**한 일:**
1. `local_store.py` 추가 — 뉴스 수집 결과를 `jsonl + parquet`로 저장하는 로컬 저장소 유틸 구현.
2. `app.py` 시작 시 `naver`/`tech` 최신 로컬 배치를 자동 로드하도록 연결.
3. `app.py`에서 뉴스 수집 성공 시 자동 로컬 저장 + 저장 경로 캡션 노출.
4. `CHANGELOG.md` 업데이트.
5. `NewsRepository`/`LocalNewsRepository` 추상화 도입으로 저장소 스위치 준비.
6. `tests/test_local_store.py` 추가로 Local 저장/복구 동작 검증.

**다음 세션 TODO:**
- Shipyard Excel 업로드/검증/Parquet 저장 파이프라인 1차 구현
- `data/` 경로/스키마 검증 테스트 추가

**블로커:** 없음.

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
