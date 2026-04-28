"""app.py에서 재사용하는 순수 유틸리티 함수 모음."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_cardnews_candidate_from_recommendation(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": rec.get("title", ""),
        "press": rec.get("press", ""),
        "summary": rec.get("summary", ""),
        "content": rec.get("summary", ""),
        "keywords": ", ".join(rec.get("overlap_terms", [])),
        "link": rec.get("link", ""),
        "date": rec.get("date", "추천"),
        "published_at": rec.get("published_at", ""),
        "img_url": rec.get("img_url", ""),
    }


def add_candidate_if_new(candidates: list[dict[str, Any]], candidate: dict[str, Any]) -> bool:
    exists = any(
        c.get("link") == candidate.get("link") and c.get("title") == candidate.get("title")
        for c in candidates
    )
    if exists:
        return False
    candidates.append(candidate)
    return True


def import_candidates_from_proposal_json(path: Path, candidates: list[dict[str, Any]]) -> int:
    if not path.exists():
        return 0
    loaded = json.loads(path.read_text(encoding="utf-8"))
    added = 0
    for proposal in loaded:
        for rec in proposal.get("recommendations", []):
            candidate = build_cardnews_candidate_from_recommendation(rec)
            if add_candidate_if_new(candidates, candidate):
                added += 1
    return added


def build_candidates_dataframe(candidates: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "번호": i + 1,
                "제목": c.get("title", ""),
                "출처": c.get("press", ""),
                "발행일": c.get("date", ""),
                "썸네일URL": c.get("img_url", ""),
                "링크": c.get("link", ""),
            }
            for i, c in enumerate(candidates)
        ]
    )
