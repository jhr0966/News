# ARCHITECTURE — News

> 모듈 경계와 데이터 플로우. 새 기능 추가 전 이 문서로 "어디에 들어갈 코드인가" 확정.

## 개요

단일 Streamlit 앱. `app.py`는 평탄 스크립트, 비즈니스 로직은 세 도메인 모듈로 분리:

```
┌──────────────────────────────────────────────────────────────┐
│                         app.py                                │
│  (Streamlit 평탄 스크립트: 페이지·탭·세션 상태·이벤트 디스패치)   │
└──────┬──────────────────┬──────────────────────┬─────────────┘
       │                  │                      │
       ▼                  ▼                      ▼
 ┌──────────┐       ┌───────────┐          ┌────────────┐
 │scraper.py│  ───► │insights.py│  ─────►  │cardnews.py │
 │ (수집)    │       │ (집계)     │          │ (렌더/export)│
 └──────────┘       └───────────┘          └────────────┘
       │                  │                      │
       ▼                  ▼                      ▼
  외부 HTTP           pandas DataFrame       PNG / HTML 카드
```

데이터 흐름은 **단방향**: `scraper → insights → cardnews`.
역방향 import는 금지 (insights가 scraper를 쓰는 것은 OK, 그 반대는 불가).

## 모듈 계약

### scraper.py — 수집 계층

**공개 함수 (외부 진입점):**
- `search_naver_news(keyword, max_results, debug) -> list[dict]`
- `fetch_latest_tech_news(site_name, site_url, max_results, debug) -> list[dict]`
- `enrich_articles_parallel(articles, progress_cb, max_workers) -> list[dict]`
- `articles_to_dataframe(articles) -> pd.DataFrame`
- `extract_keywords(text, top_n) -> str`

**공통 article dict 스키마** (scraper 가 실제로 사용하는 키):
```python
{
    "title":   str,        # HTML escape 완료
    "link":    str,        # 정규화된 절대 URL (주의: 'url' 아님)
    "press":   str,        # 언론사/사이트명
    "date":    str,        # "YYYY-MM-DD" 또는 "" (사이트 모드는 "최신 동향")
    "img_url": str,        # 이미지 URL (없으면 "") (주의: 'thumbnail' 아님)
    "summary": str,        # 리스트 페이지의 요약
    "content": str,        # enrich 후 채워짐, 없으면 ""
    "keywords": str,       # extract_keywords 결과, comma-separated
}
```

> ⚠️ `articles_to_dataframe()` 는 export 용으로 컬럼을 한국어로 rename 한다
> (`title→제목`, `link→링크`, `img_url→이미지URL` 등).
> **집계·분석은 rename 전 dict 리스트**로 해야 한다 — `insights.*` 함수는 list[dict] 를 받는다.

**내부 규약:**
- 모든 HTTP는 `_build_session()`을 통해. 직접 `requests.get` 금지.
- 파서는 `_soup()` 경유 (lxml fallback → html.parser).
- 기사 URL은 `_is_plausible_article_link` + `_same_root_domain` 양쪽 통과 필수.

### insights.py — 집계 계층

**공개 함수:**
- `by_press(articles) -> pd.DataFrame` — 언론사별 기사 수. 컬럼: `press, count`.
- `by_keyword(articles, top_n) -> pd.DataFrame` — 키워드 빈도. 컬럼: `keyword, count`.
- `trend_by_date(articles) -> pd.DataFrame` — 일자별 기사 수. 컬럼: `date, count`.
- `related_articles(articles, keyword) -> list[dict]` — 키워드 필터링 (입력과 동일 형태).

**입력:** `list[dict]` — scraper 가 반환하는 rename 전 article 리스트.
**출력:** 집계 결과는 `pd.DataFrame` (Streamlit `st.dataframe`/`st.bar_chart` 로 바로 렌더).
`related_articles` 만 list[dict] (다시 카드/테이블 렌더링에 넘기기 위함).

### cardnews.py — 렌더 계층

**공개 함수:**
- `render_html(article, template="default") -> str` — 카드 1장 HTML.
- `render_png(article, template="default", size=(1080, 1080)) -> bytes` — 이미지(Pillow).
- `render_deck(articles, template="default") -> list[bytes]` — 다수 카드 일괄.
- `available_templates() -> list[str]`

**템플릿 위치:** `components/cardnews_template/<template>.html` + `assets/styles.css`의 `.cn-*` 클래스.

**제약:**
- 이미지 합성은 `render_png`가 유일 진입점. 폰트 경로·여백 상수는 모듈 상단에 하나만.
- HTML 출력은 반드시 `html.escape`로 safe (외부 문자열 직접 format 금지).

## app.py 구조

```
1. import / page_config
2. 전역 CSS 로드 (assets/styles.css)
3. 세션 상태 초기화 (sc_*, ins_*, cn_*)
4. Pending flag 처리 (_search_pending, _enrich_pending, ...)  ← 최상단에서만 state 쓰기
5. 사이드바 (모드 선택: 스크래핑 | 인사이트 | 카드뉴스)
6. 메인 영역 (모드별 분기, 평탄 if/elif)
7. 푸터/디버그
```

## 세션 상태 키

| prefix | 도메인 |
|---|---|
| `sc_*` | 스크래핑 결과·검색어·디버그 로그 |
| `ins_*` | 인사이트 필터·선택된 차트 |
| `cn_*` | 카드뉴스 선택된 기사·템플릿·미리보기 |
| `_*_pending` | 다음 run 최상단에서 처리할 이벤트 |

## 외부 의존성

`requirements.txt`:
- `streamlit` — UI
- `requests` — HTTP
- `beautifulsoup4`, `lxml` — 파싱 (lxml 실패 시 html.parser)
- `pandas` — DataFrame
- `Pillow` (예정) — `cardnews.render_png`용

## 배포

Streamlit Cloud가 `main` 브랜치를 트래킹. `main` 머지 = 즉시 배포.
따라서 작업 브랜치에서 **Streamlit Cloud 미리보기 또는 로컬 `streamlit run app.py`**로 검증 후 머지.
