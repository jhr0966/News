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

**공통 article dict 스키마:**
```python
{
    "title": str,          # HTML escape 완료
    "url": str,            # 정규화된 절대 URL
    "press": str,          # 언론사/사이트명
    "date": str,           # "YYYY-MM-DD" 또는 ""
    "thumbnail": str,      # 이미지 URL (없으면 "")
    "summary": str,        # 리스트 페이지의 요약
    "content": str,        # enrich 후 채워짐, 없으면 ""
    "keywords": str,       # extract_keywords 결과, comma-separated
}
```

**내부 규약:**
- 모든 HTTP는 `_build_session()`을 통해. 직접 `requests.get` 금지.
- 파서는 `_soup()` 경유 (lxml fallback → html.parser).
- 기사 URL은 `_is_plausible_article_link` + `_same_root_domain` 양쪽 통과 필수.

### insights.py — 집계 계층

**공개 함수:**
- `by_press(df) -> pd.DataFrame` — 언론사별 기사 수·키워드 상위.
- `by_keyword(df, top_n) -> pd.DataFrame` — 전체 키워드 빈도.
- `trend_by_date(df) -> pd.DataFrame` — 일자별 기사 수.
- `related_articles(df, keyword) -> pd.DataFrame` — 키워드 필터링.

**입력:** `articles_to_dataframe`의 결과 DataFrame.
**출력:** 항상 `pd.DataFrame` (Streamlit에서 `st.dataframe`/`st.bar_chart`로 바로 렌더).

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
