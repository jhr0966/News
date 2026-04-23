"""Insight board: scraper 가 뽑은 article dict 리스트에서 집계·트렌드·랭킹을 뽑는다.

- 입력은 `scraper.search_naver_news` / `fetch_latest_tech_news` 가 반환하는
  **rename 전** article dict 리스트 (key: title/press/date/link/keywords/...).
- `articles_to_dataframe()` 의 한국어 컬럼 DataFrame 과 혼동하지 말 것.
- 출력은 Streamlit 바로 렌더 가능한 pd.DataFrame.

docs/ARCHITECTURE.md 의 모듈 계약을 따른다.
"""
from __future__ import annotations

from collections import Counter

import pandas as pd


_KEYWORD_SPLIT = ","


def _as_df(articles: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(articles) if articles else pd.DataFrame()


def _explode_keywords(df: pd.DataFrame) -> pd.Series:
    if "keywords" not in df.columns or df.empty:
        return pd.Series(dtype=str)
    series = (
        df["keywords"].fillna("").astype(str)
        .str.split(_KEYWORD_SPLIT).explode().str.strip()
    )
    return series[series.ne("")]


def by_press(articles: list[dict]) -> pd.DataFrame:
    """언론사별 기사 수. 컬럼: press, count."""
    df = _as_df(articles)
    if df.empty or "press" not in df.columns:
        return pd.DataFrame(columns=["press", "count"])
    return (
        df.groupby("press", dropna=False).size()
        .reset_index(name="count")
        .sort_values("count", ascending=False, ignore_index=True)
    )


def by_keyword(articles: list[dict], top_n: int = 30) -> pd.DataFrame:
    """전체 기사 키워드 빈도. 컬럼: keyword, count."""
    df = _as_df(articles)
    kws = _explode_keywords(df)
    if kws.empty:
        return pd.DataFrame(columns=["keyword", "count"])
    return pd.DataFrame(Counter(kws.tolist()).most_common(top_n),
                        columns=["keyword", "count"])


def trend_by_date(articles: list[dict]) -> pd.DataFrame:
    """일자별 기사 수. 컬럼: date, count. (date 파싱 실패는 제외)"""
    df = _as_df(articles)
    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "count"])
    dates = pd.to_datetime(df["date"], errors="coerce").dt.date.dropna()
    if dates.empty:
        return pd.DataFrame(columns=["date", "count"])
    out = dates.value_counts().sort_index().reset_index()
    out.columns = ["date", "count"]
    return out


def related_articles(articles: list[dict], keyword: str) -> list[dict]:
    """키워드를 title 또는 keywords 에 포함한 article 만 필터링."""
    if not articles or not keyword:
        return []
    kw = keyword.lower()
    out = []
    for a in articles:
        haystack = f"{a.get('title','')}\t{a.get('keywords','')}".lower()
        if kw in haystack:
            out.append(a)
    return out
