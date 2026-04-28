"""작업-뉴스 매칭 기반 자동화 과제 제안 엔진 (Rule-based v1)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd


_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]{2,}")
_STOPWORDS = {"작업", "공정", "및", "에서", "으로", "대한", "관련", "기술", "자동화"}


def _tokens(text: str) -> list[str]:
    words = _TOKEN_RE.findall((text or "").lower())
    return [w for w in words if w not in _STOPWORDS]


def score_article_for_task(task: dict[str, Any], article: dict[str, Any]) -> tuple[float, list[str]]:
    """단순 토큰 중첩 기반 점수."""
    task_text = " ".join(
        [
            str(task.get("task_name", "")),
            str(task.get("description", "")),
            str(task.get("process", "")),
        ]
    )
    art_text = " ".join(
        [
            str(article.get("title", "")),
            str(article.get("summary", "")),
            str(article.get("content", "")),
            str(article.get("keywords", "")),
        ]
    )

    task_tokens = _tokens(task_text)
    art_tokens = _tokens(art_text)
    if not task_tokens or not art_tokens:
        return 0.0, []

    task_counter = Counter(task_tokens)
    art_counter = Counter(art_tokens)
    overlap = sorted(set(task_counter) & set(art_counter))
    if not overlap:
        return 0.0, []

    overlap_strength = sum(min(task_counter[t], art_counter[t]) for t in overlap)
    score = overlap_strength / max(1, len(set(task_tokens)))
    return round(float(score), 4), overlap[:5]


def suggest_for_tasks(
    tasks_df: pd.DataFrame,
    articles: list[dict[str, Any]],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """작업별 추천 기사 top_k와 제안 초안 생성."""
    if tasks_df.empty or not articles:
        return []

    results: list[dict[str, Any]] = []
    for _, row in tasks_df.iterrows():
        task = row.to_dict()
        scored = []
        for art in articles:
            score, overlaps = score_article_for_task(task, art)
            if score <= 0:
                continue
            scored.append(
                {
                    "score": score,
                    "overlap_terms": overlaps,
                    "title": art.get("title", ""),
                    "press": art.get("press", ""),
                    "link": art.get("link", ""),
                    "summary": art.get("summary", ""),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:top_k]

        results.append(
            {
                "task_id": task.get("task_id", ""),
                "task_name": task.get("task_name", ""),
                "process": task.get("process", ""),
                "recommendation_count": len(top),
                "recommendations": top,
            }
        )
    return results


def proposals_to_markdown(proposals: list[dict[str, Any]]) -> str:
    lines = ["# 자동화 과제 제안 결과", ""]
    for p in proposals:
        lines.append(f"## {p.get('task_id', '')} · {p.get('task_name', '')} ({p.get('process', '')})")
        recs = p.get("recommendations", [])
        if not recs:
            lines.append("- 추천 기사 없음")
            lines.append("")
            continue
        for i, rec in enumerate(recs, start=1):
            lines.append(
                f"- {i}. {rec.get('title', '')} "
                f"(score={rec.get('score', 0)}, overlap={', '.join(rec.get('overlap_terms', []))})"
            )
            if rec.get("link"):
                lines.append(f"  - source: {rec['link']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def save_proposals_artifacts(
    proposals: list[dict[str, Any]],
    data_root: str | Path = "data",
) -> dict[str, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    out_dir = Path(data_root) / "artifacts" / "proposals" / now.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"proposals_{stamp}.json"
    md_path = out_dir / f"proposals_{stamp}.md"

    json_path.write_text(json.dumps(proposals, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(proposals_to_markdown(proposals), encoding="utf-8")

    return {"json": str(json_path), "markdown": str(md_path)}
