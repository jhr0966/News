"""Local-first 저장소 유틸리티.

Phase 1(MVP)에서는 뉴스 데이터를 로컬 파일(JSONL/Parquet)에 저장한다.
후속 Phase에서는 NewsRepository 인터페이스를 DB 구현체로 교체할 수 있다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd


class NewsRepository(ABC):
    """뉴스 저장소 인터페이스."""

    @abstractmethod
    def save_articles_batch(
        self,
        source: str,
        articles: list[dict[str, Any]],
        keyword: str = "",
    ) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def load_latest_articles(self, source: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class LocalNewsRepository(NewsRepository):
    """로컬 파일(JSONL/Parquet) 기반 뉴스 저장소."""

    def __init__(self, data_root: str | Path = "data") -> None:
        self.data_root = Path(data_root)
        self.raw_news_dir = self.data_root / "raw" / "news"
        self.processed_news_dir = self.data_root / "processed" / "news"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc).replace(microsecond=0)

    @staticmethod
    def _safe_slug(text: str, fallback: str = "batch") -> str:
        clean = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (text or ""))
        clean = clean.strip("_")
        return (clean[:40] or fallback).lower()

    @staticmethod
    def _dated_dir(base: Path, when: datetime) -> Path:
        path = base / when.strftime("%Y-%m-%d")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_articles_batch(
        self,
        source: str,
        articles: list[dict[str, Any]],
        keyword: str = "",
    ) -> dict[str, str]:
        if not articles:
            return {}

        now = self._utc_now()
        stamp = now.strftime("%Y%m%d_%H%M%S")
        source_slug = self._safe_slug(source, "news")
        base_name = f"{source_slug}_{stamp}"

        raw_dir = self._dated_dir(self.raw_news_dir, now)
        processed_dir = self._dated_dir(self.processed_news_dir, now)

        raw_path = raw_dir / f"{base_name}.jsonl"
        processed_path = processed_dir / f"{base_name}.parquet"

        rows: list[dict[str, Any]] = []
        with raw_path.open("w", encoding="utf-8") as f:
            for art in articles:
                row = dict(art)
                row.setdefault("collected_at", now.isoformat())
                row.setdefault("source_batch", source)
                row.setdefault("query_keyword", keyword)
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                rows.append(row)

        pd.DataFrame(rows).to_parquet(processed_path, index=False)

        return {"raw": str(raw_path), "processed": str(processed_path)}

    def load_latest_articles(self, source: str) -> list[dict[str, Any]]:
        source_slug = self._safe_slug(source, "news")
        if not self.processed_news_dir.exists():
            return []

        candidates = sorted(
            self.processed_news_dir.glob(f"*/{source_slug}_*.parquet"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return []

        df = pd.read_parquet(candidates[0])
        return df.to_dict(orient="records")

_DEFAULT_REPO = LocalNewsRepository()


def save_articles_batch(source: str, articles: list[dict[str, Any]], keyword: str = "") -> dict[str, str]:
    """기사 리스트를 raw(jsonl) + processed(parquet)로 저장."""
    return _DEFAULT_REPO.save_articles_batch(source=source, articles=articles, keyword=keyword)


def load_latest_articles(source: str) -> list[dict[str, Any]]:
    """source prefix 기준 최신 parquet 파일을 읽어 기사 리스트로 반환."""
    return _DEFAULT_REPO.load_latest_articles(source=source)
