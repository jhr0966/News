# News 개발 지침

> CLAUDE.md의 규칙을 정리한 개발자용 요약 문서.
> 3대 도메인: **뉴스 스크래핑 · 인사이트 보드 · 카드뉴스**

## 1. 토큰 절약 규칙 (최우선)

1. **코드 파일은 수정 대상만 읽는다.** "전체 파악"을 위해 모든 파일을 읽지 마라.
2. **docs/는 라우팅 표에 해당하는 문서만 1개 읽는다.** 2개 이상 동시에 읽지 마라.
3. **SESSIONS.md는 상단 1개 세션만.** 전체를 읽지 마라.
4. **단순 수정은 해당 파일만 읽고 바로 수정.** 관련 없는 파일 탐색 금지.
5. **읽기 전에 자문**: "이 파일을 안 읽으면 작업이 불가능한가?" — 아니면 읽지 마라.

## 2. 파일별 역할 및 읽는 시점

| 파일 | 역할 | 언제 읽나 |
|---|---|---|
| `app.py` | Streamlit 엔트리 (평탄 스크립트) | 페이지/탭/네비게이션/세션상태 작업 시 |
| `scraper.py` | 네이버/사이트 스크래핑 · 본문 enrich · 키워드 추출 | 크롤링·파서·세션·셀렉터 작업 시 |
| `insights.py` | 인사이트 보드 (집계·트렌드·랭킹) | 통계·차트·대시보드 작업 시 |
| `cardnews.py` | 카드뉴스 생성 (레이아웃·이미지·export) | 카드 템플릿·이미지 합성 작업 시 |
| `assets/styles.css` | 전역 CSS 토큰·컴포넌트 스타일 | CSS 수정 시에만 |
| `components/` | HTML 부분 뷰 (카드/배지/필터바 등) | 해당 위젯 마크업 수정 시 |
| `docs/INVARIANTS.md` | state/위젯 불변식 | state·widget·세션키 작업 시에만 |
| `docs/ARCHITECTURE.md` | 모듈 경계·데이터 플로우 | 아키텍처 이해 필요 시에만 |
| `docs/WORKFLOW.md` | 멀티에이전트 워크플로 | 에이전트 협업 시에만 |
| `docs/SESSIONS.md` | 세션 로그 | 이전 세션 복원 시 (상단 1개만) |
| `CHANGELOG.md` | 릴리스 이력 | 릴리스/버전 작업 시에만 |

## 3. 라우팅 표

| 작업 | 읽을 파일 (이것만) |
|---|---|
| 스크래핑 셀렉터/파서 버그 | `scraper.py` |
| 새 언론사 추가 | `app.py` (`TARGET_SITES`) + `scraper.py` (`fetch_latest_tech_news`) |
| 키워드/태그 로직 | `scraper.py` (`extract_keywords`) |
| 인사이트 보드 집계/차트 | `insights.py` |
| 카드뉴스 템플릿/이미지 | `cardnews.py` + `assets/styles.css` |
| 카드 HTML 마크업 | `components/card/*.html` + `assets/styles.css` |
| 페이지/탭/세션 상태 | `app.py` + `docs/INVARIANTS.md` |
| CSS만 수정 | `assets/styles.css` |
| CSV/엑셀 export | `scraper.py` (`articles_to_dataframe`) + `app.py` |
| 아키텍처 파악 | `docs/ARCHITECTURE.md` |
| 이전 세션 복원 | `docs/SESSIONS.md` (상단 1개) |
| 릴리스/버전 | `CHANGELOG.md` |
| 단순 문답 | **CLAUDE.md 만으로 충분** |

## 4. 불변 규칙 요약

자세한 내용: [`docs/INVARIANTS.md`](./docs/INVARIANTS.md)

- **I-1** 스크래핑 결과 쓰기는 `_search_pending` 플래그로 다음 run 최상단에서만.
- **I-2** 위젯 state 쓰기는 최상단 pending-flag 핸들러에서만.
- **I-3** `on_click=` 금지. `if st.button():` + `_do_*` 플래그 + `st.rerun()`.
- **I-4** `app.py`는 평탄 스크립트. 카드 마크업은 `cardnews.py` / `components/`로.
- **I-5** 스크래핑 결과는 도메인 필터(`_same_root_domain`) 통과 후에만 state에 저장.
- **I-6** 외부 HTTP는 항상 `_build_session()` 사용 (retry·UA 로테이션).
- **I-7** 본문 enrich는 `enrich_articles_parallel` 진입점만 사용.
- **I-8** HTML을 세션에 넣을 때는 `html.escape()`로 XSS 방어.
- **I-9** 네임스페이스: 스크래핑 `sc_`, 인사이트 `ins_`, 카드뉴스 `cn_`, pending 은 `_` prefix.
- **I-10** 카드뉴스 이미지 합성은 `cardnews.render_png()`가 유일한 진입점.

## 5. 브랜치 전략

- **`main`**: 안정 코드만. 직접 push 금지. 머지만 허용.
- **작업 브랜치**: 수정 요청마다 별도 브랜치. Streamlit Cloud 테스트 후 main 머지.
- **네이밍**: `<카테고리>-<설명>` (슬래시 금지, 하이픈 구분)
  - `fix-scraper-selector`
  - `feat-insight-trend`
  - `feat-cardnews-export`
  - `style-unify-cards`
  - `refactor-session-keys`
  - `docs-invariants`

## 6. 검증 (커밋 전 필수)

```bash
python -m py_compile app.py scraper.py insights.py cardnews.py
grep -nE 'on_click\s*=' app.py                                 # 0 매치
grep -nE 'requests\.get\(|requests\.Session\(\)' scraper.py    # 0 매치 (반드시 _build_session 경유)
```

## 7. 변경 시 갱신

작업 브랜치의 같은 커밋에서 다음을 함께 업데이트:

1. `CHANGELOG.md` [Unreleased] 섹션에 엔트리 추가
2. `docs/SESSIONS.md` 상단에 세션 항목 추가
3. 새로운 invariant 발생 시 → `docs/INVARIANTS.md`에 추가

## 8. 스택

- **Streamlit** ≥ 1.32 · `app.py` 단일 평탄 스크립트
- **BeautifulSoup4 + lxml** (fallback: `html.parser`) · `scraper.py`
- **Pandas** · 집계/테이블 (`insights.py`, `articles_to_dataframe`)
- **Pillow** (선택) · 카드뉴스 이미지 렌더 (`cardnews.py`)
- **`assets/styles.css`** · Noto Serif KR · IBM Plex Sans KR
- **배포**: Streamlit Cloud → `main` 브랜치 추적
