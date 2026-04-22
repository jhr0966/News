"""Insight board: scraper 결과 DataFrame에서 집계·트렌드·랭킹을 뽑는다.

docs/ARCHITECTURE.md 의 모듈 계약을 따른다.
입력은 항상 scraper.articles_to_dataframe() 결과.
출력은 항상 pd.DataFrame (Streamlit 에서 st.dataframe / st.bar_chart 로 바로 렌더).
"""
from __future__ import annotations

from collections import Counter

import pandas as pd


_KEYWORD_SPLIT = ","


def _explode_keywords(df: pd.DataFrame) -> pd.Series:
    """'keywords' 컬럼(comma-separated)을 펼쳐 개별 키워드 Series로."""
    if "keywords" not in df.columns or df.empty:
        return pd.Series(dtype=str)
    series = (
        df["keywords"]
        .fillna("")
        .astype(str)
        .str.split(_KEYWORD_SPLIT)
        .explode()
        .str.strip()
    )
    return series[series.ne("")]


def by_press(df: pd.DataFrame) -> pd.DataFrame:
    """언론사별 기사 수. 컬럼: press, count."""
    if df.empty or "press" not in df.columns:
        return pd.DataFrame(columns=["press", "count"])
    out = (
        df.groupby("press", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False, ignore_index=True)
    )
    return out


def by_keyword(df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    """전체 기사의 키워드 빈도. 컬럼: keyword, count."""
    kws = _explode_keywords(df)
    if kws.empty:
        return pd.DataFrame(columns=["keyword", "count"])
    counts = Counter(kws.tolist()).most_common(top_n)
    return pd.DataFrame(counts, columns=["keyword", "count"])


def trend_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """일자별 기사 수. 컬럼: date, count. (date 파싱 실패는 제외)"""
    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "count"])
    dates = pd.to_datetime(df["date"], errors="coerce").dt.date
    dates = dates.dropna()
    if dates.empty:
        return pd.DataFrame(columns=["date", "count"])
    out = (
        dates.value_counts()
        .sort_index()
        .reset_index()
    )
    out.columns = ["date", "count"]
    return out


def related_articles(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """주어진 키워드를 포함한 기사만 필터링."""
    if df.empty or not keyword:
        return df.iloc[0:0]
    mask = df.get("keywords", pd.Series([""] * len(df))).fillna("").str.contains(
        keyword, case=False, regex=False
    )
    title_mask = df.get("title", pd.Series([""] * len(df))).fillna("").str.contains(
        keyword, case=False, regex=False
    )
    return df[mask | title_mask].reset_index(drop=True)
