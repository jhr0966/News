from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_helpers import (
    add_candidate_if_new,
    build_cardnews_candidate_from_recommendation,
    build_candidates_dataframe,
    import_candidates_from_proposal_json,
)


def test_build_candidate_and_add_dedup() -> None:
    rec = {"title": "A", "press": "X", "summary": "S", "overlap_terms": ["용접"], "link": "https://a"}
    candidate = build_cardnews_candidate_from_recommendation(rec)
    candidates: list[dict] = []
    assert add_candidate_if_new(candidates, candidate) is True
    assert add_candidate_if_new(candidates, candidate) is False
    assert len(candidates) == 1


def test_import_candidates_from_json(tmp_path: Path) -> None:
    payload = [
        {"recommendations": [{"title": "A", "link": "https://a", "overlap_terms": ["x"]}]},
        {"recommendations": [{"title": "B", "link": "https://b", "overlap_terms": ["y"]}]},
    ]
    p = tmp_path / "proposals.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    candidates: list[dict] = []
    added = import_candidates_from_proposal_json(p, candidates)
    assert added == 2
    df = build_candidates_dataframe(candidates)
    assert list(df.columns) == ["번호", "제목", "출처", "발행일", "썸네일URL", "링크"]
